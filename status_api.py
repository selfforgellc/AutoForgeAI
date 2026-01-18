# status_api.py
from __future__ import annotations

import asyncio
import os
import time
from typing import Dict, List, Optional

import httpx
from fastapi import APIRouter

router = APIRouter()

DEFAULT_SERVICES = [
    {"name": "AutoForge", "url": "https://autoforgeai.onrender.com/api/status/health"},
]

def _load_services() -> List[Dict[str, str]]:
    raw = os.getenv("STATUS_SERVICES", "").strip()
    if not raw:
        return DEFAULT_SERVICES

    services: List[Dict[str, str]] = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if "|" not in item:
            services.append({"name": "Service", "url": item})
            continue
        name, url = item.split("|", 1)
        services.append({"name": name.strip(), "url": url.strip()})
    return services or DEFAULT_SERVICES

SERVICES = _load_services()

async def check_service(service: Dict[str, str]) -> Dict[str, Optional[object]]:
    name, url = service.get("name"), service.get("url")
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get(url)
            latency = round((time.perf_counter() - start) * 1000)
            return {
                "name": name,
                "status": "online" if resp.status_code == 200 else "offline",
                "latency_ms": latency,
                "http_status": resp.status_code,
            }
    except Exception:
        return {"name": name, "status": "offline", "latency_ms": None}

@router.get("/health")
def health():
    return {
        "ok": True,
        "service": "AutoForgeAI",
        "env": os.getenv("ENV", "production"),
        "ts": int(time.time()),
    }

@router.get("/")
async def status():
    results = await asyncio.gather(*(check_service(s) for s in SERVICES))
    return {
        "server": "online",
        "services": results,
    }
