"""Journal API request and response models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class JournalCreate(BaseModel):
    """Validated journal submission."""

    text: str = Field(min_length=1, max_length=10_000)

    @field_validator("text")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Journal text cannot be blank")
        return normalized


class JournalRecord(BaseModel):
    """Journal entry returned to its owner."""

    id: str
    text: str
    source: Literal["journal"] = "journal"
    created_at: datetime


class JournalListResponse(BaseModel):
    """Recent journal entries for the authenticated user."""

    items: list[JournalRecord]
    count: int
