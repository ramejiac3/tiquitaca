"""
===============================================================
app.py - Aplicación Flask para Juego de Tres en Raya con Evaluación
===============================================================

Este archivo contiene el backend principal de la aplicación, 
integrando la lógica del juego, la evaluación automática de jugadas,
la persistencia de datos en base de datos SQLite y archivos JSON, 
y la generación de estadísticas y gráficos.

FUNCIONALIDADES PRINCIPALES:
- API REST con Flask para gestionar partidas, jugadas y evaluaciones.
- Motor de IA para determinar jugadas automáticas (módulo juego_ia.py).
- Evaluación automática y humana de jugadas con una rúbrica definida.
- Almacenamiento en base de datos SQLite usando SQLAlchemy.
- Generación de reportes visuales (tableros en PNG y gráficos).
- Gestión de sesiones de usuario con Flask.

REQUISITOS:
    - Python 3.9+
    - Flask
    - Flask-SQLAlchemy
    - Matplotlib
    - NumPy

EJECUCIÓN:
    $ python app.py
    o con el comando Flask:
    $ flask --app app.py run
"""

# --- Configuración de librerías y entorno para uso sin GUI ---
import matplotlib
matplotlib.use('Agg')  # Configura matplotlib para usar backend sin interfaz gráfica, útil en servidores o scripts
import matplotlib.pyplot as plt  # Importa módulo para generación de gráficos
import numpy as np  # Importa NumPy para operaciones numéricas y matrices
import os  # Importa módulo para manejo de sistema operativo y archivos
import json  # Importa módulo para manejo de datos JSON
from datetime import datetime  # Importa clase para manejo de fechas y horas
############
from flask import Flask, request, redirect, url_for, render_template_string, send_file, session, jsonify
import sqlite3
import json
import os

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'  # Requerido para sesiones

# 👉 Credenciales básicas
USUARIO = 'admin'
CLAVE = '1234'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        clave = request.form.get('clave')
        if usuario == USUARIO and clave == CLAVE:
            session['logueado'] = True
            return redirect(url_for('descargar_json'))
        else:
            return 'Credenciales incorrectas', 401
    return render_template_string("""
        <form method="post">
            Usuario: <input name="usuario"><br>
            Clave: <input name="clave" type="password"><br>
            <input type="submit" value="Iniciar sesión">
        </form>
    """)

@app.route('/descargar-json')
def descargar_json():
    if not session.get('logueado'):
        return redirect(url_for('login'))

    db_path = 'evaluaciones.db'
    json_path = 'evaluaciones.json'

    # Extraer datos de la BD
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM evaluacion")
    filas = c.fetchall()
    conn.close()

    # Convertir a lista de diccionarios
    datos = [dict(fila) for fila in filas]

    # Guardar como archivo JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)

    # Enviar archivo como descarga
    return send_file(json_path, as_attachment=True)
############
# --- Flask y componentes de aplicación web ---
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
# Importa Flask y funciones para crear app web, manejar plantillas, solicitudes HTTP, respuestas JSON, redirecciones y sesiones

# --- Funciones del juego (lógica central separada) ---
from juego_ia import buscar_jugada, inicializar_tablero, revisar_ganador, reiniciar_indice, indice_actual
# Importa funciones clave para lógica del juego: obtener jugada IA, crear tablero, verificar ganador, reiniciar y obtener índice actual

# --- Base de datos con SQLAlchemy ---
from db_handler import create_connection  # Función para crear conexión a base de datos SQLite
from flask_sqlalchemy import SQLAlchemy  # ORM para manejar base de datos desde Flask

# --- Inicialización de Flask y configuración de base de datos ---
db = SQLAlchemy()  # Crea instancia de SQLAlchemy para manejar base de datos
app = Flask(__name__)  # Crea instancia de la aplicación Flask

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///evaluaciones.db'  # Define la ruta y tipo de base de datos SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Desactiva seguimiento de cambios para mejorar rendimiento
db.init_app(app)  # Inicializa la base de datos con la app Flask

# Crear todas las tablas definidas en modelos si no existen aún
with app.app_context():
    db.create_all()

