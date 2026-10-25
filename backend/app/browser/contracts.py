"""Browser Testing Runtime Contracts and Configuration (Phase 11J - Stage 3).

Defines resource limits, deterministic test case definitions, browser interaction
primitives, and re-exports core browser schemas from Stage 1.
"""

import enum
import re
import uuid
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.browser_testing import (
    BrowserArtifactReference,
    BrowserArtifactType,
    BrowserConsoleError,
    BrowserNetworkRecord,
    BrowserTestCaseResult,
    BrowserTestRun,
    BrowserTestStatus,
)

# Pinned Playwright image for isolated browser container
DEFAULT_PLAYWRIGHT_IMAGE = "se-intelliplatform-browser:v1.49.0"

MAX_CONCURRENT_BROWSER_SESSIONS = 2
MAX_BROWSER_SESSION_TIMEOUT_SECONDS = 60.0


class BrowserLimits(BaseModel):
    """Hardened execution bounds and container quotas for browser testing."""

    model_config = ConfigDict(extra="forbid")

    max_concurrent_sessions: int = Field(
        default=MAX_CONCURRENT_BROWSER_SESSIONS,
        ge=1,
        le=5,
        description="Maximum concurrent browser testing containers",
    )
    session_timeout_seconds: float = Field(
        default=MAX_BROWSER_SESSION_TIMEOUT_SECONDS,
        ge=5.0,
        le=120.0,
        description="Total bounded session duration across all tests",
    )
    page_load_timeout_seconds: float = Field(
        default=15.0,
        ge=1.0,
        le=30.0,
        description="Maximum time allowed for a single page navigation",
    )
    action_timeout_seconds: float = Field(
        default=5.0,
        ge=0.5,
        le=15.0,
        description="Timeout for individual element interactions (click, fill, assert)",
    )
    max_screenshots_per_run: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Maximum screenshot files generated per browser test run",
    )
    max_screenshot_bytes: int = Field(
        default=5 * 1024 * 1024,  # 5 MB
        ge=1024,
        le=10 * 1024 * 1024,
        description="Maximum allowed byte size per individual screenshot",
    )
    max_console_messages: int = Field(
        default=100,
        ge=1,
        le=200,
        description="Maximum console error and warning records retained",
    )
    max_console_message_chars: int = Field(
        default=4000,
        ge=100,
        le=8000,
        description="Maximum characters stored per console message",
    )
    max_network_records: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Maximum network diagnostic records retained",
    )
    max_dom_snapshot_chars: int = Field(
        default=10000,
        ge=500,
        le=50000,
        description="Maximum bounded characters for DOM snippet evidence",
    )
    container_memory: str = Field(
        default="1024m",
        description="Container memory limit",
    )
    container_cpus: str = Field(
        default="1.5",
        description="Container CPU quota",
    )
    container_pids: int = Field(
        default=128,
        description="Container PID limit",
    )
    container_shm_size: str = Field(
        default="512m",
        description="Container shared memory size for Chromium stability",
    )


class BrowserInteractionType(str, enum.Enum):
    """Allowlisted, deterministic browser operations (no arbitrary JavaScript)."""

    CLICK = "click"
    FILL = "fill"
    SELECT = "select"
    WAIT = "wait"
    NAVIGATE = "navigate"
    ASSERT_TEXT = "assert_text"
    ASSERT_VISIBLE = "assert_visible"
    ASSERT_URL = "assert_url"
    SCREENSHOT = "screenshot"


