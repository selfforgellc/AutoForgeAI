from typing import Dict, Any, List, Optional
import time
from collections import deque

class ConversationState:
    """In-memory short-term conversation state per session_id."""
    def __init__(self, max_turns: int = 6):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.max_turns = max_turns

    def get(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "turns": deque(maxlen=self.max_turns),
                "vehicle": None,
                "symptoms": [],
                "dtcs": [],
                "last_intent": None,
                "created_at": time.time(),
            }
        return self.sessions[session_id]

    def record(self, session_id: str, user_text: str, parsed):
        s = self.get(session_id)
        s["turns"].append({"role":"user","text":user_text})
        if parsed:
            if parsed.get("vehicle"):
                s["vehicle"] = parsed["vehicle"]
            if parsed.get("dtcs"):
                for d in parsed["dtcs"]:
                    if d not in s["dtcs"]:
                        s["dtcs"].append(d)
            if parsed.get("intent"):
                s["last_intent"] = parsed["intent"]
            if parsed.get("symptom"):
                s["symptoms"].append(parsed["symptom"])

    def push_ai(self, session_id: str, text: str):
        s = self.get(session_id)
        s["turns"].append({"role":"assistant","text":text})
