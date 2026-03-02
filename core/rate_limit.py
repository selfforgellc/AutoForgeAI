from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

from core.response import error_response

limiter = Limiter(key_func=get_remote_address)


def rate_limit_exceeded_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content=error_response("Too many requests. Please slow down.")
    )
