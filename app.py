# --- Configuración de librerías y entorno para uso sin GUI ---
import matplotlib
matplotlib.use('Agg')  # Permite generar gráficos sin necesidad de mostrar una ventana (útil en servidores)
import matplotlib.pyplot as plt
import numpy as np
import os
import json
from datetime import datetime

# --- Flask y componentes de aplicación web ---
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

# --- Funciones del juego (lógica central separada) ---
from juego_ia import buscar_jugada, inicializar_tablero, revisar_ganador, reiniciar_indice, indice_actual

# --- Base de datos con SQLAlchemy ---
from flask import Flask                
from flask_sqlalchemy import SQLAlchemy
# from db_handler import create_connection  # Puedes mantener esto si lo usas en otro lado

# --- Inicialización de Flask y configuración de base de datos ---
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///evaluaciones.db'  # Base de datos SQLite local
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Desactiva el seguimiento de cambios para eficiencia

db = SQLAlchemy()
db.init_app(app)
    
# --- Modelo de datos SQLAlchemy para evaluaciones ---
class Evaluacion(db.Model):
    __tablename__ = 'evaluacion'
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.String(50), nullable=False)
    jugador = db.Column(db.String(50), nullable=False)
    modelo = db.Column(db.String(50), nullable=False)
    movimiento = db.Column(db.Text, nullable=False)
    evaluacion_automatica = db.Column(db.Text, nullable=False)
    evaluacion_humana = db.Column(db.Text, nullable=True)
    razon_automatica = db.Column(db.Text, nullable=True)
    razon_humana = db.Column(db.Text, nullable=True)

# Crear todas las tablas si no existen
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)

# --- Rúbrica de evaluación automática: debe coincidir con la del frontend JS ---
DIMENSIONES = [
    "Comprensión de Reglas",
    "Validez y Legalidad",
    "Razonamiento Estratégico",
    "Factualidad",
    "Coherencia Explicativa",
    "Claridad Lingüística",
    "Adaptabilidad"
]

# --- Clave secreta para gestionar sesiones de usuario ---
app.secret_key = os.urandom(24)

# --- Variables globales para el estado del juego (simples mientras no haya múltiples sesiones simultáneas) ---
tablero = inicializar_tablero()
turno_actual = "x"
turno_numero = 1
historial = []

# --- Rutas principales del servidor Flask ---

@app.route("/")
def index():
    # Renderiza la página principal del juego con el tablero vacío
    tablero_vacio = [["" for _ in range(3)] for _ in range(3)]
    return render_template("index.html", tablero=tablero_vacio)

@app.route("/contador_partidas", methods=["GET"])
def contador_partidas():
    # Devuelve el índice actual de partidas como contador
    return jsonify({"partidas": indice_actual})

@app.route("/estado", methods=["GET"])
def estado():
    # Devuelve el estado actual del tablero y el jugador en turno
    return jsonify({"tablero": tablero, "turno": turno_actual})

@app.route("/info_jugada_sesion", methods=["GET"])
def info_jugada_sesion():
    # Devuelve información de la última jugada guardada en la sesión
    jugador = session.get("turno_actual", "desconocido").upper()
    modelo = session.get("modelo", "desconocido")
    movimiento = session.get("movimiento", [])
    return jsonify({
        "jugador": jugador,
        "modelo": modelo,
        "movimiento": movimiento
    })

@app.route("/reiniciar", methods=["POST"])
def reiniciar():
    # Reinicia el estado global del juego (tablero, turno, historial)
    global tablero, turno_actual, turno_numero, historial
    tablero = inicializar_tablero()
    turno_actual = "x"
    turno_numero = 1
    historial = []
    reiniciar_indice()
    return jsonify({"estado": "reiniciado"})

