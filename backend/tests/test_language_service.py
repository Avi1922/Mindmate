"""Language detection tests for supported MVP inputs."""

import pytest
from app.services.language_service import LanguageService


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("I had a really stressful day at work.", "en"),
        ("आज मेरा दिन बहुत खराब था।", "hi"),
        ("Aaj mera din bahut stressful tha", "hinglish"),
        ("Yaar aaj bahut stress ho raha hai.", "hinglish"),
        ("आज work बहुत stressful था।", "hinglish"),
    ],
)
def test_detect_supported_languages(text: str, expected: str) -> None:
    result = LanguageService().detect(text)

    assert result.language == expected
    assert 0 <= result.confidence <= 1


def test_language_detection_is_deterministic() -> None:
    service = LanguageService()

    first = service.detect("I felt peaceful after my evening walk.")
    second = service.detect("I felt peaceful after my evening walk.")

    assert first == second
