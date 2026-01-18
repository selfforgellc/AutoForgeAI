# backend/session_manager.py
"""
SessionManager — authoritative session + diagnostic state storage
"""

import time
from typing import Dict, Any, List


class SessionManager:
    def __init__(self, timeout_seconds: int = 1800):
        self.timeout_seconds = timeout_seconds
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def _now(self) -> float:
        return time.time()

    def get(self, session_id: str) -> Dict[str, Any]:
        session = self.sessions.get(session_id)

        if not session:
            session = {
                "created_at": self._now(),
                "last_active": self._now(),

                # 🔐 Locked per-session once resolved
                "tier": None,

                # Small internal flags (avoid repeated safety, etc.)
                "flags": {
                    "safety_shown": False,
                },

                # Vehicle memory
                "vehicle": {"year": None, "make": None, "model": None, "trim": None},

                # Diagnostic intelligence
                "facts": [],
                "ruled_out": [],

                "diagnostic": {
                    "phase": "INITIAL",  # INITIAL | FOCUSED
                    "system": None,
                    "component": None,
                    "last_test": None,
                },

                # Conversation history
                "history": [],
            }

            self.sessions[session_id] = session

        session["last_active"] = self._now()
        return session

    def set_phase(self, session_id: str, phase: str):
        self.get(session_id)["diagnostic"]["phase"] = phase

    def set_focus(self, session_id: str, system: str, component: str):
        diag = self.get(session_id)["diagnostic"]
        diag["phase"] = "FOCUSED"
        diag["system"] = system
        diag["component"] = component

    def set_last_test(self, session_id: str, test: str):
        self.get(session_id)["diagnostic"]["last_test"] = test

    def add_fact(self, session_id: str, fact: str):
        if not fact:
            return
        facts: List[str] = self.get(session_id)["facts"]
        if fact not in facts:
            facts.append(fact)

    def add_turn(self, session_id: str, role: str, content: str):
        hist = self.get(session_id)["history"]
        hist.append({"role": role, "content": content, "ts": self._now()})
        if len(hist) > 12:
            self.get(session_id)["history"] = hist[-12:]

    def reset(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]

    def garbage_collect(self):
        now = self._now()
        expired = []
        for sid, s in self.sessions.items():
            last_active = s.get("last_active", now)
            if (now - last_active) > self.timeout_seconds:
                expired.append(sid)
        for sid in expired:
            del self.sessions[sid]
