# FILE: backend/main.py
import os
import json
import re
import time
import traceback
from typing import Any, Dict, Optional, List, Tuple

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from db import init_db

load_dotenv()

APP_VERSION = "20.0.0"

# -------------------------------------------------
# OPTIONAL ROUTERS (keeps your existing API working)
# -------------------------------------------------
auth_router = None
subscription_router = None
push_router = None
visual_router = None
diagnose_router = None

try:
    from auth_routes import router as auth_router
except Exception:
    try:
        from routes.auth_routes import router as auth_router  # type: ignore
    except Exception:
        auth_router = None

try:
    from subscription_routes import router as subscription_router
except Exception:
    try:
        from routes.subscription_routes import router as subscription_router  # type: ignore
    except Exception:
        subscription_router = None

try:
    from push_routes import router as push_router
except Exception:
    try:
        from routes.push_routes import router as push_router  # type: ignore
    except Exception:
        push_router = None

try:
    from visual import router as visual_router
except Exception:
    try:
        from routes.visual import router as visual_router  # type: ignore
    except Exception:
        visual_router = None

try:
    from diagnose import router as diagnose_router
except Exception:
    try:
        from routes.diagnose import router as diagnose_router  # type: ignore
    except Exception:
        diagnose_router = None


# -------------------------------------------------
# APP
# -------------------------------------------------
app = FastAPI(title="AutoForge AI", version=APP_VERSION)

# -------------------------------------------------
# CORS
# -------------------------------------------------
raw_origins = (
    os.getenv("CORS_ORIGINS")
    or os.getenv("CORS_ORIGIN")
    or "http://localhost:5173,http://localhost:5174"
)

cors_origins: List[str] = [o.strip() for o in raw_origins.split(",") if o.strip()]
for o in [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]:
    if o not in cors_origins:
        cors_origins.append(o)

cors_origins = [o for o in cors_origins if o != "*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# STARTUP
# -------------------------------------------------
@app.on_event("startup")
def _startup():
    init_db()
    print(f"[AutoForgeAI] boot version={APP_VERSION}")
    print(f"[AutoForgeAI] CORS origins={cors_origins}")


# -------------------------------------------------
# ROUTERS
# -------------------------------------------------
if auth_router:
    app.include_router(auth_router)
if subscription_router:
    app.include_router(subscription_router)
if push_router:
    app.include_router(push_router)
if visual_router:
    app.include_router(visual_router)
if diagnose_router:
    app.include_router(diagnose_router)


# -------------------------------------------------
# OPENAI
# -------------------------------------------------
OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or "").strip()
OPENAI_MODEL = (os.getenv("OPENAI_MODEL") or "gpt-4.1").strip()


def _openai_ok() -> bool:
    return bool(OPENAI_API_KEY)


def _call_openai(messages: List[Dict[str, str]], temperature: float = 0.45, max_tokens: int = 1200) -> str:
    """
    Uses urllib so you don't need extra deps.
    """
    import urllib.request

    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": OPENAI_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
    j = json.loads(raw)
    return (j["choices"][0]["message"]["content"] or "").strip()


# -------------------------------------------------
# GOOGLE PROGRAMMABLE SEARCH (Tool)
# -------------------------------------------------
GOOGLE_CSE_API_KEY = (os.getenv("GOOGLE_CSE_API_KEY") or "").strip()
GOOGLE_CSE_CX = (os.getenv("GOOGLE_CSE_CX") or "").strip()
GOOGLE_CSE_ENABLED = bool(GOOGLE_CSE_API_KEY and GOOGLE_CSE_CX)

# In-memory cache: good enough for dev
_SEARCH_CACHE: Dict[str, Dict[str, Any]] = {}
_SEARCH_TTL_SECONDS = int(os.getenv("GOOGLE_CSE_CACHE_TTL_SECONDS") or "2592000")  # 30 days


