from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from db import get_session
from models.user import User
from core.auth import get_current_user
from core.stripe_config import (
    stripe,
    FRONTEND_URL,
    STRIPE_PRICE_PRO,
    STRIPE_PRICE_ELITE,
    STRIPE_PRICE_ENTERPRISE,
)

router = APIRouter()

# ✅ Permanent bypass ONLY for the locked admin identity
ADMIN_EMAIL_LOCK = "selfforgeadmin@selfforgellc.com"

PLAN_TO_PRICE = {
    "pro": STRIPE_PRICE_PRO,
    "elite": STRIPE_PRICE_ELITE,
    "enterprise": STRIPE_PRICE_ENTERPRISE,
}


def _is_locked_admin(u: User | None) -> bool:
    if not u:
        return False
    return bool(getattr(u, "is_admin", False)) and (u.email or "").strip().lower() == ADMIN_EMAIL_LOCK


def _enforce_admin_flags(session: Session, u: User) -> None:
    changed = False
    if getattr(u, "tier", "basic") != "enterprise":
        u.tier = "enterprise"
        changed = True
    if getattr(u, "subscription_active", False) is not True:
        u.subscription_active = True
        changed = True
    if (getattr(u, "subscription_plan", None) or "none") != "enterprise":
        u.subscription_plan = "enterprise"
        changed = True
    if (getattr(u, "subscription_source", None) or "none") != "manual":
        u.subscription_source = "manual"
        changed = True
    if changed:
        session.add(u)
        session.commit()


def _admin_status_payload() -> dict:
    # include both naming styles used across frontend variants
    return {
        "active": True,
        "status": "active",
        "tier": "enterprise",
        "plan": "enterprise",
        "source": "manual",
        "expires_at": None,
        "subscription_active": True,
        "subscription_plan": "enterprise",
        "subscription_source": "manual",
        "subscription_expires_at": None,
        "bypass": True,
    }

class CheckoutRequest(BaseModel):
    plan: str  # pro | elite | enterprise
    success_path: str | None = None  # default: /subscribe/success
    cancel_path: str | None = None   # default: /subscribe
    trial_days: int | None = None    # optional free trial (e.g. 1)