# --- Modelo de datos SQLAlchemy para evaluaciones ---
class Evaluacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Clave primaria autoincremental
    match_id = db.Column(db.String(50), nullable=False)  # Identificador único de la partida
    jugador = db.Column(db.String(50), nullable=False)  # Nombre o identificador del jugador
    modelo = db.Column(db.String(50), nullable=False)  # Modelo de IA que generó la jugada
    movimiento = db.Column(db.Text, nullable=False)  # Movimiento realizado en formato JSON como texto
    evaluacion_automatica = db.Column(db.Text, nullable=False)  # Evaluación automática almacenada en texto JSON
    evaluacion_humana = db.Column(db.Text, nullable=True)  # Evaluación humana (opcional) en texto JSON
    razon_automatica = db.Column(db.Text, nullable=True)  # Razón o explicación de evaluación automática
    razon_humana = db.Column(db.Text, nullable=True)  # Razón o explicación de evaluación humana

# --- Rúbrica de evaluación automática: debe coincidir con la del frontend JS ---
DIMENSIONES = [
    "Comprensión de Reglas",
    "Validez y Legalidad",
    "Razonamiento Estratégico",
    "Factualidad",
    "Coherencia Explicativa",
    "Claridad Lingüística",
    "Adaptabilidad"
]  # Lista de dimensiones utilizadas para evaluar automáticamente las jugadas

# --- Clave secreta para gestionar sesiones de usuario ---
app.secret_key = os.urandom(24)  # Genera una clave secreta aleatoria para proteger sesiones en Flask

# --- Variables globales para el estado del juego (simples mientras no haya múltiples sesiones simultáneas) ---
tablero = inicializar_tablero()  # Inicializa el tablero vacío
turno_actual = "x"  # Define que el primer turno es del jugador "x"
turno_numero = 1  # Contador del número de turno o movimiento
historial = []  # Lista para almacenar el historial de jugadas

# --- Rutas principales del servidor Flask ---

@app.route("/")
def index():
    # Renderiza la página principal del juego con un tablero vacío para iniciar partida
    tablero_vacio = [["" for _ in range(3)] for _ in range(3)]  # Crea matriz 3x3 vacía
    return render_template("index.html", tablero=tablero_vacio)  # Envía tablero a plantilla HTML

@app.route("/contador_partidas", methods=["GET"])
def contador_partidas():
    # Devuelve el índice actual de partidas jugadas en formato JSON
    return jsonify({"partidas": indice_actual})

@app.route("/estado", methods=["GET"])
def estado():
    # Proporciona el estado actual del tablero y el jugador que tiene el turno
    return jsonify({"tablero": tablero, "turno": turno_actual})

@app.route("/info_jugada_sesion", methods=["GET"])
def info_jugada_sesion():
    # Retorna información de la última jugada almacenada en la sesión del usuario
    jugador = session.get("turno_actual", "desconocido").upper()  # Obtiene jugador de sesión o "desconocido"
    modelo = session.get("modelo", "desconocido")  # Obtiene modelo IA de sesión o "desconocido"
    movimiento = session.get("movimiento", [])  # Obtiene movimiento guardado o lista vacía
    return jsonify({
        "jugador": jugador,
        "modelo": modelo,
        "movimiento": movimiento
    })

@app.route("/reiniciar", methods=["POST"])
def reiniciar():
    # Reinicia el estado global del juego, incluyendo tablero, turno y historial
    global tablero, turno_actual, turno_numero, historial
    tablero = inicializar_tablero()  # Nuevo tablero vacío
    turno_actual = "x"  # Primer turno reiniciado a "x"
    turno_numero = 1  # Número de turno reiniciado
    historial = []  # Limpia historial de jugadas
    reiniciar_indice()  # Reinicia contador global de partidas
    return jsonify({"estado": "reiniciado"})  # Confirma reinicio