def _google_cse_search(query: str, num: int = 3) -> List[Dict[str, str]]:
    """
    Returns list[{title, snippet, link}]
    """
    if not GOOGLE_CSE_ENABLED:
        return []

    q = (query or "").strip()
    if not q:
        return []

    num = max(1, min(int(num), 10))
    cache_key = f"q:{q.lower()}|n:{num}"
    now = time.time()

    cached = _SEARCH_CACHE.get(cache_key)
    if cached and (now - float(cached.get("ts", 0.0)) < _SEARCH_TTL_SECONDS):
        return cached.get("items", []) or []

    import urllib.parse
    import urllib.request

    params = urllib.parse.urlencode({"key": GOOGLE_CSE_API_KEY, "cx": GOOGLE_CSE_CX, "q": q, "num": str(num)})
    url = f"https://www.googleapis.com/customsearch/v1?{params}"

    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=25) as resp:
        raw = resp.read().decode("utf-8")
    j = json.loads(raw)

    items: List[Dict[str, str]] = []
    for it in (j.get("items") or [])[:num]:
        title = str(it.get("title") or "").strip()
        snippet = str(it.get("snippet") or "").strip()
        link = str(it.get("link") or "").strip()
        if link:
            items.append({"title": title, "snippet": snippet, "link": link})

    _SEARCH_CACHE[cache_key] = {"ts": now, "items": items}
    return items


def _make_verified_notes(items: List[Dict[str, str]]) -> str:
    if not items:
        return ""
    lines = ["VERIFIED NOTES (web search):"]
    for i, it in enumerate(items[:3], start=1):
        title = (it.get("title") or "").strip()
        snippet = (it.get("snippet") or "").strip()
        link = (it.get("link") or "").strip()
        if title:
            lines.append(f"{i}) {title}")
        if snippet:
            lines.append(f"   - {snippet}")
        if link:
            lines.append(f"   - Source: {link}")
    return "\n".join(lines).strip()


# -------------------------------------------------
# VEHICLE HELPERS
# -------------------------------------------------
def _vehicle_line(v: Any) -> str:
    v = v or {}
    year = str(v.get("year") or "").strip()
    make = str(v.get("make") or "").strip()
    model = str(v.get("model") or "").strip()
    trim = str(v.get("trim") or "").strip()
    if not (year or make or model):
        return ""
    s = f"{year} {make} {model}".strip()
    if trim:
        s += f" {trim}"
    return s


def _vehicle_sig(v: Any) -> str:
    v = v or {}
    return "|".join(
        [
            str(v.get("year") or "").strip().lower(),
            str(v.get("make") or "").strip().lower(),
            str(v.get("model") or "").strip().lower(),
            str(v.get("trim") or "").strip().lower(),
        ]
    ).strip("|")


def _is_ev_vehicle(v: Any) -> bool:
    """
    Lightweight heuristic. You can improve later with a proper vehicle DB.
    """
    v = v or {}
    make = str(v.get("make") or "").strip().lower()
    model = str(v.get("model") or "").strip().lower()
    # Tesla is always EV
    if make == "tesla":
        return True
    # Common EV model hints
    ev_markers = ["ev", "electric", "leaf", "bolt", "ioniq", "id.", "taycan", "model s", "model 3", "model x", "model y"]
    hay = f"{make} {model}"
    return any(m in hay for m in ev_markers)


# -------------------------------------------------
# INTENT / STATE (Do all 3)
# - (A) Blend diagnose + guide (guide can accept new diagnostic info)
# - (B) EV safety gate (no HV DIY, safe-only)
# - (C) Remove hard modes (no rigid schemas/mode forcing)
# -------------------------------------------------
def _is_explicit_new_case(text: str) -> bool:
    t = (text or "").lower()
    triggers = ["new problem", "different problem", "another issue", "something else", "separate issue", "start over", "reset", "new symptom"]
    return any(x in t for x in triggers)


def _is_yes(text: str) -> bool:
    t = (text or "").strip().lower()
    return t in {"yes", "y", "yeah", "yep", "ok", "okay", "sure", "show steps", "show me", "step by step", "step-by-step", "do it"}


