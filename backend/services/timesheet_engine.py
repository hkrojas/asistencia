import json
from datetime import datetime, date, timedelta
from utils.db import query_one, query_all, tx

def process_timesheet(employee_id, logical_date):
    """
    Consolida marcaciones crudas en una jornada interpretada para una fecha lógica usando Máquina de Intervalos.
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

        # Si el periodo existe y esta CERRADO, abortamos recalculo
        if period and period['state'] == 'closed':
            return False

        # --- BLOQUE TRANSACCIONAL PRINCIPAL ---
        with tx() as (conn, cur):
            # 1.5 CONCURRENCIA: Bloqueo consultivo para este empleado/fecha
            lock_key = f"{employee_id}_{logical_date}"
            cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (lock_key,))

            # 2. Obtener el horario configurado para esa fecha específica (SCD Tipo 2)
            schedule = query_one("""
                SELECT id, start_time, end_time, is_overnight, tolerance_minutes
                FROM schedule_assignments
                WHERE employee_id = %s AND day_of_week = %s
                AND %s >= valid_from AND (%s <= valid_to OR valid_to IS NULL)
            """, (employee_id, logical_date.weekday(), logical_date, logical_date))
            
            if not schedule:
                return None

            # 2.1 Tarifa de compensación
            rate = query_one("""
                SELECT id FROM compensation_rates
                WHERE employee_id = %s
                AND %s >= valid_from AND (%s <= valid_to OR valid_to IS NULL)
            """, (employee_id, logical_date, logical_date))

            # 2.2 Permisos (leave)
            leave = query_one("""
                SELECT leave_type, is_paid FROM leaves 
                WHERE employee_id = %s AND logical_date = %s
            """, (employee_id, logical_date))

            # 3. Obtener Marcaciones
            start_search = datetime.combine(logical_date, datetime.min.time())
            end_search = start_search + timedelta(hours=36 if schedule['is_overnight'] else 24)
            
            punches = query_all("""
                SELECT punch_time, punch_type
                FROM raw_punches
                WHERE employee_id = %s AND punch_time >= %s AND punch_time < %s
                ORDER BY punch_time ASC
            """, (employee_id, start_search, end_search))

            # 4. Procesar Marcaciones (Máquina de Estados e Intervalos)
            anomaly_flags = []
            filtered_punches = []
            
            # A) Debouncing (rebotes < 2 min del mismo tipo)
            for p in punches:
                if not filtered_punches:
                    filtered_punches.append(p)
                    continue
                last = filtered_punches[-1]
                diff_sec = (p['punch_time'] - last['punch_time']).total_seconds()
                if p['punch_type'] == last['punch_type'] and diff_sec < 120:
                    continue
                filtered_punches.append(p)

            # B) Emparejamiento de Intervalos
            intervals = []
            last_in = None
            for p in filtered_punches:
                if p['punch_type'] == 'in':
                    if last_in:
                        anomaly_flags.append("consecutive_in")
                    last_in = p['punch_time']
                elif p['punch_type'] == 'out':
                    if last_in:
                        intervals.append((last_in, p['punch_time']))
                        last_in = None
                    else:
                        anomaly_flags.append("orphan_out")
            
            if last_in:
                anomaly_flags.append("orphan_in")

            # 5. Cálculos Financieros y de Tiempo
            worked_minutes_total = 0
            regular_minutes = 0
            
            expected_start = datetime.combine(logical_date, schedule['start_time'])
            expected_end = datetime.combine(logical_date, schedule['end_time'])
            if schedule['is_overnight'] and expected_end <= expected_start:
                expected_end += timedelta(days=1)

            # Normalizar TZ si es necesario
            first_punch_in = None
            last_punch_out = None
            
            if intervals:
                first_punch_in = intervals[0][0]
                last_punch_out = intervals[-1][1]
                
                # TZ Normalization
                if first_punch_in.tzinfo:
                    expected_start = expected_start.replace(tzinfo=first_punch_in.tzinfo)
                    expected_end = expected_end.replace(tzinfo=first_punch_in.tzinfo)

                for start_p, end_p in intervals:
                    duration = int((end_p - start_p).total_seconds() / 60)
                    worked_minutes_total += duration
                    
                    # Calcular intersección con horario regular
                    inter_start = max(start_p, expected_start)
                    inter_end = min(end_p, expected_end)
                    if inter_end > inter_start:
                        regular_minutes += int((inter_end - inter_start).total_seconds() / 60)

            # Horas Extra y Déficit
            total_expected_mins = int((expected_end - expected_start).total_seconds() / 60)
            
            # Sobreescribir si hay permiso
            if leave:
                deficit_minutes = 0
                status = 'resolved'
            else:
                deficit_minutes = max(0, total_expected_mins - regular_minutes)
                # Overtime: lo que sobra de la jornada total
                overtime_minutes = max(0, worked_minutes_total - regular_minutes)
                
                # Status final
                if "orphan_in" in anomaly_flags or "orphan_out" in anomaly_flags:
                    status = 'incomplete'
                elif deficit_minutes > 0 or overtime_minutes > 0:
                    status = 'exception'
                else:
                    status = 'perfect'

            # 6. UPSERT Final
            cur.execute("""
                INSERT INTO daily_timesheets 
                    (employee_id, logical_date, schedule_assignment_id, compensation_rate_id, payroll_period_id,
                     first_punch_in, last_punch_out, regular_minutes, overtime_minutes, deficit_minutes, 
                     worked_minutes_total, status, anomaly_flags)
                VALUES 
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (employee_id, logical_date) DO UPDATE SET
                    schedule_assignment_id = EXCLUDED.schedule_assignment_id,
                    compensation_rate_id = EXCLUDED.compensation_rate_id,
                    payroll_period_id = EXCLUDED.payroll_period_id,
                    first_punch_in = EXCLUDED.first_punch_in,
                    last_punch_out = EXCLUDED.last_punch_out,
                    regular_minutes = EXCLUDED.regular_minutes,
                    overtime_minutes = EXCLUDED.overtime_minutes,
                    deficit_minutes = EXCLUDED.deficit_minutes,
                    worked_minutes_total = EXCLUDED.worked_minutes_total,
                    status = EXCLUDED.status,
                    anomaly_flags = EXCLUDED.anomaly_flags,
                    updated_at = NOW()
            """, (
                employee_id, logical_date, schedule['id'], rate['id'] if rate else None, period['id'] if period else None,
                first_punch_in, last_punch_out, regular_minutes, overtime_minutes, deficit_minutes,
                worked_minutes_total, status, json.dumps(anomaly_flags)
            ))
        
        return True
        
    except Exception as e:
        print(f'[timesheet_engine] Error crítico: {e}')
        return False
