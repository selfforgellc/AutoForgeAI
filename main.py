# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth_routes import router as auth_router
from subscription_routes import router as subscription_router
from status_api import router as status_router
from db import init_db

app = FastAPI(title="AutoForgeAI", version="20.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://autoforgeai.onrender.com",
        "https://selfforgellc.com",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔑 API ROUTES (single, consistent prefix)
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(subscription_router, prefix="/api/subscriptions", tags=["subscriptions"])
app.include_router(status_router, prefix="/api/status", tags=["status"])

@app.on_event("startup")
def on_startup():
    init_db()
    print("[AutoForgeAI] backend initialized")

@app.get("/")
def root():
    return {"ok": True, "service": "AutoForgeAI"}
