"""Gemini-backed incident triage."""

import json as _json
import re as _re
from pathlib import Path as _Path

from google import genai as _genai

from config import GEMINI_API_KEY as _GEMINI_API_KEY


_FALLBACK = {
    "decision": "escalate",
    "message": "Automated triage failed to produce a valid response, routed to human.",
}
_PROMPT_TEMPLATE = (_Path(__file__).resolve().parent / "prompt.txt").read_text(
    encoding="utf-8"
)
_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "decision": {
            "type": "string",
            "enum": ["respond", "ask", "escalate"],
            "description": (
                "Apply the prompt's decision rules strictly: respond requires both a "
                "clear knowledge-base topic match and concrete ticket details sufficient "
                "to apply that exact fix; ask when a topic seems to match but the ticket's "
                "supporting details are vague or absent; escalate only when no topic matches."
            ),
        },
        "message": {"type": "string"},
    },
    "required": ["decision", "message"],
    "additionalProperties": False,
}
_VALID_DECISIONS = {"respond", "ask", "escalate"}
_PROMPT_PLACEHOLDER = _re.compile(r"\{(short_description|description)\}")
_client = _genai.Client(api_key=_GEMINI_API_KEY)

__all__ = ["get_decision"]


async def get_decision(short_description: str, description: str) -> dict:
    """Return Gemini's strictly validated triage decision for a ticket."""
    rendered_description = description or "(none provided)"
    prompt_values = {
        "short_description": short_description,
        "description": rendered_description,
    }
    prompt = _PROMPT_PLACEHOLDER.sub(
        lambda match: prompt_values[match.group(1)],
        _PROMPT_TEMPLATE,
    )

    try:
        response = await _client.aio.interactions.create(
            model="gemini-3.6-flash",
            input=prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": _RESPONSE_SCHEMA,
            },
        )
        result = _json.loads(response.output_text)

        if type(result) is not dict:
            return _FALLBACK.copy()
        if set(result) != {"decision", "message"}:
            return _FALLBACK.copy()
        if result["decision"] not in _VALID_DECISIONS:
            return _FALLBACK.copy()
        if not isinstance(result["message"], str):
            return _FALLBACK.copy()

        return {
            "decision": result["decision"],
            "message": result["message"],
        }
    except Exception:
        return _FALLBACK.copy()
