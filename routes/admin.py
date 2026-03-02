
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from db import get_session
from models.user import User
from core.api_response import success
from core.auth import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users", dependencies=[Depends(require_admin)])
def list_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return success([
        {
            "id": u.id,
            "email": u.email,
            "tier": u.tier,
            "is_admin": u.is_admin
        }
        for u in users
    ])

@router.post("/users/{user_id}/tier", dependencies=[Depends(require_admin)])
def update_user_tier(user_id: str, tier: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.id == user_id)).first()
    if user:
        user.tier = tier
        session.add(user)
        session.commit()
    return success({"user_id": user_id, "new_tier": tier})

@router.post("/users/{user_id}/admin", dependencies=[Depends(require_admin)])
def set_admin(user_id: str, is_admin: bool, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.id == user_id)).first()
    if user:
        user.is_admin = is_admin
        session.add(user)
        session.commit()
    return success({"user_id": user_id, "is_admin": is_admin})
