import json
from datetime import datetime

from flask import Blueprint, jsonify, g, request

from routes.admin import require_auth
from services.audit_service import record_audit_event
from services.operations import classify_coverage, validate_prepayroll_submission
from services.permissions import can_access_building, can_view_wages
from utils.db import query_all, query_one, tx


operations_bp = Blueprint("operations", __name__)


def _actor_id():
    data = request.get_json(silent=True) or {}
    return data.get("actor_user_id") or data.get("adminId")


def _building_with_employer(building_id):
    return query_one(
        """
        SELECT b.id, b.name, b.employer_id, e.ruc AS employer_ruc
          FROM buildings b
          LEFT JOIN employers e ON e.id = b.employer_id
         WHERE b.id = %s
        """,
        (building_id,),
    )


@operations_bp.route("/admin/operations/dashboard", methods=["GET"])
@require_auth
def get_operations_dashboard():
    period_id = request.args.get("period_id")
    buildings = query_all(
        """
        SELECT
            b.id, b.name, b.code, b.cost_center, b.status,
            COALESCE(e.ruc, '') AS employer_ruc,
            COUNT(DISTINCT emp.id) FILTER (WHERE emp.status = 'active') AS active_workers,
            COUNT(DISTINCT bp.id) AS prepayroll_count,
            COUNT(DISTINCT om.id) FILTER (WHERE om.status IN ('requested', 'pending_legal_validation', 'observed')) AS pending_coverages
          FROM buildings b
          LEFT JOIN employers e ON e.id = b.employer_id
          LEFT JOIN employees emp ON emp.primary_building_id = b.id
          LEFT JOIN building_prepayrolls bp ON bp.building_id = b.id
                AND (%s IS NULL OR bp.payroll_period_id = %s)
          LEFT JOIN operational_movements om ON om.destination_building_id = b.id
                AND om.status IN ('requested', 'pending_legal_validation', 'observed')
         GROUP BY b.id, b.name, b.code, b.cost_center, b.status, e.ruc
         ORDER BY b.name
        """,
        (period_id, period_id),
    )
    for row in buildings:
        row["id"] = str(row["id"])
    current_user = getattr(g, "current_user", {}) or {}
    role = current_user.get("role", "Superadmin")
    assigned_ids = []
    if role == "BuildingAdmin":
        assignments = query_all(
            """
            SELECT building_id, can_view_wages
              FROM building_admin_assignments
             WHERE user_id = %s
               AND CURRENT_DATE >= valid_from
               AND (valid_to IS NULL OR CURRENT_DATE <= valid_to)
            """,
            (current_user.get("user_id"),),
        )
        assigned_ids = [str(row["building_id"]) for row in assignments]
    buildings = [
        row for row in buildings
        if can_access_building(role, assigned_ids, row["id"])
    ]
    if not can_view_wages(role):
        for row in buildings:
            row.pop("estimated_net", None)
    return jsonify({"buildings": buildings}), 200


