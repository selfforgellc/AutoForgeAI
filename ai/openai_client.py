# backend/ai/openai_client.py
import os
import json
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_DEFAULT_MODEL = (os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip() or "gpt-4o-mini"
_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.25"))
_TIMEOUT_S = int(os.getenv("OPENAI_TIMEOUT_S", "60"))


class OpenAIConfigError(RuntimeError):
    pass


def _client() -> OpenAI:
    key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not key:
        raise OpenAIConfigError(
            "OPENAI_API_KEY is missing. Put it in backend/.env (exact filename) and restart uvicorn."
        )
    return OpenAI(api_key=key, timeout=_TIMEOUT_S)


def _parse_json_strict(content: str) -> Dict[str, Any]:
    if not content:
        raise ValueError("Empty model response")
    c = content.strip()

    # Clean common fences if they appear (shouldn't with response_format, but just in case)
    if c.startswith("```"):
        c = c.strip("`").strip()
        if c.lower().startswith("json"):
            c = c[4:].strip()

    return json.loads(c)


def chat_json(
    *,
    system_prompt: str,
    user_prompt: str,
    model: Optional[str] = None,
    max_output_tokens: int = 900,
) -> Dict[str, Any]:
    """
    JSON-only OpenAI call with one retry if output is invalid/truncated.
    Uses response_format json_object to force JSON.
    """
    client = _client()
    mdl = (model or _DEFAULT_MODEL).strip() or _DEFAULT_MODEL

    def _call(sys_text: str) -> str:
        resp = client.chat.completions.create(
            model=mdl,
            messages=[
                {"role": "system", "content": sys_text},
                {"role": "user", "content": user_prompt},
            ],
            temperature=_TEMPERATURE,
            max_tokens=max_output_tokens,
            response_format={"type": "json_object"},
        )
        return (resp.choices[0].message.content or "").strip()

    # Attempt 1
    content = _call(system_prompt)
    try:
        return _parse_json_strict(content)
    except Exception:
        # Retry once with stricter "compact" requirement to prevent truncation
        retry_system = (
            system_prompt
            + "\n\nIMPORTANT: Return COMPACT JSON. Keep strings short. "
              "Do not pretty-print. Keep lists within the required counts. "
              "Close all quotes/braces."
        )
        content2 = _call(retry_system)
        try:
            return _parse_json_strict(content2)
        except Exception as e:
            raise RuntimeError(
                f"Model did not return valid JSON. First 240 chars: {content2[:240]!r}"
            ) from e
