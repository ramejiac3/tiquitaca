import sqlite3

DB_PATH = 'tres_raya.db'

def obtener_jugadas(limit=10):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        SELECT id, id_match, board, move, win, player, model, reason, timestamp, valid, execution_time
        FROM jugadas
        ORDER BY id ASC
        LIMIT ?
    ''', (limit,))

    resultados = c.fetchall()
    conn.close()

    return resultados

if __name__ == '__main__':
    jugadas = obtener_jugadas(5)  # por ejemplo, las primeras 5
    for j in jugadas:
        print(j)