@operations_bp.route("/admin/coverages", methods=["POST"])
@require_auth
def create_coverage():
    data = request.get_json() or {}
    required = [
        "employee_id",
        "origin_building_id",
        "destination_building_id",
        "starts_at",
        "ends_at",
        "movement_type",
        "reason",
    ]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": "Faltan datos obligatorios", "fields": missing}), 400

    origin = _building_with_employer(data["origin_building_id"])
    destination = _building_with_employer(data["destination_building_id"])
    if not origin or not destination:
        return jsonify({"error": "Edificio origen o destino no encontrado"}), 404

    decision = classify_coverage(origin, destination)
    actor = _actor_id()
    with tx() as (conn, cur):
        cur.execute(
            """
            INSERT INTO operational_movements (
                employee_id, origin_building_id, destination_building_id,
                starts_at, ends_at, movement_type, reason, requested_by,
                status, generates_overtime, generates_mobility, cost_allocation_rule,
                is_cross_employer, legal_validation_required, legal_note, evidence_url
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                data["employee_id"],
                data["origin_building_id"],
                data["destination_building_id"],
                data["starts_at"],
                data["ends_at"],
                data["movement_type"],
                data["reason"],
                actor,
                decision["status"],
                bool(data.get("generates_overtime", False)),
                bool(data.get("generates_mobility", False)),
                data.get("cost_allocation_rule", "destination_building"),
                decision["is_cross_employer"],
                decision["legal_validation_required"],
                decision["legal_note"],
                data.get("evidence_url"),
            ),
        )
        row = cur.fetchone()
        movement_id = row["id"]
        record_audit_event(
            cur,
            actor_user_id=actor,
            module="operations",
            action="create_coverage",
            entity_type="operational_movements",
            entity_id=movement_id,
            new_data={**data, **decision},
            reason=data["reason"],
            ip_address=request.remote_addr,
        )

    return jsonify({"id": str(movement_id), **decision}), 201


@operations_bp.route("/admin/incidents", methods=["POST"])
@require_auth
def create_operational_incident():
    data = request.get_json() or {}
    required = ["employee_id", "building_id", "incident_date", "incident_type", "reason"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": "Faltan datos obligatorios", "fields": missing}), 400

    actor = _actor_id()
    with tx() as (conn, cur):
        cur.execute(
            """
            INSERT INTO operational_incidents (
                employee_id, building_id, incident_date, starts_at, ends_at,
                incident_type, status, is_paid, recovers_hours,
                affects_prepayroll, affects_payroll, reason, evidence_url,
                registered_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'registered', %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                data["employee_id"],
                data["building_id"],
                data["incident_date"],
                data.get("starts_at"),
                data.get("ends_at"),
                data["incident_type"],
                data.get("is_paid"),
                bool(data.get("recovers_hours", False)),
                bool(data.get("affects_prepayroll", True)),
                bool(data.get("affects_payroll", True)),
                data["reason"],
                data.get("evidence_url"),
                actor,
            ),
        )
        row = cur.fetchone()
        incident_id = row["id"]
        record_audit_event(
            cur,
            actor_user_id=actor,
            module="operations",
            action="create_incident",
            entity_type="operational_incidents",
            entity_id=incident_id,
            new_data=data,
            reason=data["reason"],
            ip_address=request.remote_addr,
        )

    return jsonify({"id": str(incident_id), "message": "Incidencia registrada"}), 201


@operations_bp.route("/admin/daily-building-reports", methods=["POST"])
@require_auth
def create_daily_building_report():
    data = request.get_json() or {}
    if not data.get("building_id") or not data.get("report_date"):
        return jsonify({"error": "building_id y report_date son obligatorios"}), 400

    actor = _actor_id()
    with tx() as (conn, cur):
        cur.execute(
            """
            INSERT INTO daily_building_reports (
                building_id, report_date, administrator_user_id, status, summary, observations
            )
            VALUES (%s, %s, %s, %s, %s::jsonb, %s)
            ON CONFLICT (building_id, report_date) DO UPDATE SET
                administrator_user_id = EXCLUDED.administrator_user_id,
                status = EXCLUDED.status,
                summary = EXCLUDED.summary,
                observations = EXCLUDED.observations
            RETURNING id
            """,
            (
                data["building_id"],
                data["report_date"],
                actor,
                data.get("status", "draft"),
                json.dumps(data.get("summary", {})),
                data.get("observations"),
            ),
        )
        report_id = cur.fetchone()["id"]
        record_audit_event(
            cur,
            actor_user_id=actor,
            module="operations",
            action="upsert_daily_report",
            entity_type="daily_building_reports",
            entity_id=report_id,
            new_data=data,
            reason=data.get("observations"),
            ip_address=request.remote_addr,
        )

    return jsonify({"id": str(report_id)}), 201


