from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

try:
    from auth_routes import current_user, AUTH_ROUTES_VERSION
except Exception:
    from routes.auth_routes import current_user, AUTH_ROUTES_VERSION  # type: ignore

# ✅ IMPORTANT: no prefix here. Prefix is applied in main.py via include_router(..., prefix="/api/subscription")
router = APIRouter()

SUBSCRIPTION_ROUTES_VERSION = "SUBSCRIPTION_STATUS_V2_2026_01_10"


@router.get("/status")
async def subscription_status(request: Request):
    """
    IMPORTANT:
    Frontend expects:
      { "status": { "active": bool, "plan": str, "source": str, "expires_at": str|null } }

    We also include legacy top-level fields for backwards compatibility.
    """
    user = current_user(request)

    if not user:
        payload = {
            "status": {"active": False, "plan": "none", "source": "none", "expires_at": None},
            # legacy fields (safe to keep)
            "active": False,
            "plan": "none",
            "source": "none",
            "expires_at": None,
            "tier": "basic",
            "user": None,
            "version": SUBSCRIPTION_ROUTES_VERSION,
            "auth_version": AUTH_ROUTES_VERSION,
        }
        return JSONResponse(payload, status_code=200)

    active = bool(getattr(user, "subscription_active", False))
    plan = getattr(user, "subscription_plan", "none")
    source = getattr(user, "subscription_source", "unknown")
    expires_at = getattr(user, "subscription_expires_at", None)
    tier = getattr(user, "tier", "basic")

    payload = {
        # ✅ what the frontend uses
        "status": {
            "active": active,
            "plan": plan,
            "source": source,
            "expires_at": expires_at,
        },
        # legacy fields (don’t hurt; helps older code)
        "active": active,
        "plan": plan,
        "source": source,
        "expires_at": expires_at,
        "tier": tier,
        "version": SUBSCRIPTION_ROUTES_VERSION,
        "auth_version": AUTH_ROUTES_VERSION,
    }
    return JSONResponse(payload, status_code=200)
