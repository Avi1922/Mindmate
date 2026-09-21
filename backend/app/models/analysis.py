"""Text-processing API models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

SupportedLanguage = Literal["en", "hi", "hinglish", "other", "unknown"]
AnalysisSource = Literal["journal", "conversation"]
EmotionLabel = Literal["joy", "sadness", "anger", "fear", "neutral"]


class AnalysisRequest(BaseModel):
    """Text submitted to the privacy-aware processing pipeline."""

    text: str = Field(min_length=1, max_length=10_000)
    source: AnalysisSource
    source_id: str | None = Field(default=None, min_length=1, max_length=128)

    @field_validator("text")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Text cannot be blank")
        return normalized


class PIIEntitySummary(BaseModel):
    """Counts of masked entity categories; never contains detected values."""

    type: str
    count: int = Field(ge=1)


class TextProcessingResponse(BaseModel):
    """Phase 7 output before emotion classification is added."""

    source: AnalysisSource
    original_text: str
    language: SupportedLanguage
    language_confidence: float = Field(ge=0, le=1)
    anonymized_text: str
    translated_text: str
    translation_applied: bool
    pii_entities: list[PIIEntitySummary]


class EmotionScores(BaseModel):
    """Validated five-label emotion probability distribution."""

    joy: float = Field(ge=0, le=1)
    sadness: float = Field(ge=0, le=1)
    anger: float = Field(ge=0, le=1)
    fear: float = Field(ge=0, le=1)
    neutral: float = Field(ge=0, le=1)


class AnalysisResponse(TextProcessingResponse):
    """Complete Phase 8 analysis result."""

    analysis_id: str
    source_id: str | None = None
    created_at: datetime
    emotions: EmotionScores
    dominant_emotion: EmotionLabel
    mood_score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    disclaimer: str = (
        "This is an application-level text-derived estimate, not a medical diagnosis."
    )
