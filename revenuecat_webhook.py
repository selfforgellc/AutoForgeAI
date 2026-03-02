import os
import hmac
import hashlib
from typing import Any, Dict, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlmodel import select

from db import get_session
from models_user import User

router = APIRouter(prefix="/api/revenuecat", tags=["revenuecat"])

WEBHOOK_SECRET = os.getenv("REVENUECAT_WEBHOOK_SECRET", "")

def _verify_signature(raw_body: bytes, signature_header: Optional[str]) -> bool:
    """
    RevenueCat supports signed webhooks. Store the secret in REVENUECAT_WEBHOOK_SECRET.
    If you don't have signatures enabled yet, you can temporarily return True (NOT recommended for prod).
    """
    if not WEBHOOK_SECRET:
        return False
    if not signature_header:
        return False

    expected = hmac.new(WEBHOOK_SECRET.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    # signature_header format may vary based on RevenueCat settings; simplest compare:
    return hmac.compare_digest(signature_header.strip(), expected)

def _extract_app_user_id(payload: Dict[str, Any]) -> Optional[str]:
    # RevenueCat webhook payload includes an app_user_id field for the customer
    # (See RevenueCat docs: event types and fields)
    return payload.get("app_user_id") or payload.get("event", {}).get("app_user_id")

def _set_entitlement(db_user: User, active: bool, plan: str, source: str, expires_at: Optional[str]):
    db_user.subscription_active = bool(active)
    db_user.subscription_plan = plan or ("monthly" if active else "none")
    db_user.subscription_source = source or "unknown"
    db_user.subscription_expires_at = expires_at

@router.post("/webhook")
async def webhook(request: Request):
    raw = await request.body()
    sig = request.headers.get("X-RevenueCat-Signature") or request.headers.get("X-Revenuecat-Signature")

    # If you enabled signatures in RevenueCat, this is the check you want in production.
    # If not enabled yet, set REVENUECAT_WEBHOOK_SECRET and confirm the correct header key in their dashboard.
    if WEBHOOK_SECRET:
        if not _verify_signature(raw, sig):
            return JSONResponse({"error": "Invalid signature"}, status_code=401)

    payload = await request.json()
    app_user_id = _extract_app_user_id(payload)
    if not app_user_id:
        return JSONResponse({"error": "Missing app_user_id"}, status_code=400)

    event = payload.get("event") or payload  # some setups nest under "event"
    event_type = (event.get("type") or "").lower()

    # We’ll keep this robust:
    # - Any “expired”/“cancellation” event => deactivate
    # - Any “purchase”/“renewal”/“uncancellation” event => activate
    activate_types = {"initial_purchase", "renewal", "uncancellation", "product_change", "transfer"}
    deactivate_types = {"expiration", "cancellation", "billing_issue", "subscription_paused"}

    active = None
    if event_type in activate_types:
        active = True
    elif event_type in deactivate_types:
        active = False

    # If we can’t map event type, don’t mutate—just ack.
    if active is None:
        return {"ok": True, "ignored": True, "type": event_type}

    # Plan mapping: use product_id if you want (recommended).
    product_id = (event.get("product_id") or "").lower()
    plan = "monthly"
    if "year" in product_id or "annual" in product_id:
        plan = "yearly"

    # Source mapping
    store = (event.get("store") or "").lower()
    source = "apple" if "app_store" in store or "apple" in store else ("google" if "play" in store else "unknown")

    expires_at = event.get("expiration_at_ms")
    # Keep as string; you can convert later.
    expires_at_str = str(expires_at) if expires_at is not None else None

    with get_session() as s:
        user = s.exec(select(User).where(User.revenuecat_app_user_id == app_user_id)).first()
        if not user:
            return JSONResponse({"error": "User not found for app_user_id"}, status_code=404)

        _set_entitlement(user, active=active, plan=plan if active else "none", source=source, expires_at=expires_at_str)
        s.add(user)
        s.commit()

    return {"ok": True, "active": active, "plan": plan, "source": source}
