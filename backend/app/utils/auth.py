"""FastAPI authentication dependencies."""

from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.concurrency import run_in_threadpool
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.models.auth import AuthenticatedUser
from app.services.firebase_service import (
    FirebaseAuthenticationError,
    FirebaseConfigurationError,
    FirebaseService,
    get_firebase_service,
)


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    authorization: Annotated[
        HTTPAuthorizationCredentials | None,
        Security(bearer_scheme),
    ],
    firebase: Annotated[FirebaseService, Depends(get_firebase_service)],
) -> AuthenticatedUser:
    """Verify the bearer token and expose only trusted identity claims."""

    if authorization is None or authorization.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        claims = await run_in_threadpool(
            firebase.verify_id_token,
            authorization.credentials,
        )
    except FirebaseConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is not configured",
        ) from exc
    except FirebaseAuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    uid = claims.get("uid") or claims.get("sub")
    if not isinstance(uid, str) or not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has no user identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = claims.get("email")
    return AuthenticatedUser(
        uid=uid,
        email=email if isinstance(email, str) else None,
        email_verified=claims.get("email_verified") is True,
    )
