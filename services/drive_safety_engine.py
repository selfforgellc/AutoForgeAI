
def classify_roadworthiness(vhi_score, critical_count, failure_probabilities):
    if critical_count > 0:
        return "UNSAFE"

    if vhi_score < 40:
        return "HIGH_RISK"

    if vhi_score < 70:
        return "MODERATE_RISK"

    return "SAFE"

def compute_risk_band(vhi_score):
    if vhi_score >= 85:
        return "A"
    elif vhi_score >= 70:
        return "B"
    elif vhi_score >= 55:
        return "C"
    elif vhi_score >= 40:
        return "D"
    else:
        return "F"
