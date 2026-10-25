"""Browser Testing and Validation Contracts for Phase 11J.

This module defines strongly-typed data contracts for representing browser-based
test execution, individual test case results, diagnostic evidence references
(screenshots, console errors, network failures), and execution statuses.

These contracts are PURE DATA: no browser execution or container drivers
are implemented in this stage.
"""

import enum
import re
import uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ==============================================================================
# 1. Enumerations
# ==============================================================================

class BrowserTestStatus(str, enum.Enum):
    """Deterministic terminal or intermediate status of browser test execution."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    STARTUP_FAILED = "STARTUP_FAILED"
    BROWSER_ERROR = "BROWSER_ERROR"
    TIMEOUT = "TIMEOUT"
    RESOURCE_LIMIT = "RESOURCE_LIMIT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    SANDBOX_ERROR = "SANDBOX_ERROR"


class BrowserArtifactType(str, enum.Enum):
    """Categorized type of media or telemetry artifact captured during browser automation."""

    SCREENSHOT = "SCREENSHOT"
    CONSOLE_LOG = "CONSOLE_LOG"
    NETWORK_LOG = "NETWORK_LOG"
    DOM_SNAPSHOT = "DOM_SNAPSHOT"
    TRACE = "TRACE"


# ==============================================================================
# 2. Evidence & Telemetry Models
# ==============================================================================

class BrowserArtifactReference(BaseModel):
    """Metadata reference pointing to a captured browser artifact stored on disk."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this artifact reference",
    )
    artifact_type: BrowserArtifactType = Field(
        ...,
        description="Type of browser artifact (SCREENSHOT, CONSOLE_LOG, etc.)",
    )
    file_path: str = Field(
        ...,
        min_length=1,
        max_length=260,
        description="Normalized relative path to stored artifact within project storage",
    )
    size_bytes: int = Field(
        default=0,
        ge=0,
        le=10 * 1024 * 1024,  # Bounded at 10 MB
        description="Size of artifact binary or text in bytes",
    )
    content_type: str = Field(
        default="image/png",
        max_length=100,
        description="MIME type of the artifact",
    )
    caption: str | None = Field(
        default=None,
        max_length=200,
        description="Human-readable description of what this artifact depicts",
    )
    step_number: int | None = Field(
        default=None,
        ge=1,
        description="Step sequence number in test case flow when artifact was captured",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when artifact was created",
    )

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, path: str) -> str:
        """Validate artifact relative file path against traversal and absolute paths."""
        stripped = path.strip().replace("\\", "/")
        if stripped.startswith("/") or stripped.startswith("\\"):
            raise ValueError(f"Artifact file_path must be relative, not absolute: '{path}'")
        if ".." in stripped:
            raise ValueError(f"Artifact file_path must not contain path traversal ('..'): '{path}'")
        if re.search(r"^[a-zA-Z]:", stripped):
            raise ValueError(f"Artifact file_path must not contain Windows drive letters: '{path}'")
        return stripped


class BrowserConsoleError(BaseModel):
    """Captured JavaScript console error or uncaught exception from the browser."""

    model_config = ConfigDict(extra="forbid")

    level: str = Field(
        default="error",
        max_length=20,
        description="Severity level (e.g. 'error', 'warning')",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Bounded text message captured from browser console",
    )
    source: str | None = Field(
        default=None,
        max_length=200,
        description="Source script URL or origin",
    )
    line_number: int | None = Field(
        default=None,
        ge=1,
        description="Line number in source script if provided by runtime",
    )
    timestamp: datetime | None = Field(
        default=None,
        description="Timestamp when the console message occurred",
    )


class BrowserNetworkRecord(BaseModel):
    """Telemetry record for an HTTP request executed by the browser application."""

    model_config = ConfigDict(extra="forbid")

    method: str = Field(
        default="GET",
        min_length=1,
        max_length=10,
        description="HTTP method (GET, POST, PUT, DELETE, etc.)",
    )
    url: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Target request URL",
    )
    status_code: int | None = Field(
        default=None,
        ge=100,
        le=599,
        description="HTTP status code received",
    )
    response_time_ms: float | None = Field(
        default=None,
        ge=0.0,
        description="Roundtrip response duration in milliseconds",
    )
    failed: bool = Field(
        default=False,
        description="True if request encountered a network failure or HTTP error status (>=400)",
    )
    error_message: str | None = Field(
        default=None,
        max_length=500,
        description="Error detail if request failed at network transport level",
    )