@app.route("/jugar_turno", methods=["POST"])
def jugar_turno():
    # Ejecuta el turno de la IA, realiza jugada, evalúa, guarda y actualiza estado
    global tablero, turno_actual, turno_numero, historial

    movimiento, razon, modelo = buscar_jugada(tablero, turno_actual)  # Obtiene jugada de IA y razón
    
    try:
        fila = int(movimiento[1]) - 1  # Convierte coordenada fila a índice 0-based
        col = int(movimiento[2]) - 1  # Convierte coordenada columna a índice 0-based
    except (IndexError, ValueError):
        # Maneja errores si formato de movimiento es inválido
        return jsonify({"error": "Movimiento inválido.", "tablero": tablero})

    if not (0 <= fila < 3 and 0 <= col < 3):
        # Verifica que las coordenadas estén dentro del tablero
        return jsonify({"error": "Coordenadas fuera de rango.", "tablero": tablero})

    if tablero[fila][col] == "b":  # Verifica que la celda esté vacía (b = blank)
        tablero[fila][col] = turno_actual  # Coloca la marca del jugador actual
        ganador = revisar_ganador(tablero)  # Comprueba si hay ganador tras movimiento

        # Construye diccionario con información completa de la jugada
        jugada = {
            "jugador": turno_actual,
            "movimiento": movimiento,
            "razon": razon,
            "modelo": modelo,
            "ganador": ganador,
            "tablero": [row[:] for row in tablero],  # Copia profunda del tablero actual
            "evaluada": False,
            "match_id": turno_numero
        }

        # Realiza evaluación automática de la jugada según rúbrica
        jugada["evaluacion"] = evaluar_jugada_rubrica(jugada)

        historial.append(jugada)  # Añade jugada al historial en memoria
        guardar_jugada_en_archivo(jugada)  # Guarda jugada en archivo de texto para registro

        # Actualiza archivo JSON global de jugadas con la nueva jugada
        jugadas = cargar_jugadas_desde_archivo()
        jugadas.append(jugada)
        guardar_jugadas_en_archivo(jugadas)

        # Actualiza la sesión con datos actuales del juego
        session["tablero"] = tablero
        session["turno_actual"] = turno_actual
        session["movimiento"] = movimiento
        session["razon"] = razon
        session["modelo"] = modelo

        guardar_imagen_tablero(tablero, turno_numero)  # Guarda imagen visual del tablero para análisis
        turno_numero += 1  # Incrementa contador de turno

        if not ganador:
            # Cambia turno entre jugadores "x" y "o"
            turno_actual = "o" if turno_actual == "x" else "x"

        return jsonify(jugada)  # Devuelve respuesta JSON con datos de la jugada
    else:
        # Maneja caso de jugada inválida si la celda ya está ocupada
        return jsonify({
            "error": f"Jugada ilegal detectada por el modelo ({turno_actual}). Movimiento: {movimiento}",
            "tablero": tablero
        })

@app.route("/siguiente_partida", methods=["POST"])
def siguiente_partida():
    global tablero, turno_actual, turno_numero, historial, indice_actual

    indice_actual += 1  # Incrementa contador global de partidas jugadas
    
    tablero = inicializar_tablero()  # Reinicia tablero vacío
    turno_actual = "x"  # Reinicia turno a jugador "x"
    turno_numero = 1  # Reinicia contador de turnos
    historial = []  # Limpia historial de jugadas

    return jsonify({"ok": True, "mensaje": "Partida reiniciada y siguiente jugada preparada."})  # Confirma reinicio

@app.route("/verificar", methods=["GET"])
def verificar():
    # Reconstruye el tablero paso a paso desde el historial para validar consistencia
    reconstruido = [["b"] * 3 for _ in range(3)]  # Inicializa tablero vacío para reconstrucción
    
    for jugada in historial:
        jugador = jugada.get("jugador")
        movimiento = jugada.get("movimiento")
        if not movimiento or len(movimiento) < 3:
            continue  # Ignora jugadas mal formadas
        try:
            fila = int(movimiento[1]) - 1  # Calcula índice fila 0-based
            col = int(movimiento[2]) - 1  # Calcula índice columna 0-based
            reconstruido[fila][col] = jugador  # Marca jugada en tablero reconstruido
        except (IndexError, ValueError):
            # Ignora errores en formato de movimiento y sigue
            continue

    coincide = reconstruido == tablero  # Compara si el tablero reconstruido coincide con el actual
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Obtiene fecha y hora actual para registro

    if not os.path.exists("verificaciones"):
        os.makedirs("verificaciones")  # Crea carpeta para almacenar resultados si no existe

    resultado = {
        "fecha": ahora,
        "tablero_actual": tablero,
        "reconstruido_desde_historial": reconstruido,
        "coincide": coincide  # Indica si la reconstrucción es consistente
    }

    with open("verificaciones/comparacion_tablero.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=4, ensure_ascii=False)  # Guarda resultado en archivo JSON

    return jsonify(resultado)  # Retorna resultado de la verificación en formato JSON

### FUNCIONES AUXILIARES ###

def guardar_jugada_en_archivo(jugada):
    # Registra jugada con fecha y detalles en un archivo de texto para auditoría
    ruta = "historial_jugadas.txt"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ruta, "a", encoding="utf-8") as f:
        f.write(f"[{now}] Jugador: {jugada['jugador'].upper()}, "
                f"Movimiento: {jugada['movimiento']}, "
                f"Razón: {jugada['razon']}, "
                f"Ganador: {jugada['ganador']}\n")

