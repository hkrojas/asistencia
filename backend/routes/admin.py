from flask import Blueprint, jsonify, Response, request
import os
import jwt
import csv
import io
from datetime import datetime, timedelta, date
from functools import wraps
from werkzeug.security import check_password_hash
import random
import hashlib
from utils.db import query_one, query_all, tx, execute
from services.timesheet_engine import process_timesheet

admin_bp = Blueprint('admin', __name__)

def require_auth(f):
    """Decorador para proteger rutas administrativas con JWT."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'error': 'Acceso denegado. Token no proporcionado.'}), 401
        
        try:
            jwt.decode(token, os.getenv('JWT_SECRET_KEY', 'super-secret'), algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Sesión expirada. Por favor inicie sesión de nuevo.'}), 401
        except Exception:
            return jsonify({'error': 'Token inválido o malformado.'}), 401
            
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/admin/stats', methods=['GET'])
@require_auth
def get_admin_stats():
    """Calcula las métricas principales para el dashboard de RRHH."""
    try:
        stats = query_one("""
            SELECT 
                (SELECT COUNT(*) FROM employees WHERE status = 'active') as active_employees,
                (SELECT COUNT(DISTINCT employee_id) FROM raw_punches 
                 WHERE punch_time::date = CURRENT_DATE 
                 AND punch_type = 'in') as present_today,
                (SELECT COUNT(*) FROM buildings) as total_buildings,
                (
                    SELECT COALESCE(
                        ROUND(
                            100.0 * COUNT(*) FILTER (
                                WHERE dt.status IN ('perfect', 'resolved')
                                  AND dt.deficit_minutes = 0
                            ) / NULLIF(COUNT(*), 0)
                        ),
                        0
                    )::int
                    FROM daily_timesheets dt
                    JOIN payroll_periods pp ON pp.id = dt.payroll_period_id
                    WHERE pp.state = 'open'
                ) as avg_punctuality
        """)

        return jsonify({
            'active_employees': stats['active_employees'],
            'present_today': stats['present_today'],
            'total_buildings': stats['total_buildings'],
            'avg_punctuality': stats.get('avg_punctuality') or 0
        }), 200
        
    except Exception as e:
        print(f'[admin] Error en get_admin_stats: {e}')
        return jsonify({'error': 'Error al obtener estadísticas'}), 500

@admin_bp.route('/admin/attendance', methods=['GET'])
@require_auth
def get_admin_attendance():
    """Retorna el historial reciente de registros para la tabla del dashboard."""
    try:
        rows = query_all("""
            SELECT 
                rp.id,
                e.full_name AS employee_name,
                b.name      AS building_name,
                rp.punch_type,
                rp.punch_time,
                rp.confidence_score,
                rp.biometric_status
            FROM raw_punches rp
            JOIN employees e ON e.id = rp.employee_id
            LEFT JOIN devices d ON d.id = rp.device_id
            LEFT JOIN buildings b ON b.id = COALESCE(d.building_id, e.primary_building_id)
            ORDER BY rp.punch_time DESC
            LIMIT 50
        """)
        
        # Formatear la data para el frontend
        records = []
        for r in rows:
            records.append({
                'id': str(r['id']),
                'employee': r['employee_name'],
                'building': r['building_name'] or 'N/A',
                'action': r['punch_type'],
                'time': r['punch_time'].isoformat(),
                'method': 'Biométrico',
                'confidence': r['confidence_score'],
                'biometric_status': r['biometric_status']
            })
            
        return jsonify(records), 200
        
    except Exception as e:
        print(f'[admin] Error en get_admin_attendance: {e}')
        return jsonify({'error': 'Error al obtener historial de asistencia'}), 500

@admin_bp.route('/admin/exceptions/pending', methods=['GET'])
@require_auth
def get_pending_exceptions():
    """Identifica registros de salida con tiempo excedente sin resolución."""
    try:
        # Buscamos marcaciones de check_out que excedan por > 15 min el horario planificado
        rows = query_all("""
            SELECT 
                rp.id AS log_id,
                e.id AS employee_id,
                e.full_name AS employee_name,
                s.start_time,
                s.end_time,
                rp.punch_time::time AS actual_out,
                rp.punch_time::date AS date,
                EXTRACT(EPOCH FROM (rp.punch_time::time - s.end_time))/60 AS excess_minutes
            FROM raw_punches rp
            JOIN employees e ON e.id = rp.employee_id
            JOIN schedule_assignments s
              ON s.employee_id = e.id
             AND s.day_of_week = (EXTRACT(ISODOW FROM rp.punch_time)::int - 1)
             AND rp.punch_time::date >= s.valid_from
             AND (rp.punch_time::date <= s.valid_to OR s.valid_to IS NULL)
            LEFT JOIN time_exceptions te ON te.employee_id = e.id AND te.date = rp.punch_time::date
            WHERE rp.punch_type = 'out'
            AND te.id IS NULL
            AND (rp.punch_time::time - s.end_time) > INTERVAL '15 minutes'
            ORDER BY rp.punch_time DESC
        """)
        
        results = []
        for r in rows:
            results.append({
                'id': str(r['log_id']),
                'employee': r['employee_name'],
                'date': r['date'].isoformat(),
                'scheludedTime': f"{r['start_time'].strftime('%H:%M')} - {r['end_time'].strftime('%H:%M')}",
                'actualTime': f"-- : -- - {r['actual_out'].strftime('%H:%M')}",
                'excess': f"+{int(r['excess_minutes'])}m",
                'minutes': int(r['excess_minutes']),
                'employeeId': str(r['employee_id'])
            })
            
        return jsonify(results), 200
        
    except Exception as e:
        print(f'[admin] Error en get_pending_exceptions: {e}')
        return jsonify({'error': 'Error al obtener incidencias'}), 500

@admin_bp.route('/admin/exceptions/resolve', methods=['POST'])
@require_auth
def resolve_exception():
    """Registra la resolución de una incidencia en time_exceptions."""
    from flask import request
    data = request.json
    
    try:
        log_id = data.get('logId')
        res_type = data.get('resolutionType')
        admin_id = data.get('adminId', 'a1b2c3d4-0000-0000-0000-000000000002') # Admin RRHH por defecto
        
        # Primero obtenemos el employee_id y la fecha del log original
        log_data = query_one("SELECT employee_id, punch_time::date FROM raw_punches WHERE id = %s", (log_id,))
        
        if not log_data:
            return jsonify({'error': 'Log no encontrado'}), 404
            
        # Calculamos minutos de ajuste si no vienen (simplificado)
        minutes = data.get('minutes_adjusted', 60) 

        with tx() as (conn, cur):
            cur.execute("""
                INSERT INTO time_exceptions (employee_id, date, exception_type, minutes_adjusted, approved_by, reason)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (log_data['employee_id'], log_data['punch_time'], res_type, minutes, admin_id, 'Resolución desde Panel Web'))

        process_timesheet(log_data['employee_id'], log_data['punch_time'])
        
        return jsonify({'message': 'Resolución registrada y jornada recalculada con éxito'}), 200
        
    except Exception as e:
        print(f'[admin] Error en resolve_exception: {e}')
        return jsonify({'error': 'Error al registrar resolución'}), 500
