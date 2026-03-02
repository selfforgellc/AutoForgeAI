from typing import Dict, Optional, List
from datetime import datetime

# --------------------------------------------------
# In-Memory Session Store
# --------------------------------------------------

# Structure:
# {
#   vehicle_id: {
#       "history": [
#           {"role": "user", "content": "..."},
#           {"role": "assistant", "content": "..."}
#       ],
#       "last_updated": datetime
#   }
# }

_session_store: Dict[str, Dict] = {}


# --------------------------------------------------
# Add Message To Session
# --------------------------------------------------

def add_session_message(vehicle_id: str, role: str, content: str) -> None:
    if vehicle_id not in _session_store:
        _session_store[vehicle_id] = {
            "history": [],
            "last_updated": datetime.utcnow()
        }

    _session_store[vehicle_id]["history"].append({
        "role": role,
        "content": content
    })

    _session_store[vehicle_id]["last_updated"] = datetime.utcnow()


# --------------------------------------------------
# Get Session Context
# --------------------------------------------------

def get_session_context(vehicle_id: str) -> Optional[List[Dict]]:
    """
    Returns conversation history for a vehicle.
    """

    session = _session_store.get(vehicle_id)

    if not session:
        return None

    return session.get("history", [])


# --------------------------------------------------
# Clear Session
# --------------------------------------------------

def clear_session(vehicle_id: str) -> None:
    if vehicle_id in _session_store:
        del _session_store[vehicle_id]
