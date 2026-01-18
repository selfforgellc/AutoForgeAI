from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
import time

app = FastAPI(title="SelfForge Status API", version="1.0")

# Allow mobile app access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to your mobile origin later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the services to check
SERVICES = [
    {"name": "AutoForge", "url": "https://autoforge.selfforge.ai/api/health"},
    {"name": "SelfForge", "url": "https://selforge.selfforge.ai/api/health"},
]

async def check_service(service):
    """Ping a service and return status"""
    name, url = service["name"], service["url"]
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get(url)
            latency = round((time.perf_counter() - start) * 1000)
            if resp.status_code == 200:
                return {"name": name, "status": "online", "latency_ms": latency}
            else:
                return {"name": name, "status": "offline", "latency_ms": latency}
    except Exception:
        return {"name": name, "status": "offline", "latency_ms": None}


@app.get("/api/status")
async def get_status():
    """Return server, AI core, and project statuses"""
    results = await asyncio.gather(*(check_service(s) for s in SERVICES))

    # Example: if SelfForge AI core has its own check, add it here later
    ai_core_status = next((s for s in results if s["name"] == "SelfForge"), None)
    ai_status = ai_core_status["status"] if ai_core_status else "unknown"

    # Simple server indicator (the fact this endpoint responds = online)
    server_status = "online"

    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "server": server_status,
        "aiCore": ai_status,
        "services": results,
    }