@admin_bp.route('/admin/login', methods=['POST'])
def admin_login():
    """Valida credenciales contra DB y genera JWT."""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user = query_one("SELECT * FROM system_users WHERE username = %s AND is_active = TRUE", (username,))
    
    if user and check_password_hash(user['password_hash'], password):
        # Generar Token (Validez 8 horas)
        token = jwt.encode({
            'user_id': str(user['id']),
            'username': user['username'],
            'exp': datetime.utcnow() + timedelta(hours=8)
        }, os.getenv('JWT_SECRET_KEY', 'super-secret'), algorithm="HS256")
        
        return jsonify({
            'success': True,
            'token': token,
            'message': 'Bienvenido al sistema'
        }), 200
        
    return jsonify({'success': False, 'error': 'Credenciales inválidas'}), 401

@admin_bp.route('/admin/export/csv', methods=['GET'])
@require_auth
def export_attendance_csv():
    """Genera y descarga un reporte CSV basado en jornadas procesadas."""
    try:
        period_id = request.args.get('period_id')
        query = """
            SELECT 
                e.full_name, b.name AS building,
                dt.logical_date AS date, dt.first_punch_in AS first_in,
                dt.last_punch_out AS last_out, dt.status,
                dt.regular_minutes, dt.overtime_minutes, dt.deficit_minutes,
                cr.hourly_wage, cr.overtime_multiplier,
                (SELECT AVG(confidence_score) FROM raw_punches 
                 WHERE employee_id = e.id AND punch_time::date = dt.logical_date) AS bio_avg
            FROM daily_timesheets dt
            JOIN employees e ON e.id = dt.employee_id
            LEFT JOIN buildings b ON b.id = e.primary_building_id
            LEFT JOIN compensation_rates cr ON cr.id = dt.compensation_rate_id
        """
        params = []
        if period_id:
            query += " WHERE dt.payroll_period_id = %s "
            params.append(period_id)
            
        query += " ORDER BY dt.logical_date DESC, e.full_name ASC"
        rows = query_all(query, params)

        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Empleado', 'Sede', 'Fecha', 'Entrada', 'Salida', 'Estado', 'Horas Reg.', 'Horas Extra', 'Déficit (Min)', 'Biometría (Avg)', 'Tarifa Hora', 'Pago Reg.', 'Pago Extra', 'Total'])
        
        for r in rows:
            # Si no hay rate_id en el timesheet (registros viejos), buscamos el vigente
            wage = float(r['hourly_wage'] or 0)
            multiplier = float(r['overtime_multiplier'] or 1.5)
            
            reg_pay = (r['regular_minutes'] / 60.0) * wage
            ext_pay = (r['overtime_minutes'] / 60.0) * wage * multiplier
            
            writer.writerow([
                r['full_name'],
                r['building'] or 'N/A',
                r['date'].isoformat(),
                r['first_in'].strftime('%H:%M') if r['first_in'] else '--:--',
                r['last_out'].strftime('%H:%M') if r['last_out'] else '--:--',
                r['status'].capitalize(),
                f"{r['regular_minutes']/60:.1f}h",
                f"{r['overtime_minutes']/60:.1f}h",
                r['deficit_minutes'],
                f"{r['bio_avg']:.1f}%" if r['bio_avg'] else "N/A",
                f"S/ {wage:.2f}",
                f"S/ {reg_pay:.2f}",
                f"S/ {ext_pay:.2f}",
                f"S/ {(reg_pay + ext_pay):.2f}"
            ])
            
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=reporte_asistencia_final.csv"}
        )
        
    except Exception as e:
        print(f'[admin] Error en export_attendance_csv: {e}')
        return jsonify({'error': 'Error al generar CSV'}), 500

