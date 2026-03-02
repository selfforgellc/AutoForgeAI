
from fastapi import APIRouter
from sqlmodel import select
from models.system_trend import SystemTrend
from db import get_session
from core.api_response import success

router = APIRouter()

@router.get("/fleet/trends")
def fleet_trends():
    with next(get_session()) as session:
        trends = session.exec(select(SystemTrend)).all()
        results = [
            {
                "system": t.system,
                "occurrence_count": t.occurrence_count
            }
            for t in trends
        ]
    return success(results)