class DeterministicInteraction(BaseModel):
    """Specification for a single deterministic interaction on a loaded page."""

    model_config = ConfigDict(extra="forbid")

    action: BrowserInteractionType = Field(
        ...,
        description="Deterministic action verb to perform",
    )
    selector: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="CSS or text selector for the target element",
    )
    value: str | None = Field(
        default=None,
        max_length=500,
        description="Input text value for 'fill' actions",
    )
    expected_text: str | None = Field(
        default=None,
        max_length=500,
        description="Expected substring for 'assert_text' actions",
    )
    timeout_seconds: float = Field(
        default=5.0,
        ge=0.5,
        le=15.0,
        description="Maximum seconds to wait for selector/action",
    )

    @field_validator("selector")
    @classmethod
    def validate_selector_safety(cls, val: str) -> str:
        """Reject dangerous or script-injection attempts in selectors."""
        stripped = val.strip()
        if re.search(r"javascript:|data:|<script|eval\(|document\.", stripped, re.IGNORECASE):
            raise ValueError(f"Unsafe pattern detected in selector: '{val}'")
        return stripped


class DeterministicBrowserTestDefinition(BaseModel):
    """Specification for a deterministic browser smoke test case."""

    model_config = ConfigDict(extra="forbid")

    test_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_\-]+$",
        description="Deterministic identifier for test case (e.g. 'smoke_01_root_page')",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable title describing the test flow",
    )
    target_path: str = Field(
        default="/",
        min_length=1,
        max_length=300,
        description="Relative URL path to test within the internal application origin",
    )
    expected_status: int = Field(
        default=200,
        ge=200,
        le=399,
        description="Expected HTTP status code from initial page navigation",
    )
    expected_title_contains: str | None = Field(
        default=None,
        max_length=200,
        description="Substring expected to appear in document <title>",
    )
    expected_elements: list[str] = Field(
        default_factory=lambda: ["body"],
        max_length=10,
        description="List of CSS selectors expected to be visible after page load",
    )
    interactions: list[DeterministicInteraction] = Field(
        default_factory=list,
        max_length=50,
        description="Optional sequence of allowlisted interactions to execute",
    )
    capture_screenshot: bool = Field(
        default=True,
        description="Whether to capture a terminal screenshot after test completion",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Auxiliary test case annotations such as journey and requirement traceability",
    )

    @field_validator("target_path")
    @classmethod
    def validate_target_path(cls, val: str) -> str:
        """Ensure path is relative to application origin and safe."""
        stripped = val.strip()
        if re.search(r"^[a-zA-Z]+://", stripped):
            raise ValueError(f"target_path must be a relative path, not a full URL: '{val}'")
        if ".." in stripped:
            raise ValueError(f"target_path must not contain traversal: '{val}'")
        if not stripped.startswith("/"):
            stripped = "/" + stripped
        return stripped


class BrowserSessionConfig(BaseModel):
    """Runtime configuration for a browser testing execution session."""

    model_config = ConfigDict(extra="forbid")

    project_id: uuid.UUID = Field(
        ...,
        description="Target Project UUID",
    )
    version_id: uuid.UUID | None = Field(
        default=None,
        description="Target DevelopmentVersion UUID",
    )
    workflow_execution_id: uuid.UUID | None = Field(
        default=None,
        description="Associated WorkflowExecution UUID",
    )
    test_definitions: list[DeterministicBrowserTestDefinition] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Deterministic smoke test cases to execute",
    )
    limits: BrowserLimits = Field(
        default_factory=BrowserLimits,
        description="Resource and time limits",
    )


def create_default_smoke_suite(health_path: str = "/docs") -> list[DeterministicBrowserTestDefinition]:
    """Generate the standard deterministic smoke test suite for a generated web app."""
    tests = [
        DeterministicBrowserTestDefinition(
            test_id="smoke_01_root_page_load",
            name="Verify root application page renders successfully",
            target_path="/",
            expected_status=200,
            expected_elements=["body"],
            capture_screenshot=True,
        ),
    ]
    if health_path and health_path != "/":
        clean_health = health_path if health_path.startswith("/") else f"/{health_path}"
        tests.append(
            DeterministicBrowserTestDefinition(
                test_id="smoke_02_health_or_docs_endpoint",
                name=f"Verify deterministic documentation/health endpoint '{clean_health}'",
                target_path=clean_health,
                expected_status=200,
                expected_elements=["body"],
                capture_screenshot=True,
            )
        )
    return tests
