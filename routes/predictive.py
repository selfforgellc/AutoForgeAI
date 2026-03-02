from fastapi import APIRouter, Depends
from sqlmodel import Session
from datetime import datetime

from db import get_session
from models.issue import IssueStatus
from core.response import success
from core.auth import require_tier
from services.cache_service import cache_get, cache_set
from services.predictive_engine import (
    predict_failure_probability,
    estimate_maintenance_window,
)

router = APIRouter()


@router.get(
    "/vehicle/{vehicle_id}/predictive",
    dependencies=[Depends(require_tier("pro"))],
)
def predictive_analysis(
    vehicle_id: str,
    session: Session = Depends(get_session),
):
    cache_key = f"predictive:{vehicle_id}"
    cached = cache_get(cache_key)
    if cached:
        return success(cached)

    issues = (
        session.query(IssueStatus)
        .filter_by(vehicle_id=vehicle_id, resolved=False)
        .all()
    )

    results = []
    for issue in issues:
        probability = predict_failure_probability(
            issue.severity,
            issue.created_at,
        )
        window = estimate_maintenance_window(probability)

        results.append(
            {
                "diagnosis_id": issue.diagnosis_id,
                "system": issue.severity,
                "failure_probability": probability,
                "recommended_window": window,
            }
        )

    cache_set(cache_key, results)
    return success(results)
