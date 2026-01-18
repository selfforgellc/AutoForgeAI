from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth_routes import router as auth_router
from subscription_routes import router as subscription_router
from status_api import router as status_router
from db import init_db

app = FastAPI(title="AutoForgeAI", version="20.0.2")

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

        # 🔹 Future / preferred
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


@app.on_event("startup")
def on_startup():
    init_db()
    print("[AutoForgeAI] backend initialized")


@app.get("/")
def root():
    return {"ok": True, "service": "AutoForgeAI"}
