"""Shared API response models."""

from typing import Literal

from pydantic import BaseModel


class RootResponse(BaseModel):
    """Small discovery response for the API root."""

    name: str
    version: str
    docs_url: str


class HealthResponse(BaseModel):
    """Response returned by the health-check endpoint."""

    status: Literal["ok"]
    service: str
    environment: str
    version: str