@router.post("/billing/checkout-session")
def create_checkout_session(
    payload: CheckoutRequest,
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    plan = (payload.plan or "").strip().lower()
    if plan not in PLAN_TO_PRICE:
        raise HTTPException(status_code=400, detail="Invalid plan")

    price_id = PLAN_TO_PRICE.get(plan)
    if not price_id:
        raise HTTPException(
            status_code=500,
            detail=f"Stripe price id for plan '{plan}' is not configured on server",
        )

    db_user = session.exec(select(User).where(User.id == user["sub"])).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ Locked admin never goes through Stripe
    if _is_locked_admin(db_user):
        _enforce_admin_flags(session, db_user)
        success_url = FRONTEND_URL.rstrip("/") + (payload.success_path or "/subscribe/success")
        return {"url": success_url + "?bypass=1"}

    # Ensure Stripe customer exists
    if not db_user.stripe_customer_id:
        customer = stripe.Customer.create(
            email=db_user.email,
            metadata={"user_id": db_user.id},
        )
        db_user.stripe_customer_id = customer["id"]
        session.add(db_user)
        session.commit()

    success_url = FRONTEND_URL.rstrip("/") + (payload.success_path or "/subscribe/success")
    cancel_url = FRONTEND_URL.rstrip("/") + (payload.cancel_path or "/subscribe")

    params = {
        "mode": "subscription",
        "customer": db_user.stripe_customer_id,
        "line_items": [{"price": price_id, "quantity": 1}],
        "allow_promotion_codes": True,
        "billing_address_collection": "auto",
        "success_url": success_url + "?session_id={CHECKOUT_SESSION_ID}",
        "cancel_url": cancel_url,
        "metadata": {"user_id": db_user.id, "plan": plan},
    }

    # Optional free-trial support (e.g., 1 day). Stripe marks subscription as 'trialing'.
    if payload.trial_days and int(payload.trial_days) > 0:
        params["subscription_data"] = {"trial_period_days": int(payload.trial_days)}

    checkout_session = stripe.checkout.Session.create(**params)

    return {"url": checkout_session["url"]}

class PortalRequest(BaseModel):
    return_path: str | None = None

@router.post("/billing/portal")
def create_billing_portal_session(
    payload: PortalRequest,
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    db_user = session.exec(select(User).where(User.id == user["sub"])).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ Locked admin doesn't need portal
    if _is_locked_admin(db_user):
        _enforce_admin_flags(session, db_user)
        return_url = FRONTEND_URL.rstrip("/") + (payload.return_path or "/settings")
        return {"url": return_url + "?bypass=1"}

    if not db_user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer found")

    return_url = FRONTEND_URL.rstrip("/") + (payload.return_path or "/settings")

    portal_session = stripe.billing_portal.Session.create(
        customer=db_user.stripe_customer_id,
        return_url=return_url,
    )
    return {"url": portal_session["url"]}

@router.get("/billing/subscription/status")
@router.get("/billing/subscription-status")
def subscription_status(
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    db_user = session.exec(select(User).where(User.id == user["sub"])).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if _is_locked_admin(db_user):
        _enforce_admin_flags(session, db_user)
        return _admin_status_payload()

    return {
        "active": bool(db_user.subscription_active),
        "status": "active" if bool(db_user.subscription_active) else "inactive",
        "plan": db_user.subscription_plan or "none",
        "source": db_user.subscription_source or "none",
        "expires_at": db_user.subscription_expires_at,
        "tier": db_user.tier or "basic",
        "subscription_active": bool(db_user.subscription_active),
        "subscription_plan": db_user.subscription_plan or "none",
        "subscription_source": db_user.subscription_source or "none",
        "subscription_expires_at": db_user.subscription_expires_at,
        "bypass": False,
    }

@router.post("/billing/subscription/refresh")
@router.post("/billing/refresh-subscription")
def refresh_subscription_from_stripe(
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Pull current subscription state from Stripe (use after returning from Checkout)."""
    db_user = session.exec(select(User).where(User.id == user["sub"])).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if _is_locked_admin(db_user):
        _enforce_admin_flags(session, db_user)
        return _admin_status_payload()

    if not db_user.stripe_customer_id:
        return {
            "active": False,
            "status": "inactive",
            "plan": "none",
            "source": "none",
            "expires_at": None,
            "tier": db_user.tier or "basic",
            "subscription_active": False,
            "subscription_plan": "none",
            "subscription_source": "none",
            "subscription_expires_at": None,
            "bypass": False,
        }

    # Find an active subscription for the customer
    subs = stripe.Subscription.list(customer=db_user.stripe_customer_id, status="all", limit=5)
    chosen = None
    for s in subs.get("data", []):
        if s.get("status") in ("active", "trialing", "past_due"):
            chosen = s
            break

    if not chosen:
        db_user.subscription_active = False
        db_user.subscription_plan = "none"
        db_user.subscription_source = "stripe"
        db_user.subscription_expires_at = None
        db_user.tier = "basic"
        session.add(db_user)
        session.commit()
        return {
            "active": False,
            "status": "inactive",
            "plan": "none",
            "source": "stripe",
            "expires_at": None,
            "tier": "basic",
            "subscription_active": False,
            "subscription_plan": "none",
            "subscription_source": "stripe",
            "subscription_expires_at": None,
            "bypass": False,
        }

    db_user.stripe_subscription_id = chosen.get("id")
    db_user.subscription_source = "stripe"
    db_user.subscription_active = chosen.get("status") in ("active", "trialing", "past_due")

    # Determine plan by price id
    price_id = None
    try:
        items = chosen.get("items", {}).get("data", [])
        if items:
            price_id = items[0].get("price", {}).get("id")
    except Exception:
        price_id = None

    plan = "pro" if price_id == STRIPE_PRICE_PRO else "elite" if price_id == STRIPE_PRICE_ELITE else "enterprise" if price_id == STRIPE_PRICE_ENTERPRISE else "pro"
    db_user.subscription_plan = plan
    db_user.tier = plan if plan in ("pro", "enterprise") else "elite"

    # current_period_end is unix timestamp
    cpe = chosen.get("current_period_end")
    db_user.subscription_expires_at = str(cpe) if cpe else None

    session.add(db_user)
    session.commit()

    return {
        "active": bool(db_user.subscription_active),
        "status": "active" if bool(db_user.subscription_active) else "inactive",
        "plan": db_user.subscription_plan,
        "source": db_user.subscription_source,
        "expires_at": db_user.subscription_expires_at,
        "tier": db_user.tier,
        "subscription_active": bool(db_user.subscription_active),
        "subscription_plan": db_user.subscription_plan,
        "subscription_source": db_user.subscription_source,
        "subscription_expires_at": db_user.subscription_expires_at,
        "bypass": False,
    }
