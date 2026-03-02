"""
Unified API Response Module
Supports:
- success()
- failure()
- error_response()  (legacy compatibility)
- ok()              (legacy compatibility)
- fail()            (legacy compatibility)
"""

from typing import Any, Optional


def success(data: Any = None) -> dict:
    """
    Standard success response.
    """
    return {
        "success": True,
        "data": data,
        "error": None
    }


def failure(message: str, data: Optional[Any] = None) -> dict:
    """
    Standard failure response.
    """
    return {
        "success": False,
        "data": data,
        "error": message
    }


# ---- Backward Compatibility ----

def error_response(message: str) -> dict:
    """
    Legacy compatibility wrapper.
    """
    return failure(message)


def ok(data: Any = None) -> dict:
    """
    Legacy compatibility wrapper.
    """
    return success(data)


def fail(message: str) -> dict:
    """
    Legacy compatibility wrapper.
    """
    return failure(message)
