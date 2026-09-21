"""Text-processing orchestration tests."""

from app.services.language_service import LanguageService
from app.services.pii_service import PIIService
from app.services.text_processing_service import TextProcessingService


class StubTranslationService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def translate_to_english(self, text: str, language: str) -> tuple[str, bool]:
        self.calls.append((text, language))
        if language == "en":
            return text, False
        return "Today my day was very bad.", True


def test_pipeline_masks_before_translation() -> None:
    translation = StubTranslationService()
    processor = TextProcessingService(
        language=LanguageService(),
        pii=PIIService(),
        translation=translation,  # type: ignore[arg-type]
    )

    result = processor.process(
        "Mera naam Rahul Sharma hai. Aaj mera din bahut kharab tha.",
        "journal",
    )

    assert result.language == "hinglish"
    assert result.anonymized_text.startswith("Mera naam [PERSON] hai")
    assert translation.calls[0][0] == result.anonymized_text
    assert "Rahul Sharma" not in translation.calls[0][0]
    assert result.translation_applied is True


def test_english_pipeline_does_not_mark_translation_applied() -> None:
    translation = StubTranslationService()
    processor = TextProcessingService(
        language=LanguageService(),
        pii=PIIService(),
        translation=translation,  # type: ignore[arg-type]
    )

    result = processor.process(
        "Email me at private@example.com. I felt hopeful today.",
        "journal",
    )

    assert result.language == "en"
    assert result.translated_text == result.anonymized_text
    assert result.translation_applied is False
    assert result.pii_entities[0].type == "EMAIL"
