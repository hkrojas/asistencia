from flask import Blueprint, jsonify
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
