from flask import Blueprint, request, jsonify

attendance_bp = Blueprint('attendance', __name__)


@attendance_bp.route('/attendance/state', methods=['GET'])
def get_attendance_state():
    """Devuelve la próxima acción esperada (check_in o check_out)."""
    token = request.headers.get('X-Device-Token')

    if not token:
        return jsonify({'error': 'X-Device-Token header es requerido'}), 401

    # ── Lógica simulada (se reemplazará con consulta a BD) ──
    # En producción: buscar el último registro del empleado de hoy
    # y devolver check_out si ya hizo check_in, o check_in si no.
    return jsonify({
        'action': 'check_in',
        'lastRecord': None
    }), 200


@attendance_bp.route('/attendance/register', methods=['POST'])
def register_attendance():
    """Registra un ingreso o salida (stub para integración futura con Rekognition)."""
    token = request.headers.get('X-Device-Token')

    if not token:
        return jsonify({'error': 'X-Device-Token header es requerido'}), 401

    data = request.get_json(silent=True)

    if not data or 'action_type' not in data:
        return jsonify({'error': 'action_type es requerido'}), 400

    action_type = data['action_type']

    if action_type not in ('check_in', 'check_out'):
        return jsonify({'error': 'action_type inválido'}), 400

    # photo_base64 = data.get('photo')  # Se usará con Rekognition

    # ── Respuesta simulada ──
    from datetime import datetime, timezone
    return jsonify({
        'success': True,
        'message': f'{"Ingreso" if action_type == "check_in" else "Salida"} registrado correctamente.',
        'record': {
            'action_type': action_type,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'confidence_score': None  # Futuro: score de Rekognition
        }
    }), 201
