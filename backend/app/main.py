"""FastAPI application entry point."""

import logging
import re
import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.models.common import RootResponse
from app.routes.analysis import router as analysis_router
from app.routes.auth import router as auth_router
from app.routes.conversations import router as conversations_router
from app.routes.health import router as health_router
from app.routes.journal import router as journal_router
from app.routes.live import router as live_router
from app.routes.mood import router as mood_router
from app.utils.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger("mindmate.requests")
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""

    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "API for an experimental wellbeing journaling and emotion-analysis "
            "application. It is not a medical or diagnostic service."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.api_prefix}/openapi.json",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["X-Request-ID"],
    )

    @application.middleware("http")
    async def enforce_operational_requirements(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        supplied_request_id = request.headers.get("X-Request-ID", "")
        request_id = (
            supplied_request_id
            if REQUEST_ID_PATTERN.fullmatch(supplied_request_id)
            else str(uuid4())
        )
        started_at = time.perf_counter()
        response: Response

        content_length = request.headers.get("Content-Length")
        if content_length:
            try:
                request_size = int(content_length)
            except ValueError:
                request_size = -1
            if request_size < 0:
                response = JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid Content-Length header"},
                )
            elif request_size > settings.max_request_body_bytes:
                response = JSONResponse(
                    status_code=413,
                    content={"detail": "Request body is too large"},
                )
            else:
                response = await call_next(request)
        else:
            response = await call_next(request)

        duration_ms = (time.perf_counter() - started_at) * 1_000
        logger.info(
            "request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = (
            "camera=(), geolocation=(), microphone=()"
        )
        if request.url.path.startswith(settings.api_prefix):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; frame-ancestors 'none'"
            )
        if settings.app_env == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response

    application.include_router(health_router, prefix=settings.api_prefix)
    application.include_router(auth_router, prefix=settings.api_prefix)
    application.include_router(conversations_router, prefix=settings.api_prefix)
    application.include_router(journal_router, prefix=settings.api_prefix)
    application.include_router(analysis_router, prefix=settings.api_prefix)
    application.include_router(mood_router, prefix=settings.api_prefix)
    application.include_router(live_router, prefix=settings.api_prefix)

    @application.get("/", response_model=RootResponse, tags=["meta"])
    async def api_root() -> RootResponse:
        """Point developers to the interactive API documentation."""

        return RootResponse(
            name=settings.app_name,
            version=__version__,
            docs_url="/docs",
        )

    return application


app = create_app()
