"""Unit Tests for Structured Logging and Formatter Capabilities."""

import json
import logging
from app.core.logging import (
    JSONFormatter,
    TextFormatter,
    get_correlation_id,
    set_correlation_id,
    setup_logging,
)


def test_correlation_id_context():
    """Verify setting and retrieving correlation ID."""
    set_correlation_id("test-corr-123")
    assert get_correlation_id() == "test-corr-123"


def test_json_formatter_standard_fields():
    """Verify JSON formatter outputs required structured fields."""
    set_correlation_id("json-trace-456")
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Sample log message",
        args=(),
        exc_info=None,
    )
    record.request_path = "/api/v1/test"
    record.method = "POST"
    record.status_code = 200
    record.duration_ms = 12.34
    record.extra_data = {"safe_param": "value", "user_password": "supersecretpassword"}

    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test_logger"
    assert parsed["message"] == "Sample log message"
    assert parsed["correlation_id"] == "json-trace-456"
    assert parsed["request_path"] == "/api/v1/test"
    assert parsed["method"] == "POST"
    assert parsed["status_code"] == 200
    assert parsed["duration_ms"] == 12.34
    # Verify sensitive data redaction
    assert parsed["extra"]["safe_param"] == "value"
    assert parsed["extra"]["user_password"] == "[REDACTED]"


def test_text_formatter():
    """Verify text formatter formats string representation."""
    set_correlation_id("txt-trace-789")
    formatter = TextFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.WARNING,
        pathname=__file__,
        lineno=20,
        msg="Warning message",
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    assert "WARNING" in output
    assert "txt-trace-789" in output
    assert "Warning message" in output


def test_setup_logging():
    """Verify setup_logging configures root logger."""
    setup_logging(level="DEBUG", log_format="json")
    root = logging.getLogger()
    assert root.level == logging.DEBUG
    assert len(root.handlers) >= 1

    setup_logging(level="INFO", log_format="text")
    assert root.level == logging.INFO
