"""Gemini Live ephemeral-token provisioning tests."""

from types import SimpleNamespace

import pytest
from app.services.live_token_service import LiveTokenError, LiveTokenService
from app.utils.config import Settings


class FakeAuthTokens:
    def __init__(self) -> None:
        self.config: dict[str, object] | None = None

    def create(self, *, config: dict[str, object]) -> SimpleNamespace:
        self.config = config
        return SimpleNamespace(name="auth_tokens/test-single-use-token")


class FakeClient:
    def __init__(self) -> None:
        self.auth_tokens = FakeAuthTokens()


def test_live_token_is_single_use_and_configuration_locked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = FakeClient()
    monkeypatch.setattr(
        "app.services.live_token_service.genai.Client",
        lambda **_: fake_client,
    )
    service = LiveTokenService(
        Settings(
            _env_file=None,
            gemini_api_key="test-api-key",
            gemini_live_model="gemini-3.8-live",
        )
    )

    result = service.create_token()

    assert result.token == "auth_tokens/test-single-use-token"
    assert result.model == "gemini-3.8-live"
    assert fake_client.auth_tokens.config is not None
    assert fake_client.auth_tokens.config["uses"] == 1
    constraints = fake_client.auth_tokens.config["live_connect_constraints"]
    assert isinstance(constraints, dict)
    assert constraints["model"] == "gemini-3.8-live"
    config = constraints["config"]
    assert isinstance(config, dict)
    assert config["response_modalities"] == ["AUDIO"]
    assert config["input_audio_transcription"] == {}
    assert config["output_audio_transcription"] == {}
    assert "diagnose" in str(config["system_instruction"])


def test_live_token_requires_server_configuration() -> None:
    service = LiveTokenService(
        Settings(_env_file=None, gemini_api_key=None, gemini_live_model=None)
    )

    with pytest.raises(LiveTokenError, match="not configured"):
        service.create_token()
