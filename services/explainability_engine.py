
def build_confidence_explanation(base, symptom_score, obd_score, historical, system_risk, trend_multiplier):
    return {
        "base_ai_confidence": round(base, 2),
        "symptom_influence": round(symptom_score, 2),
        "obd_influence": round(obd_score, 2),
        "historical_influence": round(historical, 2),
        "system_risk_influence": round(system_risk, 2),
        "trend_multiplier": round(trend_multiplier, 2),
        "explanation": "Confidence calculated using weighted system model combining AI output, structured input, historical vehicle data, and cross-vehicle trends."
    }

def build_severity_explanation(severity, unresolved_count, ignored_count):
    return {
        "severity_level": severity,
        "unresolved_issues": unresolved_count,
        "ignored_history": ignored_count,
        "reasoning": "Severity escalated based on system criticality and unresolved/ignored issue history."
    }
