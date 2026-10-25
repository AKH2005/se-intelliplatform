"""Deterministic Real-Time Execution & Telemetry Contracts for Phase 12.

Defines the authoritative execution event models, controlled event taxonomy,
severity levels, execution kinds, and snapshot schemas for SE IntelliPlatform.
"""

from datetime import datetime, timezone
import enum
from typing import Any
import uuid
from pydantic import BaseModel, ConfigDict, Field


class ExecutionEventType(str, enum.Enum):
    """Authoritative controlled taxonomy of platform execution events."""

    # Generic execution lifecycle
    EXECUTION_CREATED = "EXECUTION_CREATED"
    EXECUTION_STARTED = "EXECUTION_STARTED"
    EXECUTION_QUEUED = "EXECUTION_QUEUED"
    EXECUTION_PROGRESS = "EXECUTION_PROGRESS"
    EXECUTION_LOG = "EXECUTION_LOG"
    EXECUTION_STATE_CHANGED = "EXECUTION_STATE_CHANGED"
    EXECUTION_CANCELLED = "EXECUTION_CANCELLED"
    EXECUTION_COMPLETED = "EXECUTION_COMPLETED"
    EXECUTION_FAILED = "EXECUTION_FAILED"

    # Multi-agent workflow specific
    WORKFLOW_STARTED = "WORKFLOW_STARTED"
    WORKFLOW_STEP_STARTED = "WORKFLOW_STEP_STARTED"
    WORKFLOW_STEP_PROGRESS = "WORKFLOW_STEP_PROGRESS"
    WORKFLOW_STEP_COMPLETED = "WORKFLOW_STEP_COMPLETED"
    WORKFLOW_STEP_FAILED = "WORKFLOW_STEP_FAILED"
    WORKFLOW_COMPLETED = "WORKFLOW_COMPLETED"
    WORKFLOW_FAILED = "WORKFLOW_FAILED"

    # Single-agent specific
    AGENT_STARTED = "AGENT_STARTED"
    AGENT_PROGRESS = "AGENT_PROGRESS"
    AGENT_COMPLETED = "AGENT_COMPLETED"
    AGENT_FAILED = "AGENT_FAILED"

    # Docker sandbox code execution specific
    SANDBOX_STARTED = "SANDBOX_STARTED"
    SANDBOX_PROGRESS = "SANDBOX_PROGRESS"
    SANDBOX_COMPLETED = "SANDBOX_COMPLETED"
    SANDBOX_FAILED = "SANDBOX_FAILED"

    # Application runtime and browser testing specific
    BROWSER_STARTED = "BROWSER_STARTED"
    BROWSER_PROGRESS = "BROWSER_PROGRESS"
    BROWSER_COMPLETED = "BROWSER_COMPLETED"
    BROWSER_FAILED = "BROWSER_FAILED"

    # Multi-tier testing specific
    TEST_STARTED = "TEST_STARTED"
    TEST_PROGRESS = "TEST_PROGRESS"
    TEST_COMPLETED = "TEST_COMPLETED"
    TEST_FAILED = "TEST_FAILED"

    # Selective regression specific
    REGRESSION_STARTED = "REGRESSION_STARTED"
    REGRESSION_PROGRESS = "REGRESSION_PROGRESS"
    REGRESSION_COMPLETED = "REGRESSION_COMPLETED"
    REGRESSION_FAILED = "REGRESSION_FAILED"

    # Multi-environment deployment, promotion, and rollback specific
    DEPLOYMENT_STARTED = "DEPLOYMENT_STARTED"
    DEPLOYMENT_PROGRESS = "DEPLOYMENT_PROGRESS"
    DEPLOYMENT_COMPLETED = "DEPLOYMENT_COMPLETED"
    DEPLOYMENT_FAILED = "DEPLOYMENT_FAILED"
    PROMOTION_STARTED = "PROMOTION_STARTED"
    PROMOTION_COMPLETED = "PROMOTION_COMPLETED"
    PROMOTION_FAILED = "PROMOTION_FAILED"
    ROLLBACK_STARTED = "ROLLBACK_STARTED"
    ROLLBACK_COMPLETED = "ROLLBACK_COMPLETED"
    ROLLBACK_FAILED = "ROLLBACK_FAILED"

    # Security & Diagnostics
    SAFETY_BLOCKED = "SAFETY_BLOCKED"
    FAILURE_DETECTED = "FAILURE_DETECTED"


