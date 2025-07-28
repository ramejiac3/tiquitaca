import sqlite3  # Importa el módulo sqlite3 para permitir la conexión y manipulación de bases de datos SQLite

DB_PATH = 'tres_raya.db'  # Define la ruta al archivo de base de datos SQLite que se utilizará

def create_connection():  # Función que crea y devuelve una conexión a la base de datos
    conn = sqlite3.connect(DB_PATH)  # Establece la conexión con la base de datos SQLite definida
    return conn  # Devuelve el objeto de conexión creado

def create_tables():  # Función que crea las tablas necesarias en la base de datos si no existen
    conn = create_connection()  # Llama a la función para establecer la conexión a la base de datos
    c = conn.cursor()  # Crea un cursor para ejecutar sentencias SQL

    # Crea la tabla 'jugadas' si no existe, utilizada para almacenar los movimientos del juego
    # Esta tabla puede haber sido creada manualmente, pero aquí se define su estructura en código
    c.execute('''
    CREATE TABLE IF NOT EXISTS jugadas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_match TEXT NOT NULL,
        board TEXT,
        move TEXT,
        win INTEGER,
        player TEXT,
        model TEXT,
        reason TEXT,
        timestamp TEXT,
        valid INTEGER,
        execution_time REAL
    )
    ''')

    # Crea la tabla 'evaluaciones' si no existe, utilizada para almacenar evaluaciones humanas de las jugadas
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS evaluaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        jugada_id INTEGER NOT NULL,
        usuario TEXT,
        criterio_1 INTEGER,
        criterio_2 INTEGER,
        criterio_3 INTEGER,
        criterio_4 INTEGER,
        criterio_5 INTEGER,
        criterio_6 INTEGER,
        criterio_7 INTEGER,
        comentario TEXT,
        fecha_eval TEXT,
        FOREIGN KEY(jugada_id) REFERENCES jugadas(id)
    )
    ''')


    conn.commit()  # Guarda los cambios realizados en la base de datos
    conn.close()  # Cierra la conexión con la base de datos

# Punto de entrada principal del script
# Llama a la función para crear las tablas solo una vez al ejecutar este archivo directamente
if __name__ == '__main__':
    create_tables()  # Ejecuta la función para crear las tablas en la base de datos
