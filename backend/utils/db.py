import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

# Pool global
_db_pool = None

def get_pool():
    global _db_pool
    if _db_pool is None:
        db_url = os.getenv('DATABASE_URL')
        # Configuración del pool: min 1, max 20 conexiones
        if db_url:
            _db_pool = pool.ThreadedConnectionPool(
                1, 20, 
                db_url, 
                cursor_factory=RealDictCursor
            )
        else:
            _db_pool = pool.ThreadedConnectionPool(
                1, 20,
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 5432)),
                dbname=os.getenv('DB_NAME', 'asistencia'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', 'postgres'),
                cursor_factory=RealDictCursor,
            )
    return _db_pool


@contextmanager
def tx():
    """
    Context manager para transacciones explícitas.
    Uso:
        with tx() as (conn, cur):
            cur.execute(...)
            # commit automático al salir del bloque si no hay excepción
    """
    pool_obj = get_pool()
    conn = pool_obj.getconn()
    conn.autocommit = False # Asegurar modo transaccional
    try:
        with conn.cursor() as cur:
            yield conn, cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool_obj.putconn(conn)


def query_one(sql, params=None):
    """Ejecuta una consulta de solo lectura y devuelve una sola fila."""
    pool_obj = get_pool()
    conn = pool_obj.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()
    finally:
        pool_obj.putconn(conn)


def query_all(sql, params=None):
    """Ejecuta una consulta de solo lectura y devuelve todas las filas."""
    pool_obj = get_pool()
    conn = pool_obj.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        pool_obj.putconn(conn)


def execute(sql, params=None):
    """
    Ejecuta una sentencia de escritura (INSERT/UPDATE/DELETE).
    Ahora utiliza el bloque transaccional tx().
    """
    with tx() as (conn, cur):
        cur.execute(sql, params)
        try:
            return cur.fetchone()
        except psycopg2.ProgrammingError:
            return None
