from flask import Blueprint, request, jsonify
import hashlib
from utils.db import query_one, query_all
from services.biometrics import verify_face

attendance_bp = Blueprint('attendance', __name__)


def _get_device_from_token(token):
    """Return the active device context for a raw device token."""
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


def _resolve_employee_id(device, requested_employee_id=None):
    """Resolve the employee for personal devices or shared kiosks."""
    if device.get('employee_id'):
        return str(device['employee_id'])

    if not requested_employee_id:
        return None

    if device.get('building_id'):
        employee = query_one(
            """
            SELECT e.id
              FROM employees e
             WHERE e.id = %s
               AND e.status = 'active'
               AND (
                    e.primary_building_id = %s
                    OR EXISTS (
                        SELECT 1
                          FROM schedule_assignments sa
                         WHERE sa.employee_id = e.id
                           AND sa.building_id = %s
                           AND sa.valid_to IS NULL
                    )
               )
            """,
            (requested_employee_id, device['building_id'], device['building_id'])
        )
    else:
        employee = query_one(
            "SELECT id FROM employees WHERE id = %s AND status = 'active'",
            (requested_employee_id,)
        )

    return str(employee['id']) if employee else None


@attendance_bp.route('/attendance/employees', methods=['GET'])
def get_attendance_employees():
    """List active employees available to the linked device or shared kiosk."""
    token = request.headers.get('X-Device-Token')

    if not token:
        return jsonify({'error': 'X-Device-Token header es requerido'}), 401

    try:
        device = _get_device_from_token(token)
        if not device:
            return jsonify({'error': 'Dispositivo no valido'}), 401

        if device.get('employee_id'):
            rows = query_all(
                """
                SELECT id, full_name
                  FROM employees
                 WHERE id = %s AND status = 'active'
                 ORDER BY full_name ASC
                """,
                (device['employee_id'],)
            )
        else:
            rows = query_all(
                """
                SELECT DISTINCT e.id, e.full_name
                  FROM employees e
                  LEFT JOIN schedule_assignments sa
                    ON sa.employee_id = e.id
                   AND sa.building_id = %s
                   AND sa.valid_to IS NULL
                 WHERE e.status = 'active'
                   AND (e.primary_building_id = %s OR sa.id IS NOT NULL)
                 ORDER BY e.full_name ASC
                """,
                (device['building_id'], device['building_id'])
            )

        return jsonify({
            'employees': [
                {'id': str(row['id']), 'full_name': row['full_name']}
                for row in rows
            ]
        }), 200
    except Exception as e:
        print(f'[attendance] Error en get_attendance_employees: {e}')
        return jsonify({'error': str(e)}), 500


@attendance_bp.route('/attendance/state', methods=['GET'])
def get_attendance_state():
    """Return the next expected action for the selected employee."""
    token = request.headers.get('X-Device-Token')

    if not token:
        return jsonify({'error': 'X-Device-Token header es requerido'}), 401

    try:
        device = _get_device_from_token(token)
        if not device:
            return jsonify({'error': 'Dispositivo no valido'}), 401

        requested_employee_id = request.args.get('employee_id') or request.args.get('employeeId')
        employee_id = _resolve_employee_id(device, requested_employee_id)
        if not employee_id:
            return jsonify({
                'action': 'check_in',
                'lastRecord': None,
                'requires_employee': True
            }), 200

        last = query_one(
            """
            SELECT punch_type, punch_time
              FROM raw_punches
             WHERE employee_id = %s
               AND punch_time::date = CURRENT_DATE
             ORDER BY punch_time DESC
             LIMIT 1
            """,
            (employee_id,)
        )

        if not last:
            return jsonify({'action': 'check_in', 'lastRecord': None}), 200

        next_action = 'check_out' if last['punch_type'] == 'in' else 'check_in'
        return jsonify({
            'action': next_action,
            'lastRecord': last['punch_time'].isoformat() if last['punch_time'] else None,
        }), 200

    except Exception as e:
        print(f'[attendance] Error en get_state: {e}')
        return jsonify({'action': 'check_in', 'lastRecord': None, 'error': str(e)}), 500


