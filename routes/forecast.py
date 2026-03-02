from fastapi import APIRouter, Depends
from sqlmodel import Session

from db import get_session
from models.issue import IssueStatus
from core.response import success
from core.auth import require_tier
from services.cache_service import cache_get, cache_set
from services.value_forecast_engine import (
    forecast_cost,
    cost_of_delay,
    prevented_cost_if_fixed_now,
)

router = APIRouter()


@router.get(
    "/vehicle/{vehicle_id}/forecast",
    dependencies=[Depends(require_tier("pro"))],
)
def forecast(
    vehicle_id: str,
    session: Session = Depends(get_session),
):
    cache_key = f"forecast:{vehicle_id}"
    cached = cache_get(cache_key)
    if cached:
        return success(cached)

    issues = (
        session.query(IssueStatus)
        .filter_by(vehicle_id=vehicle_id, resolved=False)
        .all()
    )

    open_count = len(issues)
    results = []

    for issue in issues:
        forecast_3 = forecast_cost(issue.severity, 3, open_count)
        forecast_6 = forecast_cost(issue.severity, 6, open_count)
        forecast_12 = forecast_cost(issue.severity, 12, open_count)

        delay_6 = cost_of_delay(issue.severity, 6)
        prevented = prevented_cost_if_fixed_now(issue.severity)

        results.append(
            {
                "diagnosis_id": issue.diagnosis_id,
                "severity": issue.severity,
                "forecast_3_months": forecast_3,
                "forecast_6_months": forecast_6,
                "forecast_12_months": forecast_12,
                "cost_of_delay_6_months": delay_6,
                "prevented_cost_if_fixed_now": prevented,
            }
        )

    cache_set(cache_key, results)
    return success(results)
