import sqlite3  # Importa módulo para manejar base de datos SQLite
import json    # Importa módulo para manejar archivos JSON

DB_PATH = 'tres_raya.db'    # Define la ruta del archivo de base de datos SQLite
JSON_PATH = 'jugadas.json'  # Define la ruta del archivo JSON con las jugadas

def jugada_ya_existe(cursor, id_match, board, move, player):
    # Consulta si una jugada con los mismos parámetros ya existe en la tabla 'jugadas'
    cursor.execute("""
        SELECT 1 FROM jugadas
        WHERE id_match = ? AND board = ? AND move = ? AND player = ?
        LIMIT 1
    """, (id_match, board, move, player))
    # Retorna True si encontró algún registro, False si no
    return cursor.fetchone() is not None

def importar_jugadas():
    # Abre conexión a la base de datos usando contexto 'with' para cierre automático
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()  # Crea cursor para ejecutar comandos SQL

        # Abre y lee el archivo JSON con las jugadas en formato lista de diccionarios
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            jugadas = json.load(f)

        nuevos = 0        # Contador para jugadas insertadas nuevas
        duplicados = 0    # Contador para jugadas que ya existían (no insertadas)

        # Recorre cada jugada del archivo JSON
        for row in jugadas:
            # Obtiene cada campo esperado de la jugada, con valores por defecto en caso de faltar
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

            # Verifica si la jugada ya existe en la base de datos para evitar duplicados
            if jugada_ya_existe(c, id_match, board, move, player):
                duplicados += 1  # Incrementa contador de duplicados
                continue         # Salta la inserción de esta jugada

            # Inserta la jugada nueva en la tabla 'jugadas' con los campos correspondientes
            c.execute('''
                INSERT INTO jugadas (id_match, board, move, win, player, model, reason, timestamp, valid, execution_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                id_match, board, move, win, player, model, reason, timestamp, valid, exec_time
            ))
            nuevos += 1  # Incrementa contador de jugadas nuevas insertadas

        # Confirma las inserciones realizadas en la base de datos
        conn.commit()
        # Imprime resumen de la importación: cuántas nuevas y cuántas duplicadas se detectaron
        print(f'Importación completada: {nuevos} nuevas, {duplicados} duplicadas.')

# Punto de entrada principal: si se ejecuta directamente este script, se llama a importar_jugadas()
if __name__ == "__main__":
    importar_jugadas()
