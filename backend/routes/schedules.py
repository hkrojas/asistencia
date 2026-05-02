from flask import Blueprint, request, jsonify
import hashlib
from utils.db import query_one, query_all

schedules_bp = Blueprint('schedules', __name__)

DAY_LABELS = {
    0: 'Lunes',
    1: 'Martes',
    2: 'Miércoles',
    3: 'Jueves',
    4: 'Viernes',
    5: 'Sábado',
    6: 'Domingo',
}


@schedules_bp.route('/schedule/weekly', methods=['GET'])
def get_weekly_schedule():
    """Devuelve el horario semanal del empleado asociado al dispositivo."""
    token = request.headers.get('X-Device-Token')

    if not token:
        return jsonify({'error': 'X-Device-Token header es requerido'}), 401

    try:
        # Obtener empleado desde el token (hashed)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        device = query_one(
            """
            SELECT d.employee_id, e.full_name
              FROM devices d
              JOIN employees e ON e.id = d.employee_id
             WHERE d.token_hash = %s
               AND d.is_active = TRUE
            """,
            (token_hash,)
        )

        if not device:
            return jsonify({'error': 'Dispositivo no válido'}), 401

        # Obtener horarios ordenados por día
        rows = query_all(
            """
            SELECT s.day_of_week,
                   to_char(s.start_time, 'HH24:MI') AS start_time,
                   to_char(s.end_time, 'HH24:MI')   AS end_time,
                   b.name                           AS building_name
              FROM schedule_assignments s
              LEFT JOIN buildings b ON b.id = s.building_id
             WHERE s.employee_id = %s
               AND s.valid_to IS NULL
             ORDER BY s.day_of_week
            """,
            (device['employee_id'],)
        )

        schedule = []
        for r in rows:
            dow = r['day_of_week']
            schedule.append({
                'day_of_week': dow,
                'day_label': DAY_LABELS.get(dow, ''),
                'start_time': r['start_time'],
                'end_time': r['end_time'],
                'building': r['building_name']
            })

        return jsonify({
            'employee': device['full_name'],
            'schedule': schedule,
        }), 200

    except Exception as e:
        print(f'[schedules] Error en get_weekly_schedule: {e}')
        return jsonify({'employee': '', 'schedule': [], 'error': str(e)}), 500
