from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlmodel import Session, select

from db import get_session
from models.user import User
from core.stripe_config import (
    stripe,
    STRIPE_WEBHOOK_SECRET,
    STRIPE_PRICE_PRO,
    STRIPE_PRICE_ELITE,
    STRIPE_PRICE_ENTERPRISE,
)
import stripe as stripe_lib

router = APIRouter()

def _plan_from_price(price_id: str | None) -> str:
    if not price_id:
        return "none"
    if STRIPE_PRICE_PRO and price_id == STRIPE_PRICE_PRO:
        return "pro"
    if STRIPE_PRICE_ELITE and price_id == STRIPE_PRICE_ELITE:
        return "elite"
    if STRIPE_PRICE_ENTERPRISE and price_id == STRIPE_PRICE_ENTERPRISE:
        return "enterprise"
    # fallback heuristic
    return "pro"

def _tier_from_plan(plan: str) -> str:
    if plan in ("pro", "enterprise", "elite"):
        return plan
    return "basic"

def _update_user_from_subscription(db_user: User, sub: dict):
    status = sub.get("status")
    db_user.subscription_source = "stripe"
    db_user.subscription_active = status in ("active", "trialing", "past_due")

    # price id (first item)
    price_id = None
    try:
        items = sub.get("items", {}).get("data", [])
        if items:
            price_id = items[0].get("price", {}).get("id")
    except Exception:
        price_id = None

    plan = _plan_from_price(price_id)
    db_user.subscription_plan = plan
    db_user.tier = _tier_from_plan(plan)

    cpe = sub.get("current_period_end")
    db_user.subscription_expires_at = str(cpe) if cpe else None
    db_user.stripe_subscription_id = sub.get("id")

@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, session: Session = Depends(get_session)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe_lib.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except stripe_lib.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook")
    except Exception:
        raise HTTPException(status_code=400, detail="Bad webhook payload")

    etype = event.get("type")
    data_object = event.get("data", {}).get("object", {})

    # checkout completed -> ensure user has subscription id recorded
    if etype == "checkout.session.completed":
        customer_id = data_object.get("customer")
        subscription_id = data_object.get("subscription")
        user_id = (data_object.get("metadata") or {}).get("user_id")

        db_user = None
        if user_id:
            db_user = session.exec(select(User).where(User.id == user_id)).first()
        if not db_user and customer_id:
            db_user = session.exec(select(User).where(User.stripe_customer_id == customer_id)).first()

        if db_user:
            db_user.stripe_customer_id = customer_id or db_user.stripe_customer_id
            db_user.stripe_subscription_id = subscription_id or db_user.stripe_subscription_id
            db_user.subscription_source = "stripe"
            session.add(db_user)
            session.commit()

    # subscription lifecycle
    if etype in ("customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"):
        customer_id = data_object.get("customer")
        if customer_id:
            db_user = session.exec(select(User).where(User.stripe_customer_id == customer_id)).first()
            if db_user:
                if etype == "customer.subscription.deleted":
                    db_user.subscription_active = False
                    db_user.subscription_plan = "none"
                    db_user.subscription_source = "stripe"
                    db_user.subscription_expires_at = None
                    db_user.tier = "basic"
                    db_user.stripe_subscription_id = None
                else:
                    _update_user_from_subscription(db_user, data_object)

                session.add(db_user)
                session.commit()

    # invoice paid/failed can matter for 'past_due' recovery
    if etype in ("invoice.paid", "invoice.payment_failed"):
        customer_id = data_object.get("customer")
        if customer_id:
            db_user = session.exec(select(User).where(User.stripe_customer_id == customer_id)).first()
            if db_user and db_user.stripe_subscription_id:
                sub = stripe.Subscription.retrieve(db_user.stripe_subscription_id)
                _update_user_from_subscription(db_user, sub)
                session.add(db_user)
                session.commit()

    return {"status": "success"}