def _prepayroll_blockers(building_id, period_id):
    period = query_one("SELECT starts_on, ends_on FROM payroll_periods WHERE id = %s", (period_id,))
    if not period:
        return None

    pending_coverages = query_one(
        """
        SELECT COUNT(*) AS count
          FROM operational_movements
         WHERE (origin_building_id = %s OR destination_building_id = %s)
           AND starts_at::date BETWEEN %s AND %s
           AND status IN ('requested', 'observed', 'pending_legal_validation')
        """,
        (building_id, building_id, period["starts_on"], period["ends_on"]),
    )
    unclassified_absences = query_one(
        """
        SELECT COUNT(*) AS count
          FROM daily_timesheets dt
          LEFT JOIN schedule_assignments sa ON sa.id = dt.schedule_assignment_id
          JOIN employees e ON e.id = dt.employee_id
         WHERE dt.payroll_period_id = %s
           AND COALESCE(sa.building_id, e.primary_building_id) = %s
           AND dt.status IN ('incomplete', 'exception')
           AND dt.deficit_minutes > 0
        """,
        (period_id, building_id),
    )
    unapproved_overtime = query_one(
        """
        SELECT COUNT(*) AS count
          FROM daily_timesheets dt
          LEFT JOIN schedule_assignments sa ON sa.id = dt.schedule_assignment_id
          JOIN employees e ON e.id = dt.employee_id
          LEFT JOIN time_exceptions te
            ON te.employee_id = dt.employee_id
           AND te.date = dt.logical_date
           AND te.exception_type = 'overtime'
         WHERE dt.payroll_period_id = %s
           AND COALESCE(sa.building_id, e.primary_building_id) = %s
           AND dt.overtime_minutes > 0
           AND te.id IS NULL
        """,
        (period_id, building_id),
    )

    return validate_prepayroll_submission(
        pending_coverages=(pending_coverages or {}).get("count", 0),
        unclassified_absences=(unclassified_absences or {}).get("count", 0),
        unapproved_overtime=(unapproved_overtime or {}).get("count", 0),
        unrevised_critical_shifts=0,
    )


@operations_bp.route("/admin/building-prepayrolls/generate", methods=["POST"])
@require_auth
def generate_building_prepayroll():
    data = request.get_json() or {}
    building_id = data.get("building_id")
    period_id = data.get("payroll_period_id") or data.get("period_id")
    if not building_id or not period_id:
        return jsonify({"error": "building_id y payroll_period_id son obligatorios"}), 400

    actor = _actor_id()
    blockers = _prepayroll_blockers(building_id, period_id)
    if blockers is None:
        return jsonify({"error": "Periodo no encontrado"}), 404

    with tx() as (conn, cur):
        cur.execute(
            """
            INSERT INTO building_prepayrolls (
                building_id, payroll_period_id, administrator_user_id, state, blocker_summary
            )
            VALUES (%s, %s, %s, 'draft', %s::jsonb)
            ON CONFLICT (building_id, payroll_period_id) DO UPDATE SET
                administrator_user_id = EXCLUDED.administrator_user_id,
                blocker_summary = EXCLUDED.blocker_summary
            RETURNING id
            """,
            (building_id, period_id, actor, json.dumps(blockers)),
        )
        prepayroll_id = cur.fetchone()["id"]
        cur.execute(
            "DELETE FROM building_prepayroll_items WHERE building_prepayroll_id = %s",
            (prepayroll_id,),
        )
        cur.execute(
            """
            INSERT INTO building_prepayroll_items (
                building_prepayroll_id, employee_id, source_building_id,
                regular_minutes, overtime_minutes, deficit_minutes,
                absences_count, late_count
            )
            SELECT
                %s,
                dt.employee_id,
                COALESCE(sa.building_id, e.primary_building_id) AS source_building_id,
                COALESCE(SUM(dt.regular_minutes), 0),
                COALESCE(SUM(dt.overtime_minutes), 0),
                COALESCE(SUM(dt.deficit_minutes), 0),
                COUNT(*) FILTER (WHERE dt.status IN ('incomplete', 'exception') AND dt.deficit_minutes > 0),
                COUNT(*) FILTER (WHERE dt.deficit_minutes > 0)
              FROM daily_timesheets dt
              LEFT JOIN schedule_assignments sa ON sa.id = dt.schedule_assignment_id
              JOIN employees e ON e.id = dt.employee_id
             WHERE dt.payroll_period_id = %s
               AND COALESCE(sa.building_id, e.primary_building_id) = %s
             GROUP BY dt.employee_id, COALESCE(sa.building_id, e.primary_building_id)
            """,
            (prepayroll_id, period_id, building_id),
        )
        record_audit_event(
            cur,
            actor_user_id=actor,
            module="prepayroll",
            action="generate_building_prepayroll",
            entity_type="building_prepayrolls",
            entity_id=prepayroll_id,
            new_data={"building_id": building_id, "period_id": period_id, "blockers": blockers},
            reason="Generacion de preplanilla por edificio",
            ip_address=request.remote_addr,
        )

    return jsonify({"id": str(prepayroll_id), "blockers": blockers}), 201


