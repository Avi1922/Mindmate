"""Firebase Admin initialization and ID-token verification."""

from functools import lru_cache
from typing import Any

import firebase_admin
from firebase_admin import auth, credentials, firestore
from google.cloud.firestore_v1 import Client

from app.utils.config import Settings, get_settings


class FirebaseConfigurationError(RuntimeError):
    """Raised when Firebase Admin credentials are missing or invalid."""


class FirebaseAuthenticationError(RuntimeError):
    """Raised when a Firebase ID token cannot be trusted."""


class FirebaseService:
    """Small boundary around privileged Firebase Admin operations."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _get_app(self) -> firebase_admin.App:
        try:
            return firebase_admin.get_app()
        except ValueError:
            pass

        project_id = self._settings.firebase_project_id
        client_email = self._settings.firebase_client_email
        private_key_secret = self._settings.firebase_private_key

        if not project_id or not client_email or not private_key_secret:
            raise FirebaseConfigurationError(
                "Firebase Admin credentials are not completely configured"
            )

        private_key = private_key_secret.get_secret_value().replace("\\n", "\n")
        certificate = credentials.Certificate(
            {
                "type": "service_account",
                "project_id": project_id,
                "private_key": private_key,
                "client_email": client_email,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        )

        return firebase_admin.initialize_app(certificate, {"projectId": project_id})

    def verify_id_token(self, token: str) -> dict[str, Any]:
        """Verify a client ID token and return its trusted claims."""

        try:
            return auth.verify_id_token(token, app=self._get_app())
        except FirebaseConfigurationError:
            raise
        except (
            auth.InvalidIdTokenError,
            auth.ExpiredIdTokenError,
            auth.RevokedIdTokenError,
        ) as exc:
            raise FirebaseAuthenticationError(
                "Invalid or expired Firebase ID token"
            ) from exc
        except Exception as exc:
            # Do not leak certificate, token, or upstream verification details.
            raise FirebaseAuthenticationError(
                "Firebase token verification failed"
            ) from exc

    def get_firestore_client(self) -> Client:
        """Return an Admin-authenticated Firestore client."""

        try:
            return firestore.client(app=self._get_app())
        except FirebaseConfigurationError:
            raise
        except Exception as exc:
            raise FirebaseConfigurationError(
                "Firestore client could not be initialized"
            ) from exc


@lru_cache
def get_firebase_service() -> FirebaseService:
    """Return the process-wide Firebase service."""

    return FirebaseService(get_settings())
