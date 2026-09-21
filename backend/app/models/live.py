"""Gemini Live session credential models."""

from datetime import datetime

from pydantic import BaseModel


class LiveTokenResponse(BaseModel):
    """Short-lived, single-use browser credential for Gemini Live."""

    token: str
    model: str
    expires_at: datetime
    new_session_expires_at: datetime
