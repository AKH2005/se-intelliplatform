"""Sandbox Execution Contracts, Enums, and Limits."""

import enum
import uuid
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

# ==============================================================================
# 1. Conservative Sandbox Resource Limits
# ==============================================================================

DEFAULT_TIMEOUT_SECONDS: int = 30
MAX_TIMEOUT_SECONDS: int = 60
DEFAULT_MEMORY_LIMIT: str = "512m"
DEFAULT_CPUS: float = 1.0
DEFAULT_MAX_PIDS: int = 64
DEFAULT_MAX_OUTPUT_BYTES: int = 50 * 1024  # 50 KB stdout/stderr limit

# Explicit allowlist of environment variables permitted in the sandbox
ALLOWED_ENV_VARS: set[str] = {
    "PYTHONPATH",
    "PYTHONDONTWRITEBYTECODE",
    "PYTHONUNBUFFERED",
    "LANG",
    "LC_ALL",
}


# ==============================================================================
# 2. Enumerations
# ==============================================================================

class ExecutionType(str, enum.Enum):
    """Permitted execution types for the isolated sandbox."""

    STATIC_VALIDATE = "STATIC_VALIDATE"
    TEST = "TEST"
    LINT = "LINT"



class ExecutionStatus(str, enum.Enum):
    """Deterministic terminal status of a sandbox execution run."""

    PASSED = "PASSED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    RESOURCE_LIMIT = "RESOURCE_LIMIT"
    SANDBOX_ERROR = "SANDBOX_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    SANDBOX_UNAVAILABLE = "SANDBOX_UNAVAILABLE"


# ==============================================================================
# 3. Models
# ==============================================================================

class ResourceLimits(BaseModel):
    """Resource constraints enforced on sandbox execution."""

    model_config = ConfigDict(extra="forbid")

    timeout_seconds: int = Field(
        default=DEFAULT_TIMEOUT_SECONDS,
        ge=1,
        le=MAX_TIMEOUT_SECONDS,
        description="Maximum execution duration before forced termination",
    )
    memory_limit: str = Field(
        default=DEFAULT_MEMORY_LIMIT,
        pattern=r"^[0-9]+[mMgG]$",
        description="Container memory limit string (e.g. '512m')",
    )
    cpus: float = Field(
        default=DEFAULT_CPUS,
        ge=0.1,
        le=2.0,
        description="Maximum CPU cores allocated to container",
    )
    max_pids: int = Field(
        default=DEFAULT_MAX_PIDS,
        ge=16,
        le=128,
        description="Maximum number of simultaneous processes in container",
    )
    max_output_bytes: int = Field(
        default=DEFAULT_MAX_OUTPUT_BYTES,
        ge=1024,
        le=100 * 1024,
        description="Maximum bytes captured from stdout/stderr",
    )


class ExecutionRequest(BaseModel):
    """Strongly-typed request to execute tests or validation against generated code."""

    model_config = ConfigDict(extra="forbid")

    project_id: uuid.UUID = Field(
        ...,
        description="Target project UUID owning the artifact",
    )
    workflow_execution_id: uuid.UUID | None = Field(
        default=None,
        description="Optional workflow execution UUID containing the CodeGenerationOutput artifact",
    )
    execution_type: ExecutionType = Field(
        default=ExecutionType.TEST,
        description="Execution mode: STATIC_VALIDATE or TEST",
    )
    test_target: str | None = Field(
        default=None,
        max_length=150,
        description="Optional relative test path to run (e.g. 'tests/test_main.py')",
    )
    limits: ResourceLimits = Field(
        default_factory=ResourceLimits,
        description="Deterministic resource and duration limits",
    )


class ExecutionResult(BaseModel):
    """Structured, sanitized outcome of sandbox execution."""

    model_config = ConfigDict(extra="forbid")

    execution_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Unique correlation ID for this sandbox run",
    )
    project_id: uuid.UUID = Field(
        ...,
        description="Target project UUID",
    )
    workflow_execution_id: uuid.UUID | None = Field(
        default=None,
        description="Associated workflow execution UUID if artifact-backed",
    )
    execution_type: ExecutionType = Field(
        ...,
        description="Execution type performed",
    )
    status: ExecutionStatus = Field(
        ...,
        description="Deterministic execution outcome status",
    )
    exit_code: int | None = Field(
        default=None,
        description="Process exit code (0 indicates success)",
    )
    duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Total execution runtime in seconds",
    )
    stdout: str = Field(
        default="",
        description="Captured standard output (bounded)",
    )
    stderr: str = Field(
        default="",
        description="Captured standard error (bounded)",
    )
    is_truncated: bool = Field(
        default=False,
        description="Whether stdout or stderr exceeded max_output_bytes and was truncated",
    )
    tests_passed: int = Field(
        default=0,
        ge=0,
        description="Number of passed test cases parsed from runner",
    )
    tests_failed: int = Field(
        default=0,
        ge=0,
        description="Number of failed test cases parsed from runner",
    )
    tests_total: int = Field(
        default=0,
        ge=0,
        description="Total test cases executed",
    )
    validation_errors: list[str] = Field(
        default_factory=list,
        description="Static validation errors if status is VALIDATION_ERROR",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution metadata and sandbox environment diagnostics (no secrets)",
    )
