
def compute_value_impact(severity: str, decision_type: str):
    base_cost = {
        "low": 150,
        "moderate": 600,
        "critical": 1800
    }.get(severity, 200)

    if decision_type == "fix_now":
        saved = base_cost * 0.8
        risk = 0
    elif decision_type == "monitor":
        saved = base_cost * 0.3
        risk = base_cost * 0.2
    elif decision_type == "ignore":
        saved = 0
        risk = base_cost * 1.2
    else:
        saved = 0
        risk = base_cost * 0.1

    score = saved - risk
    return saved, risk, score

def apply_decay(total_risk: float, unresolved_issues: int):
    decay_multiplier = 1 + (unresolved_issues * 0.05)
    return total_risk * decay_multiplier

from datetime import datetime

def compute_time_decay(severity: str, created_at):
    days = (datetime.utcnow() - created_at).days
    multiplier = 0.02 if severity == "low" else 0.05 if severity == "moderate" else 0.1
    return days * multiplier
