
from datetime import datetime

SYSTEM_FAILURE_BASE_PROB = {
    "braking": 0.35,
    "engine": 0.25,
    "transmission": 0.22,
    "steering": 0.28,
    "electrical": 0.15,
    "cooling": 0.18,
    "default": 0.12
}

def predict_failure_probability(system: str, created_at):
    base_prob = SYSTEM_FAILURE_BASE_PROB.get(system, SYSTEM_FAILURE_BASE_PROB["default"])
    days = (datetime.utcnow() - created_at).days
    growth = min(days * 0.01, 0.5)
    probability = min(base_prob + growth, 0.95)
    return round(probability, 2)

def estimate_maintenance_window(probability: float):
    if probability >= 0.75:
        return "Immediate service recommended"
    elif probability >= 0.5:
        return "Service within 2-4 weeks"
    elif probability >= 0.3:
        return "Monitor and schedule soon"
    else:
        return "Low urgency monitoring"
