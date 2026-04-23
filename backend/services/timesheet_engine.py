from datetime import datetime, date, timedelta
from utils.db import query_one, query_all, tx

def process_timesheet(employee_id, logical_date):
    """
    Consolida marcaciones crudas en una jornada interpretada para una fecha lógica.
    """
    try:
        # Asegurar que logical_date sea un objeto date
        if isinstance(logical_date, str):
            logical_date = datetime.strptime(logical_date, '%Y-%m-%d').date()

        # 1.2 Verificar Periodo de Nomina y Bloqueo
        period = query_one("""
            SELECT id, state FROM payroll_periods 
            WHERE %s BETWEEN starts_on AND ends_on
        """, (logical_date,))

        # Si el periodo existe y esta CERRADO, abortamos y marcamos marcaciones como tardias
        if period and period['state'] == 'closed':
            print(f"[timesheet_engine] Periodo CERRADO para {logical_date}. Bloqueando edicion.")
            with tx() as (conn, cur):
                cur.execute("""
                    UPDATE raw_punches 
                    SET ingest_status = 'late_pending_review'
                    WHERE employee_id = %s 
                    AND punch_time::date = %s
                    AND ingest_status = 'accepted'
                """, (employee_id, logical_date))
            return False # Abortamos recalculo

        # 1.3 Determinar el dia de la semana (0=Lunes, 6=Domingo)
        day_of_week = logical_date.weekday()

        # 2. Obtener el horario configurado
        schedule = query_one("""
            SELECT id, start_time, end_time, is_overnight, tolerance_minutes
            FROM schedules
            WHERE employee_id = %s AND day_of_week = %s
        """, (employee_id, day_of_week))
        
        if not schedule:
            # Si no hay horario, no procesamos timesheet (día libre)
            return None

        # 2.5 Verificar si hay un permiso (leave) registrado para este día
        leave = query_one("""
            SELECT leave_type, is_paid FROM leaves 
            WHERE employee_id = %s AND logical_date = %s
        """, (employee_id, logical_date))

        # 3. Definir ventana de búsqueda de marcaciones
        # Buscamos desde el inicio del día lógico hasta 36h después si es overnight, 24h sino.
        start_search = datetime.combine(logical_date, datetime.min.time())
        end_search = start_search + timedelta(hours=36 if schedule['is_overnight'] else 24)
        
        punches = query_all("""
            SELECT punch_time, punch_type
            FROM raw_punches
            WHERE employee_id = %s AND punch_time >= %s AND punch_time < %s
            ORDER BY punch_time ASC
        """, (employee_id, start_search, end_search))
        
        # 4. Caso: No hay marcaciones
        if not punches:
            # Si hay permiso, el status es 'leave' y deficit es 0
            if leave:
                with tx() as (conn, cur):
                    cur.execute("""
                        INSERT INTO daily_timesheets (employee_id, logical_date, schedule_id, deficit_minutes, status, payroll_period_id)
                        VALUES (%s, %s, %s, 0, 'resolved', %s)
                        ON CONFLICT (employee_id, logical_date) DO UPDATE SET
                            schedule_id = EXCLUDED.schedule_id,
                            deficit_minutes = 0,
                            status = 'resolved',
                            payroll_period_id = EXCLUDED.payroll_period_id,
                            updated_at = NOW()
                    """, (employee_id, logical_date, schedule['id'], period['id'] if period else None))
                return True

            expected_start = datetime.combine(logical_date, schedule['start_time'])
            expected_end = datetime.combine(logical_date, schedule['end_time'])
            if schedule['is_overnight'] and expected_end <= expected_start:
                expected_end += timedelta(days=1)
            
            duration = int((expected_end - expected_start).total_seconds() / 60)
            
            with tx() as (conn, cur):
                cur.execute("""
                    INSERT INTO daily_timesheets (employee_id, logical_date, schedule_id, deficit_minutes, status, payroll_period_id)
                    VALUES (%s, %s, %s, %s, 'exception', %s)
                    ON CONFLICT (employee_id, logical_date) DO UPDATE SET
                        schedule_id = EXCLUDED.schedule_id,
                        deficit_minutes = EXCLUDED.deficit_minutes,
                        status = EXCLUDED.status,
                        payroll_period_id = EXCLUDED.payroll_period_id,
                        updated_at = NOW()
                """, (employee_id, logical_date, schedule['id'], duration, period['id'] if period else None))
            return True
            
        # 5. Extraer primer IN y último OUT
        first_in = next((p['punch_time'] for p in punches if p['punch_type'] == 'in'), None)
        last_out = next((p['punch_time'] for p in reversed(punches) if p['punch_type'] == 'out'), None)
        
        # Si falta alguna de las marcaciones
        if not first_in or not last_out:
            with tx() as (conn, cur):
                cur.execute("""
                    INSERT INTO daily_timesheets (employee_id, logical_date, schedule_id, first_punch_in, last_punch_out, status, payroll_period_id)
                    VALUES (%s, %s, %s, %s, %s, 'incomplete', %s)
                    ON CONFLICT (employee_id, logical_date) DO UPDATE SET
                        first_punch_in = EXCLUDED.first_punch_in,
                        last_punch_out = EXCLUDED.last_punch_out,
                        status = 'incomplete',
                        payroll_period_id = EXCLUDED.payroll_period_id,
                        updated_at = NOW()
                """, (employee_id, logical_date, schedule['id'], first_in, last_out, period['id'] if period else None))
            return True

        # 6. Cálculos de Tiempos
        expected_start = datetime.combine(logical_date, schedule['start_time'])
        expected_end = datetime.combine(logical_date, schedule['end_time'])
        if schedule['is_overnight'] and expected_end <= expected_start:
            expected_end += timedelta(days=1)
            
        # Normalizar zonas horarias si es necesario (si punches tienen TZ)
        if first_in.tzinfo:
            expected_start = expected_start.replace(tzinfo=first_in.tzinfo)
            expected_end = expected_end.replace(tzinfo=first_in.tzinfo)

        # Minutos Trabajados dentro de jornada
        work_start = max(first_in, expected_start)
        work_end = min(last_out, expected_end)
        
        regular_mins = max(0, int((work_end - work_start).total_seconds() / 60))
        
        # Horas Extra
        overtime_mins = 0
        if last_out > (expected_end + timedelta(minutes=schedule['tolerance_minutes'])):
            overtime_mins = int((last_out - expected_end).total_seconds() / 60)
            
        # Déficit
        total_expected = int((expected_end - expected_start).total_seconds() / 60)
        deficit_mins = max(0, total_expected - regular_mins)
        
        # Si hay permiso, perdonamos el déficit
        if leave:
            deficit_mins = 0
            status = 'resolved'
        else:
            # Status final
            # Si hay déficit o demasia horas extra, es exception
            status = 'perfect' if deficit_mins == 0 and overtime_mins == 0 else 'exception'
        
        # 7. Guardar resultados (UPSERT)
        with tx() as (conn, cur):
            cur.execute("""
                INSERT INTO daily_timesheets 
                    (employee_id, logical_date, schedule_id, first_punch_in, last_punch_out, regular_minutes, overtime_minutes, deficit_minutes, status, payroll_period_id)
                VALUES 
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (employee_id, logical_date) DO UPDATE SET
                    schedule_id = EXCLUDED.schedule_id,
                    first_punch_in = EXCLUDED.first_punch_in,
                    last_punch_out = EXCLUDED.last_punch_out,
                    regular_minutes = EXCLUDED.regular_minutes,
                    overtime_minutes = EXCLUDED.overtime_minutes,
                    deficit_minutes = EXCLUDED.deficit_minutes,
                    status = EXCLUDED.status,
                    payroll_period_id = EXCLUDED.payroll_period_id,
                    updated_at = NOW()
            """, (employee_id, logical_date, schedule['id'], first_in, last_out, regular_mins, overtime_mins, deficit_mins, status, period['id'] if period else None))
        
        return True
        
    except Exception as e:
        print(f'[timesheet_engine] Error procesando {employee_id} en {logical_date}: {e}')
        return False
