import os
import uuid
from datetime import datetime, date, time, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv('backend/.env')

def seed_exceptions():
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    employee_id = 'a1b2c3d4-0000-0000-0000-000000000001' # Juan Pérez
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # Obtener el device_id real
    cur.execute("SELECT id FROM devices LIMIT 1")
    dev = cur.fetchone()
    device_id = dev['id'] if dev else str(uuid.uuid4())

    print(f"Limpiando datos previos de {employee_id} para hoy y ayer...")
    cur.execute("DELETE FROM time_exceptions WHERE employee_id = %s AND date >= %s", (employee_id, yesterday))
    cur.execute("DELETE FROM raw_punches WHERE employee_id = %s AND punch_time::date >= %s", (employee_id, yesterday))
    
    records = [
        (employee_id, device_id, datetime.combine(today, time(8, 5)), 'in'),
        (employee_id, device_id, datetime.combine(today, time(19, 45)), 'out'),
        (employee_id, device_id, datetime.combine(yesterday, time(8, 0)), 'in'),
        (employee_id, device_id, datetime.combine(yesterday, time(20, 30)), 'out')
    ]
    
    print("Insertando registros de prueba en raw_punches...")
    for emp, dev, t, act in records:
        cur.execute(
            "INSERT INTO raw_punches (employee_id, device_id, punch_time, punch_type, confidence_score) VALUES (%s, %s, %s, %s, %s)",
            (emp, dev, t, act, 98.5)
        )
    
    conn.commit()
    cur.close()
    conn.close()
    print("Seeding completado. Las incidencias deberían aparecer en el panel.")

if __name__ == "__main__":
    seed_exceptions()