# ==============================================================================
# 3. Test Case & Suite Result Models
# ==============================================================================

class BrowserTestCaseResult(BaseModel):
    """Granular verification outcome for an individual browser test case."""

    model_config = ConfigDict(extra="forbid")

    test_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Deterministic identifier for this test case (e.g. 'test_docs_endpoint')",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable title describing the validated user flow",
    )
    status: BrowserTestStatus = Field(
        ...,
        description="Outcome of this specific test case",
    )
    duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        le=120.0,
        description="Duration of this test case in seconds",
    )
    failed_step: str | None = Field(
        default=None,
        max_length=300,
        description="Description of the step that failed, if applicable",
    )
    assertion_summary: str | None = Field(
        default=None,
        max_length=1000,
        description="Summary of assertion expectations versus observed UI/HTTP state",
    )
    screenshots: list[BrowserArtifactReference] = Field(
        default_factory=list,
        max_length=5,
        description="Bounded list of screenshots associated with this test case (max 5)",
    )
    console_errors: list[BrowserConsoleError] = Field(
        default_factory=list,
        max_length=10,
        description="Bounded list of console errors recorded during this test case (max 10)",
    )
    network_errors: list[BrowserNetworkRecord] = Field(
        default_factory=list,
        max_length=10,
        description="Bounded list of failed network requests recorded during this test case (max 10)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Auxiliary test case execution annotations",
    )


class BrowserTestRun(BaseModel):
    """Aggregate result and audit record for a browser-based application test execution."""

    model_config = ConfigDict(extra="forbid")

    run_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Unique UUID for this browser test run session",
    )
    project_id: uuid.UUID = Field(
        ...,
        description="Target Project UUID",
    )
    version_id: uuid.UUID | None = Field(
        default=None,
        description="Target DevelopmentVersion UUID if testing an immutable release",
    )
    workflow_execution_id: uuid.UUID | None = Field(
        default=None,
        description="Originating WorkflowExecution UUID if artifact-backed",
    )
    status: BrowserTestStatus = Field(
        default=BrowserTestStatus.PENDING,
        description="Terminal or live lifecycle status of the browser test session",
    )
    tests_total: int = Field(
        default=0,
        ge=0,
        description="Total number of browser test cases in the executed suite",
    )
    tests_passed: int = Field(
        default=0,
        ge=0,
        description="Number of test cases that passed",
    )
    tests_failed: int = Field(
        default=0,
        ge=0,
        description="Number of test cases that failed",
    )
    tests_skipped: int = Field(
        default=0,
        ge=0,
        description="Number of test cases that were skipped",
    )
    duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Total elapsed execution duration in seconds",
    )
    test_cases: list[BrowserTestCaseResult] = Field(
        default_factory=list,
        max_length=50,
        description="List of granular test case results (max 50)",
    )
    failure_reason: str | None = Field(
        default=None,
        max_length=2000,
        description="High-level diagnostic summary explaining failure if run failed",
    )
    summary: str = Field(
        default="",
        max_length=1000,
        description="Concise human-readable outcome summary",
    )
    artifacts: list[BrowserArtifactReference] = Field(
        default_factory=list,
        max_length=20,
        description="Complete list of artifact references produced during the run (max 20)",
    )
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the test session started",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when the test session completed",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution metadata and container environment telemetry",
    )

    @model_validator(mode="after")
    def validate_status_consistency(self) -> "BrowserTestRun":
        """Validate consistency of status against failure counts."""
        if self.status == BrowserTestStatus.PASSED and self.tests_failed > 0:
            raise ValueError(
                f"BrowserTestRun cannot have status PASSED when tests_failed={self.tests_failed}."
            )
        return self


# ==============================================================================
# 5. REST API Request Contracts
# ==============================================================================

class RunBrowserTestsRequest(BaseModel):
    """Business-level parameters to execute deterministic browser smoke tests.
    
    Security: extra parameters (docker cmd, images, URLs, paths, env) are strictly forbidden.
    """

    model_config = ConfigDict(extra="forbid")

    development_version_id: uuid.UUID | None = Field(
        default=None,
        description="Target DevelopmentVersion UUID. If omitted, resolves the active release version.",
    )

