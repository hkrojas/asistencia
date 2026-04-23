
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def migrate():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    
    try:
        # 1. Crear tabla de códigos de emparejamiento
        print("Creando tabla device_pairing_codes...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS device_pairing_codes (
                id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                code_hash   VARCHAR(255) NOT NULL,
                building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
                expires_at  TIMESTAMPTZ NOT NULL,
                is_used     BOOLEAN NOT NULL DEFAULT FALSE,
                created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)

        # 2. Refactorizar tabla de dispositivos
        print("Refactorizando tabla devices...")
        
        # Eliminar datos antiguos (registros de prueba/inseguros)
        cur.execute("DELETE FROM raw_punches WHERE device_id IS NOT NULL;")
        cur.execute("DELETE FROM devices;")
        
        # Modificar columnas
        cur.execute("ALTER TABLE devices RENAME COLUMN device_token TO token_hash;")
        cur.execute("ALTER TABLE devices ALTER COLUMN employee_id DROP NOT NULL;")
        cur.execute("ALTER TABLE devices ADD COLUMN building_id UUID REFERENCES buildings(id) ON DELETE CASCADE;")
        
        # En una migración real, podríamos necesitar poblar building_id si hubiera datos,
        # pero aquí estamos limpiando la tabla por seguridad.
        
        conn.commit()
        print("OK: Migracion completada con exito.")
    except Exception as e:
        conn.rollback()
        print(f"ERROR: Error en la migracion: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    migrate()
