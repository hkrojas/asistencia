from flask import Blueprint, request, jsonify
from utils.db import query_one

devices_bp = Blueprint('devices', __name__)


@devices_bp.route('/device/verify', methods=['POST'])
def verify_device():
    """Valida un token de dispositivo y devuelve el empleado asociado."""
    data = request.get_json(silent=True)

    if not data or 'device_token' not in data:
        return jsonify({'valid': False, 'error': 'device_token es requerido'}), 400

    token = data['device_token']

    try:
        row = query_one(
            """
            SELECT d.id         AS device_id,
                   d.is_active,
                   e.id         AS employee_id,
                   e.full_name,
                   e.status     AS employee_status,
                   r.name       AS role_name,
                   b.id         AS building_id,
                   b.name       AS building_name
              FROM devices d
              JOIN employees e ON e.id = d.employee_id
              JOIN roles r     ON r.id = e.role_id
              LEFT JOIN buildings b ON b.id = e.primary_building_id
             WHERE d.device_token = %s
            """,
            (token,)
        )

        if not row:
            return jsonify({'valid': False}), 200

        if not row['is_active']:
            return jsonify({'valid': False, 'error': 'Dispositivo desactivado'}), 200

        if row['employee_status'] != 'active':
            return jsonify({'valid': False, 'error': 'Empleado inactivo'}), 200

        return jsonify({
            'valid': True,
            'employeeName': row['full_name'],
            'employeeId': str(row['employee_id']),
            'role': row['role_name'],
            'building': row['building_name'],
            'buildingId': str(row['building_id']) if row['building_id'] else None
        }), 200

    except Exception as e:
        print(f'[devices] Error en verify_device: {e}')
        return jsonify({'valid': False, 'error': 'Error interno del servidor'}), 500
