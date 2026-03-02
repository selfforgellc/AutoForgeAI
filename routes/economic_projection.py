
from fastapi import APIRouter, Depends
from sqlmodel import Session
from db import get_session
from models.issue import IssueStatus
from models.decision import Decision
from core.api_response import success
from services.economic_compound_engine import compute_compounded_risk, neglect_penalty

router = APIRouter()

@router.get("/vehicle/{vehicle_id}/economic_projection")
def economic_projection(vehicle_id: str, session: Session = Depends(get_session)):

    issues = session.query(IssueStatus).filter_by(
        vehicle_id=vehicle_id,
        resolved=False
    ).all()

    decisions = session.query(Decision).filter_by(
        vehicle_id=vehicle_id
    ).all()

    total_ignored = sum(1 for d in decisions if d.decision_type == "ignore")
    open_count = len(issues)

    projections = []
    for issue in issues:
        compounded = compute_compounded_risk(issue.severity, issue.created_at, open_count)
        penalty = neglect_penalty(total_ignored)

        projections.append({
            "diagnosis_id": issue.diagnosis_id,
            "severity": issue.severity,
            "compounded_risk_multiplier": compounded,
            "neglect_penalty_multiplier": penalty
        })

    return success(projections)
