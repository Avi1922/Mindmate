"""Authenticated identity endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.models.auth import AuthenticatedUser
from app.utils.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/me", response_model=AuthenticatedUser, summary="Get current user")
async def read_current_user(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> AuthenticatedUser:
    """Return identity claims from a verified Firebase ID token."""

    return current_user
