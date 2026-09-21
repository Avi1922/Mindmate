"""Voice conversation persistence models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class ConversationTurn(BaseModel):
    """One finalized user or assistant transcript turn."""

    role: Literal["user", "assistant"]
    text: str = Field(min_length=1, max_length=5_000)

    @field_validator("text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("Conversation turn cannot be blank")
        return normalized


class ConversationCreate(BaseModel):
    """Validated completed voice-session payload."""

    turns: list[ConversationTurn] = Field(min_length=1, max_length=100)
    started_at: datetime
    ended_at: datetime

    @model_validator(mode="after")
    def validate_conversation(self) -> "ConversationCreate":
        if self.started_at.tzinfo is None or self.ended_at.tzinfo is None:
            raise ValueError("Conversation timestamps must include a timezone")
        if self.ended_at < self.started_at:
            raise ValueError("Conversation cannot end before it starts")
        if not any(turn.role == "user" for turn in self.turns):
            raise ValueError("Conversation must include at least one user turn")
        if len(self.transcript()) > 10_000:
            raise ValueError("Conversation transcript exceeds 10,000 characters")
        return self

    def transcript(self) -> str:
        labels = {"user": "User", "assistant": "MindMate"}
        return "\n".join(f"{labels[turn.role]}: {turn.text}" for turn in self.turns)


class ConversationRecord(BaseModel):
    """Stored voice conversation returned to its authenticated owner."""

    id: str
    source: Literal["voice"] = "voice"
    transcript: str
    turns: list[ConversationTurn]
    started_at: datetime
    ended_at: datetime
    created_at: datetime


class ConversationListResponse(BaseModel):
    items: list[ConversationRecord]
    count: int
