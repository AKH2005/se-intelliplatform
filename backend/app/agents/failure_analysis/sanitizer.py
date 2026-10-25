"""Sanitization, Secret Redaction, and Browser Evidence Normalization for Failure Analysis."""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Bounded telemetry limits
MAX_BROWSER_TESTS_IN_PROMPT = 10
MAX_CONSOLE_ERRORS_PER_TEST = 10
MAX_NETWORK_ERRORS_PER_TEST = 10
MAX_MESSAGE_CHAR_LIMIT = 500
MAX_ARTIFACTS_IN_PROMPT = 5

# Common secret regex patterns
SECRET_PATTERNS: list[tuple[re.Pattern, str]] = [
    # API keys
    (re.compile(r"gsk_[a-zA-Z0-9]{20,}"), "[REDACTED_GROQ_KEY]"),
    (re.compile(r"AIza[0-9A-Za-z-_]{35}"), "[REDACTED_GEMINI_KEY]"),
    (re.compile(r"sk-[a-zA-Z0-9]{20,}"), "[REDACTED_API_KEY]"),
    # Authorization headers
    (re.compile(r"(?i)(authorization:\s*(?:bearer|basic)\s+)[^\s\r\n]+"), r"\1[REDACTED_AUTH_TOKEN]"),
    (re.compile(r"(?i)\bbearer\s+[a-zA-Z0-9_\-\.]{15,}"), "Bearer [REDACTED_TOKEN]"),
    # Passwords and secrets in key-value pairs
    (
        re.compile(r"(?i)(['\"]?(?:password|passwd|secret|api[_-]?key|access[_-]?token)['\"]?\s*[:=]\s*['\"])[^'\"\s,;]+(['\"])"),
        r"\1[REDACTED_SECRET]\2",
    ),
    # Cookies
    (re.compile(r"(?i)(?:cookie|set-cookie):\s*[^\r\n]+"), "Cookie: [REDACTED_COOKIE]"),
    # Private keys
    (
        re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]+?-----END [A-Z ]+ PRIVATE KEY-----"),
        "[REDACTED_PRIVATE_KEY]",
    ),
]


