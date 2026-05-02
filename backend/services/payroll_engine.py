from decimal import Decimal


def _amount(value):
    return Decimal(str(value or 0))


def summarize_payroll_items(items):
    """Summarize payroll items into gross, deductions, contributions, net, and company cost."""
    gross_income = Decimal("0")
    discounts = Decimal("0")
    worker_contributions = Decimal("0")
    employer_contributions = Decimal("0")

    for item in items:
        item_type = item.get("item_type")
        amount = _amount(item.get("amount"))
        if item_type == "income":
            gross_income += amount
        elif item_type == "discount":
            discounts += amount
        elif item_type == "worker_contribution":
            worker_contributions += amount
        elif item_type == "employer_contribution":
            employer_contributions += amount

    net_pay = gross_income - discounts - worker_contributions
    company_cost = gross_income + employer_contributions

    return {
        "gross_income": float(gross_income),
        "discounts": float(discounts),
        "worker_contributions": float(worker_contributions),
        "employer_contributions": float(employer_contributions),
        "net_pay": float(net_pay),
        "company_cost": float(company_cost),
    }

