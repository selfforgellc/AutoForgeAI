# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth_routes import router as auth_router
from subscription_routes import router as subscription_router
from status_api import router as status_router
from chat_routes import router as chat_router  # ✅ NEW
from db import init_db

app = FastAPI(title="AutoForgeAI", version="20.0.3")

# ✅ CORS — FRONTEND ORIGINS ONLY
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # 🔹 Local dev
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",

        # 🔹 Vercel (current)
        "https://auto-forge-frontend-fixed.vercel.app",

        # 🔹 Preferred / production
        "https://autoforgeai.vercel.app",
        "https://app.autoforgeai.com",
        "https://autoforgeai.com",
        "https://selfforgellc.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ API ROUTES
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(subscription_router, prefix="/api/subscription", tags=["subscription"])
app.include_router(status_router, prefix="/api/status", tags=["status"])

# ✅ CHAT ROUTES
# Your frontend has historically called BOTH styles; we support both to avoid breaking anything.
# - POST /chat         (some clients)
# - POST /api/chat     (other clients)
# - POST /session/reset
# - POST /api/session/reset
app.include_router(chat_router, tags=["chat"])          # root routes
app.include_router(chat_router, prefix="/api", tags=["chat"])  # /api/* aliases


@app.on_event("startup")
def on_startup():
    init_db()
    print("[AutoForgeAI] backend initialized")


@app.get("/")
def root():
    return {"ok": True, "service": "AutoForgeAI"}
