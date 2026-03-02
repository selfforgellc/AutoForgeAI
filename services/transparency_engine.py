
def build_transparency(severity: str, confidence: float):
    urgency_map = {
        "low": "Low urgency",
        "moderate": "Schedule service soon",
        "critical": "Immediate attention required"
    }

    cost_map = {
        "low": "$100 - $300",
        "moderate": "$400 - $1200",
        "critical": "$1200 - $3000+"
    }

    diy_possible = severity == "low"
    professional_required = severity in {"moderate", "critical"}

    return {
        "why_this_is_happening": "System analysis detected performance anomalies.",
        "potential_consequences": "Issue may worsen if ignored.",
        "estimated_cost_range": cost_map.get(severity),
        "diy_possible": diy_possible,
        "professional_required": professional_required,
        "urgency_level": urgency_map.get(severity),
        "risk_if_ignored": "Compounding mechanical damage likely."
    }