def guardar_imagen_tablero(tablero, turno):
    # Guarda una imagen PNG que representa el tablero actual con marcas de jugadores visibles
    if not os.path.exists("tableros"):
        os.makedirs("tableros")  # Crea carpeta para guardar imágenes si no existe

    fig, ax = plt.subplots(figsize=(3, 3))  # Crea figura y ejes para dibujo
    ax.set_xticks(np.arange(3))  # Configura ticks en eje x
    ax.set_yticks(np.arange(3))  # Configura ticks en eje y
    ax.set_xticklabels([])  # Oculta etiquetas eje x
    ax.set_yticklabels([])  # Oculta etiquetas eje y
    ax.grid(True)  # Muestra cuadrícula para simular tablero

    for i in range(3):
        for j in range(3):
            cell = tablero[i][j]
            if cell != "b":  # Si la celda no está vacía
                ax.text(j, 2 - i, cell.upper(), ha="center", va="center", fontsize=28,
                        color="#e74c3c" if cell == "x" else "#2980b9")  # Dibuja "X" rojo o "O" azul en celda

    plt.tight_layout()  # Ajusta layout para evitar recortes
    nombre = f"tableros/turno_{turno:02d}.png"  # Define nombre de archivo con número de turno
    plt.savefig(nombre)  # Guarda imagen en archivo PNG
    plt.close()  # Cierra figura para liberar memoria

def evaluar_jugada_rubrica(jugada):
    # Evalúa la jugada automáticamente basándose en palabras clave en la explicación de la jugada
    razon = str(jugada.get("razon", "")).lower()  # Obtiene texto de razón en minúsculas
    return {
        "Comprensión de Reglas": 3 if "legal" in razon or "válido" in razon else 2,
        "Validez y Legalidad": 3 if "válido" in razon else 2,
        "Razonamiento Estratégico": 3 if "bloquear" in razon or "ganar" in razon else 2,
        "Factualidad": 3 if "tablero" in razon or "posición" in razon else 2,
        "Coherencia Explicativa": 3 if "porque" in razon or "ya que" in razon else 2,
        "Claridad Lingüística": 3 if len(razon) > 15 else 2,
        "Adaptabilidad": 3 if "respuesta" in razon or "ajusté" in razon else 2
    }  # Retorna diccionario con puntajes para cada dimensión

def cargar_jugadas_desde_archivo():
    # Carga lista de jugadas desde archivo JSON si existe, retorna lista vacía si no
    if os.path.exists("jugadas.json"):
        with open("jugadas.json", "r") as f:
            return json.load(f)  # Carga contenido JSON como lista de jugadas
    return []  # Retorna lista vacía si no existe archivo

def guardar_jugadas_en_archivo(jugadas):
    # Guarda lista completa de jugadas en archivo JSON con indentación para legibilidad
    with open("jugadas.json", "w") as f:
        json.dump(jugadas, f, indent=2)