@admin_bp.route('/admin/buildings', methods=['GET', 'POST'])
@require_auth
def manage_buildings():
    from flask import request
    if request.method == 'GET':
        try:
            buildings = query_all("SELECT id, name, address FROM buildings ORDER BY name ASC")
            return jsonify(buildings), 200
        except Exception as e:
            print(f'[admin] Error en manage_buildings GET: {e}')
            return jsonify({'error': 'Error al obtener sedes'}), 500
    
    if request.method == 'POST':
        data = request.json
        try:
            name = data.get('name')
            address = data.get('address')
            if not name:
                return jsonify({'error': 'El nombre es obligatorio'}), 400
                
            with tx() as (conn, cur):
                cur.execute("""
                    INSERT INTO buildings (name, address) 
                    VALUES (%s, %s) RETURNING id
                """, (name, address))
                row = cur.fetchone()
                
            return jsonify({'message': 'Sede creada', 'id': str(row['id'])}), 201
        except Exception as e:
            print(f'[admin] Error en manage_buildings POST: {e}')
            return jsonify({'error': 'Error al crear sede'}), 500

@admin_bp.route('/admin/employees', methods=['GET', 'POST'])
@require_auth
def manage_employees():
    from flask import request
    if request.method == 'GET':
        try:
            employees = query_all("""
                SELECT 
                    e.id, e.full_name, e.job_title, e.status,
                    cr.hourly_wage,
                    b.name as building_name,
                    r.name as role_name
                FROM employees e
                LEFT JOIN buildings b ON b.id = e.primary_building_id
                JOIN roles r ON r.id = e.role_id
                LEFT JOIN compensation_rates cr ON cr.employee_id = e.id AND cr.valid_to IS NULL
                ORDER BY e.full_name ASC
            """)
            # Convert UUIDs and timestamps to strings if necessary (query_all usually handles this but safety first)
            for e in employees:
                e['id'] = str(e['id'])
            return jsonify(employees), 200
        except Exception as e:
            print(f'[admin] Error en manage_employees GET: {e}')
            return jsonify({'error': 'Error al obtener empleados'}), 500
            
    if request.method == 'POST':
        data = request.json
        try:
            full_name = data.get('full_name')
            job_title = data.get('job_title')
            building_id = data.get('primary_building_id')
            role_id = data.get('role_id', '00000000-0000-0000-0000-000000000001')
            hourly_wage = data.get('hourly_wage', 0)
            
            if not full_name:
                return jsonify({'error': 'El nombre es obligatorio'}), 400
                
            with tx() as (conn, cur):
                # 1. Crear empleado
                cur.execute("""
                    INSERT INTO employees (full_name, job_title, primary_building_id, role_id)
                    VALUES (%s, %s, %s, %s) RETURNING id
                """, (full_name, job_title, building_id, role_id))
                emp_id = cur.fetchone()['id']
                
                # 2. Crear tarifa inicial
                cur.execute("""
                    INSERT INTO compensation_rates (employee_id, hourly_wage, valid_from)
                    VALUES (%s, %s, %s)
                """, (emp_id, hourly_wage, date.today()))
                
            return jsonify({'message': 'Empleado creado', 'id': str(emp_id)}), 201
        except Exception as e:
            print(f'[admin] Error en manage_employees POST: {e}')
            return jsonify({'error': 'Error al crear empleado'}), 500

