from typing import Optional
import os
import hashlib
import re

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlmodel import select

import bcrypt
from passlib.context import CryptContext

from db import get_session
from models_user import User
from auth_utils import (
    COOKIE_NAME,
    COOKIE_SECURE,
    COOKIE_SAMESITE,
    create_session_token,
    get_user_id_from_token,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

AUTH_ROUTES_VERSION = "AUTH_DIRECT_BCRYPT_SHA256_V6_2026_01_10"

# Legacy verifier only (for old accounts that were hashed with passlib/bcrypt directly)
LEGACY_CONTEXT = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "akjohnson1027@gmail.com").strip().lower()
MAX_PASSWORD_BYTES = int(os.getenv("MAX_PASSWORD_BYTES", "4096"))


def _pw_digest(password: str) -> bytes:
    # Always 32 bytes -> always <= 72 bytes for bcrypt
    return hashlib.sha256(password.encode("utf-8")).digest()


def _hash_password(password: str) -> str:
    digest = _pw_digest(password)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(digest, salt)
    return hashed.decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    digest = _pw_digest(password)
    try:
        if bcrypt.checkpw(digest, password_hash.encode("utf-8")):
            return True
    except Exception:
        pass

    try:
        return LEGACY_CONTEXT.verify(password, password_hash)
    except Exception:
        return False


def _is_https_request(request: Request) -> bool:
    xf_proto = (request.headers.get("x-forwarded-proto") or "").lower().strip()
    if xf_proto:
        return xf_proto == "https"
    return request.url.scheme == "https"


def _set_cookie(resp: JSONResponse, request: Request, token: str) -> None:
    https = _is_https_request(request)

    secure = bool(COOKIE_SECURE) and https
    samesite = COOKIE_SAMESITE

    # If not secure (http), SameSite=None will be rejected by browsers
    if not secure:
        samesite = "lax"

    resp.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=60 * 60 * 24 * 30,
        path="/",
    )


def _clear_cookie(resp: JSONResponse) -> None:
    resp.delete_cookie(key=COOKIE_NAME, path="/")


def current_user(request: Request) -> Optional[User]:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None

    user_id = get_user_id_from_token(token)
    if not user_id:
        return None

    with get_session() as s:
        return s.get(User, user_id)


def _normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D+", "", (phone or "").strip())
    # US: allow 10 digits or 11 digits starting with 1
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        raise ValueError("Invalid phone number")
    return digits


@router.get("/ping")
async def ping():
    return {"ok": True, "version": AUTH_ROUTES_VERSION}


@router.post("/register")
async def register(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": f"[{AUTH_ROUTES_VERSION}] Invalid JSON body"}, status_code=400)

    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    if not email or not password:
        return JSONResponse({"error": f"[{AUTH_ROUTES_VERSION}] Email and password required"}, status_code=400)

    pw_bytes = password.encode("utf-8")

    if len(pw_bytes) < 8:
        return JSONResponse({"error": f"[{AUTH_ROUTES_VERSION}] Password must be at least 8 characters"}, status_code=400)

    if len(pw_bytes) > MAX_PASSWORD_BYTES:
        return JSONResponse({"error": f"[{AUTH_ROUTES_VERSION}] Password too long (max {MAX_PASSWORD_BYTES} bytes)"}, status_code=400)

    try:
        with get_session() as s:
            exists = s.exec(select(User).where(User.email == email)).first()
            if exists:
                return JSONResponse({"error": f"[{AUTH_ROUTES_VERSION}] Email already in use"}, status_code=409)

            is_admin = (email == ADMIN_EMAIL)

            password_hash = _hash_password(password)

            user = User(
                email=email,
                password_hash=password_hash,
                tier="admin" if is_admin else "basic",
                subscription_active=True if is_admin else False,
                subscription_plan="admin" if is_admin else "none",
                subscription_source="manual" if is_admin else "unknown",
                subscription_expires_at=None,
                phone=None,
            )
            s.add(user)
            s.commit()
            s.refresh(user)

        token = create_session_token(user.id)
        resp = JSONResponse(
            {
                "ok": True,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "tier": user.tier,
                    "phone": user.phone,
                },
                "version": AUTH_ROUTES_VERSION,
            }
        )
        _set_cookie(resp, request, token)
        return resp

    except Exception as e:
        return JSONResponse(
            {"error": f"[{AUTH_ROUTES_VERSION}] Register failed: {type(e).__name__}: {str(e)}"},
            status_code=500,
        )


