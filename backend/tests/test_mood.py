"""Protected daily mood API tests."""

from datetime import date, datetime, timezone
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.auth import AuthenticatedUser
from app.models.mood import DailyMoodRecord
from app.services.daily_mood_service import (
    DailyMoodNotFoundError,
    get_daily_mood_service,
)
from app.utils.auth import get_current_user


pytestmark = pytest.mark.asyncio


class StubDailyMoodService:
    def __init__(self, missing: bool = False) -> None:
        self.missing = missing
        self.calls: list[tuple[str, date, str]] = []

    def _result(self, uid: str, target_date: date, operation: str) -> DailyMoodRecord:
        self.calls.append((uid, target_date, operation))
        if self.missing:
            raise DailyMoodNotFoundError("missing")
        return DailyMoodRecord(
            date=target_date,
            mood_score=58,
            dominant_emotion="sadness",
            emotions={
                "joy": 0.18,
                "sadness": 0.42,
                "anger": 0.12,
                "fear": 0.18,
                "neutral": 0.1,
            },
            journal_count=2,
            conversation_count=1,
            analysis_count=3,
            updated_at=datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc),
        )

    def get(self, uid: str, target_date: date) -> DailyMoodRecord:
        return self._result(uid, target_date, "get")

    def rebuild(self, uid: str, target_date: date) -> DailyMoodRecord:
        return self._result(uid, target_date, "rebuild")

    def list_recent(self, uid: str, days: int) -> list[DailyMoodRecord]:
        return [self._result(uid, date(2026, 9, 20), f"history-{days}")]


def override_user() -> AuthenticatedUser:
    return AuthenticatedUser(uid="user-123", email="person@example.com")


async def api_request(
    method: str,
    path: str,
    **kwargs: Any,
) -> tuple[int, dict[str, Any]]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.request(method, path, **kwargs)
    return response.status_code, response.json()


async def test_get_daily_mood_is_user_scoped() -> None:
    service = StubDailyMoodService()
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_daily_mood_service] = lambda: service
    try:
        status_code, body = await api_request(
            "GET", "/api/mood/daily?date=2026-09-20"
        )
    finally:
        app.dependency_overrides.clear()

    assert status_code == 200
    assert body["date"] == "2026-09-20"
    assert body["mood_score"] == 58
    assert body["analysis_count"] == 3
    assert service.calls == [("user-123", date(2026, 9, 20), "get")]


async def test_rebuild_daily_mood_is_idempotent_api() -> None:
    service = StubDailyMoodService()
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_daily_mood_service] = lambda: service
    try:
        status_code, body = await api_request(
            "POST",
            "/api/mood/daily/rebuild",
            json={"date": "2026-09-20"},
        )
    finally:
        app.dependency_overrides.clear()

    assert status_code == 200
    assert body["dominant_emotion"] == "sadness"
    assert service.calls == [("user-123", date(2026, 9, 20), "rebuild")]


async def test_daily_mood_history_returns_dashboard_window() -> None:
    service = StubDailyMoodService()
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_daily_mood_service] = lambda: service
    try:
        status_code, body = await api_request(
            "GET", "/api/mood/daily/history?days=7"
        )
    finally:
        app.dependency_overrides.clear()

    assert status_code == 200
    assert body["days"] == 7
    assert body["count"] == 1
    assert body["items"][0]["date"] == "2026-09-20"
    assert service.calls == [("user-123", date(2026, 9, 20), "history-7")]


async def test_daily_mood_returns_404_when_no_analyses_exist() -> None:
    service = StubDailyMoodService(missing=True)
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_daily_mood_service] = lambda: service
    try:
        status_code, body = await api_request(
            "GET", "/api/mood/daily?date=2026-09-20"
        )
    finally:
        app.dependency_overrides.clear()

    assert status_code == 404
    assert body == {"detail": "No mood analyses are available for this date"}


async def test_daily_mood_rejects_invalid_date() -> None:
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_daily_mood_service] = StubDailyMoodService
    try:
        status_code, body = await api_request(
            "GET", "/api/mood/daily?date=not-a-date"
        )
    finally:
        app.dependency_overrides.clear()

    assert status_code == 422
    assert body["detail"]


async def test_daily_mood_history_rejects_unbounded_window() -> None:
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_daily_mood_service] = StubDailyMoodService
    try:
        status_code, body = await api_request(
            "GET", "/api/mood/daily/history?days=31"
        )
    finally:
        app.dependency_overrides.clear()

    assert status_code == 422
    assert body["detail"]


async def test_daily_mood_requires_authentication() -> None:
    status_code, body = await api_request(
        "GET", "/api/mood/daily?date=2026-09-20"
    )

    assert status_code == 401
    assert body == {"detail": "Authentication required"}
