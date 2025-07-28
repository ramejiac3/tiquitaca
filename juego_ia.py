import pandas as pd  # Importa la biblioteca pandas para manipulación y análisis de datos
import ast  # Importa la biblioteca ast para evaluar expresiones tipo string a estructuras de datos
import google.generativeai as genai  # Importa el módulo de la API de Google Generative AI
from transformers import pipeline  # Importa la función pipeline de HuggingFace Transformers para tareas de NLP

# Cargar dataset
df = pd.read_csv("dataset1.csv")  # Carga el archivo CSV 'dataset1.csv' en un DataFrame
df["board"] = df["board"].apply(ast.literal_eval)  # Convierte los strings de la columna 'board' en listas de Python
df["move"] = df["move"].apply(ast.literal_eval)  # Convierte los strings de la columna 'move' en listas de Python

indice_actual = 0  # Variable global para llevar el seguimiento del índice actual en el dataset

def buscar_jugada(tablero_actual, jugador):
    global indice_actual  # Se indica que se usará la variable global 'indice_actual'

    while indice_actual < len(df):  # Itera mientras queden filas por procesar en el dataset
        row = df.iloc[indice_actual]  # Obtiene la fila actual del DataFrame
        indice_actual += 1  # Incrementa el índice para pasar a la siguiente fila en la próxima iteración

        if row["player"] != jugador:
            continue  # Si el jugador de la fila no coincide con el actual, se omite esta fila

        movimiento = row["move"]  # Extrae el movimiento de la fila actual

        # Validar movimiento con try-except
        try:
            tablero_con_jugada = convertir_dataset_a_tablero(row["board"])  # Convierte los datos de 'board' a matriz
            tablero_sin_jugada = remover_jugada(tablero_con_jugada, movimiento, jugador)  # Elimina la jugada del tablero
        except Exception as e:
            print(f"⚠️ Error al procesar jugada en índice {indice_actual - 1}: {e}")  # Imprime un error si ocurre
            continue  # Salta a la siguiente fila del dataset si ocurre una excepción

        if tablero_sin_jugada == tablero_actual:
            if row["valid"] != 1:
                return movimiento, "Movimiento inválido por IA detectado", row["model"]  # Retorna jugada inválida
            return movimiento, row["reason"], row["model"]  # Retorna jugada válida con su razón y modelo usado

    # Si no se encuentra una jugada válida en el dataset
    return ["mark", 2, 2], "No se encontró una jugada válida restante en el dataset", "modelo_desconocido"

def remover_jugada(tablero, movimiento, jugador):
    """Elimina del tablero una jugada dada, para comparar con el tablero antes de que el jugador actuara."""
    fila = int(movimiento[1]) - 1  # Ajusta el índice de fila (base 1 a base 0)
    col = int(movimiento[2]) - 1  # Ajusta el índice de columna (base 1 a base 0)
    nuevo = [[celda for celda in fila] for fila in tablero]  # Crea una copia profunda del tablero
    if nuevo[fila][col] == jugador:
        nuevo[fila][col] = "b"  # Si la celda corresponde al jugador, la vacía (marca como "b")
    return nuevo  # Devuelve el nuevo tablero sin la jugada

def convertir_dataset_a_tablero(lista_celdas):
    tablero = [["b" for _ in range(3)] for _ in range(3)]  # Crea un tablero vacío de 3x3 (celdas en blanco)
    for celda in lista_celdas:  # Recorre cada celda del dataset
        if celda[0] == "cell":
            f, c, val = int(celda[1]) - 1, int(celda[2]) - 1, celda[3]  # Extrae fila, columna y valor
            tablero[f][c] = val  # Asigna el valor a la posición correspondiente en el tablero
    return tablero  # Devuelve el tablero construido a partir del dataset

def reiniciar_indice():
    global indice_actual  # Se refiere a la variable global
    indice_actual = 0  # Reinicia el índice global a 0

def inicializar_tablero():
    return [["b" for _ in range(3)] for _ in range(3)]  # Devuelve un nuevo tablero vacío de 3x3

def revisar_ganador(tablero):
    lineas = []  # Lista para almacenar todas las combinaciones posibles de victoria
    lineas.extend(tablero)  # Agrega todas las filas al conjunto de líneas
    for c in range(3):
        lineas.append([tablero[f][c] for f in range(3)])  # Agrega columnas al conjunto de líneas
    lineas.append([tablero[i][i] for i in range(3)])  # Agrega la diagonal principal
    lineas.append([tablero[i][2 - i] for i in range(3)])  # Agrega la diagonal secundaria
    for linea in lineas:
        if linea[0] != "b" and linea[0] == linea[1] == linea[2]:  # Verifica si hay tres iguales y no vacías
            return linea[0]  # Retorna el jugador ganador
    lleno = all(tablero[f][c] != "b" for f in range(3) for c in range(3))  # Verifica si el tablero está lleno
    if lleno:
        return "empate"  # Retorna empate si no hay ganador y el tablero está lleno
    return None  # Retorna None si no hay ganador ni empate

def obtener_ultima_jugada():
    # Simula un ejemplo, luego lo conectas con tu lógica real
    return {
        'tablero': [['X', 'O', ''], ['', 'X', ''], ['O', '', '']],  # Representación de tablero de ejemplo
        'modelo': 'Gemini',  # Nombre del modelo utilizado
        'jugada': (2, 1),  # Coordenadas de la jugada realizada (fila 2, columna 1)
        'marca': 'X'  # Marca (jugador) que realizó la jugada
    }
