"""Cache service with safe defaults.

This project originally used Redis for caching. For a "ship tonight" release,
we must not require Redis to be installed or running just to start the API.

Behavior:
- If redis is installed AND REDIS_URL is set (or defaults) AND Redis is reachable,
  we use it.
  - If Redis is not reachable at runtime, we fall back to in-memory cache.
  - We never crash the API because Redis is down.
- If redis is not installed, we use in-memory cache.
"""

from __future__ import annotations

import json
import time
from typing import Any, Optional

from core.config import settings
from core.logger import logger
from core.metrics import CACHE_HITS, CACHE_MISSES


# -----------------------------
# In-memory fallback
# -----------------------------

_mem: dict[str, tuple[float, str]] = {}  # key -> (expires_at_epoch, json_str)


def _mem_get(key: str) -> Optional[Any]:
    now = time.time()
    item = _mem.get(key)
    if not item:
        CACHE_MISSES.inc()
        return None
    exp, payload = item
    if exp and now > exp:
        _mem.pop(key, None)
        CACHE_MISSES.inc()
        return None
    CACHE_HITS.inc()
    try:
        return json.loads(payload)
    except Exception:
        return None


def _mem_set(key: str, value: Any, ttl: int = 300) -> None:
    exp = time.time() + int(ttl) if ttl else 0.0
    _mem[key] = (exp, json.dumps(value))


def _mem_delete(key: str) -> None:
    _mem.pop(key, None)


# -----------------------------
# Redis (optional)
# -----------------------------

_redis_client = None
_redis_ready = False

try:
    import redis  # type: ignore

    _redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

    # Don't block startup if Redis isn't available.
    try:
        _redis_client.ping()
        _redis_ready = True
        logger.info("cache_service: Redis enabled")
    except Exception:
        _redis_ready = False
        logger.warning("cache_service: Redis not reachable; using in-memory cache")
except Exception:
    _redis_client = None
    _redis_ready = False
    logger.warning("cache_service: redis package not available; using in-memory cache")


def cache_get(key: str) -> Optional[Any]:
    if _redis_ready and _redis_client is not None:
        try:
            value = _redis_client.get(key)
            if value:
                CACHE_HITS.inc()
            else:
                CACHE_MISSES.inc()
            return json.loads(value) if value else None
        except Exception:
            # Redis went down mid-run; fail soft.
            return _mem_get(key)
    return _mem_get(key)


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    if _redis_ready and _redis_client is not None:
        try:
            _redis_client.setex(key, int(ttl), json.dumps(value))
            return
        except Exception:
            pass
    _mem_set(key, value, ttl)


def cache_delete(key: str) -> None:
    if _redis_ready and _redis_client is not None:
        try:
            _redis_client.delete(key)
            return
        except Exception:
            pass
    _mem_delete(key)
