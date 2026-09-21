"""Gemini-backed translation of already-anonymized text."""

from functools import lru_cache

from google import genai
from google.genai import errors, types

from app.models.analysis import SupportedLanguage
from app.utils.config import Settings, get_settings


class TranslationError(RuntimeError):
    """Raised when required translation is unavailable."""


class TranslationService:
    """Translate redacted non-English text while preserving mask tokens."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def translate_to_english(
        self,
        anonymized_text: str,
        language: SupportedLanguage,
    ) -> tuple[str, bool]:
        if language == "en":
            return anonymized_text, False

        api_key_secret = self._settings.gemini_api_key
        model = self._settings.gemini_text_model
        if (
            api_key_secret is None
            or not model
            or api_key_secret.get_secret_value().startswith("replace-")
            or model.startswith("replace-")
        ):
            raise TranslationError(
                "Translation requires GEMINI_API_KEY and GEMINI_TEXT_MODEL"
            )

        fallback_model = self._settings.gemini_text_fallback_model
        models = [model]
        if fallback_model and fallback_model not in models:
            models.append(fallback_model)

        client = genai.Client(api_key=api_key_secret.get_secret_value())
        last_error: Exception | None = None

        for index, candidate_model in enumerate(models):
            try:
                response = client.models.generate_content(
                    model=candidate_model,
                    contents=anonymized_text,
                    config=types.GenerateContentConfig(
                        system_instruction=(
                            "Translate the supplied already-anonymized wellbeing "
                            "text into natural English. Preserve bracketed privacy "
                            "tokens such as [PERSON], [PHONE], [EMAIL], [ADDRESS], "
                            "and [AADHAAR] exactly. Preserve emotional meaning. "
                            "Return only the translation without commentary."
                        ),
                    ),
                )
                translated = (response.text or "").strip()
                if not translated:
                    raise TranslationError("Gemini returned an empty translation")
                return translated, True
            except errors.APIError as exc:
                last_error = exc
                is_transient = exc.code in {429, 500, 502, 503, 504}
                has_fallback = index < len(models) - 1
                if is_transient and has_fallback:
                    continue
                break
            except TranslationError:
                raise
            except Exception as exc:
                last_error = exc
                break

        raise TranslationError("Gemini translation request failed") from last_error


@lru_cache
def get_translation_service() -> TranslationService:
    return TranslationService(get_settings())
