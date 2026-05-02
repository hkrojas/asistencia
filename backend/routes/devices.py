import uuid
import hashlib
from datetime import datetime
from flask import Blueprint, request, jsonify
from utils.db import query_one, tx

devices_bp = Blueprint('devices', __name__)


@devices_bp.route('/device/verify', methods=['POST'])
def verify_device():
    """Valida un token de dispositivo y devuelve el contexto asociado."""
    data = request.get_json(silent=True)

    if not data or 'device_token' not in data:
        return jsonify({'valid': False, 'error': 'device_token es requerido'}), 400

    token = data['device_token']
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    try:
        row = query_one(
            """
            SELECT d.id         AS device_id,
                   d.is_active,
                   d.building_id,
                   b.name       AS building_name,
                   d.employee_id
              FROM devices d
              JOIN buildings b ON b.id = d.building_id
             WHERE d.token_hash = %s
               AND d.is_active = TRUE
            """,
            (token_hash,)
        )

        if not row:
            return jsonify({'valid': False, 'error': 'Dispositivo no encontrado o inactivo'}), 200

        # Si el dispositivo es un Kiosco genérico
        display_name = "Kiosco Principal"
        
        # Si está vinculado a un empleado específico (dispositivo personal)
        if row['employee_id']:
            emp = query_one("SELECT full_name FROM employees WHERE id = %s", (row['employee_id'],))
            if emp:
                display_name = emp['full_name']

        return jsonify({
            'valid': True,
            'employeeName': display_name,
            'employeeId': str(row['employee_id']) if row['employee_id'] else None,
            'requiresEmployeeSelection': row['employee_id'] is None,
            'building': row['building_name'],
            'buildingId': str(row['building_id'])
        }), 200

    except Exception as e:
        print(f'[devices] Error en verify_device: {e}')
        return jsonify({'valid': False, 'error': 'Error interno del servidor'}), 500


@devices_bp.route('/devices/pair', methods=['POST'])
def pair_device():
    """Vincula un dispositivo físico usando un código de 6 dígitos."""
    data = request.get_json(silent=True)
    if not data or 'pairing_code' not in data:
        return jsonify({'error': 'pairing_code es requerido'}), 400
        
    code = data['pairing_code']
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    
    try:
        # Verificar código
        code_row = query_one("""
            SELECT id, building_id, expires_at 
              FROM device_pairing_codes 
             WHERE code_hash = %s AND is_used = FALSE AND expires_at > NOW()
        """, (code_hash,))
        
        if not code_row:
            return jsonify({'error': 'Código inválido, usado o expirado'}), 400
            
        # Generar token real de alta entropía
        new_token = str(uuid.uuid4())
        token_hash = hashlib.sha256(new_token.encode()).hexdigest()
        
        with tx() as (conn, cur):
            # Marcar código como usado
            cur.execute("UPDATE device_pairing_codes SET is_used = TRUE WHERE id = %s", (code_row['id'],))
            
            # Crear dispositivo (Kiosco) vinculado al edificio
            cur.execute("""
                INSERT INTO devices (token_hash, building_id, alias)
                VALUES (%s, %s, %s)
            """, (token_hash, code_row['building_id'], 'Kiosco Móvil'))
            
        return jsonify({
            'device_token': new_token,
            'building_id': str(code_row['building_id'])
        }), 201
        
    except Exception as e:
        print(f'[devices] Error en pair_device: {e}')
        return jsonify({'error': 'Error interno al vincular dispositivo'}), 500
