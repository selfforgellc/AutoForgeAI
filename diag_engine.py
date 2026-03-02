import uuid
from datetime import datetime
from typing import Optional, List, Dict

from rag import retrieve_context
from ai.core import generate_ai_response
from session_manager import add_session_message


def run_diagnosis(
    vehicle_id: str,
    symptoms: Optional[List[str]] = None,
    chat_input: Optional[str] = None,
    obd_codes: Optional[List[str]] = None,
    context: Optional[List[Dict]] = None
) -> Dict:

    combined_input = ""

    if symptoms:
        combined_input += f"Symptoms: {', '.join(symptoms)}.\n"

    if obd_codes:
        combined_input += f"OBD Codes: {', '.join(obd_codes)}.\n"

    if chat_input:
        combined_input += f"User Notes: {chat_input}.\n"

    if not combined_input.strip():
        return None

    # Add to session history
    add_session_message(vehicle_id, "user", combined_input)

    rag_context = retrieve_context(combined_input)

    prompt = f"""
You are an automotive diagnostic assistant.

Relevant Knowledge:
{rag_context}

Conversation History:
{context}

User Input:
{combined_input}

Respond with JSON:
{{
  "recommendation": "...",
  "confidence": 0.0-1.0,
  "related_systems": ["..."]
}}
"""

    ai_response = generate_ai_response(prompt)

    recommendation = ai_response.get("recommendation", "Further inspection recommended.")
    confidence = float(ai_response.get("confidence", 0.65))
    confidence = max(0.0, min(confidence, 1.0))
    related_systems = ai_response.get("related_systems", [])

    # Save assistant reply in session
    add_session_message(vehicle_id, "assistant", recommendation)

    return {
        "diagnosis_id": str(uuid.uuid4()),
        "recommendation": recommendation,
        "confidence": confidence,
        "related_systems": related_systems,
        "created_at": datetime.utcnow().isoformat()
    }
