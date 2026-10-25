"""Safe, Non-Intrusive Execution Event Publisher for Phase 12.

Ensures that:
1. All telemetry emissions are non-blocking and safe.
2. Telemetry failures NEVER cause execution failures.
3. Correlation IDs, monotonic sequences, and project boundaries are preserved.
"""

from datetime import datetime, timezone
import logging
from typing import Any
import uuid

from app.core.logging import get_correlation_id
from app.telemetry.bus import get_event_bus
from app.telemetry.contracts import (
    EventSeverity,
    ExecutionEvent,
    ExecutionEventType,
    ExecutionKind,
)

logger = logging.getLogger(__name__)


class ExecutionEventPublisher:
    """Convenience publisher for dispatching execution telemetry events."""

    @classmethod
    async def emit(
        cls,
        event_type: ExecutionEventType,
        project_id: str | uuid.UUID,
        execution_id: str | uuid.UUID,
        execution_kind: ExecutionKind,
        source: str,
        status: str,
        correlation_id: str | None = None,
        parent_execution_id: str | uuid.UUID | None = None,
        payload: dict[str, Any] | None = None,
        severity: EventSeverity = EventSeverity.INFO,
    ) -> ExecutionEvent | None:
        """Safely emit an execution telemetry event to the platform event bus.

        Guarantees:
        - Never throws an unhandled exception.
        - Automatically resolves correlation ID from logging context if omitted.
        - Generates monotonic sequence number.
        - Sanitizes secrets and normalizes types.
        """
        try:
            bus = get_event_bus()
            clean_pid = str(project_id).strip().lower()
            clean_eid = str(execution_id).strip().lower()
            clean_parent = str(parent_execution_id).strip().lower() if parent_execution_id else None
            cid = correlation_id or get_correlation_id() or f"corr-{uuid.uuid4().hex[:8]}"

            sequence = bus.get_next_sequence(clean_eid)

            event = ExecutionEvent(
                event_type=event_type,
                timestamp=datetime.now(timezone.utc),
                project_id=clean_pid,
                execution_id=clean_eid,
                correlation_id=cid,
                parent_execution_id=clean_parent,
                execution_kind=execution_kind,
                source=source,
                status=status,
                sequence=sequence,
                payload=payload or {},
                severity=severity,
                created_at=datetime.now(timezone.utc),
            )

            return await bus.publish(event)
        except Exception as exc:
            # Telemetry delivery failure MUST NOT interrupt execution!
            logger.warning(
                f"Failed to publish execution event [{event_type.value}] for execution [{execution_id}]: {exc}",
                exc_info=False,
            )
            return None
