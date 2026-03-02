from __future__ import annotations

from typing import Optional
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    email: str = Field(index=True, unique=True)
    password_hash: str

    tier: str = Field(default="basic", index=True)

    # Subscription fields (used by auth_routes + subscription_routes)
    subscription_active: bool = Field(default=False, index=True)
    subscription_plan: str = Field(default="none")
    subscription_source: str = Field(default="unknown")
    subscription_expires_at: Optional[str] = Field(default=None)

    # Optional external ID you already return in /me
    revenuecat_app_user_id: Optional[str] = Field(default=None, index=True)

    # ✅ NEW: phone field
    phone: Optional[str] = Field(default=None, index=True)