@operations_bp.route("/admin/building-prepayrolls/<uuid:prepayroll_id>/send", methods=["POST"])
@require_auth
def send_building_prepayroll(prepayroll_id):
    prepayroll = query_one(
        "SELECT building_id, payroll_period_id FROM building_prepayrolls WHERE id = %s",
        (prepayroll_id,),
    )
    if not prepayroll:
        return jsonify({"error": "Preplanilla no encontrada"}), 404

    blockers = _prepayroll_blockers(prepayroll["building_id"], prepayroll["payroll_period_id"])
    if blockers and not blockers["can_send"]:
        with tx() as (conn, cur):
            cur.execute(
                "UPDATE building_prepayrolls SET blocker_summary = %s::jsonb WHERE id = %s",
                (json.dumps(blockers), prepayroll_id),
            )
        return jsonify({"error": "Preplanilla bloqueada", "blockers": blockers}), 409

    actor = _actor_id()
    with tx() as (conn, cur):
        cur.execute(
            """
            UPDATE building_prepayrolls
               SET state = 'sent_to_hr', submitted_at = NOW(), administrator_user_id = COALESCE(%s, administrator_user_id)
             WHERE id = %s
            """,
            (actor, prepayroll_id),
        )
        record_audit_event(
            cur,
            actor_user_id=actor,
            module="prepayroll",
            action="send_to_hr",
            entity_type="building_prepayrolls",
            entity_id=prepayroll_id,
            new_data={"state": "sent_to_hr"},
            reason="Envio de preplanilla a RRHH",
            ip_address=request.remote_addr,
        )
    return jsonify({"message": "Preplanilla enviada a RRHH"}), 200


@operations_bp.route("/admin/building-prepayrolls/<uuid:prepayroll_id>/observe", methods=["POST"])
@require_auth
def observe_building_prepayroll(prepayroll_id):
    data = request.get_json() or {}
    reason_code = data.get("reason_code")
    comment = data.get("comment")
    if not reason_code or not comment:
        return jsonify({"error": "reason_code y comment son obligatorios"}), 400

    actor = _actor_id()
    with tx() as (conn, cur):
        cur.execute(
            """
            INSERT INTO building_prepayroll_observations (
                building_prepayroll_id, reason_code, comment, observed_by
            )
            VALUES (%s, %s, %s, %s)
            """,
            (prepayroll_id, reason_code, comment, actor),
        )
        cur.execute(
            "UPDATE building_prepayrolls SET state = 'observed_by_hr' WHERE id = %s",
            (prepayroll_id,),
        )
        record_audit_event(
            cur,
            actor_user_id=actor,
            module="prepayroll",
            action="observe_by_hr",
            entity_type="building_prepayrolls",
            entity_id=prepayroll_id,
            new_data=data,
            reason=comment,
            ip_address=request.remote_addr,
        )
    return jsonify({"message": "Preplanilla observada"}), 200


