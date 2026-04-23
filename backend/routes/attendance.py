from flask import Blueprint, request, jsonify
import hashlib
from utils.db import query_one, query_all, execute
from services.biometrics import verify_face

attendance_bp = Blueprint('attendance', __name__)


def _get_employee_from_token(token):
    """Helper: obtiene employee_id y device_id a partir del device_token (hashed)."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return query_one(
        """
        SELECT d.id AS device_id, d.employee_id, d.building_id
          FROM devices d
         WHERE d.token_hash = %s
           AND d.is_active = TRUE
        """,
        (token_hash,)
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
            SELECT punch_type, punch_time
              FROM raw_punches
             WHERE employee_id = %s
               AND punch_time::date = CURRENT_DATE
             ORDER BY punch_time DESC
             LIMIT 1
            """,
            (device['employee_id'],)
        )

        if not last:
            return jsonify({'action': 'check_in', 'lastRecord': None}), 200

        # Si el último fue in → le toca out, y viceversa
        next_action = 'out' if last['punch_type'] == 'in' else 'in'
        return jsonify({
            'action': next_action,
            'lastRecord': last['punch_time'].isoformat() if last['punch_time'] else None,
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

        # ── Validación Biométrica ──
        photo_base64 = data.get('photo')
        biometric_result = verify_face(photo_base64, device['employee_id'])

        if not biometric_result.get('match'):
            return jsonify({
                'success': False, 
                'error': 'Validación biométrica fallida. El rostro no coincide.'
            }), 401

        confidence = biometric_result.get('confidence', 0)

        punch_type = 'in' if action_type in ('check_in', 'in') else 'out'
        client_uuid = data.get('client_uuid') # Para idempotencia
        offline_sync = data.get('offline_sync', False)
        # Si es offline_sync, el cliente envía su propio punch_time (ISO string)
        punch_time = data.get('punch_time') 

        # ── Inserción en DB ──
        # Usamos COALESCE(..., NOW()) para que si punch_time es NULL use la hora del servidor
        from utils.db import tx
        with tx() as (conn, cur):
            cur.execute(
                """
                INSERT INTO raw_punches (employee_id, device_id, punch_time, punch_type, confidence_score, offline_sync, client_uuid)
                VALUES (%s, %s, COALESCE(%s, NOW()), %s, %s, %s, %s)
                ON CONFLICT (client_uuid) DO UPDATE SET created_at = EXCLUDED.created_at -- Idempotencia
                RETURNING id, punch_type, punch_time
                """,
                (device['employee_id'], device['device_id'], punch_time, punch_type, confidence, offline_sync, client_uuid)
            )
            row = cur.fetchone()

        return jsonify({
            'success': True,
            'message': f'{"Ingreso" if punch_type == "in" else "Salida"} registrado correctamente.',
            'record': {
                'id': str(row['id']),
                'punch_type': row['punch_type'],
                'timestamp': row['punch_time'].isoformat(),
                'confidence_score': confidence,
            }
        }), 201
    except Exception as e:
        print(f'[attendance] Error en register: {e}')
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500


@attendance_bp.route('/attendance/summary', methods=['GET'])
def get_employee_summary():
    """Retorna un resumen de las últimas 7 jornadas para el empleado vinculado."""
    token = request.headers.get('X-Device-Token')
    if not token:
        return jsonify({'error': 'X-Device-Token header es requerido'}), 401

    try:
        device = _get_employee_from_token(token)
        if not device:
            return jsonify({'error': 'Dispositivo no válido'}), 401

        employee_id = device['employee_id']

        # Obtener las últimas 7 jornadas procesadas
        timesheets = query_all(
            """
            SELECT logical_date, status, regular_minutes, overtime_minutes, deficit_minutes
              FROM daily_timesheets
             WHERE employee_id = %s
             ORDER BY logical_date DESC
             LIMIT 7
            """,
            (employee_id,)
        )

        total_reg_min = sum(ts['regular_minutes'] or 0 for ts in timesheets)
        total_ovt_min = sum(ts['overtime_minutes'] or 0 for ts in timesheets)

        days_detail = []
        for ts in timesheets:
            total_worked_min = (ts['regular_minutes'] or 0) + (ts['overtime_minutes'] or 0)
            hours = total_worked_min / 60.0
            
            # Formatear el status para el usuario final
            user_status = ts['status']
            if ts['status'] == 'perfect': user_status = 'Completo'
            elif ts['status'] == 'overtime': user_status = 'Horas Extra'
            elif ts['status'] == 'deficit': user_status = 'Incompleto'
            elif ts['status'] == 'absent': user_status = 'Falta'
            elif ts['status'] == 'resolved': user_status = 'Justificado'

            days_detail.append({
                'date': ts['logical_date'].isoformat(),
                'status': user_status,
                'worked_hours': round(hours, 2),
                'overtime_minutes': ts['overtime_minutes'] or 0,
                'deficit_minutes': ts['deficit_minutes'] or 0
            })

        return jsonify({
            'success': True,
            'total_regular_hours': round(total_reg_min / 60.0, 2),
            'total_overtime_hours': round(total_ovt_min / 60.0, 2),
            'days': days_detail
        }), 200

    except Exception as e:
        print(f'[attendance] Error en get_summary: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500
