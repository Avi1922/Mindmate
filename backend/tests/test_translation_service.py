"""Gemini translation routing tests without external API calls."""

from types import SimpleNamespace

from google.genai import errors
from pydantic import SecretStr

from app.services import translation_service as translation_module
from app.services.translation_service import TranslationService
from app.utils.config import Settings


class FakeModels:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def generate_content(self, *, model: str, **_: object) -> SimpleNamespace:
        self.calls.append(model)
        if model == "gemini-3.8-flash":
            raise errors.ServerError(
                503,
                {"error": {"code": 503, "status": "UNAVAILABLE"}},
            )
        return SimpleNamespace(text="Today was very stressful.")


class FakeClient:
    def __init__(self) -> None:
        self.models = FakeModels()


def test_non_english_translation_uses_fallback_on_transient_error(monkeypatch) -> None:
    client = FakeClient()
    monkeypatch.setattr(translation_module.genai, "Client", lambda **_: client)
    service = TranslationService(
        Settings(
            gemini_api_key=SecretStr("test-key"),
            gemini_text_model="gemini-3.8-flash",
            gemini_text_fallback_model="gemini-3.5-flash-lite",
        )
    )

    translated, applied = service.translate_to_english(
        "Aaj bahut stress tha.",
        "hinglish",
    )

    assert translated == "Today was very stressful."
    assert applied is True
    assert client.models.calls == ["gemini-3.8-flash", "gemini-3.5-flash-lite"]


def test_english_does_not_call_gemini(monkeypatch) -> None:
    monkeypatch.setattr(
        translation_module.genai,
        "Client",
        lambda **_: (_ for _ in ()).throw(AssertionError("Gemini should not be called")),
    )
    service = TranslationService(Settings())

    translated, applied = service.translate_to_english("I feel calm.", "en")

    assert translated == "I feel calm."
    assert applied is False
