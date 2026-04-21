import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

try:
    print("Testing connection with default credentials...")
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        dbname='asistencia',
        user='postgres',
        password='',
        connect_timeout=5
    )
    print("Connection successful!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
