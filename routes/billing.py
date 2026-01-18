# backend/routes/billing.py
import os
import stripe
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.post("/create-checkout-session")
async def create_checkout_session(request: Request):
    data = await request.json()
    price_id = data.get("priceId")
    if not price_id:
        raise HTTPException(status_code=400, detail="Missing priceId")

    try:
        # ✅ For LIVE mode, must use your actual deployed frontend domain
        success_url = "https://autoforgeai.vercel.app/success?session_id={CHECKOUT_SESSION_ID}"
        cancel_url = "https://autoforgeai.vercel.app/cancel"

        session = stripe.checkout.Session.create(
            mode="subscription",                      # ✅ required for recurring products
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            billing_address_collection="auto",
            automatic_tax={"enabled": True},
            allow_promotion_codes=True,
        )

        return {"checkoutUrl": session.url}

    except stripe.error.InvalidRequestError as e:
        # Stripe-specific errors: bad key, wrong mode, invalid price, etc.
        return JSONResponse(
            status_code=400,
            content={"error": f"Stripe invalid request: {e.user_message or str(e)}"},
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except stripe.error.SignatureVerificationError:
        return JSONResponse(status_code=400, content={"error": "Invalid signature"})
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

    # --- Event handling ---
    etype = event["type"]
    data = event["data"]["object"]

    if etype == "checkout.session.completed":
        print(f"✅ Checkout completed: {data.get('id')}")

    elif etype == "invoice.payment_succeeded":
        print("💰 Subscription renewed")

    elif etype == "customer.subscription.deleted":
        print("❌ Subscription canceled")

    return JSONResponse(status_code=200, content={"received": True})
