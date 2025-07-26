import sqlite3

DB_PATH = 'tres_raya.db'  # Ruta al archivo de la base de datos SQLite

def obtener_jugadas(limit=10):
    # Conecta a la base de datos SQLite usando la ruta definida
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Ejecuta una consulta SQL para obtener columnas específicas de la tabla 'jugadas',
    # ordenadas ascendentemente por 'id' y limitando el resultado a 'limit' filas
    c.execute('''
        SELECT id, id_match, board, move, win, player, model, reason, timestamp, valid, execution_time
        FROM jugadas
        ORDER BY id ASC
        LIMIT ?
    ''', (limit,))

    resultados = c.fetchall()  # Recupera todas las filas resultantes de la consulta
    conn.close()  # Cierra la conexión a la base de datos

    return resultados  # Devuelve la lista de jugadas como tuplas

if __name__ == '__main__':
    jugadas = obtener_jugadas(5)  # Obtiene las primeras 5 jugadas como ejemplo
    for j in jugadas:
        print(j)  # Imprime cada jugada (fila) en consola

