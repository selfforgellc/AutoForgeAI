
from datetime import datetime

SYSTEM_RISK_CURVES = {
    "braking": {"base": 800, "daily_multiplier": 0.12},
    "engine": {"base": 1500, "daily_multiplier": 0.08},
    "transmission": {"base": 2000, "daily_multiplier": 0.07},
    "steering": {"base": 1200, "daily_multiplier": 0.10},
    "electrical": {"base": 600, "daily_multiplier": 0.05},
    "cooling": {"base": 900, "daily_multiplier": 0.06},
    "default": {"base": 500, "daily_multiplier": 0.04}
}

def compute_system_risk(system: str, created_at):
    curve = SYSTEM_RISK_CURVES.get(system, SYSTEM_RISK_CURVES["default"])
    days = (datetime.utcnow() - created_at).days
    risk = curve["base"] * (1 + (curve["daily_multiplier"] * days))
    return round(risk, 2)
