import re

# all canonical intents and their common phrasings
INTENT_SYNONYMS = {
    "no_heat": [
        "no heat", "no hot air", "no warm air", "not blowing hot air", "heater not working",
        "heater blows cold", "vents cold", "no heat from vents", "no cabin heat", "no heat from dash",
        "air not hot", "cold air from vents"
    ],
    "ac_not_cold": [
        "ac not cold", "a c not cold", "air not cold", "ac warm", "a c warm", "ac blowing warm air"
    ],
    "rough_idle": [
        "rough idle", "engine shakes", "car shakes at idle", "vibration at idle", "rough idle at stoplight"
    ],
    "cranks_no_start": [
        "cranks but wont start", "cranks but will not start", "cranks no start", "turns over no start"
    ],
    "no_crank": [
        "no crank", "turn key no crank", "click no crank", "won't crank", "won't turn over"
    ],
    "vibration_speed": [
        "vibration at speed", "vibration at highway speed", "shakes at 65 mph", "wheel shake highway"
    ]
}

def normalize_text(txt: str) -> str:
    if not txt:
        return ""
    txt = txt.lower()
    txt = re.sub(r"[^a-z0-9\s]", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    # synonym-level swaps
    txt = txt.replace("hot air", "heat").replace("warm air", "heat")
    return txt
