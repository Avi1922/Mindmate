"""Authenticated voice conversation persistence endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.concurrency import run_in_threadpool

from app.models.auth import AuthenticatedUser
from app.models.conversation import (
    ConversationCreate,
    ConversationListResponse,
    ConversationRecord,
)
from app.services.conversation_service import (
    ConversationService,
    ConversationStorageError,
    get_conversation_service,
)
from app.utils.auth import get_current_user

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post(
    "",
    response_model=ConversationRecord,
    status_code=status.HTTP_201_CREATED,
    summary="Save a completed voice conversation",
)
async def create_conversation(
    payload: ConversationCreate,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    conversations: Annotated[ConversationService, Depends(get_conversation_service)],
) -> ConversationRecord:
    """Store a validated transcript for the authenticated user."""

    try:
        return await run_in_threadpool(
            conversations.create_conversation,
            current_user.uid,
            payload.turns,
            payload.transcript(),
            payload.started_at,
            payload.ended_at,
        )
    except ConversationStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Conversation storage is temporarily unavailable",
        ) from exc


@router.get(
    "",
    response_model=ConversationListResponse,
    summary="List saved voice conversations",
)
async def list_conversations(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    conversations: Annotated[ConversationService, Depends(get_conversation_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ConversationListResponse:
    """Return the authenticated user's newest conversations first."""

    try:
        items = await run_in_threadpool(
            conversations.list_conversations,
            current_user.uid,
            limit,
        )
    except ConversationStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Conversation storage is temporarily unavailable",
        ) from exc
    return ConversationListResponse(items=items, count=len(items))
