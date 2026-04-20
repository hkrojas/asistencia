from flask import Blueprint, request, jsonify

devices_bp = Blueprint('devices', __name__)


@devices_bp.route('/device/verify', methods=['POST'])
def verify_device():
    """Valida un token de dispositivo y devuelve el empleado asociado."""
    data = request.get_json(silent=True)

    if not data or 'device_token' not in data:
        return jsonify({'valid': False, 'error': 'device_token es requerido'}), 400

    token = data['device_token']

    # ── Lógica simulada (se reemplazará con consulta a BD) ──
    MOCK_DEVICES = {
        'token-simulado-juan-perez': {
            'valid': True,
            'employeeName': 'Juan Pérez',
            'employeeId': 'a1b2c3d4-0000-0000-0000-000000000001',
        }
    }

    device = MOCK_DEVICES.get(token)

    if device:
        return jsonify(device), 200

    return jsonify({'valid': False}), 200