def cargar_evaluaciones_desde_archivo():
    # Lee archivo de evaluaciones JSON donde cada línea es un JSON independiente
    evaluaciones = []
    try:
        with open("evaluaciones.json", "r", encoding="utf-8") as f:
            for linea in f:
                ev = json.loads(linea)  # Convierte línea JSON a diccionario
                print(type(ev))  # Debug: imprime tipo de objeto (debe ser dict)
                evaluaciones.append(ev)
    except FileNotFoundError:
        pass  # Si archivo no existe, simplemente retorna lista vacía
    return evaluaciones

def guardar_evaluacion_en_archivo(evaluacion):
    # Carga evaluaciones previas, añade una nueva y guarda todas en archivo JSON
    evaluaciones = cargar_evaluaciones_desde_archivo()
    evaluaciones.append(evaluacion)
    with open("evaluaciones.json", "w", encoding="utf-8") as f:
        json.dump(evaluaciones, f, indent=2, ensure_ascii=False)

def guardar_evaluaciones_completas(match_id, jugadas):
    # Para una partida, guarda todas las evaluaciones no evaluadas con valores iniciales
    evaluaciones = [j for j in jugadas if j.get("match_id") == match_id]
    dimensiones = [
        "Comprensión de Reglas", "Validez y Legalidad", "Razonamiento Estratégico",
        "Factualidad", "Coherencia Explicativa", "Claridad Lingüística", "Adaptabilidad"
    ]

    for ev in evaluaciones:
        if not ev.get("evaluada", False):
            # Inicializa evaluación con ceros y razón por defecto para jugadas no evaluadas
            ev["evaluacion"] = {dim: 0 for dim in dimensiones}
            ev["razon"] = "No evaluada por el usuario"
            ev["evaluada"] = False

    # Guarda cada evaluación como línea JSON en archivo de forma acumulativa
    with open("evaluaciones.json", "a", encoding="utf-8") as f:
        for ev in evaluaciones:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")

def obtener_jugadas():
    # Obtiene todas las jugadas almacenadas en la base de datos SQLite
    conn = create_connection()  # Abre conexión a base de datos
    c = conn.cursor()  # Crea cursor para ejecutar consultas
    c.execute('SELECT * FROM jugadas')  # Consulta todas las filas de la tabla jugadas
    jugadas = c.fetchall()  # Recupera resultados de la consulta
    conn.close()  # Cierra conexión
    return jugadas  # Retorna lista de jugadas

def insertar_evaluacion_bd(match_id, movimiento, evaluacion, razon, jugador, modelo):
    # Inserta o actualiza una evaluación en la base de datos para una jugada específica
    movimiento_json = json.dumps(movimiento)  # Convierte movimiento a cadena JSON
    evaluacion_json = json.dumps(evaluacion)  # Convierte evaluación a cadena JSON

    # Busca evaluación existente con mismo match_id, movimiento y jugador
    existente = Evaluacion.query.filter_by(match_id=match_id, movimiento=movimiento_json, jugador=jugador).first()
    if existente:
        # Actualiza evaluación existente con nuevos datos
        existente.evaluacion = evaluacion_json
        existente.razon = razon
        existente.modelo = modelo
        existente.id = existente.id  # No cambia ID primaria
    else:
        # Crea nueva evaluación y la añade a la sesión
        nueva_eval = Evaluacion(
            match_id=str(match_id),
            jugador=jugador,
            modelo=modelo,
            movimiento=movimiento_json,
            evaluacion=evaluacion_json,
            razon=razon
        )
        db.session.add(nueva_eval)  # Añade nueva evaluación a la base de datos
    db.session.commit()  # Guarda cambios en la base de datos

