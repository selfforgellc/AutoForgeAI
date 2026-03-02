
from sqlmodel import select
from models.system_trend import SystemTrend
from db import get_session
from datetime import datetime

TREND_ESCALATION_THRESHOLD = 10

def record_system_occurrence(system: str):
    with next(get_session()) as session:
        trend = session.exec(select(SystemTrend).where(SystemTrend.system == system)).first()
        if not trend:
            trend = SystemTrend(system=system, occurrence_count=1)
            session.add(trend)
        else:
            trend.occurrence_count += 1
            trend.last_updated = datetime.utcnow()
        session.commit()

def get_trend_multiplier(system: str):
    with next(get_session()) as session:
        trend = session.exec(select(SystemTrend).where(SystemTrend.system == system)).first()
        if not trend:
            return 1.0
        if trend.occurrence_count >= TREND_ESCALATION_THRESHOLD:
            return 1.2
        return 1.0
