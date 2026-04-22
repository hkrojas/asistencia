from flask import Blueprint, jsonify, Response, request
import csv
import io
from datetime import datetime, timedelta, date
from utils.db import query_one, query_all
from services.timesheet_engine import process_timesheet

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/stats', methods=['GET'])
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

        query_one("""
            INSERT INTO time_exceptions (employee_id, date, exception_type, minutes_adjusted, approved_by, reason)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (log_data['employee_id'], log_data['punch_time'], res_type, minutes, admin_id, 'Resolución desde Panel Web'))
        
        return jsonify({'message': 'Resolución registrada con éxito'}), 200
        
    except Exception as e:
        print(f'[admin] Error en resolve_exception: {e}')
        return jsonify({'error': 'Error al registrar resolución'}), 500
@admin_bp.route('/admin/login', methods=['POST'])
def admin_login():
    """Valida las credenciales del administrador para el panel web."""
    from flask import request
    data = request.json
    
    username = data.get('username')
    password = data.get('password')
    
    # Lógica MVP de validación
    if username == "admin" and password == "Hernandez2026":
        return jsonify({
            'success': True,
            'token': 'admin-token-xyz',
            'message': 'Login exitoso'
        }), 200
        
    return jsonify({
        'success': False,
        'error': 'Credenciales incorrectas'
    }), 401

@admin_bp.route('/admin/export/csv', methods=['GET'])
def export_attendance_csv():
    """Genera y descarga un reporte CSV basado en jornadas procesadas."""
    try:
        rows = query_all("""
            SELECT 
                e.full_name,
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
        writer.writerow(['Empleado', 'Sede', 'Fecha', 'Entrada', 'Salida', 'Estado', 'Horas Reg.', 'Horas Extra', 'Déficit (Min)', 'Biometría (Avg)'])
        
        for r in rows:
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
                f"{r['bio_avg']:.1f}%" if r['bio_avg'] else "N/A"
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
                
            new_id = query_one("""
                INSERT INTO buildings (name, address) 
                VALUES (%s, %s) RETURNING id
            """, (name, address))
            return jsonify({'message': 'Sede creada', 'id': str(new_id['id'])}), 201
        except Exception as e:
            print(f'[admin] Error en manage_buildings POST: {e}')
            return jsonify({'error': 'Error al crear sede'}), 500

@admin_bp.route('/admin/employees', methods=['GET', 'POST'])
def manage_employees():
    from flask import request
    if request.method == 'GET':
        try:
            employees = query_all("""
                SELECT 
                    e.id, e.full_name, e.job_title, e.status,
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
            role_id = data.get('role_id', '00000000-0000-0000-0000-000000000001') # Default Worker
            
            if not full_name:
                return jsonify({'error': 'El nombre es obligatorio'}), 400
                
            new_id = query_one("""
                INSERT INTO employees (full_name, job_title, primary_building_id, role_id)
                VALUES (%s, %s, %s, %s) RETURNING id
            """, (full_name, job_title, building_id, role_id))
            return jsonify({'message': 'Empleado creado', 'id': str(new_id['id'])}), 201
        except Exception as e:
            print(f'[admin] Error en manage_employees POST: {e}')
            return jsonify({'error': 'Error al crear empleado'}), 500

@admin_bp.route('/admin/roles', methods=['GET'])
def get_roles():
    try:
        roles = query_all("SELECT id, name FROM roles ORDER BY name ASC")
        for r in roles:
            r['id'] = str(r['id'])
        return jsonify(roles), 200
    except Exception as e:
        return jsonify({'error': 'Error al obtener roles'}), 500

@admin_bp.route('/admin/employees/<uuid:employee_id>/schedule', methods=['GET', 'POST'])
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
                    query_one("DELETE FROM schedules WHERE employee_id = %s AND day_of_week = %s RETURNING id", (employee_id, day_num))
                    continue

                query_one("""
                    INSERT INTO schedules (employee_id, day_of_week, start_time, end_time, building_id, is_overnight, tolerance_minutes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (employee_id, day_of_week) 
                    DO UPDATE SET 
                        start_time = EXCLUDED.start_time,
                        end_time = EXCLUDED.end_time,
                        building_id = EXCLUDED.building_id,
                        is_overnight = EXCLUDED.is_overnight,
                        tolerance_minutes = EXCLUDED.tolerance_minutes
                    RETURNING id
                """, (employee_id, day_num, start, end, build_id, overnight, tol))
                
            return jsonify({'message': 'Horario actualizado correctamente'}), 200
        except Exception as e:
            print(f'[admin] Error en POST schedule: {e}')
            return jsonify({'error': 'Error al actualizar horario'}), 500

@admin_bp.route('/admin/timesheets/process', methods=['POST'])
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
