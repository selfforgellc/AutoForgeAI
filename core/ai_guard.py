from datetime import datetime, timedelta
from fastapi import HTTPException

# --------------------------------------------------
# Per-Vehicle AI Usage Tracking
# --------------------------------------------------

AI_DAILY_LIMIT = 50  # Adjust as needed

_usage_store = {}


def check_ai_usage(vehicle_id: str):
    now = datetime.utcnow()

    if vehicle_id not in _usage_store:
        _usage_store[vehicle_id] = {
            "count": 0,
            "reset_time": now + timedelta(days=1)
        }

    record = _usage_store[vehicle_id]

    if now >= record["reset_time"]:
        record["count"] = 0
        record["reset_time"] = now + timedelta(days=1)

    if record["count"] >= AI_DAILY_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Daily AI usage limit reached for this vehicle."
        )

    record["count"] += 1
