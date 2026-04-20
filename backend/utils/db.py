import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """
    Establece y retorna una conexión a PostgreSQL.
    Usa RealDictCursor para que las filas se devuelvan como diccionarios.
    Las credenciales se leen desde variables de entorno (.env).
    """
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        dbname=os.getenv('DB_NAME', 'asistencia'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres'),
        cursor_factory=RealDictCursor,
    )


def query_one(sql, params=None):
    """Ejecuta una consulta y devuelve una sola fila como dict (o None)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()
    finally:
        conn.close()


def query_all(sql, params=None):
    """Ejecuta una consulta y devuelve todas las filas como lista de dicts."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()


def execute(sql, params=None):
    """Ejecuta una sentencia de escritura (INSERT/UPDATE/DELETE) y hace commit."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            # Intentar fetchone para INSERT … RETURNING
            try:
                row = cur.fetchone()
            except psycopg2.ProgrammingError:
                row = None
        conn.commit()
        return row
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
