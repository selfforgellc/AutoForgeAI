# backend/kb/matcher_hybrid.py
import os
import re
import time
from typing import Dict, Any, List, Optional, Tuple

from .loader import load_all, compile_packs

# ---------------------------------------------------------------------
# Intent synonyms and normalization
# ---------------------------------------------------------------------
INTENT_SYNONYMS = {
    "no_heat": [
        "no heat", "no hot air", "heater blows cold", "no cabin heat", "cold air from vents"
    ],
    "ac_not_cold": [
        "ac not cold", "air conditioner warm", "a c not cold", "warm air from ac"
    ],
    "rough_idle": [
        "rough idle", "shaking at idle", "idles rough", "vibrates at idle"
    ],
    "no_crank": [
        "no crank", "won t crank", "clicking no start", "starter clicks"
    ],
    "burning_smell_vents": [
        "burning smell vents", "burning smell from vents", "burning smell heater",
        "burning plastic smell heat", "electrical smell vents", "smoke from vents"
    ],
}

INTENT_TO_SYSTEMS = {
    "no_heat": ["cooling", "hvac"],
    "ac_not_cold": ["hvac", "engine"],
    "rough_idle": ["engine", "fuel", "ignition", "air_intake"],
    "no_crank": ["electrical", "starting", "battery"],
    "burning_smell_vents": ["hvac", "electrical", "cooling"],
    "generic": [],
}

def normalize_text(text: str) -> str:
    t = (text or "").lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def match_intent(text_lc: str) -> str:
    for key, phrases in INTENT_SYNONYMS.items():
        for p in phrases:
            if p in text_lc:
                return key
    return "generic"

def extract_dtcs(message: str) -> List[str]:
    # OBD-II style: P0300, P0171, etc.
    return re.findall(r"\b[PCBU]\d{4}\b", (message or "").upper())

def _smart_literal_hit(text_lc: str, item: Dict[str, Any]) -> float:
    # Strong boosts if exact phrases appear in summary/title
    title = normalize_text(item.get("title", ""))
    summ = normalize_text(item.get("summary", ""))
    score = 0.0
    for k in ["no heat", "rough idle", "no crank", "ac not cold", "burning smell"]:
        if k in text_lc and (k in title or k in summ):
            score += 2.0
    return score

def _system_bias(intent_key: str, item: Dict[str, Any]) -> float:
    related = INTENT_TO_SYSTEMS.get(intent_key, [])
    if not related:
        return 0.0
    systems = item.get("systems", []) or []
    hit = sum(1 for s in related if s in systems)
    if hit <= 0:
        return 0.0
    return min(1.25, 0.35 * hit)

def score_item(text_lc: str, item: Dict[str, Any], intent_key: str, dtcs: List[str]) -> float:
    # Keyword overlap on title/summary/steps/causes
    blob = []
    blob.append(item.get("id", ""))
    blob.append(item.get("title", ""))
    blob.append(item.get("summary", ""))
    for c in item.get("causes", []) or []:
        blob.append(c.get("name", ""))
        blob.append(c.get("description", ""))
    for s in item.get("steps", []) or []:
        blob.append(s.get("step", ""))
        blob.append(s.get("details", ""))

    doc = normalize_text(" ".join(blob))
    qw = [w for w in text_lc.split() if len(w) > 2]
    dw = set(doc.split())
    base = sum(1.0 for w in qw if w in dw)

    # DTC bonus
    dtc_bonus = 0.0
    item_dtcs = set((item.get("dtc_bonus") or []))
    for d in dtcs:
        if d in item_dtcs:
            dtc_bonus += 1.0

    return base + dtc_bonus + _smart_literal_hit(text_lc, item) + _system_bias(intent_key, item)

# ---------------------------------------------------------------------
# Cached KB (avoids reloading/compiling constantly)
# ---------------------------------------------------------------------
_CACHED: Dict[str, Any] = {"packs": None, "compiled": None, "loaded_at": 0.0}
_RELOAD_SECONDS = int(os.getenv("KB_RELOAD_SECONDS", "0"))  # 0 = never reload automatically

def _get_compiled() -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    now = time.time()
    if _CACHED["packs"] is None or _CACHED["compiled"] is None:
        packs = load_all()
        compiled = compile_packs(packs)
        _CACHED.update({"packs": packs, "compiled": compiled, "loaded_at": now})
    elif _RELOAD_SECONDS > 0 and (now - float(_CACHED["loaded_at"])) > _RELOAD_SECONDS:
        packs = load_all()
        compiled = compile_packs(packs)
        _CACHED.update({"packs": packs, "compiled": compiled, "loaded_at": now})
    return _CACHED["packs"], _CACHED["compiled"]

def match_knowledge_hybrid(message: str, tier: str = "basic") -> Dict[str, Any]:
    packs, compiled = _get_compiled()

    text_lc = normalize_text(message)
    dtcs = extract_dtcs(message or "")
    intent_key = match_intent(text_lc)

    best_score = 0.0
    best_item: Optional[Dict[str, Any]] = None

    for item in compiled:
        s = score_item(text_lc, item, intent_key, dtcs)
        if s > best_score:
            best_score = s
            best_item = item

    if not best_item or best_score < 0.85:
        return {"matched": False, "matched_score": round(best_score, 2), "intent": intent_key}

    tiers = best_item.get("tiers", {})
    max_steps = tiers.get(tier, {}).get("max_steps", len(best_item.get("steps", [])))

    return {
        "matched": True,
        "matched_score": round(best_score, 2),
        "intent": intent_key,
        "id": best_item.get("id"),
        "title": best_item.get("title"),
        "systems": best_item.get("systems", []),
        "summary": best_item.get("summary", ""),
        "possible_causes": best_item.get("causes", []),
        "steps": (best_item.get("steps", []) or [])[:max_steps],
        "dtc_hits": [d for d in dtcs if d in (best_item.get("dtc_bonus") or [])],
    }
