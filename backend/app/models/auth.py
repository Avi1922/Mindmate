"""Authentication-related API models."""

from pydantic import BaseModel


class AuthenticatedUser(BaseModel):
    """Safe subset of claims returned for an authenticated Firebase user."""

    uid: str
    email: str | None = None
    email_verified: bool = False
