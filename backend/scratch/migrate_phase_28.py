import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/asistencia')

def migrate():
    print("Iniciando migracion Fase 28: Degradacion Controlada de Biometria...")
    
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        print("Anadiendo columnas biometric_status y biometric_provider a raw_punches...")
        
        cur.execute("""
            ALTER TABLE raw_punches 
            ADD COLUMN IF NOT EXISTS biometric_status VARCHAR(20) 
            CHECK (biometric_status IN ('passed', 'failed', 'unavailable', 'bypassed')),
            ADD COLUMN IF NOT EXISTS biometric_provider VARCHAR(50);
        """)
        
        print("Actualizando registros existentes a 'bypassed'...")
        cur.execute("""
            UPDATE raw_punches 
            SET biometric_status = 'bypassed', 
                biometric_provider = 'legacy_migration' 
            WHERE biometric_status IS NULL;
        """)
        
        cur.execute("""
            ALTER TABLE raw_punches 
            ALTER COLUMN biometric_status SET NOT NULL;
        """)
        
        conn.commit()
        print("Migracion completada con exito.")
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur: cur.close()
        if conn: conn.close()

if __name__ == "__main__":
    migrate()