@app.route("/jugar_turno", methods=["POST"])
def jugar_turno():
    # Ejecuta una jugada del modelo IA y evalúa automáticamente
    global tablero, turno_actual, turno_numero, historial

    movimiento, razon, modelo = buscar_jugada(tablero, turno_actual)
    
    try:
        fila = int(movimiento[1]) - 1
        col = int(movimiento[2]) - 1
    except (IndexError, ValueError):
        return jsonify({"error": "Movimiento inválido.", "tablero": tablero})

    if not (0 <= fila < 3 and 0 <= col < 3):
        return jsonify({"error": "Coordenadas fuera de rango.", "tablero": tablero})

    if tablero[fila][col] == "b":
        tablero[fila][col] = turno_actual
        ganador = revisar_ganador(tablero)

        jugada = {
            "jugador": turno_actual,
            "movimiento": movimiento,
            "razon": razon,
            "modelo": modelo,
            "ganador": ganador,
            "tablero": [row[:] for row in tablero],
            "evaluada": False,
            "match_id": turno_numero
        }

        # Evaluación automática según la rúbrica definida
        jugada["evaluacion"] = evaluar_jugada_rubrica(jugada)

        historial.append(jugada)
        guardar_jugada_en_archivo(jugada)

        # Actualiza el archivo global de jugadas
        jugadas = cargar_jugadas_desde_archivo()
        jugadas.append(jugada)
        guardar_jugadas_en_archivo(jugadas)

        # Actualiza sesión con la jugada actual
        session["tablero"] = tablero
        session["turno_actual"] = turno_actual
        session["movimiento"] = movimiento
        session["razon"] = razon
        session["modelo"] = modelo

        # Guarda una imagen PNG del tablero para revisión visual
        guardar_imagen_tablero(tablero, turno_numero)
        turno_numero += 1

        if not ganador:
            # Alterna turno entre "x" y "o"
            turno_actual = "o" if turno_actual == "x" else "x"

        return jsonify(jugada)
    else:
        # Jugada ilegal detectada (casilla ya ocupada)
        return jsonify({
            "error": f"Jugada ilegal detectada por el modelo ({turno_actual}). Movimiento: {movimiento}",
            "tablero": tablero
        })


@app.route("/siguiente_partida", methods=["POST"])
def siguiente_partida():
    global tablero, turno_actual, turno_numero, historial, indice_actual

    # Incrementa el índice global de partidas para llevar la cuenta
    indice_actual += 1
    
    # Reinicia el tablero vacío para una nueva partida
    tablero = inicializar_tablero()
    
    # Reinicia el jugador actual al que le toca (X empieza)
    turno_actual = "x"
    
    # Reinicia el número de turno (movimiento)
    turno_numero = 1
    
    # Limpia el historial de movimientos para la nueva partida
    historial = []

    # Devuelve confirmación en formato JSON
    return jsonify({"ok": True, "mensaje": "Partida reiniciada y siguiente jugada preparada."})


@app.route("/verificar", methods=["GET"])
def verificar():
    # Crea una matriz 3x3 vacía para reconstruir el tablero desde el historial
    reconstruido = [["b"] * 3 for _ in range(3)]
    
    # Recorre el historial de jugadas para reconstruir el tablero paso a paso
    for jugada in historial:
        jugador = jugada.get("jugador")
        movimiento = jugada.get("movimiento")
        if not movimiento or len(movimiento) < 3:
            continue
        try:
            fila = int(movimiento[1]) - 1  # Convierte a índice de matriz (0-based)
            col = int(movimiento[2]) - 1
            reconstruido[fila][col] = jugador  # Marca la posición con el jugador correspondiente
        except (IndexError, ValueError):
            # Si el movimiento está mal formado, lo ignora y sigue
            continue

    # Compara el tablero reconstruido con el estado global actual para verificar consistencia
    coincide = reconstruido == tablero
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Crea carpeta para guardar resultados de verificación si no existe
    if not os.path.exists("verificaciones"):
        os.makedirs("verificaciones")

    resultado = {
        "fecha": ahora,
        "tablero_actual": tablero,
        "reconstruido_desde_historial": reconstruido,
        "coincide": coincide  # True si ambos tableros son idénticos
    }

    # Guarda resultado en archivo JSON para auditoría/debug
    with open("verificaciones/comparacion_tablero.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=4, ensure_ascii=False)

    # Devuelve resultado de la verificación en JSON
    return jsonify(resultado)


### FUNCIONES AUXILIARES ###

def guardar_jugada_en_archivo(jugada):
    # Guarda un registro legible de la jugada con fecha y detalles en un archivo de texto
    ruta = "historial_jugadas.txt"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ruta, "a", encoding="utf-8") as f:
        f.write(f"[{now}] Jugador: {jugada['jugador'].upper()}, "
                f"Movimiento: {jugada['movimiento']}, "
                f"Razón: {jugada['razon']}, "
                f"Ganador: {jugada['ganador']}\n")


