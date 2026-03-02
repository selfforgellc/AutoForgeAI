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
    create_access_token,
    get_bearer_token_from_headers,
    get_user_id_from_access_token,
)

router = APIRouter()

AUTH_ROUTES_VERSION = "AUTH_BEARER_HMAC_SHA256_V1_2026_01_18"

LEGACY_CONTEXT = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "akjohnson1027@gmail.com").strip().lower()
MAX_PASSWORD_BYTES = int(os.getenv("MAX_PASSWORD_BYTES", "4096"))


def _pw_digest(password: str) -> bytes:
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


def _normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D+", "", (phone or "").strip())
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        raise ValueError("Invalid phone number")
    return digits


def current_user(request: Request) -> Optional[User]:
    bearer = get_bearer_token_from_headers(request.headers.get("authorization"))
    if not bearer:
        return None

    user_id = get_user_id_from_access_token(bearer)
    if not user_id:
        return None

    with get_session() as s:
        return s.get(User, user_id)


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

        access_token = create_access_token(user.id)

        return JSONResponse(
            {
                "ok": True,
                "access_token": access_token,
                "user": {"id": user.id, "email": user.email, "tier": user.tier, "phone": user.phone},
                "version": AUTH_ROUTES_VERSION,
            }
        )

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

        access_token = create_access_token(user.id)

        return JSONResponse(
            {
                "ok": True,
                "access_token": access_token,
                "user": {"id": user.id, "email": user.email, "tier": user.tier, "phone": user.phone},
                "version": AUTH_ROUTES_VERSION,
            }
        )

    except Exception as e:
        return JSONResponse(
            {"error": f"[{AUTH_ROUTES_VERSION}] Login failed: {type(e).__name__}: {str(e)}"},
            status_code=500,
        )


@router.post("/logout")
async def logout():
    # Stateless tokens: client just deletes token.
    return JSONResponse({"ok": True, "version": AUTH_ROUTES_VERSION})


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

        return JSONResponse({"ok": True, "version": AUTH_ROUTES_VERSION})

    except Exception as e:
        return JSONResponse(
            {"error": f"[{AUTH_ROUTES_VERSION}] Delete failed: {type(e).__name__}: {str(e)}"},
            status_code=500,
        )
