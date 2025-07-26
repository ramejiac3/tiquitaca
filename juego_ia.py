import pandas as pd
import ast
import google.generativeai as genai
from transformers import pipeline

# Cargar dataset
df = pd.read_csv("dataset1.csv")
df["board"] = df["board"].apply(ast.literal_eval)
df["move"] = df["move"].apply(ast.literal_eval)

indice_actual = 0  # Variable global

def buscar_jugada(tablero_actual, jugador):
    global indice_actual

    while indice_actual < len(df):
        row = df.iloc[indice_actual]
        indice_actual += 1

        if row["player"] != jugador:
            continue

        movimiento = row["move"]

        # Validar movimiento con try-except
        try:
            tablero_con_jugada = convertir_dataset_a_tablero(row["board"])
            tablero_sin_jugada = remover_jugada(tablero_con_jugada, movimiento, jugador)
        except Exception as e:
            print(f"⚠️ Error al procesar jugada en índice {indice_actual - 1}: {e}")
            continue  # Salta a la siguiente fila del dataset

        if tablero_sin_jugada == tablero_actual:
            if row["valid"] != 1:
                return movimiento, "Movimiento inválido por IA detectado", row["model"]
            return movimiento, row["reason"], row["model"]

    # Si no encuentra jugadas válidas
    return ["mark", 2, 2], "No se encontró una jugada válida restante en el dataset", "modelo_desconocido"

def remover_jugada(tablero, movimiento, jugador):
    """Elimina del tablero una jugada dada, para comparar con el tablero antes de que el jugador actuara."""
    fila = int(movimiento[1]) - 1
    col = int(movimiento[2]) - 1
    nuevo = [[celda for celda in fila] for fila in tablero]
    if nuevo[fila][col] == jugador:
        nuevo[fila][col] = "b"
    return nuevo

def convertir_dataset_a_tablero(lista_celdas):
    tablero = [["b" for _ in range(3)] for _ in range(3)]
    for celda in lista_celdas:
        if celda[0] == "cell":
            f, c, val = int(celda[1]) - 1, int(celda[2]) - 1, celda[3]
            tablero[f][c] = val
    return tablero

def reiniciar_indice():
    global indice_actual
    indice_actual = 0

def inicializar_tablero():
    return [["b" for _ in range(3)] for _ in range(3)]

def revisar_ganador(tablero):
    lineas = []
    lineas.extend(tablero)
    for c in range(3):
        lineas.append([tablero[f][c] for f in range(3)])
    lineas.append([tablero[i][i] for i in range(3)])
    lineas.append([tablero[i][2 - i] for i in range(3)])
    for linea in lineas:
        if linea[0] != "b" and linea[0] == linea[1] == linea[2]:
            return linea[0]
    lleno = all(tablero[f][c] != "b" for f in range(3) for c in range(3))
    if lleno:
        return "empate"
    return None

def obtener_ultima_jugada():
    # Simula un ejemplo, luego lo conectas con tu lógica real
    return {
        'tablero': [['X', 'O', ''], ['', 'X', ''], ['O', '', '']],
        'modelo': 'Gemini',
        'jugada': (2, 1),  # Fila 2, columna 1
        'marca': 'X'
    }