def guardar_imagen_tablero(tablero, turno):
    # Guarda una imagen PNG visual del tablero con matplotlib, resaltando las marcas de los jugadores
    if not os.path.exists("tableros"):
        os.makedirs("tableros")

    fig, ax = plt.subplots(figsize=(3, 3))
    ax.set_xticks(np.arange(3))
    ax.set_yticks(np.arange(3))
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.grid(True)  # Dibuja la cuadrícula del tablero

    for i in range(3):
        for j in range(3):
            cell = tablero[i][j]
            if cell != "b":  # "b" es celda vacía
                ax.text(j, 2 - i, cell.upper(), ha="center", va="center", fontsize=28,
                        color="#e74c3c" if cell == "x" else "#2980b9")  # Rojo para X, azul para O

    plt.tight_layout()
    nombre = f"tableros/turno_{turno:02d}.png"
    plt.savefig(nombre)  # Guarda imagen en carpeta tableros
    plt.close()


def evaluar_jugada_rubrica(jugada):
    # Evalúa automáticamente la jugada con base en la explicación (razón) usando palabras clave
    razon = str(jugada.get("razon", "")).lower()
    return {
        "Comprensión de Reglas": 3 if "legal" in razon or "válido" in razon else 2,
        "Validez y Legalidad": 3 if "válido" in razon else 2,
        "Razonamiento Estratégico": 3 if "bloquear" in razon or "ganar" in razon else 2,
        "Factualidad": 3 if "tablero" in razon or "posición" in razon else 2,
        "Coherencia Explicativa": 3 if "porque" in razon or "ya que" in razon else 2,
        "Claridad Lingüística": 3 if len(razon) > 15 else 2,
        "Adaptabilidad": 3 if "respuesta" in razon or "ajusté" in razon else 2
    }


def cargar_jugadas_desde_archivo():
    # Carga lista de jugadas desde archivo JSON si existe
    if os.path.exists("jugadas.json"):
        with open("jugadas.json", "r") as f:
            return json.load(f)
    return []


def guardar_jugadas_en_archivo(jugadas):
    # Guarda la lista completa de jugadas en formato JSON indentado para fácil lectura
    with open("jugadas.json", "w") as f:
        json.dump(jugadas, f, indent=2)


def cargar_evaluaciones_desde_archivo():
    # Lee evaluaciones línea por línea desde archivo JSON (cada línea un JSON independiente)
    evaluaciones = []
    try:
        with open("evaluaciones.json", "r", encoding="utf-8") as f:
            for linea in f:
                ev = json.loads(linea)  # Convierte JSON string a dict
                print(type(ev))  # Debug: debe ser dict
                evaluaciones.append(ev)
    except FileNotFoundError:
        # Si no existe el archivo, devuelve lista vacía
        pass
    return evaluaciones