@operations_bp.route("/admin/building-prepayrolls/<uuid:prepayroll_id>/approve", methods=["POST"])
@require_auth
def approve_building_prepayroll(prepayroll_id):
    actor = _actor_id()
    with tx() as (conn, cur):
        cur.execute(
            """
            UPDATE building_prepayrolls
               SET state = 'approved_by_hr', approved_at = NOW()
             WHERE id = %s
            """,
            (prepayroll_id,),
        )
        record_audit_event(
            cur,
            actor_user_id=actor,
            module="prepayroll",
            action="approve_by_hr",
            entity_type="building_prepayrolls",
            entity_id=prepayroll_id,
            new_data={"state": "approved_by_hr"},
            reason="Aprobacion RRHH",
            ip_address=request.remote_addr,
        )
    return jsonify({"message": "Preplanilla aprobada por RRHH"}), 200


@operations_bp.route("/admin/consolidation/<uuid:period_id>", methods=["GET"])
@require_auth
def get_payroll_consolidation(period_id):
    rows = query_all(
        """
        SELECT state, COUNT(*) AS count
          FROM building_prepayrolls
         WHERE payroll_period_id = %s
         GROUP BY state
        """,
        (period_id,),
    )
    movements = query_one(
        """
        SELECT COUNT(*) AS count
          FROM operational_movements om
          JOIN payroll_periods pp ON om.starts_at::date BETWEEN pp.starts_on AND pp.ends_on
         WHERE pp.id = %s
        """,
        (period_id,),
    )
    return jsonify(
        {
            "period_id": str(period_id),
            "prepayroll_states": {row["state"]: row["count"] for row in rows},
            "workers_with_movements": (movements or {}).get("count", 0),
        }
    ), 200


@operations_bp.route("/admin/payroll-runs", methods=["POST"])
@require_auth
def create_payroll_run():
    data = request.get_json() or {}
    period_id = data.get("payroll_period_id") or data.get("period_id")
    if not period_id:
        return jsonify({"error": "payroll_period_id es obligatorio"}), 400

    pending = query_one(
        """
        SELECT COUNT(*) AS count
          FROM building_prepayrolls
         WHERE payroll_period_id = %s
           AND state NOT IN ('approved_by_hr', 'consolidated', 'closed')
        """,
        (period_id,),
    )
    approved = query_one(
        """
        SELECT COUNT(*) AS count
          FROM building_prepayrolls
         WHERE payroll_period_id = %s
           AND state IN ('approved_by_hr', 'consolidated', 'closed')
        """,
        (period_id,),
    )
    if int((pending or {}).get("count", 0)) > 0 or int((approved or {}).get("count", 0)) == 0:
        return jsonify({"error": "No se puede crear planilla con preplanillas pendientes o sin aprobaciones"}), 409

    actor = _actor_id()
    with tx() as (conn, cur):
        cur.execute(
            """
            INSERT INTO payroll_runs (payroll_period_id, state)
            VALUES (%s, 'in_review')
            RETURNING id
            """,
            (period_id,),
        )
        run_id = cur.fetchone()["id"]
        record_audit_event(
            cur,
            actor_user_id=actor,
            module="payroll",
            action="create_run",
            entity_type="payroll_runs",
            entity_id=run_id,
            new_data={"payroll_period_id": period_id, "state": "in_review"},
            reason="Creacion de planilla central",
            ip_address=request.remote_addr,
        )
    return jsonify({"id": str(run_id), "state": "in_review"}), 201


@operations_bp.route("/admin/payroll-runs/<uuid:run_id>/validate-hr", methods=["POST"])
@require_auth
def validate_payroll_hr(run_id):
    with tx() as (conn, cur):
        cur.execute("UPDATE payroll_runs SET state = 'hr_validated' WHERE id = %s", (run_id,))
    return jsonify({"message": "Planilla validada por RRHH"}), 200


@operations_bp.route("/admin/payroll-runs/<uuid:run_id>/validate-finance", methods=["POST"])
@require_auth
def validate_payroll_finance(run_id):
    with tx() as (conn, cur):
        cur.execute("UPDATE payroll_runs SET state = 'finance_validated' WHERE id = %s", (run_id,))
    return jsonify({"message": "Planilla validada por Finanzas"}), 200


