"""Preference boundaries, auth, streaks and safe AI grounding."""

from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from app.main import app
from app.models.auth import AuthenticatedUser
from app.models.conversation import ConversationTurn
from app.models.profile import ProfilePreferences
from app.services import wellness_service
from app.utils.auth import get_current_user
from httpx import ASGITransport, AsyncClient


@pytest.mark.parametrize(
    "dates,today,current,longest",
    [
        (["2026-10-11", "2026-10-12"], date(2026, 10, 13), 2, 2),
        (["2026-10-09", "2026-10-10"], date(2026, 10, 13), 0, 2),
        (
            ["2026-10-11", "2026-10-12", "2026-10-13", "2026-10-13"],
            date(2026, 10, 13),
            3,
            3,
        ),
        ([], date(2026, 10, 13), 0, 0),
    ],
)
def test_streak_grace_missing_days_and_duplicates(dates, today, current, longest):
    result = wellness_service.calculate_streak(dates, today)
    assert result["current"] == current
    assert result["longest"] == longest
    assert result["checked_in_today"] == (today.isoformat() in dates)


@pytest.mark.asyncio
async def test_profile_auth_and_preference_validation(monkeypatch):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        assert (await client.get("/api/profile")).status_code == 401
        app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
            uid="owner"
        )
        save = Mock(side_effect=lambda uid, p: p)
        monkeypatch.setattr(wellness_service, "save_profile", save)
        try:
            response = await client.put(
                "/api/profile",
                json={"goal": "Manage everyday stress", "onboarding_complete": True},
            )
            assert response.status_code == 200
            assert save.call_args.args[0] == "owner"
            assert (
                await client.put("/api/profile", json={"personal_id": "123"})
            ).status_code == 422
            assert (
                await client.post(
                    "/api/assistant/chat",
                    json={"turns": [{"role": "assistant", "text": "hello"}]},
                )
            ).status_code == 422
            assert (await client.post("/api/mood/insight?days=31")).status_code == 422
        finally:
            app.dependency_overrides.clear()


def test_chat_masks_pii_before_provider(monkeypatch):
    monkeypatch.setattr(
        wellness_service, "read_profile", lambda uid: ProfilePreferences()
    )
    generate = Mock(return_value="A gentle reply")
    monkeypatch.setattr(wellness_service, "generate_reply", generate)
    wellness_service.chat_reply(
        "owner", [ConversationTurn(role="user", text="My email is private@example.com")]
    )
    content = generate.call_args.args[0][0].parts[0].text
    assert "private@example.com" not in content
    assert "[EMAIL]" in content


def test_insight_uses_stored_rules_without_provider_requests(monkeypatch):
    from app.services.mood_messages import mood_message

    record = SimpleNamespace(date=datetime.now(UTC).date(), mood_score=85)
    monkeypatch.setattr(
        wellness_service,
        "get_daily_mood_service",
        lambda: SimpleNamespace(list_recent=lambda uid, days: [record]),
    )
    generate = Mock()
    monkeypatch.setattr(wellness_service, "generate_reply", generate)
    assert (
        wellness_service.mood_insight("owner", 30)
        == mood_message(85)
        == "Your mood is great today."
    )
    generate.assert_not_called()


@pytest.mark.asyncio
async def test_ai_outage_returns_safe_error_and_profile_is_user_scoped(monkeypatch):
    from app.services.gemini_text import CompanionUnavailable

    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(uid="owner")
    monkeypatch.setattr(
        wellness_service,
        "read_profile",
        lambda uid: ProfilePreferences(goal="Build a reflection habit"),
    )
    monkeypatch.setattr(
        wellness_service,
        "chat_reply",
        Mock(
            side_effect=CompanionUnavailable("MindMate AI is temporarily unavailable.")
        ),
    )
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            assert (await client.get("/api/profile")).json()[
                "goal"
            ] == "Build a reflection habit"
            response = await client.post(
                "/api/assistant/chat",
                json={"turns": [{"role": "user", "text": "fixture"}]},
            )
            assert response.status_code == 503
            assert "temporarily unavailable" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
