
from datetime import datetime

SEVERITY_BASE_COST = {
    "low": 300,
    "moderate": 1200,
    "critical": 3500
}

def forecast_cost(severity: str, months: int, open_issue_count: int):
    base_cost = SEVERITY_BASE_COST.get(severity, 800)
    
    # Monthly escalation curve (nonlinear)
    monthly_growth = 0.08 if severity == "critical" else 0.05 if severity == "moderate" else 0.03
    projected = base_cost * (1 + (monthly_growth * months))
    
    # Multi-issue stress factor
    stress_factor = 1 + (open_issue_count * 0.06)
    
    return round(projected * stress_factor, 2)

def cost_of_delay(severity: str, months: int):
    base_cost = SEVERITY_BASE_COST.get(severity, 800)
    delay_penalty_rate = 0.1 if severity == "critical" else 0.06 if severity == "moderate" else 0.03
    return round(base_cost * delay_penalty_rate * months, 2)

def prevented_cost_if_fixed_now(severity: str):
    base_cost = SEVERITY_BASE_COST.get(severity, 800)
    prevention_multiplier = 0.75
    return round(base_cost * prevention_multiplier, 2)
