from sqlmodel import SQLModel, Field
import uuid

class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str
    password: str

    # Access tier used by feature gating in the app
    # basic | pro | elite | enterprise
    tier: str = "basic"

    is_admin: bool = False

    # Stripe identifiers
    stripe_customer_id: str | None = None
    stripe_subscription_id: str | None = None

    # Subscription tracking (Stripe or other sources)
    subscription_active: bool = False
    subscription_plan: str = "none"          # none | pro | elite | enterprise
    subscription_source: str = "none"        # stripe | revenuecat | manual | none
    subscription_expires_at: str | None = None  # ISO timestamp