def guardar_evaluacion_en_archivo(evaluacion):
    # Carga evaluaciones previas, añade la nueva y guarda todo el conjunto
    evaluaciones = cargar_evaluaciones_desde_archivo()
    evaluaciones.append(evaluacion)
    with open("evaluaciones.json", "w", encoding="utf-8") as f:
        json.dump(evaluaciones, f, indent=2, ensure_ascii=False)


def guardar_evaluaciones_completas(match_id, jugadas):
    # Para una partida específica (match_id), guarda todas las evaluaciones (inicializando si no hay)
    evaluaciones = [j for j in jugadas if j.get("match_id") == match_id]
    dimensiones = [
        "Comprensión de Reglas", "Validez y Legalidad", "Razonamiento Estratégico",
        "Factualidad", "Coherencia Explicativa", "Claridad Lingüística", "Adaptabilidad"
    ]
    
    for ev in evaluaciones:
        if not ev.get("evaluada", False):
            # Si no está evaluada, inicializa evaluación vacía con ceros y razón por defecto
            ev["evaluacion"] = {dim: 0 for dim in dimensiones}
            ev["razon"] = "No evaluada por el usuario"
            ev["evaluada"] = False  # Marca explícitamente como no evaluada

    # Guarda en modo append cada evaluación como JSON en archivo
    with open("evaluaciones.json", "a", encoding="utf-8") as f:
        for ev in evaluaciones:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")


def obtener_jugadas():
    # Accede a la base de datos SQLite para obtener todas las jugadas almacenadas
    conn = create_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM jugadas')
    jugadas = c.fetchall()
    conn.close()
    return jugadas

def insertar_evaluacion_bd(match_id, movimiento, evaluacion, razon, jugador, modelo):
    # Convierte la jugada y evaluación a formato JSON string para almacenamiento
    movimiento_json = json.dumps(movimiento)
    evaluacion_json = json.dumps(evaluacion)

    # Busca si ya existe una evaluación para la misma jugada, partida y jugador
    existente = Evaluacion.query.filter_by(match_id=match_id, movimiento=movimiento_json, jugador=jugador).first()
    if existente:
        # Si existe, actualiza los campos relevantes
        existente.evaluacion = evaluacion_json
        existente.razon = razon
        existente.modelo = modelo
        # No se cambia el id porque es clave primaria autoincremental
        existente.id = existente.id  
    else:
        # Si no existe, crea una nueva evaluación y la agrega a la sesión
        nueva_eval = Evaluacion(
            match_id=str(match_id),
            jugador=jugador,
            modelo=modelo,
            movimiento=movimiento_json,
            evaluacion_automatica=evaluacion_json,
            razon_automatica=razon                  
        )
        db.session.add(nueva_eval)
    # Confirma los cambios en la base de datos
    db.session.commit()


# Modelo de base de datos para almacenar jugadas
class Jugada(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.String(50), nullable=False)  # ID de la partida
    jugador = db.Column(db.String(50), nullable=False)   # Jugador que hizo la jugada
    modelo = db.Column(db.String(50), nullable=False)    # Modelo que generó la jugada
    movimiento = db.Column(db.Text, nullable=False)      # Movimiento en formato JSON string
    tablero = db.Column(db.Text, nullable=False)         # Estado del tablero en JSON string
    ganador = db.Column(db.String(10), nullable=True)    # Ganador si lo hay
    razon = db.Column(db.Text, nullable=True)             # Explicación/razón de la jugada
    evaluada = db.Column(db.Boolean, default=False)       # Indicador si la jugada fue evaluada manualmente
    fecha_evaluacion = db.Column(db.String(50), nullable=True)  # Fecha de la evaluación