def _is_no(text: str) -> bool:
    t = (text or "").strip().lower()
    return t in {"no", "n", "nope", "nah", "not now", "shop", "shop advice", "later"}


def _should_search(vehicle: Any, user_text: str, session: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Search only for "don't guess" facts (locations/specs), or when the user corrects us.
    """
    if not GOOGLE_CSE_ENABLED:
        return (False, "")

    vline = _vehicle_line(vehicle)
    if not vline:
        return (False, "")

    t = (user_text or "").lower()

    location_kw = [
        "where is", "where's", "location", "located", "find",
        "battery", "12v", "fuse box", "relay", "junction box",
        "jump start", "jump point", "jack point",
        "cabin filter", "fuel filter", "oil filter", "air filter",
        "starter", "alternator", "obd port", "obd2 port",
    ]
    spec_kw = [
        "oil capacity", "how many quarts", "how many liters",
        "oil type", "oil weight", "coolant type",
        "spark plug gap", "plug gap", "firing order",
        "torque spec", "torque specs", "tire pressure", "psi",
    ]
    correction_kw = [
        "not under the hood", "isn't under the hood", "isnt under the hood",
        "that's wrong", "thats wrong", "wrong",
        "no it's not", "no its not",
    ]

    wants_location = any(k in t for k in location_kw) or any(k in t for k in correction_kw)
    wants_spec = any(k in t for k in spec_kw)

    if not (wants_location or wants_spec):
        return (False, "")

    # tighten query by topic
    if "battery" in t or "12v" in t:
        q = f"{vline} 12V battery location"
    elif "fuse" in t or "relay" in t:
        q = f"{vline} fuse box location"
    elif "jump" in t or "jack" in t:
        q = f"{vline} jump start terminals jack points location"
    elif "oil capacity" in t or "how many quarts" in t:
        q = f"{vline} oil capacity quarts"
    elif "spark plug gap" in t or "plug gap" in t:
        q = f"{vline} spark plug gap"
    elif "obd" in t:
        q = f"{vline} OBD2 port location"
    else:
        q = f"{vline} {user_text}".strip()

    return (True, q)


# -------------------------------------------------
# PROMPT (Alive, master mechanic, adaptive)
# -------------------------------------------------
SYSTEM_PROMPT = """
You are AutoForge AI — a MASTER MECHANIC.
This is all you've ever done.

Voice:
- Calm, confident, helpful to beginners.
- Sounds human. No corporate tone. No "as an AI".

Critical behaviors:
- You move the conversation forward based on what the user just said.
- You do NOT reset and repeat the full "common causes" list after the user answers a question.
- Ask ONLY ONE best next question at a time when narrowing.
- If the user gives new info during a step-by-step guide, you adapt the plan and continue (do not crash, do not reset).

EV safety gate:
- If the vehicle is an EV (especially Tesla), you DO NOT provide DIY instructions involving high-voltage components.
- You CAN provide safe steps: 12V checks, basic resets, verifying charge equipment, calling roadside, what to ask a shop.
- If the best next step is high-risk/advanced, say so and give "what to ask for" at a shop.

Web notes:
- You may receive VERIFIED NOTES from web search.
- Treat VERIFIED NOTES as higher priority than your memory.
- If notes conflict with memory, trust notes.

OUTPUT (STRICT JSON ONLY — no markdown, no extra text):
{
  "assistant_text": "string",
  "offer_step_by_step": true/false,
  "confidence": 0-100,
  "topic": "short string"
}

Formatting inside assistant_text:
- Keep it readable.
- Use:
  Quick answer:
  Why it matters:
  Next step:
  (ONE question max if needed)
- If you offer step-by-step: end with a clear yes/no prompt.
"""

def _safe_json(s: str) -> Dict[str, Any]:
    try:
        return json.loads(s)
    except Exception:
        m = re.search(r"\{.*\}", s, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return {}
        return {}


def _infer_offer_flag(text: str) -> bool:
    t = (text or "").lower()
    return ("step-by-step" in t or "step by step" in t) and ("yes" in t and "no" in t)


def _never_show_ai_error(vehicle: Any, user_msg: str, session: Dict[str, Any]) -> str:
    """
    User-facing fallback that still feels like a mechanic, not a crash.
    """
    vline = _vehicle_line(vehicle)
    prefix = f"Vehicle: {vline}\n\n" if vline else ""
    return (
        prefix
        + "Alright — I didn’t get that response cleanly on my side, but we’re not stuck.\n\n"
        + "Tell me ONE thing:\n"
        + "When you try, what do you see/hear? (totally dead / clicks / cranks / starts then dies / dash lights)\n\n"
        + "If you’re not sure, just say “totally dead” or “clicks”."
    ).strip()


# -------------------------------------------------
# API MODELS
# -------------------------------------------------
class ChatRequest(BaseModel):
    session_id: str
    message: str
    vehicle: Optional[Any] = None
    active_vehicle_id: Optional[Any] = None
    core_context: Optional[Any] = None
    ai_context: Optional[Any] = None
    ai_context_text: Optional[str] = None

class ChatResponse(BaseModel):
    assistant_text: str
    confidence: Optional[int] = None
    mode: Optional[str] = None
    phase: Optional[str] = None
    topic: Optional[str] = None

class ResetRequest(BaseModel):
    session_id: str


# -------------------------------------------------
# SESSION STORE (dev)
# -------------------------------------------------
# Each session keeps lightweight state, but we DO NOT force the model into rigid modes.
# We only store intent + whether we are in a step-by-step flow, and basic facts.
_SESSIONS: Dict[str, Dict[str, Any]] = {}


def _reset_session_state(session: Dict[str, Any]) -> None:
    session["messages"] = []
    session["intent"] = "diagnose"   # diagnose | guide | shop
    session["case_active"] = False
    session["facts"] = {}
    session["vehicle_sig"] = ""
    session["last_question"] = ""
    session["last_offer"] = False


# -------------------------------------------------
# CHAT ROUTE
# -------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    sid = (req.session_id or "").strip()
    user_msg = (req.message or "").strip()
    vehicle = req.vehicle or {}

    if not sid:
        return ChatResponse(assistant_text="Missing session_id.", confidence=0, mode="error", phase="discover", topic="error")
    if not user_msg:
        return ChatResponse(assistant_text="Tell me what it’s doing (ex: won’t start, overheating, misfire).", confidence=0, mode="error", phase="discover", topic="error")

    session = _SESSIONS.setdefault(sid, {})
    if "messages" not in session:
        _reset_session_state(session)

    # If vehicle changed, clean reset (prevents cross-vehicle confusion)
    vsig = _vehicle_sig(vehicle)
    if vsig and session.get("vehicle_sig") and session.get("vehicle_sig") != vsig:
        _reset_session_state(session)
    session["vehicle_sig"] = vsig

    # user wants a new case
    if _is_explicit_new_case(user_msg):
        _reset_session_state(session)

    # yes/no buttons: set intent (but still allow adaptive follow-ups)
    if _is_yes(user_msg):
        session["intent"] = "guide"
    elif _is_no(user_msg):
        session["intent"] = "shop"

    # remember "no scanner"
    lower = user_msg.lower()
    if "no scanner" in lower or "dont know" in lower or "don't know" in lower:
        session["facts"]["codes"] = "unknown"

    # If OpenAI not available, keep it simple
    if not _openai_ok():
        vline = _vehicle_line(vehicle)
        prefix = f"Vehicle: {vline}\n\n" if vline else ""
        return ChatResponse(
            assistant_text=(prefix + "Tell me what it’s doing and when it happens. If you don’t have codes, say “no scanner.”").strip(),
            confidence=55,
            mode="fallback",
            phase="discover",
            topic="general",
        )

    # Search tool (only when needed)
    do_search, query = _should_search(vehicle, user_msg, session)
    verified_notes = ""
    if do_search:
        try:
            items = _google_cse_search(query, num=3)
            verified_notes = _make_verified_notes(items)
        except Exception:
            verified_notes = ""

    # Determine EV flag for safety gating
    is_ev = _is_ev_vehicle(vehicle)

    # Build context (soft, not a hard-mode script)
    vline = _vehicle_line(vehicle) or "Unknown vehicle"
    context = {
        "vehicle": vline,
        "is_ev": is_ev,
        "user_intent": session.get("intent", "diagnose"),  # diagnose | guide | shop
        "case_active": bool(session.get("case_active", False)),
        "known_facts": session.get("facts", {}),
        "last_question": session.get("last_question", ""),
        "rules": [
            "Do NOT repeat the entire common causes list after the first assistant reply in a case.",
            "If the user answers you (or corrects you), acknowledge and continue forward.",
            "If user_intent == guide, provide step-by-step SAFE actions. If EV and it involves HV, stop and give shop/roadside instructions.",
            "If user_intent == shop, provide what to say/ask and expected tests. No DIY.",
        ],
    }

    # History: enough to feel alive but not bloated
    history = session.get("messages", [])[-16:]

    messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    if verified_notes:
        messages.append({"role": "system", "content": verified_notes})
    messages.append({"role": "system", "content": "CONTEXT:\n" + json.dumps(context)})

    for h in history:
        if h.get("role") in ("user", "assistant"):
            messages.append({"role": h["role"], "content": h["content"]})

    messages.append({"role": "user", "content": user_msg})

    try:
        raw = _call_openai(messages)
        data = _safe_json(raw)

        if not data or "assistant_text" not in data:
            raise ValueError("Model returned invalid JSON")

        assistant_text = str(data.get("assistant_text") or "").strip()
        topic = str(data.get("topic") or "general").strip()
        confidence = int(data.get("confidence") or 70)

        offer_flag = bool(data.get("offer_step_by_step", False))
        if not offer_flag and _infer_offer_flag(assistant_text):
            offer_flag = True

        # Store last question (best-effort)
        qmatches = re.findall(r"([^\n\?]{0,200}\?)", assistant_text)
        if qmatches:
            session["last_question"] = qmatches[-1].strip()

        # Mark case active after the first real assistant response
        if not session.get("case_active"):
            session["case_active"] = True

        # Save transcript
        session["messages"].append({"role": "user", "content": user_msg})
        session["messages"].append({"role": "assistant", "content": assistant_text})

        # If assistant offered steps, keep buttons available (frontend handles it)
        session["last_offer"] = offer_flag

        return ChatResponse(
            assistant_text=assistant_text,
            confidence=confidence,
            mode="llm",
            phase=session.get("intent", "diagnose"),
            topic=topic,
        )

    except Exception:
        print("[/chat] error:")
        traceback.print_exc()

        # IMPORTANT: never show "AI error" to the user
        safe_reply = _never_show_ai_error(vehicle, user_msg, session)

        session["messages"].append({"role": "user", "content": user_msg})
        session["messages"].append({"role": "assistant", "content": safe_reply})

        return ChatResponse(
            assistant_text=safe_reply,
            confidence=45,
            mode="fallback",
            phase=session.get("intent", "diagnose"),
            topic="recovery",
        )


# -------------------------------------------------
# RESET SESSION
# -------------------------------------------------
@app.post("/session/reset")
def session_reset(req: ResetRequest) -> Dict[str, Any]:
    sid = (req.session_id or "").strip()
    if not sid:
        return {"ok": False, "error": "Missing session_id"}
    _SESSIONS.pop(sid, None)
    return {"ok": True}


# -------------------------------------------------
# HEALTH
# -------------------------------------------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "openai_key_loaded": bool(OPENAI_API_KEY),
        "model": OPENAI_MODEL,
        "google_cse_enabled": GOOGLE_CSE_ENABLED,
        "cors_origins": cors_origins,
    }
