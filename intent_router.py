# backend/intent_router.py
import re

def interpret_user_intent(text: str) -> str:
    t = text.lower()

    if any(p in t for p in ["how do i test", "how do i check", "how to test"]):
        return "REQUEST_TEST"

    if any(p in t for p in ["no", "yes", "it does", "it doesn't", "still", "now"]):
        return "REPORT_RESULT"

    if any(p in t for p in ["check the", "focus on", "let's check"]):
        return "SELECT_COMPONENT"

    return "NEW_INFO"
