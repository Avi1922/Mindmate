"""Operational health endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app import __version__
from app.models.common import HealthResponse
from app.utils.config import Settings, get_settings


router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse, summary="Check API health")
async def health_check(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse:
    """Confirm that the API process and settings layer are available."""

    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
        version=__version__,
    )