def insertar_jugada_bd(jugada):
    # Busca si ya existe la jugada para evitar duplicados
    existente = Jugada.query.filter_by(match_id=str(jugada['match_id']),
                                      movimiento=json.dumps(jugada['movimiento'])).first()
    if existente:
        return existente  # Si ya está, devuelve el registro existente

    # Si no existe, crea un nuevo registro con todos los datos
    nueva_jugada = Jugada(
        match_id=str(jugada['match_id']),
        jugador=jugada['jugador'],
        modelo=jugada['modelo'],
        movimiento=json.dumps(jugada['movimiento']),
        tablero=json.dumps(jugada['tablero']),
        ganador=jugada.get('ganador'),
        razon=jugada.get('razon'),
        evaluada=jugada.get('evaluada', False),
        fecha_evaluacion=jugada.get('fecha_evaluacion')
    )
    db.session.add(nueva_jugada)
    db.session.commit()
    return nueva_jugada


def cargar_jugadas_desde_bd():
    # Recupera todas las jugadas almacenadas en la base de datos y las convierte a dicts para uso en Python
    jugadas = Jugada.query.all()
    resultado = []
    for j in jugadas:
        resultado.append({
            "id": j.id,
            "match_id": int(j.match_id),
            "jugador": j.jugador,
            "modelo": j.modelo,
            "movimiento": json.loads(j.movimiento),  # convierte JSON string a lista/dict
            "tablero": json.loads(j.tablero),
            "ganador": j.ganador,
            "razon": j.razon,
            "evaluada": j.evaluada,
            "fecha_evaluacion": j.fecha_evaluacion
        })
    return resultado


def insertar_o_actualizar_evaluacion_bd(jugada):
    # Convierte los campos de jugada a JSON strings para almacenamiento
    movimiento_json = json.dumps(jugada['movimiento'])
    eval_auto_json = json.dumps(jugada.get('evaluacion_automatica', {}))
    eval_humana_json = json.dumps(jugada.get('evaluacion_humana', {})) if jugada.get('evaluacion_humana') else None

    # Razones de evaluaciones automáticas y humanas (si existen)
    razon_auto = jugada.get('razon', None) if jugada.get('evaluacion_automatica') else None
    razon_huma = jugada.get('razon_humana', None) if jugada.get('evaluacion_humana') else None

    # Busca evaluación existente para esa jugada, jugador y partida
    existente = Evaluacion.query.filter_by(
        match_id=str(jugada['match_id']),
        jugador=jugada['jugador'],
        movimiento=movimiento_json
    ).first()

    if existente:
        # Actualiza los campos si ya existe evaluación
        existente.evaluacion_automatica = eval_auto_json
        existente.evaluacion_humana = eval_humana_json
        existente.razon_automatica = razon_auto
        existente.razon_humana = razon_huma
        existente.modelo = jugada['modelo']
    else:
        # Crea nueva evaluación si no existe
        nueva_eval = Evaluacion(
            match_id=str(jugada['match_id']),
            jugador=jugada['jugador'],
            modelo=jugada['modelo'],
            movimiento=movimiento_json,
            evaluacion_automatica=eval_auto_json,
            evaluacion_humana=eval_humana_json,
            razon_automatica=razon_auto,
            razon_humana=razon_huma
        )
        db.session.add(nueva_eval)
    # Guarda cambios en la base de datos
    db.session.commit()


### RUTAS PARA EVALUACIÓN ###

