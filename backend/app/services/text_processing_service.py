"""Orchestration for the Phase 7 privacy-aware text pipeline."""

from functools import lru_cache

from app.models.analysis import (
    AnalysisSource,
    PIIEntitySummary,
    TextProcessingResponse,
)
from app.services.language_service import LanguageService
from app.services.pii_service import PIIService
from app.services.translation_service import (
    TranslationService,
    get_translation_service,
)


class TextProcessingService:
    def __init__(
        self,
        language: LanguageService,
        pii: PIIService,
        translation: TranslationService,
    ) -> None:
        self._language = language
        self._pii = pii
        self._translation = translation

    def process(self, text: str, source: AnalysisSource) -> TextProcessingResponse:
        detection = self._language.detect(text)
        masked = self._pii.mask(text)
        translated_text, translation_applied = self._translation.translate_to_english(
            masked.anonymized_text,
            detection.language,
        )

        entity_summaries = [
            PIIEntitySummary(type=entity_type, count=count)
            for entity_type, count in sorted(masked.entity_counts.items())
        ]

        return TextProcessingResponse(
            source=source,
            original_text=text,
            language=detection.language,
            language_confidence=detection.confidence,
            anonymized_text=masked.anonymized_text,
            translated_text=translated_text,
            translation_applied=translation_applied,
            pii_entities=entity_summaries,
        )


@lru_cache
def get_text_processing_service() -> TextProcessingService:
    return TextProcessingService(
        language=LanguageService(),
        pii=PIIService(),
        translation=get_translation_service(),
    )
