"""Smoke tests for the Phase 3 FastAPI skeleton."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.utils.config import get_settings


pytestmark = pytest.mark.asyncio


async def test_root_points_to_api_documentation() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert response.json()["docs_url"] == "/docs"
    assert response.json()["name"] == "MindMate API"


async def test_health_check() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "MindMate API",
        "environment": get_settings().app_env,
        "version": "0.1.0",
    }
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["permissions-policy"] == (
        "camera=(), geolocation=(), microphone=()"
    )
    assert response.headers["content-security-policy"] == (
        "default-src 'none'; frame-ancestors 'none'"
    )
    assert response.headers["x-request-id"]


async def test_valid_request_id_is_preserved_for_support_correlation() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/health", headers={"X-Request-ID": "client-request-123"}
        )

    assert response.headers["x-request-id"] == "client-request-123"


async def test_oversized_declared_request_is_rejected_before_processing() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/journal",
            content=b"{}",
            headers={"Content-Length": "65537"},
        )

    assert response.status_code == 413
    assert response.json() == {"detail": "Request body is too large"}
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-request-id"]


async def test_cors_preflight_allows_configured_frontend() -> None:
    origin = get_settings().frontend_origin
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.options(
            "/api/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-credentials"] == "true"


async def test_cors_preflight_rejects_unknown_origin() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.options(
            "/api/health",
            headers={
                "Origin": "https://attacker.example",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