@operations_bp.route("/admin/payroll-runs/<uuid:run_id>/close", methods=["POST"])
@require_auth
def close_payroll_run(run_id):
    run = query_one("SELECT * FROM payroll_runs WHERE id = %s", (run_id,))
    if not run:
        return jsonify({"error": "Planilla no encontrada"}), 404
    if run["state"] != "finance_validated":
        return jsonify({"error": "La planilla requiere validacion de Finanzas antes del cierre"}), 409

    actor = _actor_id()
    snapshot = {
        "closed_at": datetime.utcnow().isoformat(),
        "totals": {
            "gross": float(run["total_gross"] or 0),
            "discounts": float(run["total_discounts"] or 0),
            "worker_contributions": float(run["total_worker_contributions"] or 0),
            "employer_contributions": float(run["total_employer_contributions"] or 0),
            "net": float(run["total_net"] or 0),
        },
    }
    with tx() as (conn, cur):
        cur.execute(
            "UPDATE payroll_runs SET state = 'closed', closed_at = NOW(), closed_by = %s WHERE id = %s",
            (actor, run_id),
        )
        cur.execute(
            "INSERT INTO payroll_snapshots (payroll_run_id, snapshot_data) VALUES (%s, %s::jsonb)",
            (run_id, json.dumps(snapshot)),
        )
        record_audit_event(
            cur,
            actor_user_id=actor,
            module="payroll",
            action="close_run",
            entity_type="payroll_runs",
            entity_id=run_id,
            new_data=snapshot,
            reason=(request.get_json(silent=True) or {}).get("reason", "Cierre de planilla"),
            ip_address=request.remote_addr,
        )
    return jsonify({"message": "Planilla cerrada", "snapshot": snapshot}), 200


@operations_bp.route("/admin/payroll-payslips/generate", methods=["POST"])
@require_auth
def generate_payroll_payslips():
    data = request.get_json() or {}
    run_id = data.get("payroll_run_id")
    run = query_one("SELECT state FROM payroll_runs WHERE id = %s", (run_id,))
    if not run or run["state"] != "closed":
        return jsonify({"error": "Solo se generan boletas de pago desde planilla cerrada"}), 409

    with tx() as (conn, cur):
        cur.execute(
            """
            INSERT INTO payroll_payslips (payroll_run_id, employee_id)
            SELECT DISTINCT payroll_run_id, employee_id
              FROM payroll_items
             WHERE payroll_run_id = %s
            ON CONFLICT DO NOTHING
            """,
            (run_id,),
        )
    return jsonify({"message": "Boletas de pago de remuneraciones generadas"}), 201


@operations_bp.route("/admin/salary-payment-batches", methods=["POST"])
@require_auth
def create_salary_payment_batch():
    data = request.get_json() or {}
    run_id = data.get("payroll_run_id")
    run = query_one("SELECT state, total_net FROM payroll_runs WHERE id = %s", (run_id,))
    if not run or run["state"] != "closed":
        return jsonify({"error": "Solo se preparan pagos de sueldos desde planilla cerrada"}), 409

    actor = _actor_id()
    with tx() as (conn, cur):
        cur.execute(
            """
            INSERT INTO salary_payment_batches (payroll_run_id, state, total_amount, prepared_by)
            VALUES (%s, 'prepared', %s, %s)
            RETURNING id
            """,
            (run_id, run["total_net"] or 0, actor),
        )
        batch_id = cur.fetchone()["id"]
    return jsonify({"id": str(batch_id), "state": "prepared"}), 201


@operations_bp.route("/admin/audit-events", methods=["GET"])
@require_auth
def list_audit_events():
    rows = query_all(
        """
        SELECT id, module, action, entity_type, entity_id, reason, created_at
          FROM audit_events
         ORDER BY created_at DESC
         LIMIT 100
        """
    )
    for row in rows:
        row["id"] = str(row["id"])
        if row["entity_id"]:
            row["entity_id"] = str(row["entity_id"])
        row["created_at"] = row["created_at"].isoformat()
    return jsonify(rows), 200
