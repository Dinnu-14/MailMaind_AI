"""Minimal Gemini REST client. Never fakes success: errors are raised to the caller."""
import json
import re
import time

import httpx

from app.core.config import settings

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
_BREAKER_SECONDS = 60
_failed_at: float = 0.0
last_error: str | None = None


class GeminiError(Exception):
    pass


def is_configured() -> bool:
    return settings.gemini_configured


def is_available() -> bool:
    """Configured and not in the short cool-down after a failure."""
    return is_configured() and (time.time() - _failed_at) > _BREAKER_SECONDS


def generate_json(prompt: str, system: str | None = None, timeout: float = 45.0):
    """Call Gemini and return parsed JSON. Raises GeminiError on any failure."""
    global _failed_at, last_error
    if not is_configured():
        raise GeminiError("GEMINI_API_KEY is not set")
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
    }
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}
    try:
        resp = httpx.post(
            API_URL.format(model=settings.gemini_model),
            params={"key": settings.gemini_api_key},
            json=payload,
            timeout=timeout,
        )
        if resp.status_code != 200:
            raise GeminiError(f"Gemini API returned HTTP {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        result = parse_json_text(text)
        last_error = None
        return result
    except GeminiError as e:
        _failed_at, last_error = time.time(), str(e)
        raise
    except Exception as e:  # network errors, malformed payloads, bad JSON
        _failed_at, last_error = time.time(), f"{type(e).__name__}: {e}"[:300]
        raise GeminiError(last_error) from e


def parse_json_text(text: str):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    return json.loads(text)
