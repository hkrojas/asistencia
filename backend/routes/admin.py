from flask import Blueprint, jsonify, Response
import csv
import io
from utils.db import query_one, query_all

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
    """Genera y descarga un reporte CSV de asistencia con excepciones."""
    try:
        rows = query_all("""
            SELECT 
                e.full_name,
                b.name AS building,
                rp.punch_time::date AS date,
                MIN(rp.punch_time) FILTER (WHERE rp.punch_type = 'in') AS first_in,
                MAX(rp.punch_time) FILTER (WHERE rp.punch_type = 'out') AS last_out,
                te.exception_type AS resolution,
                te.minutes_adjusted AS extra_minutes,
                AVG(rp.confidence_score) AS bio_avg
            FROM raw_punches rp
            JOIN employees e ON e.id = rp.employee_id
            LEFT JOIN buildings b ON b.id = e.primary_building_id
            LEFT JOIN time_exceptions te ON te.employee_id = e.id AND te.date = rp.punch_time::date
            GROUP BY e.full_name, b.name, rp.punch_time::date, te.exception_type, te.minutes_adjusted
            ORDER BY rp.punch_time::date DESC
        """)

        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Empleado', 'Sede', 'Fecha', 'Entrada', 'Salida', 'Resolución WFM', 'Minutos Extra', 'Biometría (Avg)'])
        
        for r in rows:
            writer.writerow([
                r['full_name'],
                r['building'] or 'N/A',
                r['date'].isoformat(),
                r['first_in'].strftime('%H:%M') if r['first_in'] else '--:--',
                r['last_out'].strftime('%H:%M') if r['last_out'] else '--:--',
                r['resolution'] or 'Normal',
                r['extra_minutes'] or 0,
                f"{r['bio_avg']:.1f}%" if r['bio_avg'] else "N/A"
            ])
            
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=reporte_asistencia.csv"}
        )
        
    except Exception as e:
        print(f'[admin] Error en export_attendance_csv: {e}')
        return jsonify({'error': 'Error al generar CSV'}), 500
