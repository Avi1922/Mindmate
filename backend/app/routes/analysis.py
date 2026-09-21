"""Privacy-aware text-processing endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool

from app.models.analysis import AnalysisRequest, AnalysisResponse
from app.models.auth import AuthenticatedUser
from app.services.analysis_service import (
    AnalysisService,
    AnalysisStorageError,
    get_analysis_service,
)
from app.services.emotion_service import EmotionAnalysisError
from app.services.translation_service import TranslationError
from app.utils.auth import get_current_user


router = APIRouter(prefix="/analyze", tags=["analysis"])


@router.post("", response_model=AnalysisResponse, summary="Analyze text safely")
async def analyze_text(
    payload: AnalysisRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    analyzer: Annotated[
        AnalysisService,
        Depends(get_analysis_service),
    ],
) -> AnalysisResponse:
    """Process, classify, score, and persist an authenticated user's text."""

    try:
        return await run_in_threadpool(
            analyzer.analyze,
            current_user.uid,
            payload.text,
            payload.source,
            payload.source_id,
        )
    except TranslationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Translation is temporarily unavailable",
        ) from exc
    except EmotionAnalysisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Emotion analysis is temporarily unavailable",
        ) from exc
    except AnalysisStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analysis storage is temporarily unavailable",
        ) from exc
