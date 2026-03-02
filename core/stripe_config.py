import os
import stripe

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_test_change_me")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_change_me")

# Price IDs (Stripe Dashboard -> Products -> Pricing)
STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO", "")
STRIPE_PRICE_ELITE = os.getenv("STRIPE_PRICE_ELITE", "")
STRIPE_PRICE_ENTERPRISE = os.getenv("STRIPE_PRICE_ENTERPRISE", "")

# Public URL of your frontend (used for redirects)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

stripe.api_key = STRIPE_SECRET_KEY
