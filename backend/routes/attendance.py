from flask import Blueprint, request, jsonify
from utils.db import query_one, execute

attendance_bp = Blueprint('attendance', __name__)


def _get_employee_from_token(token):
    """Helper: obtiene employee_id y device_id a partir del device_token."""
    return query_one(
        """
        SELECT d.id AS device_id, d.employee_id
          FROM devices d
         WHERE d.device_token = %s
           AND d.is_active = TRUE
        """,
        (token,)
    )


@attendance_bp.route('/attendance/state', methods=['GET'])
def get_attendance_state():
    """Devuelve la próxima acción esperada (check_in o check_out)."""
    token = request.headers.get('X-Device-Token')

    if not token:
        return jsonify({'error': 'X-Device-Token header es requerido'}), 401

    try:
        device = _get_employee_from_token(token)
        if not device:
            return jsonify({'error': 'Dispositivo no válido'}), 401

        # Buscar el último registro de HOY para este empleado
        last = query_one(
            """
            SELECT action_type, timestamp
              FROM attendance_logs
             WHERE employee_id = %s
               AND timestamp::date = CURRENT_DATE
             ORDER BY timestamp DESC
             LIMIT 1
            """,
            (device['employee_id'],)
        )

        if not last:
            return jsonify({'action': 'check_in', 'lastRecord': None}), 200

        # Si el último fue check_in → le toca check_out, y viceversa
        next_action = 'check_out' if last['action_type'] == 'check_in' else 'check_in'
        return jsonify({
            'action': next_action,
            'lastRecord': last['timestamp'].isoformat() if last['timestamp'] else None,
        }), 200

    except Exception as e:
        print(f'[attendance] Error en get_state: {e}')
        return jsonify({'action': 'check_in', 'lastRecord': None, 'error': str(e)}), 500


@attendance_bp.route('/attendance/register', methods=['POST'])
def register_attendance():
    """Registra un ingreso o salida en attendance_logs."""
    token = request.headers.get('X-Device-Token')

    if not token:
        return jsonify({'error': 'X-Device-Token header es requerido'}), 401

    data = request.get_json(silent=True)

    if not data or 'action_type' not in data:
        return jsonify({'error': 'action_type es requerido'}), 400

    action_type = data['action_type']

    if action_type not in ('check_in', 'check_out'):
        return jsonify({'error': 'action_type inválido'}), 400

    try:
        device = _get_employee_from_token(token)
        if not device:
            return jsonify({'success': False, 'error': 'Dispositivo no válido'}), 401

        # photo_s3_key = data.get('photo')  # Futuro: subir a S3 y guardar key

        row = execute(
            """
            INSERT INTO attendance_logs (employee_id, device_id, action_type)
            VALUES (%s, %s, %s)
            RETURNING id, action_type, timestamp
            """,
            (device['employee_id'], device['device_id'], action_type)
        )

        return jsonify({
            'success': True,
            'message': f'{"Ingreso" if action_type == "check_in" else "Salida"} registrado correctamente.',
            'record': {
                'id': str(row['id']),
                'action_type': row['action_type'],
                'timestamp': row['timestamp'].isoformat(),
                'confidence_score': None,
            }
        }), 201

    except Exception as e:
        print(f'[attendance] Error en register: {e}')
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500
