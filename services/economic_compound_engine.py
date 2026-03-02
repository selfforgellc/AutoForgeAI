
from datetime import datetime

SEVERITY_MULTIPLIERS = {
    "low": 0.02,
    "moderate": 0.05,
    "critical": 0.10
}

def compute_compounded_risk(severity: str, created_at, total_open_issues: int):
    days = (datetime.utcnow() - created_at).days
    base_growth = SEVERITY_MULTIPLIERS.get(severity, 0.03)
    
    # Nonlinear growth curve
    growth = days * base_growth
    
    # Multi-issue stress multiplier
    stress_multiplier = 1 + (total_open_issues * 0.07)
    
    compounded = (1 + growth) * stress_multiplier
    return round(compounded, 2)

def neglect_penalty(total_ignored: int):
    return round(1 + (total_ignored * 0.15), 2)
