import os
import json
from openai import OpenAI
from core.response import error_response

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set in environment")

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_ai_response(prompt: str) -> dict:

    system_message = """
You are an expert automotive diagnostic assistant.

You MUST respond in valid JSON format:

{
  "recommendation": "clear actionable explanation",
  "confidence": number_between_0_and_1,
  "related_systems": ["list", "of", "systems"]
}

Do not include extra text.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            timeout=20
        )

        content = response.choices[0].message.content.strip()
        parsed = json.loads(content)

        return parsed

    except Exception:
        return {
            "recommendation": "AI temporarily unavailable. Please try again.",
            "confidence": 0.4,
            "related_systems": []
        }
