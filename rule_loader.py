# backend/rule_loader.py
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import yaml

RULES_DIR = os.path.join(os.path.dirname(__file__), "rules")
VOICE_FILE = os.path.join(os.path.dirname(__file__), "prompts", "voice_pack.yaml")


@dataclass
class AppliedRule:
    id: str
    priority: int
    system_lock: Optional[str]
    component_hints: List[str]
    forbidden_systems: List[str]
    forbidden_claims: List[str]
    safety_flags: List[str]
    safety_message: str
    questions_confirm: List[str]
    questions_disambiguate: List[str]
    micro_steps: List[str]
    what_it_means: str
    cap_initial: float
    cap_after: float


class RuleLoader:
    def __init__(self) -> None:
        self.rules: List[Dict[str, Any]] = []
        self.voice: Dict[str, Any] = {}
        self.reload()

    def reload(self) -> None:
        self.rules = []
        # Load YAML rule files
        for name in os.listdir(RULES_DIR):
            if not name.endswith(".yaml"):
                continue
            path = os.path.join(RULES_DIR, name)
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            for r in data.get("rules", []):
                r["_domain"] = data.get("domain", "unknown")
                self.rules.append(r)

        # Sort by priority desc
        self.rules.sort(key=lambda r: int(r.get("priority", 0)), reverse=True)

        # Load voice pack
        with open(VOICE_FILE, "r", encoding="utf-8") as f:
            self.voice = yaml.safe_load(f) or {}

    def _match_rule(self, rule: Dict[str, Any], text: str) -> bool:
        t = text.lower()
        trg = rule.get("triggers", {}) or {}
        kws = trg.get("keywords", []) or []
        regs = trg.get("regex", []) or []

        for kw in kws:
            if kw.lower() in t:
                return True

        for pattern in regs:
            try:
                if re.search(pattern, text, flags=re.IGNORECASE):
                    return True
            except re.error:
                continue

        return False

    def apply(self, text: str) -> List[AppliedRule]:
        matches: List[AppliedRule] = []

        for r in self.rules:
            if not self._match_rule(r, text):
                continue

            lock = r.get("lock", {}) or {}
            forbid = r.get("forbid", {}) or {}
            safety = r.get("safety", {}) or {}
            qs = r.get("questions", {}) or {}
            nxt = r.get("next_actions", {}) or {}
            caps = r.get("confidence_caps", {}) or {}

            matches.append(
                AppliedRule(
                    id=str(r.get("id", "unknown")),
                    priority=int(r.get("priority", 0)),
                    system_lock=(lock.get("system") if lock.get("system") != "auto" else None),
                    component_hints=list(lock.get("component_hints", []) or []),
                    forbidden_systems=list(forbid.get("systems", []) or []),
                    forbidden_claims=list(forbid.get("claims", []) or []),
                    safety_flags=list((safety.get("flags", []) or [])),
                    safety_message=str(safety.get("message", "") or ""),
                    questions_confirm=list((qs.get("confirm", []) or [])),
                    questions_disambiguate=list((qs.get("disambiguate", []) or [])),
                    micro_steps=list((nxt.get("micro_steps", []) or [])),
                    what_it_means=str(nxt.get("what_it_means", "") or ""),
                    cap_initial=float(caps.get("initial_max", 0.55)),
                    cap_after=float(caps.get("after_evidence_max", 0.80)),
                )
            )

        return matches

    def build_guardrails(self, applied: List[AppliedRule]) -> Dict[str, Any]:
        # Combine matched rules into one set of guardrails
        system_lock = None
        component_hints: List[str] = []
        forbidden_systems: List[str] = []
        forbidden_claims: List[str] = []
        safety_flags: List[str] = []
        safety_messages: List[str] = []
        confirm_qs: List[str] = []
        disambig_qs: List[str] = []
        micro_steps: List[str] = []
        what_it_means = ""

        cap_initial = 0.55
        cap_after = 0.80

        for r in applied:
            if r.system_lock and not system_lock:
                system_lock = r.system_lock

            component_hints.extend([c for c in r.component_hints if c not in component_hints])
            forbidden_systems.extend([s for s in r.forbidden_systems if s not in forbidden_systems])
            forbidden_claims.extend([c for c in r.forbidden_claims if c not in forbidden_claims])

            for f in r.safety_flags:
                if f not in safety_flags:
                    safety_flags.append(f)
            if r.safety_message and r.safety_message not in safety_messages:
                safety_messages.append(r.safety_message)

            for q in r.questions_disambiguate:
                if q not in disambig_qs:
                    disambig_qs.append(q)
            for q in r.questions_confirm:
                if q not in confirm_qs:
                    confirm_qs.append(q)

            for s in r.micro_steps:
                if s not in micro_steps:
                    micro_steps.append(s)

            if not what_it_means and r.what_it_means:
                what_it_means = r.what_it_means

            cap_initial = min(cap_initial, r.cap_initial)
            cap_after = min(cap_after, r.cap_after)

        return {
            "system_lock": system_lock,
            "component_hints": component_hints[:6],
            "forbidden_systems": forbidden_systems,
            "forbidden_claims": forbidden_claims[:10],
            "safety_flags": safety_flags,
            "safety_message": " ".join(safety_messages).strip(),
            "questions_disambiguate": disambig_qs[:2],
            "questions_confirm": confirm_qs[:3],
            "micro_steps": micro_steps[:3],
            "what_it_means": what_it_means,
            "cap_initial": cap_initial,
            "cap_after": cap_after,
            "voice": self.voice,
        }
