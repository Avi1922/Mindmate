"""Daily mood aggregation API models."""

from datetime import date as Date
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.analysis import EmotionLabel, EmotionScores


class DailyMoodRequest(BaseModel):
    """Optional date for rebuilding a daily mood record."""

    date: Date | None = None


class DailyMoodRecord(BaseModel):
    """One explainable, non-diagnostic daily mood summary."""

    date: Date
    mood_score: int = Field(ge=0, le=100)
    dominant_emotion: EmotionLabel
    emotions: EmotionScores
    journal_count: int = Field(ge=0)
    conversation_count: int = Field(ge=0)
    analysis_count: int = Field(ge=1)
    updated_at: datetime
    disclaimer: str = (
        "This is an application-level text-derived estimate, not a medical diagnosis."
    )


class DailyMoodListResponse(BaseModel):
    """A bounded series of daily mood records for dashboard charts."""

    count: int = Field(ge=0)
    days: int = Field(ge=1, le=30)
    items: list[DailyMoodRecord]
