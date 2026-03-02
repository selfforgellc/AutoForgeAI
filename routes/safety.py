from services.resolution_engine import should_auto_close

from fastapi import APIRouter, Depends
from sqlmodel import Session
from db import get_session
from models.issue import IssueStatus
from core.api_response import success
from services.vhi_engine import calculate_vhi
from services.drive_safety_engine import classify_roadworthiness, compute_risk_band
from services.predictive_engine import predict_failure_probability
from services.economic_compound_engine import compute_compounded_risk, neglect_penalty
from models.decision import Decision

router = APIRouter()

@router.get("/vehicle/{vehicle_id}/safety")
def vehicle_safety(vehicle_id: str, session: Session = Depends(get_session)):

    issues = session.query(IssueStatus).filter_by(
        vehicle_id=vehicle_id,
        resolved=False
    ).all()

    decisions = session.query(Decision).filter_by(
        vehicle_id=vehicle_id
    ).all()

    open_issue_count = len(issues)
    critical_count = sum(1 for i in issues if i.severity == "critical")
    total_ignored = sum(1 for d in decisions if d.decision_type == "ignore")

    failure_probs = [
        predict_failure_probability(i.severity, i.created_at)
        for i in issues
    ]

    compounded = [
        compute_compounded_risk(i.severity, i.created_at, open_issue_count)
        for i in issues
    ]

    penalty = neglect_penalty(total_ignored)

    vhi_score = calculate_vhi(
        open_issue_count,
        critical_count,
        failure_probs,
        compounded,
        penalty
    )

    road_status = classify_roadworthiness(vhi_score, critical_count, failure_probs)
    risk_band = compute_risk_band(vhi_score)

    
    auto_closed = False
    if should_auto_close(vhi_score):
        auto_closed = True

    return success({

        "vehicle_id": vehicle_id,
        "vhi_score": vhi_score,
        "roadworthiness": road_status,
        "risk_band": risk_band,
        "critical_issues": critical_count
    })
