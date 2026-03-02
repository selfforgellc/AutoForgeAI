import re
from typing import Dict, Any, List, Tuple
from .loader import load_all, compile_packs

# Detect diagnostic trouble codes (P/U/C/B)
DTC_RE = re.compile(r'\b([PUCB][0-9A-F]{4})\b', re.I)

def extract_dtcs(text: str) -> List[str]:
    """Extract any OBD-II DTC codes (P0xxx, U0xxx, etc.) from the message."""
    return [m.group(1).upper() for m in DTC_RE.finditer(text or "")]

# ---------------------------
# SMARTER SCORING ALGORITHM
# ---------------------------
def score_item(item: Dict[str, Any], text_lc: str, dtcs: List[str], dtc_index: Dict[str, Any]) -> float:
    """
    Scores a knowledge entry by comparing included/excluded patterns and DTC matches.
    """
    score = 0.0
    text_clean = re.sub(r'[^a-z0-9\s]', ' ', text_lc)  # remove punctuation
    text_words = set(text_clean.split())

    # ----- inclusion patterns -----
    for kind, pat in item.get("_inc", []):
        if kind == "lit":
            # relaxed literal match: all words in the phrase appear somewhere
            phrase_words = set(re.sub(r'[^a-z0-9\s]', ' ', pat.lower()).split())
            if phrase_words and phrase_words.issubset(text_words):
                score += 1.0
            # partial match fallback
            elif any(w in text_words for w in phrase_words):
                score += 0.5
        elif kind == "re" and pat.search(text_lc):
            score += 1.5

    # ----- exclusion patterns -----
    for kind, pat in item.get("_exc", []):
        if (kind == "lit" and pat in text_lc) or (kind == "re" and pat.search(text_lc)):
            score -= 3.0  # strong penalty

    # ----- DTC bonus -----
    wanted = set([c.upper() for c in item.get("dtc_bonus", [])])
    if wanted:
        matched = len(wanted.intersection(dtcs))
        score += matched * 0.75  # partial fractional bonus

    return score

# ---------------------------
# TIER SIMPLIFICATION
# ---------------------------
def simplify_for_tier(steps: List[Dict[str, Any]], tier_cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Trim and simplify diagnostic steps according to the user tier."""
    max_steps = tier_cfg.get("max_steps", len(steps))
    out = steps[:max_steps]
    if tier_cfg.get("language_level") == "simple":
        repl = {
            r"\bverify\b": "check",
            r"\bperform\b": "do",
            r"\bdiagnostic\b": "test",
            r"\boscilloscope\b": "scanner",
        }
        _tmp = []
        for s in out:
            d = s.get("details", "")
            for k, v in repl.items():
                d = re.sub(k, v, d, flags=re.IGNORECASE)
            _tmp.append({**s, "details": d})
        out = _tmp
    return out

# ---------------------------
# MAIN MATCH FUNCTION
# ---------------------------
def match_knowledge(message: str, tier: str = "basic") -> Dict[str, Any]:
    """
    Main entry: match a user message against all knowledge packs and return the best structured hit.
    """
    packs = load_all()
    compiled = compile_packs(packs)
    dtc_index = packs.get("dtc_index", {})
    text_lc = (message or "").lower()
    dtcs = extract_dtcs(message or "")

    best: Tuple[float, Dict[str, Any]] = (-999, None)

    for item in compiled:
        s = score_item(item, text_lc, dtcs, dtc_index)
        if s > best[0]:
            best = (s, item)

    score, item = best

    # fallback if confidence is too low
    if not item or score < 0.5:
        return {
            "id": "generic.insufficient_data",
            "title": "Need more details",
            "systems": [],
            "summary": (
                "I couldn't confidently match the symptom. Add more specifics about when it happens, "
                "temperature or load conditions, noises, or any DTC codes."
            ),
            "possible_causes": [
                {
                    "name": "Insufficient data",
                    "description": "Symptom description is too general or not recognized yet.",
                    "likelihood": ""
                }
            ],
            "steps": [
                {
                    "step": "Add details",
                    "details": "Include noises, smells, recent repairs, and scan-tool data (STFT/LTFT, codes).",
                    "tools": "None",
                    "expected": ""
                }
            ],
            "matched_score": score,
        }

    # Simplify output according to tier
    tier_cfg = item.get("tiers", {}).get(tier, {}) if tier in ("basic", "pro", "elite") else {}
    steps = simplify_for_tier(item.get("steps", []), tier_cfg)

    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "systems": item.get("systems", []),
        "summary": item.get("summary", ""),
        "possible_causes": item.get("causes", []),
        "steps": steps,
        "dtc_hits": [d for d in dtcs if d in item.get("dtc_bonus", [])],
        "matched_score": round(score, 2)
    }
