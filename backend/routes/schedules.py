from flask import Blueprint, request, jsonify

schedules_bp = Blueprint('schedules', __name__)


@schedules_bp.route('/schedule/weekly', methods=['GET'])
def get_weekly_schedule():
    """Devuelve el horario semanal del empleado asociado al dispositivo."""
    token = request.headers.get('X-Device-Token')

    if not token:
        return jsonify({'error': 'X-Device-Token header es requerido'}), 401

    # ── Datos simulados (se reemplazará con consulta a BD) ──
    MOCK_SCHEDULE = [
        {'day_of_week': 0, 'day_label': 'Lunes',     'start_time': '08:00', 'end_time': '17:00'},
        {'day_of_week': 1, 'day_label': 'Martes',     'start_time': '08:00', 'end_time': '17:00'},
        {'day_of_week': 2, 'day_label': 'Miércoles',  'start_time': '08:00', 'end_time': '17:00'},
        {'day_of_week': 3, 'day_label': 'Jueves',     'start_time': '08:00', 'end_time': '17:00'},
        {'day_of_week': 4, 'day_label': 'Viernes',    'start_time': '08:00', 'end_time': '17:00'},
    ]

    return jsonify({
        'employee': 'Juan Pérez',
        'schedule': MOCK_SCHEDULE
    }), 200
