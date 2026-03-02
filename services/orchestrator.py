from services.explainability_engine import build_confidence_explanation, build_severity_explanation
from services.trend_engine import record_system_occurrence, get_trend_multiplier
from datetime import datetime

from services.system_risk_engine import compute_system_risk

from diag_engine import run_diagnosis
from services.confidence_engine import compute_weighted_confidence

def run_pipeline(vehicle_id, symptoms=None, chat_input=None, obd_codes=None):
    result = run_diagnosis(
        vehicle_id=vehicle_id,
        symptoms=symptoms,
        chat_input=chat_input,
        obd_codes=obd_codes,
        context=None
    )

    if not result:
        return None

    base_conf = result["confidence"]
    symptom_score = 0.9 if symptoms else 0.4
    obd_score = 0.95 if obd_codes else 0.0
    historical_score = 0.6
    system_risk = 0.7

    confidence = compute_weighted_confidence(
        base_conf,
        symptom_score,
        obd_score,
        historical_score,
        system_risk
    )

    result["confidence"] = confidence
    result["uncertainty_percentage"] = round(1 - confidence, 2)

    
    # Add projected risk preview
    if result.get("related_systems"):
        primary_system = result["related_systems"][0]
    else:
        primary_system = "default"

    projected_risk = compute_system_risk(primary_system, datetime.utcnow())

    
    # Record global occurrence
    record_system_occurrence(primary_system)

    # Apply trend multiplier to confidence
    trend_multiplier = get_trend_multiplier(primary_system)
    result["confidence"] = min(result["confidence"] * trend_multiplier, 1.0)

    result["projected_risk"] = projected_risk


    
    # Build explainability block
    explanation = build_confidence_explanation(
        base_conf,
        symptom_score,
        obd_score,
        historical_score,
        system_risk,
        trend_multiplier
    )

    severity_details = build_severity_explanation(
        result.get("severity", "unknown"),
        0,
        0
    )

    result["explainability"] = {
        "confidence_breakdown": explanation,
        "severity_breakdown": severity_details
    }

    return result


