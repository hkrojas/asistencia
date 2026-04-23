import psycopg2
import os
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv('DATABASE_URL')

def migrate():
    print("Iniciando migracion Fase 29: Periodos de Nomina y Bloqueo Historico...")
    
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # 1. Crear tabla payroll_periods
        print("Creando tabla payroll_periods...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payroll_periods (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(100),
                starts_on DATE NOT NULL,
                ends_on DATE NOT NULL,
                state VARCHAR(20) DEFAULT 'open' CHECK (state IN ('open', 'closed')),
                closed_at TIMESTAMPTZ,
                closed_by UUID,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        
        # 2. Alterar daily_timesheets
        print("Alterando tabla daily_timesheets...")
        cur.execute("""
            ALTER TABLE daily_timesheets 
            ADD COLUMN IF NOT EXISTS payroll_period_id UUID REFERENCES payroll_periods(id),
            ADD COLUMN IF NOT EXISTS is_locked BOOLEAN DEFAULT FALSE;
        """)
        
        # 3. Alterar raw_punches
        print("Alterando tabla raw_punches...")
        cur.execute("""
            ALTER TABLE raw_punches 
            ADD COLUMN IF NOT EXISTS ingest_status VARCHAR(30) DEFAULT 'accepted' 
            CHECK (ingest_status IN ('accepted', 'late_pending_review', 'rejected'));
        """)
        
        conn.commit()
        print("Migracion completada con exito.")
        
    except Exception as e:
        print(f"Error durante la migracion: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur: cur.close()
        if conn: conn.close()

if __name__ == "__main__":
    migrate()
