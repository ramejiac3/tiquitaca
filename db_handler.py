import sqlite3

DB_PATH = 'tres_raya.db'

def create_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

def create_tables():
    conn = create_connection()
    c = conn.cursor()

    # Tabla jugadas (ya la creaste con DB Browser, esta función la puedes usar para crear si quieres crear desde código)
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

    # Tabla evaluaciones (puedes crearla aquí si quieres)
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

    conn.commit()
    conn.close()

# Llama esta función sólo una vez para crear tablas, luego la puedes comentar o eliminar
if __name__ == '__main__':
    create_tables()
