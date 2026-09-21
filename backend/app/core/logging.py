"""Structured Logging with Correlation ID and Context Tracking."""

import contextvars
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

# Context variable for request correlation tracking across async boundaries
correlation_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default="system-init"
)


def get_correlation_id() -> str:
    """Return the active correlation ID for the current async task context."""
    return correlation_id_ctx.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set the active correlation ID for the current async task context."""
    correlation_id_ctx.set(correlation_id)


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id(),
        }

        # Include contextual extras if passed
        if hasattr(record, "request_path"):
            log_entry["request_path"] = record.request_path
        if hasattr(record, "method"):
            log_entry["method"] = record.method
        if hasattr(record, "status_code"):
            log_entry["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            # Sanitize any accidental sensitive keys
            sanitized = {}
            for k, v in record.extra_data.items():
                if any(secret in k.lower() for secret in ("password", "secret", "token", "key")):
                    sanitized[k] = "[REDACTED]"
                else:
                    sanitized[k] = v
            log_entry["extra"] = sanitized

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter for local development console."""

    def format(self, record: logging.LogRecord) -> str:
        cid = get_correlation_id()
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        msg = f"[{timestamp}] [{record.levelname:<8}] [{cid}] {record.name}: {record.getMessage()}"
        if record.exc_info:
            msg += f"\n{self.formatException(record.exc_info)}"
        return msg


def setup_logging(level: str = "INFO", log_format: str = "json") -> None:
    """Initialize root logger configuration."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    if log_format.lower() == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(TextFormatter())

    root_logger.addHandler(handler)

    # Suppress verbose third-party loggers
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").propagate = False