def redact_secrets(text: str | None) -> str:
    """Deterministically strip secrets, tokens, keys, and credentials from text."""
    if not text:
        return ""
    result = text
    for pattern, replacement in SECRET_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def normalize_browser_evidence(browser_test_run: Any | None) -> dict[str, Any]:
    """Normalize and bound browser execution telemetry into safe, redacted structured data."""
    if browser_test_run is None:
        return {}

    run_status = (
        browser_test_run.status.value
        if hasattr(browser_test_run.status, "value")
        else str(browser_test_run.status)
    )

    norm_tests: list[dict[str, Any]] = []
    available_browser_ids: list[str] = [
        str(getattr(browser_test_run, "run_id", "")),
        "browser_run",
        "browser_stdout",
        "browser_stderr",
    ]

    test_cases = getattr(browser_test_run, "test_cases", []) or []
    for idx, tc in enumerate(test_cases[:MAX_BROWSER_TESTS_IN_PROMPT]):
        tc_id = getattr(tc, "test_id", f"browser_test_{idx}")
        tc_name = getattr(tc, "name", f"Test {idx}")
        tc_status = getattr(tc, "status", "UNKNOWN")
        tc_duration = getattr(tc, "duration_seconds", 0.0)
        tc_err = getattr(tc, "error_message", None)
        tc_err_clean = redact_secrets(tc_err)[:MAX_MESSAGE_CHAR_LIMIT] if tc_err else None

        available_browser_ids.append(tc_id)
        available_browser_ids.append(tc_name)
        available_browser_ids.append(f"browser_test_{idx}")

        # Console errors
        norm_console: list[dict[str, Any]] = []
        c_errors = getattr(tc, "console_errors", []) or []
        for c_idx, cerr in enumerate(c_errors[:MAX_CONSOLE_ERRORS_PER_TEST]):
            c_msg = getattr(cerr, "message", str(cerr))
            c_type = getattr(cerr, "level", getattr(cerr, "error_type", "error"))
            c_id = f"console_err_{idx}_{c_idx}"
            available_browser_ids.append(c_id)
            norm_console.append({
                "evidence_id": c_id,
                "type": c_type,
                "message": redact_secrets(c_msg)[:MAX_MESSAGE_CHAR_LIMIT],
            })

        # Network failures / network errors
        norm_network: list[dict[str, Any]] = []
        n_errors = getattr(tc, "network_errors", None) or getattr(tc, "network_failures", None) or []
        for n_idx, nerr in enumerate(n_errors[:MAX_NETWORK_ERRORS_PER_TEST]):
            n_url = getattr(nerr, "url", "")
            n_status = getattr(nerr, "status_code", None)
            n_method = getattr(nerr, "method", "GET")
            n_err_msg = getattr(nerr, "error_message", None) or getattr(nerr, "failure_text", "")
            n_id = f"network_err_{idx}_{n_idx}"
            available_browser_ids.append(n_id)
            norm_network.append({
                "evidence_id": n_id,
                "method": n_method,
                "url": redact_secrets(n_url)[:MAX_MESSAGE_CHAR_LIMIT],
                "status_code": n_status,
                "failure_text": redact_secrets(n_err_msg)[:MAX_MESSAGE_CHAR_LIMIT],
            })

        # Step failures or assertion summary
        tc_err = getattr(tc, "assertion_summary", None) or getattr(tc, "error_message", None)
        tc_err_clean = redact_secrets(tc_err)[:MAX_MESSAGE_CHAR_LIMIT] if tc_err else None

        step_fails = []
        if getattr(tc, "failed_step", None):
            step_fails.append(redact_secrets(tc.failed_step)[:MAX_MESSAGE_CHAR_LIMIT])
        for sf in (getattr(tc, "step_failures", []) or [])[:5]:
            step_fails.append(redact_secrets(str(sf))[:MAX_MESSAGE_CHAR_LIMIT])

        meta = getattr(tc, "metadata", {}) or {}

        norm_tests.append({
            "test_id": tc_id,
            "name": tc_name,
            "status": tc_status.value if hasattr(tc_status, "value") else str(tc_status),
            "duration_seconds": tc_duration,
            "error_message": tc_err_clean,
            "step_failures": step_fails,
            "console_errors": norm_console,
            "network_failures": norm_network,
            "screenshot_artifact_id": getattr(tc, "screenshot_artifact_id", None),
            "page_title": redact_secrets(meta.get("page_title") or getattr(tc, "page_title", None)),
            "current_url": redact_secrets(meta.get("current_url") or getattr(tc, "current_url", None)),
        })

    # Normalized artifacts (metadata only, no binary content)
    norm_artifacts: list[dict[str, Any]] = []
    artifacts = getattr(browser_test_run, "artifacts", []) or []
    for art in artifacts[:MAX_ARTIFACTS_IN_PROMPT]:
        art_id = str(getattr(art, "artifact_id", ""))
        available_browser_ids.append(art_id)
        norm_artifacts.append({
            "artifact_id": art_id,
            "artifact_type": getattr(art, "artifact_type", "SCREENSHOT"),
            "file_path": getattr(art, "file_path", ""),
            "mime_type": getattr(art, "mime_type", "image/png"),
            "size_bytes": getattr(art, "size_bytes", 0),
            "caption": redact_secrets(getattr(art, "caption", "")),
        })

    clean_fail_reason = redact_secrets(getattr(browser_test_run, "failure_reason", None))
    clean_summary = redact_secrets(getattr(browser_test_run, "summary", ""))

    return {
        "run_id": str(getattr(browser_test_run, "run_id", "")),
        "status": run_status,
        "duration_seconds": getattr(browser_test_run, "duration_seconds", 0.0),
        "tests_total": getattr(browser_test_run, "tests_total", 0),
        "tests_passed": getattr(browser_test_run, "tests_passed", 0),
        "tests_failed": getattr(browser_test_run, "tests_failed", 0),
        "tests_skipped": getattr(browser_test_run, "tests_skipped", 0),
        "failure_reason": clean_fail_reason[:MAX_MESSAGE_CHAR_LIMIT] if clean_fail_reason else None,
        "summary": clean_summary[:MAX_MESSAGE_CHAR_LIMIT],
        "test_cases": norm_tests,
        "artifacts": norm_artifacts,
        "available_browser_ids": list(dict.fromkeys(filter(None, available_browser_ids))),
    }