# Modelo de base de datos para almacenar jugadas
class Jugada(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Clave primaria autoincremental
    match_id = db.Column(db.String(50), nullable=False)  # Identificador de partida
    jugador = db.Column(db.String(50), nullable=False)  # Jugador que realizó la jugada
    modelo = db.Column(db.String(50), nullable=False)  # Modelo IA asociado a la jugada
    movimiento = db.Column(db.Text, nullable=False)  # Movimiento en formato JSON string
    tablero = db.Column(db.Text, nullable=False)  # Estado del tablero en JSON string
    ganador = db.Column(db.String(10), nullable=True)  # Ganador si existe
    razon = db.Column(db.Text, nullable=True)  # Razón o explicación de la jugada
    evaluada = db.Column(db.Boolean, default=False)  # Indica si la jugada fue evaluada manualmente
    fecha_evaluacion = db.Column(db.String(50), nullable=True)  # Fecha en que se evaluó

def insertar_jugada_bd(jugada):
    # Inserta una jugada en la base de datos si no existe previamente para evitar duplicados
    existente = Jugada.query.filter_by(match_id=str(jugada['match_id']),
                                      movimiento=json.dumps(jugada['movimiento'])).first()
    if existente:
        return existente  # Devuelve registro existente si ya fue guardado

    # Crea nuevo registro con los datos de la jugada
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
    db.session.add(nueva_jugada)  # Añade nueva jugada a la sesión
    db.session.commit()  # Guarda cambios en la base de datos
    return nueva_jugada  # Retorna la jugada insertada

def cargar_jugadas_desde_bd():
    # Recupera todas las jugadas de la base de datos y las transforma a diccionarios para uso en Python
    jugadas = Jugada.query.all()  # Consulta todas las jugadas almacenadas
    resultado = []
    for j in jugadas:
        resultado.append({
            "id": j.id,
            "match_id": int(j.match_id),
            "jugador": j.jugador,
            "modelo": j.modelo,
            "movimiento": json.loads(j.movimiento),  # Convierte JSON string a objeto Python
            "tablero": json.loads(j.tablero),
            "ganador": j.ganador,
            "razon": j.razon,
            "evaluada": j.evaluada,
            "fecha_evaluacion": j.fecha_evaluacion
        })
    return resultado  # Retorna lista de diccionarios con jugadas

def insertar_o_actualizar_evaluacion_bd(jugada):
    # Inserta o actualiza evaluaciones automáticas y humanas en la base de datos
    movimiento_json = json.dumps(jugada['movimiento'])  # Convierte movimiento a JSON string
    eval_auto_json = json.dumps(jugada.get('evaluacion_automatica', {}))  # Eval. automática como JSON string
    eval_humana_json = json.dumps(jugada.get('evaluacion_humana', {})) if jugada.get('evaluacion_humana') else None

    # Obtiene razones para evaluaciones si existen
    razon_auto = jugada.get('razon', None) if jugada.get('evaluacion_automatica') else None
    razon_huma = jugada.get('razon_humana', None) if jugada.get('evaluacion_humana') else None

    # Busca evaluación existente para el mismo match_id, jugador y movimiento
    existente = Evaluacion.query.filter_by(
        match_id=str(jugada['match_id']),
        jugador=jugada['jugador'],
        movimiento=movimiento_json
    ).first()

    if existente:
        # Actualiza campos de evaluación existente
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
    db.session.commit()  # Guarda los cambios en la base de datos


### RUTAS PARA EVALUACIÓN ###

@app.route("/evaluar", methods=["GET", "POST"])
def evaluar():
    # Carga todas las jugadas almacenadas en un archivo JSON local
    jugadas = cargar_jugadas_desde_archivo()

    # Obtiene todos los match_id únicos y los ordena ascendentemente
    match_ids = sorted(set(j['match_id'] for j in jugadas))
    siguiente_match_id = None
    
    # Busca el primer match_id que tenga jugadas pendientes de evaluación
    for mid in match_ids:
        if any(not j.get("evaluada", False) for j in jugadas if j['match_id'] == mid):
            siguiente_match_id = mid
            break

    # Si no hay jugadas pendientes, devuelve mensaje informativo
    if siguiente_match_id is None:
        return "No hay jugadas pendientes para evaluar."

    # Filtra todas las jugadas del match seleccionado
    jugadas_del_match = [j for j in jugadas if j['match_id'] == siguiente_match_id]
    # De esas, filtra solo las que aún no han sido evaluadas
    jugadas_no_evaluadas = [j for j in jugadas_del_match if not j.get("evaluada", False)]

    # Si no quedan jugadas no evaluadas, redirige para recargar la página
    if not jugadas_no_evaluadas:
        return redirect(url_for("evaluar"))

    # Selecciona la primera jugada no evaluada para mostrar en el formulario
    jugada_actual = jugadas_no_evaluadas[0]

    if request.method == "POST":
        # Obtiene la razón escrita por el evaluador desde el formulario
        razon = request.form.get('razon', '')
        rubrica = {}
        # Recorre los campos del formulario para extraer la puntuación de cada dimensión
        for key in request.form:
            if key.startswith("rubrica[") and key.endswith("]"):
                dim = key[7:-1]  # Extrae el nombre de la dimensión evaluada
                rubrica[dim] = int(request.form.get(key))

        # Actualiza la jugada actual en la lista con la evaluación y la razón
        for j in jugadas:
            if j['match_id'] == jugada_actual['match_id'] and j['movimiento'] == jugada_actual['movimiento']:
                j['evaluacion'] = rubrica
                j['razon'] = razon
                j['evaluada'] = True
                break

        # Si todas las jugadas del match ya están evaluadas, guarda el archivo final con evaluaciones completas
        if all(j.get("evaluada", False) for j in jugadas_del_match):
            guardar_evaluaciones_completas(siguiente_match_id, jugadas_del_match)

        # Guarda los cambios en el archivo principal de jugadas
        guardar_jugadas_en_archivo(jugadas)

        # Intenta guardar la evaluación en la base de datos, manejando errores si ocurren
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

        # Redirige para evaluar la siguiente jugada pendiente
        return redirect(url_for("evaluar"))

    # Renderiza la plantilla HTML de evaluación pasando la jugada actual y la función enumerate
    return render_template("evaluar.html", jugada=jugada_actual, enumerate=enumerate)


@app.route("/evaluaciones_historial")
def evaluaciones_historial():
    # Define las dimensiones evaluadas para mostrar en la página de historial
    dimensiones = [
        "Comprensión de Reglas",
        "Validez y Legalidad",
        "Razonamiento Estratégico",
        "Factualidad",
        "Coherencia Explicativa",
        "Claridad Lingüística",
        "Adaptabilidad",
    ]

    # Define valores de promedio de ejemplo para cada dimensión (se puede obtener dinámicamente)
    promedios = {
        "Comprensión de Reglas": 2.5,
        "Validez y Legalidad": 2.2,
        "Razonamiento Estratégico": 1.8,
        "Factualidad": 2.7,
        "Coherencia Explicativa": 2.3,
        "Claridad Lingüística": 2.9,
        "Adaptabilidad": 2.0,
    }

    # Carga evaluaciones desde archivo JSON local
    evaluaciones = cargar_evaluaciones_desde_archivo()

    # Normaliza y prepara los datos para facilitar su visualización en la plantilla
    for ev in evaluaciones:
        ev.setdefault("evaluacion", "")
        ev.setdefault("tablero", "")
        ev.setdefault("razon", "")
        ev.setdefault("movimiento", "")
        ev.setdefault("jugador", "")
        ev.setdefault("modelo", "")
        ev.setdefault("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # Convierte movimientos tipo "mark" a un formato legible para mostrar
        if (isinstance(ev["movimiento"], list) and len(ev["movimiento"]) >= 3
                and ev["movimiento"][0] == "mark"):
            fila = ev["movimiento"][1]
            columna = ev["movimiento"][2]
            ev["movimiento_legible"] = f"Marcar fila {fila}, columna {columna}"
        else:
            ev["movimiento_legible"] = str(ev["movimiento"])

        # Formatea la razón para mostrarla como texto continuo, ya sea lista o string
        if isinstance(ev["razon"], list):
            ev["razon_texto"] = "\n".join(ev["razon"])
        elif isinstance(ev["razon"], str):
            ev["razon_texto"] = ev["razon"]
        else:
            ev["razon_texto"] = ""

        # Mantiene el tablero en formato lista para facilitar su uso en la plantilla
        if isinstance(ev["tablero"], list):
            ev["tablero"] = ev["tablero"]

    # Renderiza la plantilla HTML con los datos procesados para el historial de evaluaciones
    return render_template("evaluaciones_historial.html", evaluaciones=evaluaciones, dimensiones=dimensiones, promedios=promedios)


@app.route("/rubrica")
def ver_rubrica():
    # Define la estructura completa de la rúbrica con dimensiones y niveles explicativos
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
    # Renderiza la plantilla HTML que muestra la rúbrica completa para referencia
    return render_template("rubrica.html", rubrica=rubrica)

@app.route('/guardar_evaluacion', methods=['POST'])
def guardar_evaluacion():
    # Carga todas las jugadas guardadas en el archivo JSON local
    jugadas = cargar_jugadas_desde_archivo()

    # Obtiene datos del formulario enviados vía POST
    match_id = int(request.form.get("match_id"))
    razon = request.form.get("razon", "").strip()

    # Recupera datos guardados en la sesión sobre la jugada actual
    jugador = session.get("turno_actual", "desconocido")
    modelo = session.get("modelo", "desconocido")
    movimiento = session.get("movimiento", [])
    tablero_actual = session.get("tablero", [["b"]*3 for _ in range(3)])
    ganador = session.get("ganador", None)

    # Extrae la evaluación (puntuaciones) de la rúbrica enviada desde el formulario
    rubrica = {}
    for key in request.form:
        if key.startswith("rubrica[") and key.endswith("]"):
            dim = key[7:-1]  # Extrae el nombre de la dimensión evaluada
            rubrica[dim] = int(request.form.get(key))

    # Busca la jugada correspondiente a este match_id que aún no esté evaluada
    jugada_actual = None
    for j in jugadas:
        if j['match_id'] == match_id and not j.get("evaluada", False):
            jugada_actual = j
            break

    if jugada_actual:
        # Actualiza la jugada con los datos de la evaluación humana
        jugada_actual["jugador"] = jugador
        jugada_actual["modelo"] = modelo
        jugada_actual["movimiento"] = movimiento
        jugada_actual["tablero"] = tablero_actual
        jugada_actual["ganador"] = ganador
        jugada_actual["evaluacion"] = rubrica
        jugada_actual["razon"] = razon
        jugada_actual["evaluada"] = True
        jugada_actual["fecha_evaluacion"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Guarda los cambios en el archivo de jugadas como respaldo
        guardar_jugadas_en_archivo(jugadas)

        # Intenta guardar la evaluación en la base de datos, manejando posibles errores
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

    # Redirige a la página principal después de guardar la evaluación
    return redirect(url_for("index"))


@app.route("/siguiente_jugada", methods=["POST"])
def siguiente_jugada():
    # Redirige a la ruta 'evaluar' para mostrar la siguiente jugada pendiente de evaluación
    return redirect(url_for("evaluar"))


# Funciones auxiliares para manejo de evaluaciones y estadísticas para gráficos

def cargar_evaluaciones():
    # Intenta cargar evaluaciones guardadas desde archivo JSON local
    try:
        with open("evaluaciones.json", "r", encoding="utf-8") as f:
            evaluaciones = json.load(f)
        return evaluaciones
    except Exception:
        # Si ocurre un error o no existe el archivo, retorna lista vacía
        return []

def calcular_promedios(evaluaciones):
    # Inicializa acumuladores y contadores para cada dimensión de la rúbrica
    suma_por_dim = {dim: 0 for dim in DIMENSIONES}
    conteo_por_dim = {dim: 0 for dim in DIMENSIONES}

    # Recorre cada evaluación para sumar las puntuaciones por dimensión
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
                    # Ignora valores que no sean numéricos
                    pass

    # Calcula el promedio para cada dimensión, asignando 0 si no hay evaluaciones
    promedios = {}
    for dim in DIMENSIONES:
        if conteo_por_dim[dim] > 0:
            promedios[dim] = round(suma_por_dim[dim] / conteo_por_dim[dim], 2)
        else:
            promedios[dim] = 0

    return promedios


@app.route("/grafico_radar")
def grafico_radar():
    # Carga evaluaciones almacenadas para generar estadísticas
    evaluaciones = cargar_evaluaciones()
    # Calcula promedios por dimensión para mostrar en gráfico radar
    promedios = calcular_promedios(evaluaciones)
    # Renderiza la plantilla con las dimensiones y los promedios calculados
    return render_template("grafico_radar.html", dimensiones=DIMENSIONES, promedios=promedios)


if __name__ == "__main__":
    # Inicia la aplicación Flask en modo debug para desarrollo
    app.run(debug=True)

