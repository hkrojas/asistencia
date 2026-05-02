GLOBAL_BUILDING_ROLES = {"Superadmin", "CompanyAdmin", "HR", "Finance", "Auditor"}
WAGE_VISIBLE_ROLES = {"Superadmin", "CompanyAdmin", "HR", "Finance"}


def can_access_building(role, assigned_building_ids, building_id):
    """Return whether a role can access a building-scoped record."""
    if role in GLOBAL_BUILDING_ROLES:
        return True
    if role == "BuildingAdmin":
        return str(building_id) in {str(value) for value in (assigned_building_ids or [])}
    return False


def can_view_wages(role, assignment=None):
    """Return whether wage/bank/payment-sensitive data may be shown."""
    if role in WAGE_VISIBLE_ROLES:
        return True
    if role == "BuildingAdmin":
        return bool((assignment or {}).get("can_view_wages"))
    return False

