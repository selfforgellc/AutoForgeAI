
def compute_weighted_confidence(base, symptom_score, obd_score, historical, system_risk):
    confidence = (
        base * 0.35 +
        symptom_score * 0.20 +
        obd_score * 0.20 +
        historical * 0.15 +
        system_risk * 0.10
    )
    return max(0.0, min(confidence, 1.0))
