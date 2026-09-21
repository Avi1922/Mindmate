"""Authenticated daily mood endpoints."""

from datetime import date, datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.concurrency import run_in_threadpool

from app.models.auth import AuthenticatedUser
from app.models.mood import DailyMoodListResponse, DailyMoodRecord, DailyMoodRequest
from app.services.daily_mood_service import (
    DailyMoodNotFoundError,
    DailyMoodService,
    DailyMoodStorageError,
    get_daily_mood_service,
)
from app.utils.auth import get_current_user


router = APIRouter(prefix="/mood/daily", tags=["mood"])


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


@router.get(
    "/history",
    response_model=DailyMoodListResponse,
    summary="Get recent daily mood records",
)
async def get_daily_mood_history(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    service: Annotated[DailyMoodService, Depends(get_daily_mood_service)],
    days: Annotated[int, Query(ge=1, le=30)] = 7,
) -> DailyMoodListResponse:
    """Return existing daily records from the latest UTC date window."""

    try:
        items = await run_in_threadpool(
            service.list_recent,
            current_user.uid,
            days,
        )
        return DailyMoodListResponse(count=len(items), days=days, items=items)
    except DailyMoodStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Daily mood storage is temporarily unavailable",
        ) from exc


@router.get("", response_model=DailyMoodRecord, summary="Get a daily mood record")
async def get_daily_mood(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    service: Annotated[DailyMoodService, Depends(get_daily_mood_service)],
    target_date: Annotated[date | None, Query(alias="date")] = None,
) -> DailyMoodRecord:
    """Return the requested UTC date, defaulting to today."""

    try:
        return await run_in_threadpool(
            service.get,
            current_user.uid,
            target_date or _utc_today(),
        )
    except DailyMoodNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No mood analyses are available for this date",
        ) from exc
    except DailyMoodStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Daily mood storage is temporarily unavailable",
        ) from exc


@router.post("/rebuild", response_model=DailyMoodRecord, summary="Rebuild a daily mood record")
async def rebuild_daily_mood(
    payload: DailyMoodRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    service: Annotated[DailyMoodService, Depends(get_daily_mood_service)],
) -> DailyMoodRecord:
    """Idempotently recompute a UTC date from its saved analyses."""

    try:
        return await run_in_threadpool(
            service.rebuild,
            current_user.uid,
            payload.date or _utc_today(),
        )
    except DailyMoodNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No mood analyses are available for this date",
        ) from exc
    except DailyMoodStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Daily mood storage is temporarily unavailable",
        ) from exc
