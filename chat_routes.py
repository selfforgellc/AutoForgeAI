# chat_routes.py
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

CHAT_ROUTES_VERSION = "CHAT_ROUTES_V1_2026_01_19"

# In-memory sessions (safe for tonight). If you restart the server, sessions reset.
# Later we can persist to DB if you want.
_SESSIONS: Dict[str, List[Dict[str, str]]] = {}


def _get_json_body_or_empty(request_json: Any) -> Dict[str, Any]:
    return request_json if isinstance(request_json, dict) else {}


def _build_system_prompt(vehicle: Optional[dict]) -> str:
    v = vehicle or {}
    v_label = "Unknown vehicle"
    if v.get("year") and v.get("make") and v.get("model"):
        v_label = f"{v.get('year')} {v.get('make')} {v.get('model')}".strip()

    return (
        "You are AutoForgeAI: an expert master mechanic assistant.\n"
        "Your job: ask the MINIMUM number of high-value questions, then provide a structured diagnostic plan.\n"
        "Always be practical: quick checks first, then deeper tests.\n"
        "If the user says they do not have a scanner, adapt.\n"
        f"Vehicle context: {v_label}\n"
        "Output format:\n"
        "1) Quick triage\n"
        "2) Clarifying questions (max 3)\n"
        "3) Likely causes (ranked)\n"
        "4) Next tests (step-by-step)\n"
        "5) If still not fixed: what to report back\n"
    )


@router.post("/session/reset")
async def session_reset(request: Request):
    """
    Frontend calls this to wipe chat context.
    Supports:
      POST /session/reset
      POST /api/session/reset  (because we mount this router under /api too)
    Body:
      { "session_id": "..." }
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    sid = str((body or {}).get("session_id") or "").strip()
    if not sid:
        return JSONResponse(
            {"ok": False, "error": f"[{CHAT_ROUTES_VERSION}] session_id required"},
            status_code=400,
        )

    _SESSIONS.pop(sid, None)
    return {"ok": True, "version": CHAT_ROUTES_VERSION, "session_id": sid}


@router.post("/chat")
async def chat(request: Request):
    """
    Supports:
      POST /chat
      POST /api/chat  (because we mount this router under /api too)

    Expected body (what your frontend sends):
    {
      "session_id": "af_...",
      "message": "text",
      "vehicle": {...} | null,
      "active_vehicle_id": "..." | null
    }
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    body = _get_json_body_or_empty(body)
    sid = str(body.get("session_id") or "").strip()
    msg = str(body.get("message") or "").strip()
    vehicle = body.get("vehicle") if isinstance(body.get("vehicle"), dict) else None

    if not sid:
        return JSONResponse(
            {"error": f"[{CHAT_ROUTES_VERSION}] session_id required"},
            status_code=400,
        )
    if not msg:
        return JSONResponse(
            {"error": f"[{CHAT_ROUTES_VERSION}] message required"},
            status_code=400,
        )

    # Maintain basic conversation history
    history = _SESSIONS.get(sid, [])
    history.append({"role": "user", "content": msg})
    history = history[-20:]  # cap history
    _SESSIONS[sid] = history

    # Try to use OpenAI if configured; otherwise provide a useful fallback response
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    if openai_key:
        # Optional OpenAI integration (works if openai package exists).
        # If openai isn't installed, we fall back.
        try:
            from openai import OpenAI  # type: ignore

            client = OpenAI(api_key=openai_key)

            system_prompt = _build_system_prompt(vehicle)

            # Convert history to OpenAI message format
            messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
            for h in history:
                if h.get("role") in ("user", "assistant") and h.get("content"):
                    messages.append({"role": h["role"], "content": h["content"]})

            # Choose model via env; default is solid and modern
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.4,
            )

            assistant_text = (resp.choices[0].message.content or "").strip() or "…"

            history.append({"role": "assistant", "content": assistant_text})
            _SESSIONS[sid] = history[-20:]

            return {
                "assistant_text": assistant_text,
                "mode": "llm",
                "phase": "discover",
                "topic": "diagnostics",
                "confidence": 72,
                "version": CHAT_ROUTES_VERSION,
            }

        except Exception as e:
            # fall through to offline response
            pass

    # Fallback response (still useful tonight)
    system_prompt = _build_system_prompt(vehicle)
    assistant_text = (
        f"⚠️ AI model is not connected yet (missing OPENAI_API_KEY or OpenAI SDK).\n\n"
        f"{system_prompt}\n"
        f"Quick triage:\n"
        f"- What symptom is happening? (no-start / stall / misfire / overheating / noise / vibration)\n"
        f"- When does it happen (cold start, hot, idle, accelerating)?\n"
        f"- Any warning lights or codes? If no scanner, say 'no scanner'.\n\n"
        f"Reply with those 3 and I’ll narrow it down."
    )

    history.append({"role": "assistant", "content": assistant_text})
    _SESSIONS[sid] = history[-20:]

    return {
        "assistant_text": assistant_text,
        "mode": "fallback",
        "phase": "discover",
        "topic": "diagnostics",
        "confidence": 35,
        "version": CHAT_ROUTES_VERSION,
    }
