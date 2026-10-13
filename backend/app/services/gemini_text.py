"""Bounded Gemini requests shared by reflective features."""

import logging

import httpx
from google import genai
from google.genai import errors, types

from app.utils.config import get_settings

logger = logging.getLogger(__name__)


class CompanionUnavailable(RuntimeError):
    pass


def generate_reply(contents: object, instruction: str) -> str:
    settings = get_settings()
    if not settings.gemini_api_key or not settings.gemini_text_model:
        raise CompanionUnavailable("AI companion is not configured")
    models = list(
        dict.fromkeys(
            filter(
                None, [settings.gemini_text_model, settings.gemini_text_fallback_model]
            )
        )
    )
    with genai.Client(
        api_key=settings.gemini_api_key.get_secret_value(),
        http_options=types.HttpOptions(
            timeout=12000, retry_options=types.HttpRetryOptions(attempts=1)
        ),
    ) as client:
        for model in models:
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=instruction, max_output_tokens=600
                    ),
                )
                if response.text and response.text.strip():
                    return response.text.strip()
            except errors.APIError as exc:
                logger.warning(
                    "Gemini request failed model=%s code=%s", model, exc.code
                )
                if exc.code not in {429, 500, 502, 503, 504}:
                    break
            except (httpx.TimeoutException, TimeoutError):
                logger.warning("Gemini request timed out model=%s", model)
                continue
            except Exception:
                logger.warning("Gemini request did not complete model=%s", model)
    raise CompanionUnavailable(
        "MindMate AI is temporarily unavailable. Please try again later."
    )
