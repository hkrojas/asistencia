LEGAL_PENDING_NOTE = (
    "SUPUESTO PENDIENTE DE VALIDACION LEGAL: cobertura entre edificios con RUC/empleador distinto."
)


def _normalized_ruc(building):
    if not building:
        return None
    return building.get("employer_ruc") or building.get("ruc")


def classify_coverage(origin_building, destination_building):
    """Classify an inter-building coverage for approval and legal validation."""
    origin_ruc = _normalized_ruc(origin_building)
    destination_ruc = _normalized_ruc(destination_building)
    is_cross_employer = bool(origin_ruc and destination_ruc and origin_ruc != destination_ruc)

    if is_cross_employer:
        return {
            "is_cross_employer": True,
            "legal_validation_required": True,
            "approval_blocked": True,
            "status": "pending_legal_validation",
            "legal_note": LEGAL_PENDING_NOTE,
        }

    return {
        "is_cross_employer": False,
        "legal_validation_required": False,
        "approval_blocked": False,
        "status": "requested",
        "legal_note": None,
    }


def validate_prepayroll_submission(
    pending_coverages=0,
    unclassified_absences=0,
    unapproved_overtime=0,
    unrevised_critical_shifts=0,
):
    """Return blocking reasons before an administrator sends building prepayroll to HR."""
    errors = []
    if pending_coverages:
        errors.append(f"{pending_coverages} coberturas pendientes")
    if unclassified_absences:
        errors.append(f"{unclassified_absences} faltas sin clasificar")
    if unapproved_overtime:
        errors.append(f"{unapproved_overtime} horas extra sin aprobacion")
    if unrevised_critical_shifts:
        errors.append(f"{unrevised_critical_shifts} turnos criticos sin revisar")

    return {
        "can_send": not errors,
        "errors": errors,
        "blocker_count": (
            int(pending_coverages or 0)
            + int(unclassified_absences or 0)
            + int(unapproved_overtime or 0)
            + int(unrevised_critical_shifts or 0)
        ),
    }

