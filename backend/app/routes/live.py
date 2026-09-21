"""Authenticated Gemini Live session bootstrap endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool

from app.models.auth import AuthenticatedUser
from app.models.live import LiveTokenResponse
from app.services.live_token_service import (
    LiveTokenError,
    LiveTokenService,
    get_live_token_service,
)
from app.utils.auth import get_current_user


router = APIRouter(prefix="/live", tags=["live"])


@router.post(
    "/token",
    response_model=LiveTokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a short-lived Gemini Live token",
)
async def create_live_token(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    service: Annotated[LiveTokenService, Depends(get_live_token_service)],
) -> LiveTokenResponse:
    """Provision one constrained token for the authenticated user."""

    del current_user  # Authentication is required; no user data is sent to Gemini here.
    try:
        return await run_in_threadpool(service.create_token)
    except LiveTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini Live is temporarily unavailable",
        ) from exc
