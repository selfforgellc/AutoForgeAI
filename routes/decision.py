
from services.resolution_engine import downgrade_severity_after_resolution, should_auto_close
from models.resolution_history import ResolutionHistory

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session
from db import get_session
from core.api_response import success
from models.issue import IssueStatus
from models.decision import Decision
from datetime import datetime

router = APIRouter()

class DecisionRequest(BaseModel):
    vehicle_id: str
    diagnosis_id: str
    decision_type: str

@router.post("/decision")
def make_decision(body: DecisionRequest, session: Session = Depends(get_session)):

    decision = Decision(
        vehicle_id=body.vehicle_id,
        diagnosis_id=body.diagnosis_id,
        decision_type=body.decision_type
    )
    session.add(decision)

    # Auto resolve issues if fix_now
    if body.decision_type == "fix_now":
        issues = session.query(IssueStatus).filter_by(
            vehicle_id=body.vehicle_id,
            resolved=False
        ).all()

        for issue in issues:
            issue.resolved = True
            issue.resolved_at = datetime.utcnow()

    
    # Record resolution history if fixing
    if body.decision_type == "fix_now":
        for issue in issues:
            history = ResolutionHistory(
                vehicle_id=body.vehicle_id,
                diagnosis_id=issue.diagnosis_id,
                previous_severity=issue.severity
            )
            session.add(history)

            issue.severity = downgrade_severity_after_resolution(issue.severity)

    session.commit()


    return success({"decision_id": decision.id})
