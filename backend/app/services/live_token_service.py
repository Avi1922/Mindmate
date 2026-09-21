"""Secure provisioning of constrained Gemini Live ephemeral tokens."""

from datetime import UTC, datetime, timedelta
from functools import lru_cache

from google import genai
from google.genai import types

from app.models.live import LiveTokenResponse
from app.utils.config import Settings, get_settings


class LiveTokenError(RuntimeError):
    """Raised when a usable Gemini Live token cannot be provisioned."""


SYSTEM_INSTRUCTION = (
    "You are MindMate, a warm and concise wellbeing reflection companion. "
    "Listen carefully, ask one gentle question at a time, and help the user "
    "name feelings without judging them. Never diagnose a medical or mental "
    "health condition, claim clinical certainty, or present yourself as a "
    "replacement for a qualified professional. If the user describes immediate "
    "danger, encourage them to contact local emergency services or a trusted "
    "person nearby. Respond naturally in the language the user speaks."
)


class LiveTokenService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create_token(self) -> LiveTokenResponse:
        api_key = self._settings.gemini_api_key
        model = self._settings.gemini_live_model
        if api_key is None or not model:
            raise LiveTokenError("Gemini Live is not configured")

        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=15)
        new_session_expires_at = now + timedelta(minutes=1)

        try:
            client = genai.Client(
                api_key=api_key.get_secret_value(),
                http_options=types.HttpOptions(api_version="v1beta"),
            )
            token = client.auth_tokens.create(
                config={
                    "uses": 1,
                    "expire_time": expires_at,
                    "new_session_expire_time": new_session_expires_at,
                    "live_connect_constraints": {
                        "model": model,
                        "config": {
                            "response_modalities": ["AUDIO"],
                            "system_instruction": SYSTEM_INSTRUCTION,
                            "input_audio_transcription": {},
                            "output_audio_transcription": {},
                        },
                    },
                    "lock_additional_fields": [],
                }
            )
            if not token.name:
                raise LiveTokenError("Gemini returned an empty Live token")
            return LiveTokenResponse(
                token=token.name,
                model=model,
                expires_at=expires_at,
                new_session_expires_at=new_session_expires_at,
            )
        except LiveTokenError:
            raise
        except Exception as exc:
            raise LiveTokenError("Gemini Live token provisioning failed") from exc


@lru_cache
def get_live_token_service() -> LiveTokenService:
    return LiveTokenService(get_settings())
