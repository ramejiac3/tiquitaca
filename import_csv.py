# Importa el módulo sqlite3 para manejar la base de datos SQLite
import sqlite3
# Importa el módulo json para trabajar con archivos JSON
import json

# Ruta del archivo de base de datos SQLite
DB_PATH = 'tres_raya.db'
# Ruta del archivo JSON que contiene las jugadas a importar
JSON_PATH = 'jugadas.json'

# Función para verificar si una jugada ya existe en la base de datos, evitando duplicados
def jugada_ya_existe(cursor, id_match, board, move, player):
    # Ejecuta una consulta que busca una jugada específica con los parámetros dados
    cursor.execute("""
        SELECT 1 FROM jugadas
        WHERE id_match = ? AND board = ? AND move = ? AND player = ?
        LIMIT 1
    """, (id_match, board, move, player))
    # Retorna True si se encuentra una coincidencia, False en caso contrario
    return cursor.fetchone() is not None

# Función principal para importar jugadas desde un archivo JSON a la base de datos
def importar_jugadas():
    # Establece una conexión con la base de datos utilizando un contexto de manejo seguro
    with sqlite3.connect(DB_PATH) as conn:
        # Crea un cursor para ejecutar comandos SQL
        c = conn.cursor()

        # Abre el archivo JSON que contiene las jugadas
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            # Carga el contenido del archivo JSON en una lista de diccionarios
            jugadas = json.load(f)

        # Inicializa contadores para jugadas nuevas y duplicadas
        nuevos = 0
        duplicados = 0

        # Itera sobre cada jugada en el archivo JSON
        for row in jugadas:
            # Extrae los datos de cada jugada del diccionario
            id_match = row.get('id_match')
            board = row.get('board')
            move = row.get('move')
            win = int(row.get('win', 0))  # Se convierte a entero, por defecto 0 si no existe
            player = row.get('player')
            model = row.get('model')
            reason = row.get('reason')
            timestamp = row.get('timestamp')
            valid = int(row.get('valid', 1))  # Se convierte a entero, por defecto 1 (válido)
            exec_time = float(row.get('execution_time', 0.0))  # Se convierte a float, por defecto 0.0

            # Verifica si la jugada ya existe en la base de datos
            if jugada_ya_existe(c, id_match, board, move, player):
                # Incrementa el contador de duplicados y salta a la siguiente jugada
                duplicados += 1
                continue

            # Inserta la nueva jugada en la tabla 'jugadas'
            c.execute('''
                INSERT INTO jugadas (id_match, board, move, win, player, model, reason, timestamp, valid, execution_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                id_match, board, move, win, player, model, reason, timestamp, valid, exec_time
            ))
            # Incrementa el contador de nuevas jugadas
            nuevos += 1

        # Guarda los cambios realizados en la base de datos
        conn.commit()
        # Muestra un resumen de la importación en consola
        print(f'Importación completada: {nuevos} nuevas, {duplicados} duplicadas.')

# Punto de entrada del programa: ejecuta la función de importación si se ejecuta este archivo directamente
if __name__ == "__main__":
    importar_jugadas()
