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
                (SELECT COUNT(DISTINCT employee_id) FROM attendance_logs 
                 WHERE timestamp::date = CURRENT_DATE 
                 AND action_type = 'check_in') as present_today,
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
                al.id,
                e.full_name AS employee_name,
                b.name      AS building_name,
                al.action_type,
                al.timestamp,
                al.is_manual_override
            FROM attendance_logs al
            JOIN employees e ON e.id = al.employee_id
            LEFT JOIN buildings b ON b.id = al.building_id
            ORDER BY al.timestamp DESC
            LIMIT 50
        """)
        
        # Formatear la data para el frontend
        records = []
        for r in rows:
            records.append({
                'id': str(r['id']),
                'employee': r['employee_name'],
                'building': r['building_name'] or 'N/A',
                'action': r['action_type'],
                'time': r['timestamp'].isoformat(),
                'method': 'Manual' if r['is_manual_override'] else 'Biométrico'
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
                al.id AS log_id,
                e.id AS employee_id,
                e.full_name AS employee_name,
                s.start_time,
                s.end_time,
                al.timestamp::time AS actual_out,
                al.timestamp::date AS date,
                EXTRACT(EPOCH FROM (al.timestamp::time - s.end_time))/60 AS excess_minutes
            FROM attendance_logs al
            JOIN employees e ON e.id = al.employee_id
            JOIN schedules s ON s.employee_id = e.id AND s.day_of_week = EXTRACT(DOW FROM al.timestamp)
            LEFT JOIN time_exceptions te ON te.employee_id = e.id AND te.date = al.timestamp::date
            WHERE al.action_type = 'check_out'
            AND te.id IS NULL
            AND (al.timestamp::time - s.end_time) > INTERVAL '15 minutes'
            ORDER BY al.timestamp DESC
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
        log_data = query_one("SELECT employee_id, timestamp::date FROM attendance_logs WHERE id = %s", (log_id,))
        
        if not log_data:
            return jsonify({'error': 'Log no encontrado'}), 404
            
        # Calculamos minutos de ajuste si no vienen (simplificado)
        minutes = data.get('minutes_adjusted', 60) 

        query_one("""
            INSERT INTO time_exceptions (employee_id, date, exception_type, minutes_adjusted, approved_by, reason)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (log_data['employee_id'], log_data['timestamp'], res_type, minutes, admin_id, 'Resolución desde Panel Web'))
        
        return jsonify({'message': 'Resolución registrada con éxito'}), 200
        
    except Exception as e:
        print(f'[admin] Error en resolve_exception: {e}')
        return jsonify({'error': 'Error al registrar resolución'}), 500
@admin_bp.route('/admin/export/csv', methods=['GET'])
def export_attendance_csv():
    """Genera y descarga un reporte CSV de asistencia con excepciones."""
    try:
        rows = query_all("""
            SELECT 
                e.full_name,
                b.name AS building,
                al.timestamp::date AS date,
                MIN(al.timestamp) FILTER (WHERE al.action_type = 'check_in') AS check_in,
                MAX(al.timestamp) FILTER (WHERE al.action_type = 'check_out') AS check_out,
                te.exception_type AS resolution,
                te.minutes_adjusted AS extra_minutes
            FROM attendance_logs al
            JOIN employees e ON e.id = al.employee_id
            LEFT JOIN buildings b ON b.id = al.building_id
            LEFT JOIN time_exceptions te ON te.employee_id = e.id AND te.date = al.timestamp::date
            GROUP BY e.full_name, b.name, al.timestamp::date, te.exception_type, te.minutes_adjusted
            ORDER BY al.timestamp::date DESC
        """)

        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Empleado', 'Sede', 'Fecha', 'Entrada', 'Salida', 'Resolución WFM', 'Minutos Extra'])
        
        for r in rows:
            writer.writerow([
                r['full_name'],
                r['building'] or 'N/A',
                r['date'].isoformat(),
                r['check_in'].strftime('%H:%M') if r['check_in'] else '--:--',
                r['check_out'].strftime('%H:%M') if r['check_out'] else '--:--',
                r['resolution'] or 'Normal',
                r['extra_minutes'] or 0
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
