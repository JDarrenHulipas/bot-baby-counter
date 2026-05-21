import sqlite3
from datetime import datetime, timedelta

DB_NAME = "contador_bebe.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            comando TEXT,
            fecha DATE DEFAULT (DATE('now', 'localtime')),
            hora TEXT DEFAULT (TIME('now', 'localtime'))
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sueno (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            fecha DATE DEFAULT (DATE('now', 'localtime')),
            horas_texto TEXT
        )
    ''')
    conn.commit()
    conn.close()

def registrar_evento(user_id, comando):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Validar límites diarios
    if comando in ['/biberon', '/ejercicios']:
        limite = 4 if comando == '/biberon' else 2
        cursor.execute(
            "SELECT COUNT(*) FROM registros WHERE comando = ? AND fecha = DATE('now', 'localtime')", 
            (comando,)
        )
        count = cursor.fetchone()[0]
        if count >= limite:
            conn.close()
            return False, count

    cursor.execute("INSERT INTO registros (user_id, comando) VALUES (?, ?)", (user_id, comando))
    conn.commit()
    
    # Contar cuántos lleva hoy
    cursor.execute(
        "SELECT COUNT(*) FROM registros WHERE comando = ? AND fecha = DATE('now', 'localtime')", 
        (comando,)
    )
    total_hoy = cursor.fetchone()[0]
    conn.close()
    return True, total_hoy

def registrar_sueno_hora(user_id, horas_texto):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sueno (user_id, horas_texto) VALUES (?, ?)", (user_id, horas_texto))
    conn.commit()
    conn.close()

def obtener_resumen_diario():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT comando, COUNT(*) FROM registros WHERE fecha = DATE('now', 'localtime') GROUP BY comando"
    )
    datos = dict(cursor.fetchall())
    
    cursor.execute("SELECT horas_texto FROM sueno WHERE fecha = DATE('now', 'localtime')")
    horas_sueno = [row[0] for row in cursor.fetchall()]
    conn.close()
    return datos, horas_sueno

def obtener_resumen_semanal():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Últimos 7 días
    cursor.execute("""
        SELECT comando, COUNT(*) FROM registros 
        WHERE fecha >= DATE('now', '-6 days', 'localtime') 
        GROUP BY comando
    """)
    datos = dict(cursor.fetchall())
    conn.close()
    return datos