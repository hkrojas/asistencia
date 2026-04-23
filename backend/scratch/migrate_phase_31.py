from utils.db import tx

def migrate_phase_31():
    with tx() as (conn, cur):
        print("Migrating Phase 31: Interval Machine and Concurrency...")
        
        # 1. Add columns to daily_timesheets
        cur.execute("""
            ALTER TABLE daily_timesheets 
            ADD COLUMN IF NOT EXISTS worked_minutes_total INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS anomaly_flags JSONB DEFAULT '[]'::jsonb;
        """)
        
        print("Migration completed successfully.")

if __name__ == "__main__":
    migrate_phase_31()
