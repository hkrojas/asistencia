from utils.db import query_one

def migrate():
    print('Starting migration for Phase 24...')
    
    # 1. Añadir hourly_wage a employees
    try:
        query_one("ALTER TABLE employees ADD COLUMN hourly_wage NUMERIC(10, 2) DEFAULT 0;")
        print('Column hourly_wage added to employees.')
    except Exception as e:
        print(f'Note: hourly_wage might already exist or error: {e}')

    # 2. Crear tabla leaves
    try:
        query_one("""
            CREATE TABLE IF NOT EXISTS leaves (
                id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                employee_id     UUID         NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
                logical_date    DATE         NOT NULL,
                leave_type      VARCHAR(50)  NOT NULL, -- 'Vacaciones', 'Salud', 'Personal'
                is_paid         BOOLEAN      NOT NULL DEFAULT TRUE,
                created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
                UNIQUE (employee_id, logical_date)
            );
        """)
        print('Table leaves created.')
    except Exception as e:
        print(f'Error creating table leaves: {e}')

    print('Migration completed.')

if __name__ == '__main__':
    migrate()
