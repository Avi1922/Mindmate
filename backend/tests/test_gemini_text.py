"""Bounded fallback behavior without spending provider quota."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest
from app.services import gemini_text
from google.genai import errors
from pydantic import SecretStr


def setup_client(monkeypatch, side_effect):
    monkeypatch.setattr(
        gemini_text,
        "get_settings",
        lambda: SimpleNamespace(
            gemini_api_key=SecretStr("test-key"),
            gemini_text_model="primary",
            gemini_text_fallback_model="fallback",
        ),
    )
    client = MagicMock()
    client.__enter__.return_value = client
    client.models.generate_content.side_effect = side_effect
    constructor = MagicMock(return_value=client)
    monkeypatch.setattr(gemini_text.genai, "Client", constructor)
    return client, constructor


def test_temporary_provider_error_uses_fallback(monkeypatch):
    client, constructor = setup_client(
        monkeypatch,
        [
            errors.ServerError(503, {"message": "busy"}),
            SimpleNamespace(text="A helpful reflection"),
        ],
    )
    assert (
        gemini_text.generate_reply("fixture", "instruction") == "A helpful reflection"
    )
    assert [
        c.kwargs["model"] for c in client.models.generate_content.call_args_list
    ] == ["primary", "fallback"]
    assert constructor.call_args.kwargs["http_options"].timeout == 12000
    assert constructor.call_args.kwargs["http_options"].retry_options.attempts == 1
    client.__exit__.assert_called_once()


def test_invalid_key_is_not_retried(monkeypatch):
    client, _ = setup_client(
        monkeypatch, [errors.ClientError(400, {"message": "invalid key"})]
    )
    with pytest.raises(gemini_text.CompanionUnavailable):
        gemini_text.generate_reply("fixture", "instruction")
    assert client.models.generate_content.call_count == 1


def test_timeout_and_empty_fallback_fail_safely(monkeypatch):
    client, _ = setup_client(
        monkeypatch, [httpx.ReadTimeout("timeout"), SimpleNamespace(text="")]
    )
    with pytest.raises(gemini_text.CompanionUnavailable):
        gemini_text.generate_reply("fixture", "instruction")
    assert client.models.generate_content.call_count == 2
