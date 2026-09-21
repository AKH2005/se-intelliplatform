"""FastAPI Application Main Entrypoint."""

import logging
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import RequestResponseEndpoint

from app.api.error_handlers import register_error_handlers
from app.api.v1.api import api_v1_router
from app.core.config import settings
from app.core.database import engine
from app.core.logging import get_correlation_id, set_correlation_id, setup_logging

logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager handling startup and shutdown events."""
    # 1. Startup: Initialize structured logging
    setup_logging(level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)
    logger.info(
        f"Starting {settings.PROJECT_NAME} v{settings.VERSION} "
        f"[env={settings.ENVIRONMENT}, debug={settings.DEBUG}]"
    )

    yield

    # 2. Shutdown: Dispose database connections
    logger.info(f"Shutting down {settings.PROJECT_NAME}. Disposing connection pools...")
    await engine.dispose()
    logger.info("Application shutdown complete.")


def create_application() -> FastAPI:
    """Factory function for FastAPI application instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="AI-Powered Multi-Agent Platform for Smart Software Development",
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan,
    )

    # Configure CORS for local development and future frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID"],
    )

    # Middleware: Request Correlation ID & Access Logging
    @app.middleware("http")
    async def correlation_id_and_logging_middleware(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Extract or generate correlation ID
        incoming_cid = request.headers.get("X-Correlation-ID") or request.headers.get("X-Request-ID")
        correlation_id = incoming_cid or f"req-{uuid.uuid4().hex[:12]}"
        set_correlation_id(correlation_id)

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            # Let the exception bubble up to the centralized exception handler
            raise

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Correlation-ID"] = correlation_id

        # Skip access log for static or noisy endpoints if needed
        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)",
            extra={
                "request_path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response

    # Centralized RFC 7807 Exception Handlers
    register_error_handlers(app)

    # Mount API routers
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    return app


app = create_application()
