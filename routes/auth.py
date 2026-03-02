from __future__ import annotations

import hashlib

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from core.api_response import success
from core.auth import create_token
from db import get_session
from models.user import User


router = APIRouter()


class RegisterBody(BaseModel):
    email: str
    password: str


class LoginBody(BaseModel):
    email: str
    password: str


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _prep_password(password: str) -> bytes:
    """bcrypt hard limit is 72 bytes; sha256-prehash anything longer."""
    raw = (password or "").encode("utf-8")
    if len(raw) <= 72:
        return raw
    return hashlib.sha256(raw).digest()


def _hash_password(password: str) -> str:
    prepared = _prep_password(password)
    hashed = bcrypt.hashpw(prepared, bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    try:
        prepared = _prep_password(plain)
        return bcrypt.checkpw(prepared, hashed.encode("utf-8"))
    except Exception:
        return False


@router.post("/auth/register")
def register(
    body: RegisterBody | None = None,
    email: str | None = None,
    password: str | None = None,
    session: Session = Depends(get_session),
):
    """Register supports BOTH JSON body and legacy query params."""
    if body is not None:
        email = body.email
        password = body.password

    email_n = _normalize_email(email or "")
    if not email_n or not password:
        raise HTTPException(status_code=422, detail="Email and password are required")

    existing = session.exec(select(User).where(User.email == email_n)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")

    user = User(
        email=email_n,
        password=_hash_password(password),
        tier="basic",
        is_admin=False,
        subscription_active=False,
        subscription_plan="none",
        subscription_source="none",
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    return success({"user_id": user.id})


@router.post("/auth/login")
def login(
    body: LoginBody | None = None,
    email: str | None = None,
    password: str | None = None,
    session: Session = Depends(get_session),
):
    """Login supports BOTH JSON body and legacy query params."""
    if body is not None:
        email = body.email
        password = body.password

    email_n = _normalize_email(email or "")
    if not email_n or not password:
        raise HTTPException(status_code=422, detail="Email and password are required")

    user = session.exec(select(User).where(User.email == email_n)).first()
    if not user or not _verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(user.id, user.tier)

    return success(
        {
            "token": token,
            "tier": user.tier,
            "user_id": user.id,
            "is_admin": bool(getattr(user, "is_admin", False)),
        }
    )
