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
                (SELECT COUNT(*) FROM buildings) as total_buildings
        """)
        
        # Simulación de métrica de puntualidad o promedio si se requiere
        # Por ahora enviamos las 3 bases solicitadas
        return jsonify({
            'active_employees': stats['active_employees'],
            'present_today': stats['present_today'],
            'total_buildings': stats['total_buildings'],
            'avg_punctuality': 94 # Estático por ahora
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
                rp.confidence_score
            FROM raw_punches rp
            JOIN employees e ON e.id = rp.employee_id
            LEFT JOIN buildings b ON b.id = e.primary_building_id
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
                'confidence': r['confidence_score']
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
            JOIN schedules s ON s.employee_id = e.id AND s.day_of_week = EXTRACT(DOW FROM rp.punch_time)
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
        
        return jsonify({'message': 'Resolución registrada con éxito'}), 200
        
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
        rows = query_all("""
            SELECT 
                e.full_name,
                e.hourly_wage,
                b.name AS building,
                dt.logical_date AS date,
                dt.first_punch_in AS first_in,
                dt.last_punch_out AS last_out,
                dt.status,
                dt.regular_minutes,
                dt.overtime_minutes,
                dt.deficit_minutes,
                (SELECT AVG(confidence_score) FROM raw_punches 
                 WHERE employee_id = e.id AND punch_time::date = dt.logical_date) AS bio_avg
            FROM daily_timesheets dt
            JOIN employees e ON e.id = dt.employee_id
            LEFT JOIN buildings b ON b.id = e.primary_building_id
            ORDER BY dt.logical_date DESC, e.full_name ASC
        """)

        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Empleado', 'Sede', 'Fecha', 'Entrada', 'Salida', 'Estado', 'Horas Reg.', 'Horas Extra', 'Déficit (Min)', 'Biometría (Avg)', 'Tarifa Hora', 'Pago Reg.', 'Pago Extra', 'Total'])
        
        for r in rows:
            wage = float(r['hourly_wage'] or 0)
            reg_pay = (r['regular_minutes'] / 60.0) * wage
            ext_pay = (r['overtime_minutes'] / 60.0) * wage * 1.5
            
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
                    e.id, e.full_name, e.job_title, e.status, e.hourly_wage,
                    b.name as building_name,
                    r.name as role_name
                FROM employees e
                LEFT JOIN buildings b ON b.id = e.primary_building_id
                JOIN roles r ON r.id = e.role_id
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
                cur.execute("""
                    INSERT INTO employees (full_name, job_title, primary_building_id, role_id, hourly_wage)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id
                """, (full_name, job_title, building_id, role_id, hourly_wage))
                row = cur.fetchone()
                
            return jsonify({'message': 'Empleado creado', 'id': str(row['id'])}), 201
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
                FROM schedules 
                WHERE employee_id = %s
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
                
                if not active:
                    # Si no es día laboral, eliminar si existe
                with tx() as (conn, cur):
                    cur.execute("""
                        INSERT INTO schedules (employee_id, day_of_week, start_time, end_time, building_id, is_overnight, tolerance_minutes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (employee_id, day_of_week) 
                        DO UPDATE SET 
                            start_time = EXCLUDED.start_time,
                            end_time = EXCLUDED.end_time,
                            building_id = EXCLUDED.building_id,
                            is_overnight = EXCLUDED.is_overnight,
                            tolerance_minutes = EXCLUDED.tolerance_minutes
                    """, (employee_id, day_num, start, end, build_id, overnight, tol))
                
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
