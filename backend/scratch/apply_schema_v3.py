import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def apply_schema():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("Error: DATABASE_URL not found in .env")
        return

    schema_path = 'backend/schema.sql'
    if not os.path.exists(schema_path):
        print(f"Error: {schema_path} not found")
        return

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        print(f"Leyendo {schema_path}...")
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        print("Aplicando esquema a la base de datos...")
        cur.execute(sql)
        conn.commit()
        print("¡Esquema aplicado con éxito!")
        
    except Exception as e:
        print(f"Error al aplicar esquema: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    apply_schema()
