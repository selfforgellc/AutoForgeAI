from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import Field, SQLModel, Session, select

from db import get_session

# IMPORTANT:
# We intentionally depend on the existing auth current_user in your auth_routes module.
# This keeps your cookie auth behavior consistent across the app.
try:
    from auth_routes import current_user as auth_current_user
except Exception:
    from routes.auth_routes import current_user as auth_current_user  # type: ignore


router = APIRouter(prefix="/api/push", tags=["push"])


class PushSubscriptionRow(SQLModel, table=True):
    __tablename__ = "push_subscriptions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_key: str = Field(index=True)

    # endpoint is the stable unique identifier for a subscription
    endpoint: str = Field(index=True)

    # store full subscription JSON for pywebpush
    subscription_json: str

    created_at: datetime = Field(default_factory=datetime.utcnow)


class SubscribeIn(BaseModel):
    subscription: Dict[str, Any]


class UnsubscribeIn(BaseModel):
    endpoint: str


def _get_user_key(user: Any) -> str:
    # Prefer stable numeric ID if available; else fall back to email/username.
    for attr in ("id", "user_id", "uid"):
        if hasattr(user, attr) and getattr(user, attr) is not None:
            return str(getattr(user, attr))
    if isinstance(user, dict):
        for k in ("id", "user_id", "uid", "email", "username"):
            if user.get(k):
                return str(user.get(k))
    for attr in ("email", "username"):
        if hasattr(user, attr) and getattr(user, attr):
            return str(getattr(user, attr))
    return "unknown"


async def _authed_user(request: Request):
    u = auth_current_user(request)
    if hasattr(u, "__await__"):
        u = await u
    return u


@router.post("/subscribe")
async def subscribe(payload: SubscribeIn, request: Request):
    user = await _authed_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    sub = payload.subscription or {}
    endpoint = sub.get("endpoint")
    keys = (sub.get("keys") or {}) if isinstance(sub.get("keys"), dict) else {}

    if not endpoint or not isinstance(endpoint, str):
        raise HTTPException(status_code=400, detail="Missing subscription.endpoint")

    user_key = _get_user_key(user)

    with get_session() as session:  # type: Session
        existing = session.exec(select(PushSubscriptionRow).where(PushSubscriptionRow.endpoint == endpoint)).first()
        if existing:
            existing.user_key = user_key
            existing.subscription_json = json.dumps(sub)
            session.add(existing)
            session.commit()
            return {"ok": True, "updated": True}

        row = PushSubscriptionRow(
            user_key=user_key,
            endpoint=endpoint,
            subscription_json=json.dumps(sub),
        )
        session.add(row)
        session.commit()

    return {"ok": True, "created": True}


@router.post("/unsubscribe")
async def unsubscribe(payload: UnsubscribeIn, request: Request):
    user = await _authed_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    endpoint = (payload.endpoint or "").strip()
    if not endpoint:
        raise HTTPException(status_code=400, detail="Missing endpoint")

    user_key = _get_user_key(user)

    with get_session() as session:  # type: Session
        row = session.exec(
            select(PushSubscriptionRow).where(
                PushSubscriptionRow.user_key == user_key, PushSubscriptionRow.endpoint == endpoint
            )
        ).first()
        if row:
            session.delete(row)
            session.commit()

    return {"ok": True}


def _require_vapid() -> Dict[str, str]:
    private_key = os.getenv("VAPID_PRIVATE_KEY", "").strip()
    subject = os.getenv("VAPID_SUBJECT", "mailto:admin@selfforge.ai").strip()
    if not private_key:
        raise HTTPException(
            status_code=500,
            detail="Missing VAPID_PRIVATE_KEY on backend. Generate VAPID keys and set env vars.",
        )
    return {"private_key": private_key, "subject": subject}


@router.post("/test")
async def test_push(request: Request):
    user = await _authed_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    vapid = _require_vapid()

    # pywebpush is the standard lightweight library
    try:
        from pywebpush import webpush, WebPushException  # type: ignore
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Missing dependency: pywebpush. Install with: pip install pywebpush",
        )

    user_key = _get_user_key(user)

    with get_session() as session:  # type: Session
        rows = session.exec(select(PushSubscriptionRow).where(PushSubscriptionRow.user_key == user_key)).all()

    if not rows:
        raise HTTPException(status_code=400, detail="No push subscription found for this user. Enable Push in Profile.")

    payload = {
        "title": "AutoForge",
        "body": "✅ Test push from AutoForge. You will also receive maintenance reminders here.",
        "data": {"url": "/"},
    }

    sent = 0
    failed = 0

    for row in rows:
        try:
            sub = json.loads(row.subscription_json)
            webpush(
                subscription_info=sub,
                data=json.dumps(payload),
                vapid_private_key=vapid["private_key"],
                vapid_claims={"sub": vapid["subject"]},
            )
            sent += 1
        except Exception:
            failed += 1

    return {"ok": True, "sent": sent, "failed": failed}