@router.post("/login")
async def login(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": f"[{AUTH_ROUTES_VERSION}] Invalid JSON body"}, status_code=400)

    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    if not email or not password:
        return JSONResponse({"error": f"[{AUTH_ROUTES_VERSION}] Email and password required"}, status_code=400)

    pw_bytes = password.encode("utf-8")
    if len(pw_bytes) > MAX_PASSWORD_BYTES:
        return JSONResponse({"error": f"[{AUTH_ROUTES_VERSION}] Password too long (max {MAX_PASSWORD_BYTES} bytes)"}, status_code=400)

    try:
        with get_session() as s:
            user = s.exec(select(User).where(User.email == email)).first()
            if not user:
                return JSONResponse({"error": f"[{AUTH_ROUTES_VERSION}] Invalid credentials"}, status_code=401)

            if not _verify_password(password, user.password_hash):
                return JSONResponse({"error": f"[{AUTH_ROUTES_VERSION}] Invalid credentials"}, status_code=401)

        token = create_session_token(user.id)
        resp = JSONResponse(
            {
                "ok": True,
                "user": {"id": user.id, "email": user.email, "tier": user.tier, "phone": user.phone},
                "version": AUTH_ROUTES_VERSION,
            }
        )
        _set_cookie(resp, request, token)
        return resp

    except Exception as e:
        return JSONResponse(
            {"error": f"[{AUTH_ROUTES_VERSION}] Login failed: {type(e).__name__}: {str(e)}"},
            status_code=500,
        )


@router.post("/logout")
async def logout():
    resp = JSONResponse({"ok": True, "version": AUTH_ROUTES_VERSION})
    _clear_cookie(resp)
    return resp


@router.get("/me")
async def me(request: Request):
    user = current_user(request)
    if not user:
        return {"user": None, "version": AUTH_ROUTES_VERSION}

    return {
        "version": AUTH_ROUTES_VERSION,
        "user": {
            "id": user.id,
            "email": user.email,
            "tier": user.tier,
            "phone": user.phone,
            "subscription_active": user.subscription_active,
            "subscription_plan": user.subscription_plan,
            "subscription_source": user.subscription_source,
            "subscription_expires_at": user.subscription_expires_at,
            "revenuecat_app_user_id": user.revenuecat_app_user_id,
        },
    }


@router.post("/update-phone")
async def update_phone(request: Request):
    user = current_user(request)
    if not user:
        return JSONResponse({"error": f"[{AUTH_ROUTES_VERSION}] Not logged in"}, status_code=401)

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": f"[{AUTH_ROUTES_VERSION}] Invalid JSON body"}, status_code=400)

    raw_phone = body.get("phone") or ""
    try:
        phone = _normalize_phone(str(raw_phone))
    except Exception:
        return JSONResponse({"error": f"[{AUTH_ROUTES_VERSION}] Invalid phone number"}, status_code=400)

    try:
        with get_session() as s:
            db_user = s.get(User, user.id)
            if not db_user:
                return JSONResponse({"error": f"[{AUTH_ROUTES_VERSION}] User not found"}, status_code=404)

            db_user.phone = phone
            s.add(db_user)
            s.commit()
            s.refresh(db_user)

        return JSONResponse({"ok": True, "phone": phone, "version": AUTH_ROUTES_VERSION})
    except Exception as e:
        return JSONResponse(
            {"error": f"[{AUTH_ROUTES_VERSION}] Update phone failed: {type(e).__name__}: {str(e)}"},
            status_code=500,
        )


@router.delete("/me")
async def delete_account(request: Request):
    user = current_user(request)
    if not user:
        return JSONResponse({"error": f"[{AUTH_ROUTES_VERSION}] Not logged in"}, status_code=401)

    try:
        with get_session() as s:
            db_user = s.get(User, user.id)
            if db_user:
                s.delete(db_user)
                s.commit()

        resp = JSONResponse({"ok": True, "version": AUTH_ROUTES_VERSION})
        _clear_cookie(resp)
        return resp

    except Exception as e:
        return JSONResponse(
            {"error": f"[{AUTH_ROUTES_VERSION}] Delete failed: {type(e).__name__}: {str(e)}"},
            status_code=500,
        )
