from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List

OBD_PATH = Path(__file__).resolve().parent.parent / "data" / "obd_codes.json"

class OBDIndex:
    def __init__(self, path: Path = OBD_PATH):
        self.data: Dict[str, Dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))

    def lookup_code(self, code: str) -> Dict[str, Any] | None:
        code = code.strip().upper()
        return self.data.get(code)

    def suggest_from_symptoms(self, text: str) -> List[Dict[str, Any]]:
        t = text.lower()
        hits = []
        # super-lite heuristics for phase 1
        if any(k in t for k in ["misfire", "shake", "rough idle"]):
            hits.append({"code": "P0300", **self.data["P0300"]})
        if any(k in t for k in ["lean", "hiss", "vacuum", "maf", "stft", "ltft"]):
            hits.append({"code": "P0171", **self.data["P0171"]})
        if any(k in t for k in ["cat", "catalytic", "rotten egg", "p0420"]):
            hits.append({"code": "P0420", **self.data["P0420"]})
        if any(k in t for k in ["evap", "gas cap", "p0442"]):
            hits.append({"code": "P0442", **self.data["P0442"]})
        return hits[:3]
