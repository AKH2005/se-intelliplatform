"""Deterministic Secret Redaction and Safe Payload Sanitization for Telemetry."""

import json
from typing import Any
from app.telemetry.contracts import MAX_STRING_FIELD_CHARS

SENSITIVE_KEY_SUBSTRINGS: tuple[str, ...] = (
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "credential",
    "private_key",
    "client_secret",
    "auth_header",
    "cookie",
    "jwt",
)


def sanitize_value(val: Any) -> Any:
    """Recursively sanitize values to prevent secret leakage and bounded size."""
    if isinstance(val, str):
        if len(val) > MAX_STRING_FIELD_CHARS:
            return val[:MAX_STRING_FIELD_CHARS] + f"\n[TRUNCATED: string exceeded {MAX_STRING_FIELD_CHARS} characters]"
        return val

    if isinstance(val, dict):
        sanitized_dict: dict[str, Any] = {}
        for k, v in val.items():
            k_str = str(k).lower()
            if any(sub in k_str for sub in SENSITIVE_KEY_SUBSTRINGS):
                sanitized_dict[str(k)] = "[REDACTED]"
            else:
                sanitized_dict[str(k)] = sanitize_value(v)
        return sanitized_dict

    if isinstance(val, (list, tuple, set)):
        return [sanitize_value(item) for item in val]

    if isinstance(val, (int, float, bool)) or val is None:
        return val

    # Fallback to string representation for other types
    try:
        s = str(val)
        if len(s) > MAX_STRING_FIELD_CHARS:
            return s[:MAX_STRING_FIELD_CHARS] + f"\n[TRUNCATED: string exceeded {MAX_STRING_FIELD_CHARS} characters]"
        return s
    except Exception:
        return "[UNSERIALIZABLE_OBJECT]"


def sanitize_event_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    """Sanitize an execution event payload dictionary against sensitive secrets and bounded size."""
    if not payload:
        return {}
    return sanitize_value(payload)