@attendance_bp.route('/attendance/register', methods=['POST'])
def register_attendance():
    """Register an in/out punch after device, employee, and biometric validation."""
    token = request.headers.get('X-Device-Token')

    if not token:
        return jsonify({'error': 'X-Device-Token header es requerido'}), 401

    data = request.get_json(silent=True)

    if not data or 'action_type' not in data:
        return jsonify({'error': 'action_type es requerido'}), 400

    action_aliases = {
        'check_in': 'in',
        'in': 'in',
        'check_out': 'out',
        'out': 'out',
    }
    action_type = data['action_type']

    if action_type not in action_aliases:
        return jsonify({'error': 'action_type invalido'}), 400

    try:
        device = _get_device_from_token(token)
        if not device:
            return jsonify({'success': False, 'error': 'Dispositivo no valido'}), 401

        requested_employee_id = data.get('employee_id') or data.get('employeeId')
        employee_id = _resolve_employee_id(device, requested_employee_id)
        if not employee_id:
            return jsonify({
                'success': False,
                'requires_employee': True,
                'error': 'employee_id es requerido para kioscos compartidos.'
            }), 400

        photo_base64 = data.get('photo')
        if not photo_base64:
            return jsonify({
                'success': False,
                'error': 'La fotografia es obligatoria para registrar asistencia.'
            }), 400

        biometric_result = verify_face(photo_base64, employee_id)
        match = biometric_result.get('match', False)
        bio_status = biometric_result.get('status', 'failed')
        bio_provider = biometric_result.get('provider', 'none')
        confidence = biometric_result.get('confidence', 0)

        if not match:
            return jsonify({
                'success': False,
                'error': 'Validacion biometrica fallida o no disponible.',
                'biometric_status': bio_status
            }), 401

        punch_type = action_aliases[action_type]
        client_uuid = data.get('client_uuid')
        offline_sync = data.get('offline_sync', False)
        punch_time = data.get('punch_time')

        from utils.db import tx
        with tx() as (conn, cur):
            cur.execute(
                """
                INSERT INTO raw_punches (
                    employee_id, device_id, punch_time, punch_type,
                    confidence_score, biometric_status, biometric_provider,
                    offline_sync, client_uuid
                )
                VALUES (%s, %s, COALESCE(%s, NOW()), %s, %s, %s, %s, %s, %s)
                ON CONFLICT (client_uuid) DO UPDATE SET created_at = EXCLUDED.created_at
                RETURNING id, punch_type, punch_time
                """,
                (
                    employee_id, device['device_id'], punch_time, punch_type,
                    confidence, bio_status, bio_provider,
                    offline_sync, client_uuid
                )
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
                'biometric_status': bio_status
            }
        }), 201
    except Exception as e:
        print(f'[attendance] Error en register: {e}')
        return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500


@attendance_bp.route('/attendance/summary', methods=['GET'])
def get_employee_summary():
    """Return a 7-day summary for a personal device or selected kiosk employee."""
    token = request.headers.get('X-Device-Token')
    if not token:
        return jsonify({'error': 'X-Device-Token header es requerido'}), 401

    try:
        device = _get_device_from_token(token)
        if not device:
            return jsonify({'error': 'Dispositivo no valido'}), 401

        requested_employee_id = request.args.get('employee_id') or request.args.get('employeeId')
        employee_id = _resolve_employee_id(device, requested_employee_id)
        if not employee_id:
            return jsonify({
                'success': False,
                'requires_employee': True,
                'error': 'employee_id es requerido para kioscos compartidos.'
            }), 400

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

            user_status = ts['status']
            if ts['status'] == 'perfect':
                user_status = 'Completo'
            elif ts['status'] == 'overtime':
                user_status = 'Horas Extra'
            elif ts['status'] == 'deficit':
                user_status = 'Incompleto'
            elif ts['status'] == 'absent':
                user_status = 'Falta'
            elif ts['status'] == 'resolved':
                user_status = 'Justificado'

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
