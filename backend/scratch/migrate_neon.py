import os
import sys
# Añadir el path para importar db
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.db import get_connection

def migrate():
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'schema.sql')
    print(f"Reading schema from {schema_path}...")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        sql = f.read()

    print("Connecting to Neon...")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            print("Applying schema...")
            cur.execute(sql)
        conn.commit()
        print("Schema applied successfully!")
    except Exception as e:
        print(f"Error applying schema: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
