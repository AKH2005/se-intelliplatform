"""Strongly-typed contracts for Application Runtime Subsystem (Phase 11J - Stage 2)."""

import enum
import uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.runtime import ApplicationRuntimeManifest


# ==============================================================================
# 1. Constants
# ==============================================================================

DEFAULT_APPLICATION_MEMORY_LIMIT: str = "512m"
DEFAULT_APPLICATION_CPUS: float = 1.0
DEFAULT_APPLICATION_MAX_PIDS: int = 64
DEFAULT_STARTUP_TIMEOUT_SECONDS: float = 15.0
MAX_SESSION_TIMEOUT_SECONDS: float = 60.0
DEFAULT_HEALTH_POLL_INTERVAL: float = 0.5
MAX_LOG_BYTES: int = 50 * 1024  # 50 KB stdout/stderr buffer
MAX_LOG_LINES: int = 200
MAX_CONCURRENT_RUNTIMES: int = 2

# Explicit allowlist of environment variables passed into the application container
ALLOWED_RUNTIME_ENV_VARS: dict[str, str] = {
    "PYTHONPATH": "/workspace",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONUNBUFFERED": "1",
}


# ==============================================================================
# 2. Enumerations
# ==============================================================================

class RuntimeStatus(str, enum.Enum):
    """Deterministic terminal or lifecycle state of an application runtime session."""

    PENDING = "PENDING"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    READY = "READY"
    STARTUP_FAILED = "STARTUP_FAILED"
    TIMEOUT = "TIMEOUT"
    RESOURCE_LIMIT = "RESOURCE_LIMIT"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    STOPPED = "STOPPED"


# ==============================================================================
# 3. Models
# ==============================================================================

class RuntimeLimits(BaseModel):
    """Resource and timing constraints enforced on application runtime containers."""

    model_config = ConfigDict(extra="forbid")

    memory_limit: str = Field(
        default=DEFAULT_APPLICATION_MEMORY_LIMIT,
        description="Container memory limit string (e.g. '512m')",
    )
    cpus: float = Field(
        default=DEFAULT_APPLICATION_CPUS,
        ge=0.25,
        le=2.0,
        description="CPU cores allocated to container",
    )
    max_pids: int = Field(
        default=DEFAULT_APPLICATION_MAX_PIDS,
        ge=16,
        le=256,
        description="Maximum concurrent PIDs / threads",
    )
    startup_timeout_seconds: float = Field(
        default=DEFAULT_STARTUP_TIMEOUT_SECONDS,
        ge=1.0,
        le=30.0,
        description="Maximum time allowed for application readiness health check",
    )
    session_timeout_seconds: float = Field(
        default=MAX_SESSION_TIMEOUT_SECONDS,
        ge=5.0,
        le=60.0,
        description="Hard maximum runtime session lifetime",
    )
    health_poll_interval_seconds: float = Field(
        default=DEFAULT_HEALTH_POLL_INTERVAL,
        ge=0.1,
        le=2.0,
        description="Interval between consecutive health check probes",
    )
    max_stdout_bytes: int = Field(
        default=MAX_LOG_BYTES,
        description="Maximum captured stdout bytes before truncation",
    )
    max_stderr_bytes: int = Field(
        default=MAX_LOG_BYTES,
        description="Maximum captured stderr bytes before truncation",
    )
    max_log_lines: int = Field(
        default=MAX_LOG_LINES,
        description="Maximum captured log lines before truncation",
    )


class RuntimeSessionConfig(BaseModel):
    """Immutable runtime configuration bundle assembled for container launch."""

    model_config = ConfigDict(extra="forbid")

    session_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Unique session UUID",
    )
    project_id: uuid.UUID = Field(..., description="Target Project UUID")
    version_id: uuid.UUID | None = Field(
        default=None,
        description="Target DevelopmentVersion UUID if version-scoped",
    )
    container_name: str = Field(..., description="Deterministic Docker container name")
    network_name: str = Field(..., description="Deterministic Docker internal network name")
    manifest: ApplicationRuntimeManifest = Field(..., description="Validated runtime manifest")
    limits: RuntimeLimits = Field(
        default_factory=RuntimeLimits,
        description="Enforced resource limits",
    )
    internal_url: str = Field(..., description="Internal Docker DNS URL (e.g. http://app-1234:8000)")
    application_port: int = Field(..., description="Internal listening port")


class RuntimeSessionResult(BaseModel):
    """Authoritative outcome and diagnostic telemetry of an application runtime session."""

    model_config = ConfigDict(extra="forbid")

    runtime_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Unique session result UUID",
    )
    project_id: uuid.UUID = Field(..., description="Project UUID")
    version_id: uuid.UUID | None = Field(default=None, description="DevelopmentVersion UUID")
    status: RuntimeStatus = Field(..., description="Terminal status of runtime session")
    internal_url: str = Field(..., description="Internal container URL (internal Docker network only)")
    container_name: str = Field(..., description="Container name")
    network_name: str = Field(..., description="Internal bridge network name")
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when startup initiated",
    )
    ready_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when application passed health readiness",
    )
    stopped_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when runtime stopped and cleaned up",
    )
    duration_seconds: float = Field(default=0.0, ge=0.0, description="Total active session duration")
    health_status: str | None = Field(default=None, description="Diagnostic health check outcome summary")
    exit_code: int | None = Field(default=None, description="Container exit code if terminated")
    stdout_summary: str = Field(default="", max_length=MAX_LOG_BYTES * 2, description="Bounded stdout summary")
    stderr_summary: str = Field(default="", max_length=MAX_LOG_BYTES * 2, description="Bounded stderr summary")
    is_truncated: bool = Field(default=False, description="True if output exceeded buffer limits")
    failure_reason: str | None = Field(default=None, max_length=2000, description="Diagnostic failure reason")
    resource_limit_reason: str | None = Field(default=None, max_length=500, description="Resource limit exceeded detail")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Auxiliary runtime telemetry")
