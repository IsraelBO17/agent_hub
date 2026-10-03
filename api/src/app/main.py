"""create_app(): the only place the service is wired together (standard §6, §7).

Middleware, error handlers, routers and the lifespan. Feature routers and job modules are
imported here and nowhere else.
"""

import asyncio
import contextlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app import __version__
from app.core import health
from app.core.db import init_db
from app.core.errors import install_error_handlers
from app.core.jobs.runner import configure_retention, work_loop
from app.core.lifecycle import shutting_down
from app.core.logging import configure_logging
from app.core.middleware import (
    BodySizeLimitMiddleware,
    RequestIdMiddleware,
    SecurityHeadersMiddleware,
)
from app.core.settings import get_settings
from app.features.auth import router as auth_router
from app.features.auth.google import GoogleVerifier

CONTRACT = Path(
    "openapi.yaml"
)  # the working directory is the repository root (and /app in the image)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level, json_output=settings.log_json)
    configure_retention(settings.job_retention_days)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        db = init_db(settings)
        # One client for Google's signing keys, for the life of the process (standard §16).
        google_http = httpx.AsyncClient(timeout=settings.google_timeout_seconds)
        app.state.google_verifier = GoogleVerifier(
            google_http,
            certs_url=settings.google_certs_url,
            client_id=settings.google_client_id,
            issuers=settings.google_issuers,
            cache_seconds=settings.google_keys_cache_seconds,
        )
        worker: asyncio.Task[None] | None = None
        if settings.run_worker_in_api:  # small services: no separate worker task (standard §13)
            worker = asyncio.create_task(work_loop(db.sessions, settings, shutting_down))
        yield
        shutting_down.set()
        if worker is not None:
            with contextlib.suppress(asyncio.CancelledError):
                await worker
        await google_http.aclose()
        await db.engine.dispose()

    app = FastAPI(
        title=settings.service_name,
        version=__version__,
        lifespan=lifespan,
        # The contract is the hand-written openapi.yaml, not FastAPI's generated schema.
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
        # FastAPI's built-in OpenTelemetry spans use the global providers; exporters come from the
        # deployment's distro, not from FastAPI (standard §17).
        telemetry={"auto_configure": False},
    )
    install_error_handlers(
        app,
        errors_base_url=settings.errors_base_url,
        validation_status=settings.validation_status,
    )

    # The last added is the outermost: RequestId -> SecurityHeaders -> CORS -> BodySizeLimit -> app.
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_body_bytes)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Request-Id"],
        expose_headers=["X-Request-Id", "Location", "Retry-After"],
    )
    app.add_middleware(SecurityHeadersMiddleware, hsts=settings.env != "local")
    app.add_middleware(RequestIdMiddleware)

    app.include_router(health.router)
    app.include_router(auth_router.auth)
    app.include_router(auth_router.me_router)

    if settings.docs_enabled:

        @app.get("/openapi.yaml", include_in_schema=False)
        async def contract() -> FileResponse:
            return FileResponse(CONTRACT, media_type="application/yaml")

    return app