@admin_bp.route('/admin/roles', methods=['GET'])
@require_auth
def get_roles():
    try:
        roles = query_all("SELECT id, name FROM roles ORDER BY name ASC")
        for r in roles:
            r['id'] = str(r['id'])
        return jsonify(roles), 200
    except Exception as e:
        return jsonify({'error': 'Error al obtener roles'}), 500

@admin_bp.route('/admin/employees/<uuid:employee_id>/schedule', methods=['GET', 'POST'])
@require_auth
def manage_employee_schedule(employee_id):
    from flask import request
    if request.method == 'GET':
        try:
            schedules = query_all("""
                SELECT 
                    day_of_week, start_time, end_time, 
                    building_id, is_overnight, tolerance_minutes
                FROM schedule_assignments 
                WHERE employee_id = %s AND valid_to IS NULL
                ORDER BY day_of_week ASC
            """, (employee_id,))
            
            for s in schedules:
                if s['start_time']: s['start_time'] = s['start_time'].strftime('%H:%M')
                if s['end_time']: s['end_time'] = s['end_time'].strftime('%H:%M')
                s['building_id'] = str(s['building_id']) if s['building_id'] else None
                
            return jsonify(schedules), 200
        except Exception as e:
            print(f'[admin] Error en GET schedule: {e}')
            return jsonify({'error': 'Error al obtener horario'}), 500

    if request.method == 'POST':
        data = request.json # Arreglo de objetos por día
        if not isinstance(data, list):
            return jsonify({'error': 'Se esperaba un arreglo de horarios'}), 400
            
        try:
            for day in data:
                day_num = day.get('day_of_week')
                start = day.get('start_time')
                end = day.get('end_time')
                build_id = day.get('building_id')
                overnight = day.get('is_overnight', False)
                tol = day.get('tolerance_minutes', 15)
                active = day.get('active', True)
                
                if active and (not start or not end):
                    return jsonify({'error': 'start_time y end_time son obligatorios para dÃ­as activos'}), 400

                # Day-level deactivation is handled after fetching the active row.
                with tx() as (conn, cur):
                    # Buscamos si ya existe un registro vigente idéntico
                    cur.execute("""
                        SELECT id, start_time, end_time, building_id, is_overnight, tolerance_minutes
                        FROM schedule_assignments
                        WHERE employee_id = %s AND day_of_week = %s AND valid_to IS NULL
                    """, (employee_id, day_num))
                    existing = cur.fetchone()

                    if not active:
                        if existing:
                            cur.execute("""
                                UPDATE schedule_assignments
                                SET valid_to = %s
                                WHERE id = %s
                            """, (date.today() - timedelta(days=1), existing['id']))
                        continue

                    # Lógica de Versiones (SCD Tipo 2)
                    if existing:
                        # Si algo cambió, cerramos el actual e insertamos nuevo
                        changed = (
                            existing['start_time'].strftime('%H:%M') != start or 
                            existing['end_time'].strftime('%H:%M') != end or
                            str(existing['building_id']) != str(build_id) or
                            existing['is_overnight'] != overnight or
                            existing['tolerance_minutes'] != tol
                        )
                        
                        if changed:
                            # Cerrar actual
                            cur.execute("""
                                UPDATE schedule_assignments 
                                SET valid_to = %s 
                                WHERE id = %s
                            """, (date.today() - timedelta(days=1), existing['id']))
                            
                            # Insertar nuevo
                            cur.execute("""
                                INSERT INTO schedule_assignments (employee_id, day_of_week, start_time, end_time, building_id, is_overnight, tolerance_minutes, valid_from)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """, (employee_id, day_num, start, end, build_id, overnight, tol, date.today()))
                    else:
                        # Si no existe, insertar nuevo
                        cur.execute("""
                            INSERT INTO schedule_assignments (employee_id, day_of_week, start_time, end_time, building_id, is_overnight, tolerance_minutes, valid_from)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (employee_id, day_num, start, end, build_id, overnight, tol, date.today()))
                
            return jsonify({'message': 'Horario actualizado correctamente'}), 200
        except Exception as e:
            print(f'[admin] Error en POST schedule: {e}')
            return jsonify({'error': 'Error al actualizar horario'}), 500

@admin_bp.route('/admin/leaves', methods=['POST'])
@require_auth
def create_leave():
    """Registra una ausencia justificada para un empleado."""
    try:
        data = request.json
        employee_id = data.get('employee_id')
        logical_date = data.get('logical_date')
        leave_type = data.get('leave_type')
        is_paid = data.get('is_paid', True)

        if not employee_id or not logical_date or not leave_type:
            return jsonify({'error': 'Faltan datos obligatorios'}), 400

        with tx() as (conn, cur):
            cur.execute("""
                INSERT INTO leaves (employee_id, logical_date, leave_type, is_paid)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (employee_id, logical_date) DO UPDATE SET
                    leave_type = EXCLUDED.leave_type,
                    is_paid = EXCLUDED.is_paid
            """, (employee_id, logical_date, leave_type, is_paid))
        
        # Al registrar un permiso, forzamos el reprocesamiento del timesheet para ese día
        from services.timesheet_engine import process_timesheet
        process_timesheet(employee_id, logical_date)
        
        return jsonify({'message': 'Permiso registrado correctamente'}), 201
    except Exception as e:
        print(f'[admin] Error en POST leaves: {e}')
        return jsonify({'error': 'Error al registrar permiso'}), 500

@admin_bp.route('/admin/timesheets/process', methods=['POST'])
@require_auth
def process_all_timesheets():
    """
    Procesa las jornadas para todos los empleados activos en un rango de fechas.
    """
    try:
        data = request.json or {}
        # Default: últimos 7 días
        period_id = data.get('period_id')

        if period_id:
            period = query_one(
                """
                SELECT id, starts_on, ends_on, state
                  FROM payroll_periods
                 WHERE id = %s
                """,
                (period_id,)
            )
            if not period:
                return jsonify({'error': 'Periodo no encontrado'}), 404
            if period['state'] == 'closed':
                return jsonify({'error': 'No se puede procesar un periodo cerrado'}), 400

            start_date = period['starts_on']
            end_date = period['ends_on']
        else:
            end_date = date.today()
            start_date = end_date - timedelta(days=7)
        
            if 'start_date' in data:
                start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            if 'end_date' in data:
                end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            
        # Obtener empleados activos
        active_employees = query_all("SELECT id FROM employees WHERE status = 'active'")
        
        count = 0
        current_date = start_date
        while current_date <= end_date:
            for emp in active_employees:
                if process_timesheet(emp['id'], current_date):
                    count += 1
            current_date += timedelta(days=1)
            
        return jsonify({
            'message': 'Procesamiento completado',
            'days_processed': (end_date - start_date).days + 1,
            'records_updated': count
        }), 200
    except Exception as e:
        print(f'[admin] Error en process_all_timesheets: {e}')
        return jsonify({'error': str(e)}), 500
@admin_bp.route('/admin/devices/pairing-code', methods=['POST'])
@require_auth
def generate_pairing_code():
    """Genera un código de emparejamiento de 6 dígitos para un edificio."""
    data = request.get_json(silent=True)
    if not data or 'building_id' not in data:
        return jsonify({'error': 'building_id es requerido'}), 400
        
    building_id = data['building_id']
    # Generar código de 6 dígitos
    code = f"{random.randint(0, 999999):06d}"
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    expires_at = datetime.now() + timedelta(minutes=15)
    
    try:
        with tx() as (conn, cur):
            cur.execute("""
                INSERT INTO device_pairing_codes (code_hash, building_id, expires_at)
                VALUES (%s, %s, %s)
            """, (code_hash, building_id, expires_at))
            
        return jsonify({
            'code': code,
            'expires_at': expires_at.isoformat()
        }), 201
    except Exception as e:
        print(f'[admin] Error al generar pairing code: {e}')
        return jsonify({'error': 'Error interno al generar código'}), 500

@admin_bp.route('/admin/payroll-periods', methods=['GET', 'POST'])
@require_auth
def manage_payroll_periods():
    if request.method == 'GET':
        try:
            periods = query_all("SELECT * FROM payroll_periods ORDER BY starts_on DESC")
            for p in periods:
                p['id'] = str(p['id'])
                p['starts_on'] = p['starts_on'].isoformat()
                p['ends_on'] = p['ends_on'].isoformat()
                if p['closed_at']: p['closed_at'] = p['closed_at'].isoformat()
            return jsonify(periods), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    if request.method == 'POST':
        data = request.json
        try:
            name = data.get('name')
            start = data.get('starts_on')
            end = data.get('ends_on')
            
            with tx() as (conn, cur):
                cur.execute("""
                    INSERT INTO payroll_periods (name, starts_on, ends_on)
                    VALUES (%s, %s, %s) RETURNING id
                """, (name, start, end))
                row = cur.fetchone()
            return jsonify({'id': str(row['id'])}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/payroll-periods/<uuid:period_id>/close', methods=['POST'])
@require_auth
def close_payroll_period(period_id):
    """Cierra el periodo y bloquea todos los timesheets asociados."""
    try:
        period = query_one(
            "SELECT id, state FROM payroll_periods WHERE id = %s",
            (period_id,)
        )
        if not period:
            return jsonify({'error': 'Periodo no encontrado'}), 404
        if period['state'] == 'closed':
            return jsonify({'error': 'El periodo ya esta cerrado'}), 400

        unresolved = query_one("""
            SELECT COUNT(*) AS unresolved_count
              FROM daily_timesheets
             WHERE payroll_period_id = %s
               AND status <> 'resolved'
               AND (
                    status IN ('incomplete', 'exception')
                    OR (anomaly_flags IS NOT NULL AND anomaly_flags <> '[]'::jsonb)
                    OR overtime_minutes > 0
               )
        """, (period_id,))
        unresolved_count = int(unresolved['unresolved_count'] or 0) if unresolved else 0
        if unresolved_count > 0:
            return jsonify({
                'error': 'No se puede cerrar un periodo con incidencias WFM pendientes',
                'unresolved_count': unresolved_count
            }), 409

        with tx() as (conn, cur):
            cur.execute("""
                UPDATE payroll_periods 
                SET state = 'closed', closed_at = NOW()
                WHERE id = %s
            """, (period_id,))
            
            # 2. Bloqueo masivo en daily_timesheets
            cur.execute("""
                UPDATE daily_timesheets 
                SET is_locked = TRUE 
                WHERE payroll_period_id = %s
            """, (period_id,))
            
        return jsonify({'message': 'Periodo cerrado y bloqueado con exito'}), 200
    except Exception as e:
        print(f'[admin] Error al cerrar periodo: {e}')
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/wfm/issues', methods=['GET'])
@require_auth
def get_wfm_issues():
    """Retorna los timesheets con anomalías o pendientes de revisión en periodos abiertos."""
    try:
        rows = query_all("""
            SELECT 
                dt.id, e.full_name, dt.logical_date, dt.status, dt.anomaly_flags, 
                dt.overtime_minutes, dt.first_punch_in, dt.last_punch_out
            FROM daily_timesheets dt
            JOIN employees e ON e.id = dt.employee_id
            JOIN payroll_periods pp ON pp.id = dt.payroll_period_id
            WHERE pp.state = 'open'
            AND dt.status <> 'resolved'
            AND (
                dt.status IN ('incomplete', 'exception') 
                OR (dt.anomaly_flags IS NOT NULL AND dt.anomaly_flags <> '[]'::jsonb)
                OR dt.overtime_minutes > 0
            )
            ORDER BY dt.logical_date DESC, e.full_name ASC
        """)
        
        for r in rows:
            r['id'] = str(r['id'])
            r['logical_date'] = r['logical_date'].isoformat()
            if r['first_punch_in']: r['first_punch_in'] = r['first_punch_in'].isoformat()
            if r['last_punch_out']: r['last_punch_out'] = r['last_punch_out'].isoformat()
            
        return jsonify(rows), 200
    except Exception as e:
        print(f'[admin] Error en get_wfm_issues: {e}')
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/wfm/resolve/<uuid:timesheet_id>', methods=['POST'])
@require_auth
def resolve_wfm_issue(timesheet_id):
    """Resuelve una anomalía insertando una marcación manual y recalculando."""
    data = request.json
    action = data.get('action') # 'manual_in', 'manual_out'
    time_str = data.get('time') # 'HH:MM'
    reason = data.get('reason')
    if action not in ('manual_in', 'manual_out'):
        return jsonify({'error': 'Accion correctiva invalida'}), 400
    if not time_str or not reason:
        return jsonify({'error': 'Hora y justificacion son obligatorias'}), 400
    
    try:
        # 1. Obtener datos básicos del timesheet
        ts = query_one("SELECT employee_id, logical_date FROM daily_timesheets WHERE id = %s", (timesheet_id,))
        if not ts:
            return jsonify({'error': 'Timesheet no encontrado'}), 404
            
        # 2. Insertar marcación manual
        punch_type = 'in' if action == 'manual_in' else 'out'
        # Construir el timestamp completo
        punch_time = datetime.combine(ts['logical_date'], datetime.strptime(time_str, '%H:%M').time())
        
        # Si es overnight o fuera de fecha lógica, esto podría ser complejo, 
        # pero por ahora asumimos que la hora ingresada es para esa fecha lógica.
        
        with tx() as (conn, cur):
            cur.execute("""
                INSERT INTO raw_punches (employee_id, punch_time, punch_type, ingest_status, biometric_status)
                VALUES (%s, %s, %s, 'accepted', 'bypassed')
            """, (ts['employee_id'], punch_time, punch_type))

            cur.execute("""
                INSERT INTO time_exceptions (
                    employee_id, date, exception_type, minutes_adjusted, approved_by, reason
                )
                VALUES (%s, %s, 'manual_punch', 0, %s, %s)
            """, (
                ts['employee_id'],
                ts['logical_date'],
                data.get('adminId', 'a1b2c3d4-0000-0000-0000-000000000002'),
                reason
            ))
            
        # 3. Recalcular
        process_timesheet(ts['employee_id'], ts['logical_date'])
        
        return jsonify({'message': 'Acción correctiva aplicada y jornada recalculada'}), 200
        
    except Exception as e:
        print(f'[admin] Error en resolve_wfm_issue: {e}')
        return jsonify({'error': str(e)}), 500
