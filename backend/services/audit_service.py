import json


def record_audit_event(
    cursor,
    *,
    module,
    action,
    entity_type,
    entity_id=None,
    actor_user_id=None,
    old_data=None,
    new_data=None,
    reason=None,
    ip_address=None,
):
    """Persist a cross-module audit event using the caller's transaction cursor."""
    cursor.execute(
        """
        INSERT INTO audit_events (
            actor_user_id, module, action, entity_type, entity_id,
            old_data, new_data, reason, ip_address
        )
        VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s)
        """,
        (
            actor_user_id,
            module,
            action,
            entity_type,
            entity_id,
            json.dumps(old_data) if old_data is not None else None,
            json.dumps(new_data) if new_data is not None else None,
            reason,
            ip_address,
        ),
    )

