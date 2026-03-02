
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.config import settings

import os
SECRET = os.getenv("JWT_SECRET", "CHANGE_ME_IN_PRODUCTION")
ALGORITHM = "HS256"

security = HTTPBearer()

def create_token(user_id: str, tier: str):
    payload = {
        "sub": user_id,
        "tier": tier,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET, algorithms=[ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def require_tier(required_tier: str):
    def dependency(user=Depends(get_current_user)):
        tier_order = ["basic", "pro", "enterprise"]
        if tier_order.index(user["tier"]) < tier_order.index(required_tier):
            raise HTTPException(status_code=403, detail="Upgrade required")
        return user
    return dependency


from sqlmodel import select
from db import get_session
from models.user import User

def require_admin(user=Depends(get_current_user)):
    with next(get_session()) as session:
        db_user = session.exec(select(User).where(User.id == user["sub"])).first()
        if not db_user or not db_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
    return user


from datetime import datetime
from sqlmodel import select
from models.usage import Usage
from core.tier_limits import TIER_DAILY_LIMITS

def enforce_usage_limit(user=Depends(get_current_user)):
    today = datetime.utcnow().strftime("%Y-%m-%d")

    with next(get_session()) as session:
        usage = session.exec(
            select(Usage).where(
                Usage.user_id == user["sub"],
                Usage.date == today
            )
        ).first()

        limit = TIER_DAILY_LIMITS.get(user["tier"], 5)

        if usage and usage.diagnosis_count >= limit:
            raise HTTPException(status_code=429, detail="Daily usage limit reached")

        if not usage:
            usage = Usage(user_id=user["sub"], date=today, diagnosis_count=1)
        else:
            usage.diagnosis_count += 1

        session.add(usage)
        session.commit()

    return user
