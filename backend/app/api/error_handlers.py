"""Centralized Exception Handlers Mapping Exceptions to RFC 7807 Problem Details."""

import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import ApplicationError
from app.core.logging import get_correlation_id

logger = logging.getLogger(__name__)


def create_problem_response(
    status_code: int,
    title: str,
    detail: str,
    type_uri: str,
    request: Request,
    extra: dict | None = None,
    headers: dict | None = None,
) -> JSONResponse:
    """Construct an RFC 7807 compliant problem details response."""
    payload = {
        "type": type_uri,
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": str(request.url.path),
        "trace_id": get_correlation_id(),
    }
    if extra:
        payload.update(extra)

    response_headers = {"Content-Type": "application/problem+json"}
    if headers:
        response_headers.update(headers)

    # Ensure CORS headers are attached to error responses so browser clients never encounter "Failed to fetch"
    origin = request.headers.get("origin")
    if origin:
        import re
        from app.core.config import settings

        is_allowed = origin in settings.CORS_ORIGINS
        if not is_allowed and settings.CORS_ORIGIN_REGEX:
            try:
                is_allowed = bool(re.match(settings.CORS_ORIGIN_REGEX, origin))
            except Exception:
                is_allowed = False

        if is_allowed:
            response_headers["Access-Control-Allow-Origin"] = origin
            response_headers["Access-Control-Allow-Credentials"] = "true"
            response_headers["Access-Control-Expose-Headers"] = "X-Correlation-ID"

    return JSONResponse(
        status_code=status_code,
        content=payload,
        headers=response_headers,
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on the FastAPI application."""

    @app.exception_handler(ApplicationError)
    async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
        logger.warning(f"Application error [{exc.title}]: {exc.detail}")
        headers = {}
        if exc.status_code == 429:
            headers["Retry-After"] = str(getattr(exc, "retry_after_seconds", 60))
        return create_problem_response(
            status_code=exc.status_code,
            title=exc.title,
            detail=exc.detail,
            type_uri=exc.type_uri,
            request=request,
            extra=exc.extra,
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = []
        for err in exc.errors():
            loc = " -> ".join(str(item) for item in err.get("loc", []))
            msg = err.get("msg", "Invalid input")
            errors.append({"field": loc, "message": msg, "type": err.get("type")})

        logger.info(f"Validation error on {request.method} {request.url.path}: {errors}")
        return create_problem_response(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            title="Validation Error",
            detail="The request payload failed schema validation.",
            type_uri="https://api.se-intelliplatform.local/errors/validation-failed",
            request=request,
            extra={"validation_errors": errors},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        title = "HTTP Error"
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            title = "Endpoint Not Found"
        elif exc.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            title = "Method Not Allowed"

        return create_problem_response(
            status_code=exc.status_code,
            title=title,
            detail=str(exc.detail),
            type_uri="https://api.se-intelliplatform.local/errors/http-error",
            request=request,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Crucial security requirement: NEVER expose internal stack traces to clients
        logger.exception(f"Unhandled exception during {request.method} {request.url.path}: {exc}")
        return create_problem_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            title="Internal Server Error",
            detail="An unexpected internal server error occurred. Please contact support with the trace_id.",
            type_uri="https://api.se-intelliplatform.local/errors/internal-error",
            request=request,
        )
