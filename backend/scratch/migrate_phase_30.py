import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def migrate():
    print("Starting migration for Phase 30 (SCD Type 2)...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # 1. Create schedule_assignments
        print("Creating schedule_assignments table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schedule_assignments (
                id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                employee_id         UUID         NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
                building_id         UUID         REFERENCES buildings(id) ON DELETE SET NULL,
                day_of_week         SMALLINT     NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
                start_time          TIME         NOT NULL,
                end_time            TIME         NOT NULL,
                is_overnight        BOOLEAN      NOT NULL DEFAULT FALSE,
                tolerance_minutes   INTEGER      NOT NULL DEFAULT 15,
                valid_from          DATE         NOT NULL DEFAULT '2026-01-01',
                valid_to            DATE,
                created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
            );
        """)

        # 2. Create compensation_rates
        print("Creating compensation_rates table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS compensation_rates (
                id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                employee_id         UUID         NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
                hourly_wage         NUMERIC(10, 2) NOT NULL DEFAULT 0,
                overtime_multiplier NUMERIC(5, 2)  NOT NULL DEFAULT 1.5,
                valid_from          DATE         NOT NULL DEFAULT '2026-01-01',
                valid_to            DATE,
                created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
            );
        """)

        # 3. Update daily_timesheets
        print("Updating daily_timesheets columns...")
        cur.execute("ALTER TABLE daily_timesheets ADD COLUMN IF NOT EXISTS schedule_assignment_id UUID REFERENCES schedule_assignments(id);")
        cur.execute("ALTER TABLE daily_timesheets ADD COLUMN IF NOT EXISTS compensation_rate_id UUID REFERENCES compensation_rates(id);")

        # 4. Migrate data from schedules to schedule_assignments
        print("Migrating schedules to schedule_assignments...")
        cur.execute("""
            INSERT INTO schedule_assignments (employee_id, building_id, day_of_week, start_time, end_time, is_overnight, tolerance_minutes, valid_from)
            SELECT employee_id, building_id, day_of_week, start_time, end_time, is_overnight, tolerance_minutes, '2026-01-01'
            FROM schedules
            ON CONFLICT DO NOTHING;
        """)

        # 5. Migrate current wages from employees to compensation_rates
        # We'll check if hourly_wage exists in employees first
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'employees' AND column_name = 'hourly_wage';")
        has_wage_col = cur.fetchone()
        
        if has_wage_col:
            print("Migrating hourly_wage from employees to compensation_rates...")
            cur.execute("""
                INSERT INTO compensation_rates (employee_id, hourly_wage, valid_from)
                SELECT id, hourly_wage, '2026-01-01'
                FROM employees
                ON CONFLICT DO NOTHING;
            """)
        else:
            print("No hourly_wage column found in employees. Creating initial records with 0...")
            cur.execute("""
                INSERT INTO compensation_rates (employee_id, hourly_wage, valid_from)
                SELECT id, 0, '2026-01-01'
                FROM employees
                ON CONFLICT DO NOTHING;
            """)

        # 6. Drop legacy schedules table
        # print("Dropping legacy schedules table...")
        # cur.execute("DROP TABLE IF EXISTS schedules CASCADE;")

        conn.commit()
        print("Migration Phase 30 completed successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Migration Phase 30 failed: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    migrate()
