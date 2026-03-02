from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, select

from core.config import settings
from db import engine, get_session
from models.user import User

from routes.admin import router as admin_router
from routes.auth import router as auth_router
from routes.billing import router as billing_router
from routes.decision import router as decision_router
from routes.diagnose import router as diagnose_router
from routes.economic_projection import router as economic_projection_router
from routes.explainability import router as explainability_router
from routes.fleet import router as fleet_router
from routes.fleet_enterprise import router as fleet_enterprise_router
from routes.forecast import router as forecast_router
from routes.issues import router as issues_router
from routes.predictive import router as predictive_router
from routes.safety import router as safety_router
from routes.stripe_webhook import router as stripe_webhook_router
from routes.vhi import router as vhi_router

LOCKED_ADMIN_EMAIL = "selfforgeadmin@selfforgellc.com"
LOCKED_ADMIN_PASSWORD = "JJAJCJOJ2025!"


def _migrate_sqlite_table_columns(table: str, required: dict[str, str]) -> None:
    """Add missing sqlite columns without dropping data."""
    try:
        url = str(engine.url)
    except Exception:
        url = ""
    if "sqlite" not in url:
        return

    try:
        with engine.connect() as conn:
            rows = conn.exec_driver_sql(f"PRAGMA table_info('{table}')").fetchall()
            existing = {r[1] for r in rows}
            # If table doesn't exist yet, create_all will handle it
            if not existing:
                return
            for col, coltype in required.items():
                if col in existing:
                    continue
                conn.exec_driver_sql(f"ALTER TABLE '{table}' ADD COLUMN {col} {coltype}")
    except Exception:
        # never block startup
        return


def _migrate_sqlite() -> None:
    # user table
    _migrate_sqlite_table_columns(
        "user",
        {
            "password": "TEXT DEFAULT ''",
            "stripe_customer_id": "TEXT",
            "stripe_subscription_id": "TEXT",
            "subscription_active": "BOOLEAN DEFAULT 0",
            "subscription_plan": "TEXT DEFAULT 'none'",
            "subscription_source": "TEXT DEFAULT 'none'",
            "subscription_expires_at": "TEXT",
            "tier": "TEXT DEFAULT 'basic'",
            "is_admin": "BOOLEAN DEFAULT 0",
        },
    )

    # issue_status table (SQLModel table name is usually "issuestatus" unless you set __tablename__)
    # Your project table is named "issuestatus" based on IssueStatus model.
    _migrate_sqlite_table_columns(
        "issuestatus",
        {
            "created_at": "TEXT",
            "resolved": "BOOLEAN DEFAULT 0",
            "resolved_at": "TEXT",
            "resolved_reason": "TEXT",
        },
    )


def _allowed_origins() -> list[str]:
    # For dev + capacitor builds, wildcard CORS is simplest and prevents “fake CORS” errors.
    # Using allow_credentials=False lets "*" work properly.
    extra = os.getenv("ALLOWED_ORIGINS", "").strip()
    if extra:
        return [x.strip() for x in extra.split(",") if x.strip()]
    return ["*"]


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=False,  # IMPORTANT for "*" wildcard
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    _migrate_sqlite()
    SQLModel.metadata.create_all(engine)

    # Create/lock your admin account on every boot (idempotent)
    from routes.auth import _hash_password, _normalize_email

    email = _normalize_email(os.getenv("ADMIN_EMAIL", LOCKED_ADMIN_EMAIL))
    password = os.getenv("ADMIN_PASSWORD", LOCKED_ADMIN_PASSWORD)

    with next(get_session()) as session:
        existing = session.exec(select(User).where(User.email == email)).first()
        if not existing:
            u = User(
                email=email,
                password=_hash_password(password),
                tier="enterprise",
                is_admin=True,
                subscription_active=True,
                subscription_plan="enterprise",
                subscription_source="manual",
            )
            session.add(u)
            session.commit()
        else:
            # Enforce locked admin flags
            changed = False
            if not getattr(existing, "is_admin", False):
                existing.is_admin = True
                changed = True
            if getattr(existing, "tier", "basic") != "enterprise":
                existing.tier = "enterprise"
                changed = True
            if getattr(existing, "subscription_active", False) is not True:
                existing.subscription_active = True
                changed = True
            if (getattr(existing, "subscription_plan", None) or "none") != "enterprise":
                existing.subscription_plan = "enterprise"
                changed = True
            if (getattr(existing, "subscription_source", None) or "none") != "manual":
                existing.subscription_source = "manual"
                changed = True
            if changed:
                session.add(existing)
                session.commit()


# Routers
app.include_router(auth_router)
app.include_router(billing_router)
app.include_router(stripe_webhook_router)
app.include_router(admin_router)

app.include_router(diagnose_router)
app.include_router(decision_router)
app.include_router(issues_router)
app.include_router(predictive_router)
app.include_router(fleet_router)
app.include_router(explainability_router)
app.include_router(economic_projection_router)
app.include_router(forecast_router)
app.include_router(vhi_router)
app.include_router(safety_router)
app.include_router(fleet_enterprise_router)


@app.get("/health")
def health():
    return {"status": "ok", "env": getattr(settings, "ENV", "unknown")}


@app.get("/ready")
def ready():
    try:
        engine.connect()
        return {"status": "ready"}
    except Exception:
        return {"status": "not_ready"}