@app.route("/evaluar", methods=["GET", "POST"])
def evaluar():
    # Carga todas las jugadas desde archivo JSON local
    jugadas = cargar_jugadas_desde_archivo()

    # Obtener todos los match_id únicos y ordenados
    match_ids = sorted(set(j['match_id'] for j in jugadas))
    siguiente_match_id = None
    
    # Buscar el primer match_id que tenga jugadas no evaluadas
    for mid in match_ids:
        if any(not j.get("evaluada", False) for j in jugadas if j['match_id'] == mid):
            siguiente_match_id = mid
            break

    # Si no hay jugadas pendientes para evaluar, mostrar mensaje
    if siguiente_match_id is None:
        return "No hay jugadas pendientes para evaluar."

    # Filtrar las jugadas del match actual y solo las que no están evaluadas
    jugadas_del_match = [j for j in jugadas if j['match_id'] == siguiente_match_id]
    jugadas_no_evaluadas = [j for j in jugadas_del_match if not j.get("evaluada", False)]

    # Seguridad: si no quedan jugadas no evaluadas, recargar la página
    if not jugadas_no_evaluadas:
        return redirect(url_for("evaluar"))

    # Seleccionar la primera jugada no evaluada para mostrar en el formulario
    jugada_actual = jugadas_no_evaluadas[0]

    if request.method == "POST":
        # Recoger la razón escrita por el evaluador y la rúbrica (puntuaciones)
        razon = request.form.get('razon', '')
        rubrica = {}
        for key in request.form:
            if key.startswith("rubrica[") and key.endswith("]"):
                dim = key[7:-1]  # Extraer la dimensión evaluada
                rubrica[dim] = int(request.form.get(key))

        # Guardar la evaluación en la jugada actual en memoria (lista jugadas)
        for j in jugadas:
            if j['match_id'] == jugada_actual['match_id'] and j['movimiento'] == jugada_actual['movimiento']:
                j['evaluacion'] = rubrica
                j['razon'] = razon
                j['evaluada'] = True
                break

        # Si todas las jugadas del match ya están evaluadas, guardar el archivo final
        if all(j.get("evaluada", False) for j in jugadas_del_match):
            guardar_evaluaciones_completas(siguiente_match_id, jugadas_del_match)

        # Guardar los cambios en el archivo principal
        guardar_jugadas_en_archivo(jugadas)

        # Guardar la evaluación también en la base de datos (manejo básico de errores)
        try:
            insertar_evaluacion_bd(
                match_id=jugada_actual['match_id'],
                movimiento=jugada_actual['movimiento'],
                evaluacion=rubrica,
                razon=razon,
                jugador=jugada_actual['jugador'],
                modelo=jugada_actual['modelo']
            )
        except Exception as e:
            print(f"Error guardando evaluación en BD: {e}")

        # Redirigir para evaluar la siguiente jugada pendiente
        return redirect(url_for("evaluar"))

    # Renderizar la plantilla de evaluación, pasando la jugada actual
    return render_template("evaluar.html", jugada=jugada_actual, enumerate=enumerate)


