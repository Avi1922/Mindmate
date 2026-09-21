"""FastAPI application entry point."""

import logging
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

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
    )

    @application.middleware("http")
    async def add_security_headers(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        if request.url.path.startswith(settings.api_prefix):
            response.headers["Cache-Control"] = "no-store"
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
