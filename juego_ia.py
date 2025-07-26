import pandas as pd  # Biblioteca para manejo de datos en formato DataFrame
import ast           # Módulo para evaluar expresiones literales (listas, diccionarios, etc.) en strings
import google.generativeai as genai  # Librería para IA generativa de Google (usada en otro lugar)
from transformers import pipeline     # Pipeline para modelos Transformers (usado en otro lado)

# Carga un dataset CSV con las jugadas y sus datos
df = pd.read_csv("dataset1.csv")

# Convierte las columnas 'board' y 'move' que están en formato string a listas reales
df["board"] = df["board"].apply(ast.literal_eval)
df["move"] = df["move"].apply(ast.literal_eval)

indice_actual = 0  # Índice global para recorrer el dataset fila por fila

def buscar_jugada(tablero_actual, jugador):
    global indice_actual

    # Recorre las filas desde el índice actual hacia adelante
    while indice_actual < len(df):
        row = df.iloc[indice_actual]  # Obtiene la fila actual
        indice_actual += 1             # Incrementa el índice para la próxima búsqueda

        if row["player"] != jugador:
            # Si el jugador de esta fila no es el que buscamos, saltamos
            continue

        movimiento = row["move"]

        # Intentamos validar el movimiento con manejo de errores
        try:
            # Reconstruye el tablero que contiene la jugada
            tablero_con_jugada = convertir_dataset_a_tablero(row["board"])
            # Elimina la jugada para obtener el tablero anterior a la jugada
            tablero_sin_jugada = remover_jugada(tablero_con_jugada, movimiento, jugador)
        except Exception as e:
            # Si hay error al procesar esta jugada, muestra advertencia y sigue con la siguiente
            print(f"⚠️ Error al procesar jugada en índice {indice_actual - 1}: {e}")
            continue

        # Compara si el tablero sin la jugada coincide con el tablero actual que tenemos
        if tablero_sin_jugada == tablero_actual:
            if row["valid"] != 1:
                # Si el movimiento está marcado como inválido en dataset, devuelve error con motivo
                return movimiento, "Movimiento inválido por IA detectado", row["model"]
            # Si es válido, devuelve el movimiento, la razón explicada y el modelo que hizo la jugada
            return movimiento, row["reason"], row["model"]

    # Si recorre todo el dataset sin encontrar jugadas válidas, devuelve movimiento por defecto y aviso
    return ["mark", 2, 2], "No se encontró una jugada válida restante en el dataset", "modelo_desconocido"

def remover_jugada(tablero, movimiento, jugador):
    """Elimina del tablero una jugada dada, para comparar con el tablero antes de que el jugador actuara."""
    fila = int(movimiento[1]) - 1  # Convierte coordenada fila (de string a índice 0-based)
    col = int(movimiento[2]) - 1   # Convierte coordenada columna (de string a índice 0-based)
    nuevo = [[celda for celda in fila] for fila in tablero]  # Copia profunda del tablero
    if nuevo[fila][col] == jugador:
        nuevo[fila][col] = "b"  # Marca la celda como vacía ("b")
    return nuevo

def convertir_dataset_a_tablero(lista_celdas):
    # Crea un tablero vacío (3x3) con "b" indicando celda vacía
    tablero = [["b" for _ in range(3)] for _ in range(3)]
    # Itera las celdas que vienen del dataset para llenarlas en el tablero
    for celda in lista_celdas:
        if celda[0] == "cell":
            f, c, val = int(celda[1]) - 1, int(celda[2]) - 1, celda[3]
            tablero[f][c] = val  # Asigna valor ("x", "o" o "b") en la posición correcta
    return tablero

def reiniciar_indice():
    global indice_actual
    indice_actual = 0  # Reinicia el índice para comenzar a buscar desde el principio

def inicializar_tablero():
    # Devuelve un tablero vacío 3x3
    return [["b" for _ in range(3)] for _ in range(3)]

def revisar_ganador(tablero):
    # Revisa todas las filas, columnas y diagonales para detectar un ganador
    lineas = []
    lineas.extend(tablero)  # filas
    for c in range(3):
        lineas.append([tablero[f][c] for f in range(3)])  # columnas
    lineas.append([tablero[i][i] for i in range(3)])      # diagonal principal
    lineas.append([tablero[i][2 - i] for i in range(3)])  # diagonal secundaria

    for linea in lineas:
        if linea[0] != "b" and linea[0] == linea[1] == linea[2]:
            return linea[0]  # Retorna ganador ("x" o "o")

    # Si no hay ganador, revisa si el tablero está lleno (empate)
    lleno = all(tablero[f][c] != "b" for f in range(3) for c in range(3))
    if lleno:
        return "empate"  # Indica empate

    return None  # No hay ganador ni empate aún

def obtener_ultima_jugada():
    # Ejemplo simulado que retorna datos de la última jugada (debes conectarlo con tu lógica real)
    return {
        'tablero': [['X', 'O', ''], ['', 'X', ''], ['O', '', '']],
        'modelo': 'Gemini',
        'jugada': (2, 1),  # Fila 2, columna 1
        'marca': 'X'
    }