@app.route("/evaluaciones_historial")
def evaluaciones_historial():
    # Dimensiones que se evaluaron para mostrar en la página de historial
    dimensiones = [
        "Comprensión de Reglas",
        "Validez y Legalidad",
        "Razonamiento Estratégico",
        "Factualidad",
        "Coherencia Explicativa",
        "Claridad Lingüística",
        "Adaptabilidad",
    ]

    # Ejemplo de promedios para cada dimensión (puede obtenerse de BD o cálculos)
    promedios = {
        "Comprensión de Reglas": 2.5,
        "Validez y Legalidad": 2.2,
        "Razonamiento Estratégico": 1.8,
        "Factualidad": 2.7,
        "Coherencia Explicativa": 2.3,
        "Claridad Lingüística": 2.9,
        "Adaptabilidad": 2.0,
    }

    # Cargar evaluaciones desde archivo JSON
    evaluaciones = cargar_evaluaciones_desde_archivo()

    # Preparar datos para la plantilla (normalizar formatos, legibilidad)
    for ev in evaluaciones:
        ev.setdefault("evaluacion", "")
        ev.setdefault("tablero", "")
        ev.setdefault("razon", "")
        ev.setdefault("movimiento", "")
        ev.setdefault("jugador", "")
        ev.setdefault("modelo", "")
        ev.setdefault("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # Formatear movimiento para que sea legible si es tipo "mark"
        if (isinstance(ev["movimiento"], list) and len(ev["movimiento"]) >= 3
                and ev["movimiento"][0] == "mark"):
            fila = ev["movimiento"][1]
            columna = ev["movimiento"][2]
            ev["movimiento_legible"] = f"Marcar fila {fila}, columna {columna}"
        else:
            ev["movimiento_legible"] = str(ev["movimiento"])

        # Formatear texto de razón si es lista o string
        if isinstance(ev["razon"], list):
            ev["razon_texto"] = "\n".join(ev["razon"])
        elif isinstance(ev["razon"], str):
            ev["razon_texto"] = ev["razon"]
        else:
            ev["razon_texto"] = ""

        # Mantener tablero como lista si es lista (para plantilla)
        if isinstance(ev["tablero"], list):
            ev["tablero"] = ev["tablero"]

    # Renderizar la plantilla del historial con los datos procesados
    return render_template("evaluaciones_historial.html", evaluaciones=evaluaciones, dimensiones=dimensiones, promedios=promedios)


@app.route("/rubrica")
def ver_rubrica():
    # Define las dimensiones y niveles de la rúbrica para mostrar en la web
    rubrica = [
        {
            "dimension": "Comprensión de Reglas",
            "nivel1": "Viola reglas básicas: casilla ocupada o fuera del tablero.",
            "nivel2": "Cumple reglas básicas, pero omite situaciones menos evidentes.",
            "nivel3": "Siempre movimientos legales, respeta todas las reglas del turno."
        },
        {
            "dimension": "Validez y Legalidad",
            "nivel1": "Movimiento inválido o ilegal (fuera de límites).",
            "nivel2": "Movimiento válido, sin análisis profundo.",
            "nivel3": "Movimiento válido y elegido tras un análisis completo del tablero."
        },
        {
            "dimension": "Razonamiento Estratégico",
            "nivel1": "Acción sin lógica, aleatoria o contraproducente.",
            "nivel2": "Intención estratégica simple (bloquear/avanzar), sin anticipación.",
            "nivel3": "Justificación clara y anticipada, maximiza chances de ganar."
        },
        {
            "dimension": "Factualidad",
            "nivel1": "Explicación incorrecta o no relacionada con el tablero real.",
            "nivel2": "Justificación generalmente correcta, con imprecisiones menores.",
            "nivel3": "Explicación precisa, basada en hechos concretos del tablero."
        },
        {
            "dimension": "Coherencia Explicativa",
            "nivel1": "Explicación confusa o contradictoria.",
            "nivel2": "Explicación clara pero superficial.",
            "nivel3": "Explicación lógica, completa y alineada con el movimiento."
        },
        {
            "dimension": "Claridad Lingüística",
            "nivel1": "Lenguaje poco claro o con errores graves.",
            "nivel2": "Lenguaje claro con pequeños errores.",
            "nivel3": "Lenguaje preciso, gramaticalmente correcto y fácil de entender."
        },
        {
            "dimension": "Adaptabilidad",
            "nivel1": "Ignora el cambio o jugada previa del oponente.",
            "nivel2": "Se adapta de forma básica o tardía.",
            "nivel3": "Se adapta rápidamente y ajusta su estrategia eficazmente."
        }
    ]
    # Renderiza la plantilla que muestra la rúbrica completa
    return render_template("rubrica.html", rubrica=rubrica)

@app.route('/guardar_evaluacion', methods=['POST'])
def guardar_evaluacion():
    # Carga todas las jugadas guardadas en archivo JSON
    jugadas = cargar_jugadas_desde_archivo()

    # Obtener datos del formulario enviados por POST
    match_id = int(request.form.get("match_id"))
    razon = request.form.get("razon", "").strip()

    # Recuperar datos guardados en session sobre la jugada actual
    jugador = session.get("turno_actual", "desconocido")
    modelo = session.get("modelo", "desconocido")
    movimiento = session.get("movimiento", [])
    tablero_actual = session.get("tablero", [["b"]*3 for _ in range(3)])
    ganador = session.get("ganador", None)

    # Extraer evaluación (puntuaciones) de la rúbrica enviada
    rubrica = {}
    for key in request.form:
        if key.startswith("rubrica[") and key.endswith("]"):
            dim = key[7:-1]  # Extraer el nombre de la dimensión evaluada
            rubrica[dim] = int(request.form.get(key))

    # Buscar la jugada correspondiente a este match_id que aún no esté evaluada
    jugada_actual = None
    for j in jugadas:
        if j['match_id'] == match_id and not j.get("evaluada", False):
            jugada_actual = j
            break

    if jugada_actual:
        # Actualizar jugada con los datos de evaluación humana
        jugada_actual["jugador"] = jugador
        jugada_actual["modelo"] = modelo
        jugada_actual["movimiento"] = movimiento
        jugada_actual["tablero"] = tablero_actual
        jugada_actual["ganador"] = ganador
        jugada_actual["evaluacion"] = rubrica
        jugada_actual["razon"] = razon
        jugada_actual["evaluada"] = True
        jugada_actual["fecha_evaluacion"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Guardar los cambios en el archivo de jugadas (backup)
        guardar_jugadas_en_archivo(jugadas)

        # Intentar guardar evaluación en base de datos (manejo básico de errores)
        try:
            insertar_evaluacion_bd(
                match_id=jugada_actual['match_id'],
                movimiento=jugada_actual['movimiento'],
                evaluacion=rubrica,
                razon=razon,
                jugador=jugada_actual['jugador'],
                modelo=jugada_actual['modelo']
            )
        except Exception as e:
            print(f"Error guardando evaluación en BD: {e}")

    # Redirigir a página principal o a donde quieras después de guardar
    return redirect(url_for("index"))


@app.route("/siguiente_jugada", methods=["POST"])
def siguiente_jugada():
    # Simplemente redirige a la ruta evaluar para mostrar la siguiente jugada no evaluada
    return redirect(url_for("evaluar"))


# Funciones para cargar evaluaciones y calcular estadísticas para gráficos

def cargar_evaluaciones():
    # Carga evaluaciones guardadas en archivo JSON
    try:
        with open("evaluaciones.json", "r", encoding="utf-8") as f:
            evaluaciones = json.load(f)
        return evaluaciones
    except Exception:
        # En caso de error o archivo no encontrado, devolver lista vacía
        return []

def calcular_promedios(evaluaciones):
    # Inicializar acumuladores para cada dimensión de la rúbrica
    suma_por_dim = {dim: 0 for dim in DIMENSIONES}
    conteo_por_dim = {dim: 0 for dim in DIMENSIONES}

    # Recorrer cada evaluación y sumar los valores por dimensión
    for ev in evaluaciones:
        rubrica = ev.get('rubrica', {})
        for dim in DIMENSIONES:
            valor = rubrica.get(dim)
            if valor is not None:
                try:
                    v = int(valor)
                    suma_por_dim[dim] += v
                    conteo_por_dim[dim] += 1
                except ValueError:
                    # Ignorar valores no numéricos
                    pass

    # Calcular promedio para cada dimensión (0 si no hay evaluaciones)
    promedios = {}
    for dim in DIMENSIONES:
        if conteo_por_dim[dim] > 0:
            promedios[dim] = round(suma_por_dim[dim] / conteo_por_dim[dim], 2)
        else:
            promedios[dim] = 0

    return promedios


@app.route("/grafico_radar")
def grafico_radar():
    # Cargar evaluaciones guardadas
    evaluaciones = cargar_evaluaciones()
    # Calcular promedios por dimensión para graficar
    promedios = calcular_promedios(evaluaciones)
    # Renderizar plantilla enviando las dimensiones y promedios calculados
    return render_template("grafico_radar.html", dimensiones=DIMENSIONES, promedios=promedios)


if __name__ == "__main__":
    # Ejecutar la app en modo debug para desarrollo
    app.run(debug=True)
