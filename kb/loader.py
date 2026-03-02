# backend/kb/loader.py
import os, json, glob
from typing import Dict, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_DIR = os.path.abspath(os.path.join(os.path.dirname(BASE_DIR), "knowledge"))

def _read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _validate_item(item: Dict[str, Any], path: str) -> bool:
    required = ["id", "title", "systems", "summary", "steps"]
    for key in required:
        if key not in item:
            print(f"[KB WARN] Missing '{key}' in {path}")
            return False
    return True

def load_all() -> Dict[str, Any]:
    packs = {}

    for path in glob.glob(os.path.join(KNOWLEDGE_DIR, "*.json")):
        name = os.path.basename(path).lower()
        if name == "dtc_index.json":
            packs["dtc_index"] = _read_json(path)
            continue

        try:
            data = _read_json(path)
            # ✅ Handle different structures
            if isinstance(data, dict):
                # either a single item or bundle (id → item)
                if "id" in data:
                    if _validate_item(data, path):
                        packs[data["id"]] = data
                else:
                    for key, val in data.items():
                        if isinstance(val, dict) and "id" in val:
                            packs[val["id"]] = val
            elif isinstance(data, list):
                # ✅ your case — list of full KB entries
                for entry in data:
                    if isinstance(entry, dict) and "id" in entry:
                        if _validate_item(entry, path):
                            packs[entry["id"]] = entry
            else:
                print(f"[KB WARN] Unknown data format in {path}")

        except Exception as e:
            print(f"[KB ERROR] Failed to load {path}: {e}")

    print(f"[KB INFO] Loaded {len(packs)} knowledge entries.")
    return packs

def compile_packs(packs: Dict[str, Any]) -> list:
    compiled = []
    for _id, item in packs.items():
        if _id == "dtc_index":
            continue
        it = dict(item)
        it.setdefault("causes", [])
        it.setdefault("tiers", {})
        it.setdefault("dtc_bonus", [])
        it["_inc"] = []
        it["_exc"] = []
        compiled.append(it)
    return compiled
