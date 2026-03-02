# auth_utils.py
import base64
import hashlib
import hmac
import json
import os
import time
from typing import Optional

# Kept for compatibility with older code imports
COOKIE_NAME = os.getenv("COOKIE_NAME", "autoforge_session")
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "none")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "1")

AUTH_SECRET = os.getenv("AUTH_SECRET", "").strip()
if not AUTH_SECRET:
    # Fallback: still works, but you should set AUTH_SECRET in Render env vars.
    # If this changes between deploys, all existing tokens become invalid.
    AUTH_SECRET = os.getenv("SECRET_KEY", "CHANGE_ME_SET_AUTH_SECRET_IN_RENDER")

AUTH_ISSUER = os.getenv("AUTH_ISSUER", "autoforgeai")
ACCESS_TOKEN_TTL_SECONDS = int(os.getenv("ACCESS_TOKEN_TTL_SECONDS", "2592000"))  # 30 days


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode("utf-8"))


def _sign(data: bytes) -> str:
    sig = hmac.new(AUTH_SECRET.encode("utf-8"), data, hashlib.sha256).digest()
    return _b64url_encode(sig)


def create_access_token(user_id: int, ttl_seconds: int = ACCESS_TOKEN_TTL_SECONDS) -> str:
    now = int(time.time())
    payload = {
        "iss": AUTH_ISSUER,
        "sub": str(user_id),
        "iat": now,
        "exp": now + int(ttl_seconds),
        "v": 1,
    }
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = _b64url_encode(payload_json)
    sig = _sign(payload_b64.encode("utf-8"))
    return f"{payload_b64}.{sig}"


def get_user_id_from_access_token(token: str) -> Optional[int]:
    try:
        if not token or "." not in token:
            return None
        payload_b64, sig = token.split(".", 1)
        expected_sig = _sign(payload_b64.encode("utf-8"))
        if not hmac.compare_digest(sig, expected_sig):
            return None

        payload_json = _b64url_decode(payload_b64)
        payload = json.loads(payload_json.decode("utf-8"))

        if payload.get("iss") != AUTH_ISSUER:
            return None

        exp = int(payload.get("exp", 0))
        if exp and int(time.time()) > exp:
            return None

        sub = payload.get("sub")
        if sub is None:
            return None

        user_id = int(sub)
        if user_id <= 0:
            return None
        return user_id
    except Exception:
        return None


def get_bearer_token_from_headers(auth_header: Optional[str]) -> Optional[str]:
    if not auth_header:
        return None
    auth_header = auth_header.strip()
    if not auth_header.lower().startswith("bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip() or None


# Backwards compatibility names (your code imported these previously)
def create_session_token(user_id: int) -> str:
    return create_access_token(user_id)


def get_user_id_from_token(token: str) -> Optional[int]:
    return get_user_id_from_access_token(token)
