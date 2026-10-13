"""Authenticated journal endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.concurrency import run_in_threadpool

from app.models.analysis import AnalysisResponse
from app.models.auth import AuthenticatedUser
from app.models.journal import JournalCreate, JournalListResponse, JournalRecord
from app.services.journal_service import (
    JournalService,
    JournalStorageError,
    get_journal_service,
)
from app.utils.auth import get_current_user

router = APIRouter(prefix="/journal", tags=["journal"])


@router.post(
    "",
    response_model=JournalRecord,
    status_code=status.HTTP_201_CREATED,
    summary="Create a journal entry",
)
async def create_journal(
    payload: JournalCreate,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    journals: Annotated[JournalService, Depends(get_journal_service)],
) -> JournalRecord:
    """Store raw journal text in the authenticated user's private collection."""

    try:
        return await run_in_threadpool(
            journals.create_journal,
            current_user.uid,
            payload.text,
        )
    except JournalStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Journal storage is temporarily unavailable",
        ) from exc


@router.get("", response_model=JournalListResponse, summary="List journal entries")
async def list_journals(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    journals: Annotated[JournalService, Depends(get_journal_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> JournalListResponse:
    """Return the authenticated user's newest journal entries first."""

    try:
        items = await run_in_threadpool(
            journals.list_journals,
            current_user.uid,
            limit,
        )
    except JournalStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Journal storage is temporarily unavailable",
        ) from exc

    return JournalListResponse(items=items, count=len(items))


@router.post("/{journal_id}/analysis")
async def analyze_existing_journal(
    journal_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> AnalysisResponse:
    from app.services.emotion_service import EmotionAnalysisError
    from app.services.journal_analysis_service import (
        JournalMissing,
        analyze_saved_journal,
    )
    from app.services.translation_service import TranslationError

    if not journal_id or len(journal_id) > 128 or "/" in journal_id:
        raise HTTPException(400, "Invalid journal ID")
    try:
        return await run_in_threadpool(
            analyze_saved_journal, current_user.uid, journal_id
        )
    except JournalMissing as exc:
        raise HTTPException(404, "Journal not found") from exc
    except (TranslationError, EmotionAnalysisError) as exc:
        raise HTTPException(
            503,
            "AI analysis is temporarily unavailable. Your journal is saved; retry analysis later.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            503, "Analysis could not be completed. Your journal is saved."
        ) from exc
