"""FastAPI Application Main Entrypoint - Live Reload."""

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

    from app.agents.registry import (
        register_browser_journey_agents,
        register_code_generation_agents,
        register_default_agents,
        register_failure_analysis_agents,
        register_remediation_agents,
        register_test_generation_agents,
    )
    register_default_agents()
    register_code_generation_agents()
    register_failure_analysis_agents()
    register_remediation_agents()
    register_test_generation_agents()
    register_browser_journey_agents()

    # Database schema management & automated migration synchronization
    try:
        from app.models.base import Base
        import app.models  # noqa: F401
        from sqlalchemy import inspect as sa_inspect, text

        async with engine.begin() as conn:
            if settings.ENVIRONMENT not in ("production", "staging"):
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Development environment: Local database tables verified.")

            # Reconcile schema: ensure missing columns are added idempotently across all database drivers
            def reconcile_schema(sync_conn):
                inspector = sa_inspect(sync_conn)
                tables = inspector.get_table_names()

                # 1. Ensure projects.owner_id exists
                if "projects" in tables:
                    p_cols = [c["name"] for c in inspector.get_columns("projects")]
                    if "owner_id" not in p_cols:
                        logger.info("Auto-reconciling schema: Adding missing 'owner_id' column to 'projects'.")
                        try:
                            sync_conn.execute(text("ALTER TABLE projects ADD COLUMN owner_id UUID REFERENCES users(id) ON DELETE SET NULL;"))
                            sync_conn.execute(text("CREATE INDEX IF NOT EXISTS ix_projects_owner_id ON projects (owner_id);"))
                        except Exception as e:
                            logger.warning(f"Could not add owner_id to projects: {e}")

                # 2. Ensure assistant_conversations.user_id exists
                if "assistant_conversations" in tables:
                    ac_cols = [c["name"] for c in inspector.get_columns("assistant_conversations")]
                    if "user_id" not in ac_cols:
                        logger.info("Auto-reconciling schema: Adding missing 'user_id' column to 'assistant_conversations'.")
                        try:
                            sync_conn.execute(text("ALTER TABLE assistant_conversations ADD COLUMN user_id UUID REFERENCES users(id) ON DELETE CASCADE;"))
                            sync_conn.execute(text("CREATE INDEX IF NOT EXISTS ix_assistant_conversations_user_project ON assistant_conversations (user_id, project_id);"))
                        except Exception as e:
                            logger.warning(f"Could not add user_id to assistant_conversations: {e}")

            await conn.run_sync(reconcile_schema)
            logger.info("Database schema reconciliation completed successfully.")
    except Exception as exc:
        logger.warning(f"Database schema initialization notice: {exc}")

    # Automatically ensure application preview runtime on Port 8001
    try:
        import asyncio
        from app.runtime.preview_runtime_manager import preview_runtime_manager
        asyncio.create_task(preview_runtime_manager.ensure_running())
    except Exception as exc:
        logger.warning(f"Could not initialize preview runtime on startup: {exc}")

    yield

    # 2. Shutdown: Dispose database connections & stop runtime
    logger.info(f"Shutting down {settings.PROJECT_NAME}. Disposing connection pools...")
    try:
        from app.runtime.preview_runtime_manager import preview_runtime_manager
        preview_runtime_manager.stop_runtime()
    except Exception:
        pass
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

    # Configure CORS for local development and deployed frontend (e.g. Vercel)
    cors_kwargs = {
        "allow_origins": settings.CORS_ORIGINS,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
        "expose_headers": ["X-Correlation-ID"],
    }
    if settings.CORS_ORIGIN_REGEX:
        cors_kwargs["allow_origin_regex"] = settings.CORS_ORIGIN_REGEX

    app.add_middleware(CORSMiddleware, **cors_kwargs)

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

    # Mount Live Preview Root Route Compatibility Router
    from app.api.preview_compatibility import preview_root_router
    app.include_router(preview_root_router)

    @app.get("/health")
    def health_root():
        return {"status": "ok", "app": settings.PROJECT_NAME}

    return app


app = create_application()
# Trigger uvicorn reload: groq openai/gpt-oss-20b activated
