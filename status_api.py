# FILE: status_api.py
from __future__ import annotations

import asyncio
import os
import time
from typing import Dict, List, Optional

import httpx
from fastapi import APIRouter

router = APIRouter()

# Define the services to check (override via env if desired)
# You can set STATUS_SERVICES as a comma-separated list:
# STATUS_SERVICES="AutoForge|https://autoforge.selfforge.ai/api/health,SelfForge|https://selforge.selfforge.ai/api/health"
DEFAULT_SERVICES = [
    {"name": "AutoForge", "url": "https://autoforge.selfforge.ai/api/health"},
    {"name": "SelfForge", "url": "https://selforge.selfforge.ai/api/health"},
]


def _load_services() -> List[Dict[str, str]]:
    raw = os.getenv("STATUS_SERVICES", "").strip()
    if not raw:
        return DEFAULT_SERVICES

    services: List[Dict[str, str]] = []
    # Format: Name|URL,Name2|URL2
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if "|" not in item:
            # If someone provided just a URL, name it generically
            services.append({"name": "Service", "url": item})
            continue
        name, url = item.split("|", 1)
        services.append({"name": name.strip() or "Service", "url": url.strip()})
    return services or DEFAULT_SERVICES


SERVICES = _load_services()


async def check_service(service: Dict[str, str]) -> Dict[str, Optional[object]]:
    """Ping a service and return status + latency."""
    name, url = service.get("name", "Service"), service.get("url", "")
    start = time.perf_counter()

    try:
        timeout_s = float(os.getenv("STATUS_TIMEOUT_SECONDS", "3"))
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            resp = await client.get(url)
            latency = round((time.perf_counter() - start) * 1000)

            if resp.status_code == 200:
                return {"name": name, "status": "online", "latency_ms": latency}
            return {
                "name": name,
                "status": "offline",
                "latency_ms": latency,
                "http_status": resp.status_code,
            }
    except Exception:
        return {"name": name, "status": "offline", "latency_ms": None}


@router.get("/health")
def health():
    """Simple liveness probe for Render and quick sanity checks."""
    return {"ok": True, "service": "AutoForgeAI", "ts": int(time.time())}


@router.get("/api/status")
async def get_status():
    """Return server and downstream service status."""
    results = await asyncio.gather(*(check_service(s) for s in SERVICES))

    # Example: if SelfForge AI core has its own check, add it here later
    ai_core_status = next((s for s in results if s.get("name") == "SelfForge"), None)
    ai_status = ai_core_status.get("status") if ai_core_status else "unknown"

    # If this endpoint responds, the server itself is online
    server_status = "online"

    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "server": server_status,
        "aiCore": ai_status,
        "services": results,
    }