class ExecutionKind(str, enum.Enum):
    """Categorical classification of the execution authority."""

    WORKFLOW = "WORKFLOW"
    AGENT = "AGENT"
    SANDBOX = "SANDBOX"
    BROWSER = "BROWSER"
    TEST = "TEST"
    REGRESSION = "REGRESSION"
    ASSISTANT_ACTION = "ASSISTANT_ACTION"
    DEPLOYMENT = "DEPLOYMENT"


class EventSeverity(str, enum.Enum):
    """Severity classification of an execution event."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# Bounded limits for event safety and DoS prevention
MAX_PAYLOAD_BYTES: int = 65_536  # 64 KB max payload size
MAX_STRING_FIELD_CHARS: int = 8_192  # 8 KB per individual string
MAX_RING_BUFFER_PER_EXECUTION: int = 200  # retain last 200 events per execution for replay
MAX_SUBSCRIBERS_PER_PROJECT: int = 100  # max concurrent subscribers
DEFAULT_SUBSCRIBER_QUEUE_SIZE: int = 500  # max queued events per subscriber


class ExecutionEvent(BaseModel):
    """Canonical platform real-time execution event envelope.

    Invariants:
    1. Stable event identity: Every event has a unique event_id.
    2. Monotonic sequence: Events within an execution stream have sequence >= 1.
    3. Project isolation: Events are strictly scoped to project_id.
    4. Deterministic serialization: Safe dictionary and JSON serialization.
    """

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this telemetry event",
    )
    event_type: ExecutionEventType = Field(
        ...,
        description="Controlled event taxonomy type",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the event occurred",
    )
    project_id: str = Field(
        ...,
        description="Project UUID string owning this execution stream",
    )
    execution_id: str = Field(
        ...,
        description="Execution correlation UUID string",
    )
    correlation_id: str = Field(
        ...,
        description="Request or transaction correlation ID",
    )
    parent_execution_id: str | None = Field(
        default=None,
        description="Parent execution UUID string for hierarchical tracking",
    )
    execution_kind: ExecutionKind = Field(
        ...,
        description="Categorical kind of execution",
    )
    source: str = Field(
        ...,
        description="Authoritative component generating the event",
    )
    status: str = Field(
        ...,
        description="Current lifecycle status of the execution",
    )
    sequence: int = Field(
        ge=1,
        description="Monotonically increasing sequence number per execution stream",
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured, sanitized contextual data for the event",
    )
    severity: EventSeverity = Field(
        default=EventSeverity.INFO,
        description="Severity level of the event",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC creation timestamp",
    )


class ExecutionStateSnapshot(BaseModel):
    """State snapshot of an active or recent execution for instant client hydration."""

    model_config = ConfigDict(extra="forbid")

    execution_id: str = Field(..., description="Unique execution UUID")
    project_id: str = Field(..., description="Project UUID string")
    correlation_id: str = Field(..., description="Correlation ID")
    parent_execution_id: str | None = Field(default=None, description="Parent execution UUID if nested")
    execution_kind: ExecutionKind = Field(..., description="Kind of execution")
    source: str = Field(..., description="Authoritative origin component")
    status: str = Field(..., description="Current execution status (RUNNING, COMPLETED, FAILED, etc.)")
    current_phase: str | None = Field(default=None, description="Current descriptive phase or active step")
    progress_pct: float | None = Field(default=None, ge=0.0, le=100.0, description="Estimated progress percentage")
    started_at: datetime = Field(..., description="When the execution started")
    updated_at: datetime = Field(..., description="When the execution last emitted telemetry")
    completed_at: datetime | None = Field(default=None, description="When the execution finished")
    duration_seconds: float | None = Field(default=None, description="Elapsed execution duration")
    total_events: int = Field(default=0, ge=0, description="Total events emitted so far")
    last_sequence: int = Field(default=0, ge=0, description="Highest monotonic sequence number emitted")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Execution metadata and tags")
    recent_events: list[ExecutionEvent] = Field(
        default_factory=list,
        description="Bounded buffer of recent execution events for hydration",
    )
