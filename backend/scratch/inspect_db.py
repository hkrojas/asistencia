
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def inspect():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'devices';")
    cols = cur.fetchall()
    print(f"Columns in 'devices': {[c[0] for c in cols]}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    inspect()
