import sqlite3  # Importa el módulo sqlite3 para interactuar con bases de datos SQLite

DB_PATH = 'tres_raya.db'  # Ruta al archivo de base de datos SQLite que contiene las jugadas del juego

def obtener_jugadas(limit=10):  # Define una función para obtener un número limitado de jugadas desde la base de datos
    conn = sqlite3.connect(DB_PATH)  # Establece una conexión con la base de datos SQLite
    c = conn.cursor()  # Crea un cursor para ejecutar comandos SQL

    c.execute('''  
        SELECT id, id_match, board, move, win, player, model, reason, timestamp, valid, execution_time
        FROM jugadas
        ORDER BY id ASC  
        LIMIT ?  
    ''', (limit,))  # Pasa el valor del límite como parámetro para prevenir inyecciones SQL

    resultados = c.fetchall()  # Recupera todos los resultados de la consulta en una lista de tuplas
    conn.close()  # Cierra la conexión con la base de datos

    return resultados  # Devuelve la lista de jugadas obtenidas

if __name__ == '__main__':  # Punto de entrada principal del script cuando se ejecuta directamente
    jugadas = obtener_jugadas(5)  # Llama a la función para obtener las primeras 5 jugadas registradas
    for j in jugadas:  # Itera sobre cada jugada obtenida
        print(j)  # Imprime la información de la jugada en la consola
