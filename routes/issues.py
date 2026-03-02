from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from db import get_session
from models.issue import IssueStatus
from core.api_response import success
from services.cache_service import cache_get, cache_set, cache_delete

router = APIRouter()


class CreateIssueBody(BaseModel):
    summary: str
    severity: int | None = 5


class ResolveIssueBody(BaseModel):
    reason: str


def _safe_int(x, default=0):
    try:
        return int(x)
    except Exception:
        return default


def _issue_to_payload(issue: IssueStatus) -> dict:
    created = issue.created_at or datetime.utcnow()
    days_unresolved = (datetime.utcnow() - created).days

    sev = _safe_int(issue.severity, 0)
    # Keep your earlier “risk” simple (don’t crash)
    projected_risk = round(500 * (1 + 0.04 * days_unresolved), 2)

    return {
        "id": issue.id,
        "diagnosis_id": issue.diagnosis_id,
        "severity": sev,
        "resolved": bool(issue.resolved),
        "created_at": created.isoformat() if created else None,
        "resolved_at": issue.resolved_at.isoformat() if issue.resolved_at else None,
        "resolved_reason": issue.resolved_reason,
        "days_unresolved": days_unresolved,
        "projected_risk": projected_risk,
    }


@router.get("/vehicle/{vehicle_id}/issues")
def get_issues(
    vehicle_id: str,
    include_resolved: int = 0,
    session: Session = Depends(get_session),
):
    cache_key = f"issues:{vehicle_id}:incl={int(include_resolved)}"
    cached = cache_get(cache_key)
    if cached:
        return success(cached)

    stmt = select(IssueStatus).where(IssueStatus.vehicle_id == vehicle_id)
    if not include_resolved:
        stmt = stmt.where(IssueStatus.resolved == False)  # noqa

    issues = session.exec(stmt).all()
    # newest first (created_at can be None in old rows)
    issues.sort(key=lambda x: x.created_at or datetime(1970, 1, 1), reverse=True)

    results = [_issue_to_payload(i) for i in issues]
    cache_set(cache_key, results)
    return success(results)


@router.post("/vehicle/{vehicle_id}/issues")
def create_issue(vehicle_id: str, body: CreateIssueBody, session: Session = Depends(get_session)):
    summary = (body.summary or "").strip()
    if not summary:
        raise HTTPException(status_code=422, detail="summary is required")

    sev = body.severity if body.severity is not None else 5
    sev = max(1, min(10, _safe_int(sev, 5)))

    issue = IssueStatus(
        vehicle_id=vehicle_id,
        diagnosis_id=summary,
        severity=str(sev),
        resolved=False,
        created_at=datetime.utcnow(),
        resolved_at=None,
        resolved_reason=None,
    )
    session.add(issue)
    session.commit()

    cache_delete(f"issues:{vehicle_id}:incl=0")
    cache_delete(f"issues:{vehicle_id}:incl=1")

    return success({"id": issue.id})


@router.patch("/vehicle/{vehicle_id}/issues/{issue_id}/resolve")
def resolve_issue(vehicle_id: str, issue_id: str, body: ResolveIssueBody, session: Session = Depends(get_session)):
    reason = (body.reason or "").strip()
    if not reason:
        raise HTTPException(status_code=422, detail="reason is required")

    stmt = select(IssueStatus).where(IssueStatus.id == issue_id, IssueStatus.vehicle_id == vehicle_id)
    issue = session.exec(stmt).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    issue.resolved = True
    issue.resolved_reason = reason
    issue.resolved_at = datetime.utcnow()

    session.add(issue)
    session.commit()

    cache_delete(f"issues:{vehicle_id}:incl=0")
    cache_delete(f"issues:{vehicle_id}:incl=1")

    return success({"ok": True})