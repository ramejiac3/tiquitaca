import sqlite3
import json

DB_PATH = 'tres_raya.db'
JSON_PATH = 'jugadas.json'

def jugada_ya_existe(cursor, id_match, board, move, player):
    cursor.execute("""
        SELECT 1 FROM jugadas
        WHERE id_match = ? AND board = ? AND move = ? AND player = ?
        LIMIT 1
    """, (id_match, board, move, player))
    return cursor.fetchone() is not None

def importar_jugadas():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()

        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            jugadas = json.load(f)

        nuevos = 0
        duplicados = 0
        for row in jugadas:
            id_match = row.get('id_match')
            board = row.get('board')
            move = row.get('move')
            win = int(row.get('win', 0))
            player = row.get('player')
            model = row.get('model')
            reason = row.get('reason')
            timestamp = row.get('timestamp')
            valid = int(row.get('valid', 1))
            exec_time = float(row.get('execution_time', 0.0))

            if jugada_ya_existe(c, id_match, board, move, player):
                duplicados += 1
                continue

            c.execute('''
                INSERT INTO jugadas (id_match, board, move, win, player, model, reason, timestamp, valid, execution_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                id_match, board, move, win, player, model, reason, timestamp, valid, exec_time
            ))
            nuevos += 1

        conn.commit()
        print(f'Importación completada: {nuevos} nuevas, {duplicados} duplicadas.')

if __name__ == "__main__":
    importar_jugadas()
