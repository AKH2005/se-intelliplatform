"""Authoritative In-Process Execution Event Bus & Pub-Sub Broker for Phase 12.

Provides bounded, thread-safe asynchronous event distribution with:
- Monotonically increasing sequence numbers per execution stream
- Strict project and execution subscriber isolation
- Automatic payload secret redaction
- Bounded ring buffer for reconnect replay and hydration
- Backpressure protection against slow or stale subscribers
- Bounded concurrency and memory management
"""

import abc
import asyncio
from collections import deque
from datetime import datetime, timezone
import logging
from typing import Any

from app.telemetry.contracts import (
    DEFAULT_SUBSCRIBER_QUEUE_SIZE,
    MAX_RING_BUFFER_PER_EXECUTION,
    MAX_SUBSCRIBERS_PER_PROJECT,
    EventSeverity,
    ExecutionEvent,
    ExecutionEventType,
    ExecutionKind,
    ExecutionStateSnapshot,
)
from app.telemetry.redaction import sanitize_event_payload

logger = logging.getLogger(__name__)


class AbstractExecutionEventBus(abc.ABC):
    """Abstract interface defining platform execution event distribution contracts."""

    @abc.abstractmethod
    async def publish(self, event: ExecutionEvent) -> ExecutionEvent:
        """Publish an event to all authorized subscribers."""
        pass

    @abc.abstractmethod
    async def subscribe(
        self,
        project_id: str,
        execution_id: str | None = None,
    ) -> asyncio.Queue[ExecutionEvent]:
        """Register a subscriber queue for a project or specific execution."""
        pass

    @abc.abstractmethod
    async def unsubscribe(
        self,
        queue: asyncio.Queue[ExecutionEvent],
        project_id: str,
        execution_id: str | None = None,
    ) -> None:
        """Unregister and clean up a subscriber queue."""
        pass

    @abc.abstractmethod
    def get_events(
        self,
        project_id: str,
        execution_id: str,
        since_sequence: int = 0,
    ) -> list[ExecutionEvent]:
        """Retrieve buffered events for an execution stream since a given sequence number."""
        pass

    @abc.abstractmethod
    def get_execution_snapshot(
        self,
        project_id: str,
        execution_id: str,
    ) -> ExecutionStateSnapshot | None:
        """Get the current state snapshot of an execution."""
        pass

    @abc.abstractmethod
    def list_active_executions(self, project_id: str) -> list[ExecutionStateSnapshot]:
        """List all currently active executions for a project."""
        pass


class InMemoryExecutionEventBus(AbstractExecutionEventBus):
    """Authoritative in-process implementation of the Execution Event Bus."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        # project_id -> set of subscriber queues
        self._project_subscribers: dict[str, set[asyncio.Queue[ExecutionEvent]]] = {}
        # execution_id -> set of subscriber queues
        self._execution_subscribers: dict[str, set[asyncio.Queue[ExecutionEvent]]] = {}
        # execution_id -> next monotonic sequence number (int)
        self._sequences: dict[str, int] = {}
        # execution_id -> bounded deque of ExecutionEvent
        self._ring_buffers: dict[str, deque[ExecutionEvent]] = {}
        # execution_id -> ExecutionStateSnapshot
        self._active_snapshots: dict[str, ExecutionStateSnapshot] = {}

    def _normalize_id(self, identifier: Any) -> str:
        return str(identifier).strip().lower()

    def get_next_sequence(self, execution_id: str) -> int:
        """Return and increment the monotonic sequence number for an execution."""
        clean_eid = self._normalize_id(execution_id)
        current = self._sequences.get(clean_eid, 1)
        self._sequences[clean_eid] = current + 1
        return current

    async def publish(self, event: ExecutionEvent) -> ExecutionEvent:
        """Publish an execution event.

        Guarantees:
        - Payload is sanitized for secrets and truncated if oversized.
        - Event is recorded in the execution ring buffer.
        - State snapshot is updated.
        - Distributed asynchronously to all authorized project and execution subscribers.
        - Slow subscribers do not block fast publishers (backpressure handling).
        """
        clean_pid = self._normalize_id(event.project_id)
        clean_eid = self._normalize_id(event.execution_id)

        # 1. Sanitize payload
        sanitized_payload = sanitize_event_payload(event.payload)
        safe_event = event.model_copy(update={"payload": sanitized_payload})

        async with self._lock:
            # 2. Append to execution ring buffer
            if clean_eid not in self._ring_buffers:
                self._ring_buffers[clean_eid] = deque(maxlen=MAX_RING_BUFFER_PER_EXECUTION)
            self._ring_buffers[clean_eid].append(safe_event)

            # 3. Update or create ExecutionStateSnapshot
            snapshot = self._active_snapshots.get(clean_eid)
            now = datetime.now(timezone.utc)
            phase = safe_event.payload.get("phase") or safe_event.payload.get("step_id") or safe_event.event_type.value
            progress = safe_event.payload.get("progress_pct")

            if snapshot is None:
                snapshot = ExecutionStateSnapshot(
                    execution_id=clean_eid,
                    project_id=clean_pid,
                    correlation_id=safe_event.correlation_id,
                    parent_execution_id=safe_event.parent_execution_id,
                    execution_kind=safe_event.execution_kind,
                    source=safe_event.source,
                    status=safe_event.status,
                    current_phase=phase,
                    progress_pct=progress,
                    started_at=safe_event.timestamp,
                    updated_at=now,
                    completed_at=now if "COMPLETED" in safe_event.status or "FAILED" in safe_event.status else None,
                    duration_seconds=safe_event.payload.get("duration_seconds"),
                    total_events=1,
                    last_sequence=safe_event.sequence,
                    metadata=safe_event.payload.get("metadata", {}),
                    recent_events=[safe_event],
                )
                self._active_snapshots[clean_eid] = snapshot
            else:
                snapshot.status = safe_event.status
                snapshot.updated_at = now
                snapshot.total_events += 1
                snapshot.last_sequence = max(snapshot.last_sequence, safe_event.sequence)
                if phase:
                    snapshot.current_phase = phase
                if progress is not None:
                    snapshot.progress_pct = progress
                if "COMPLETED" in safe_event.status or "FAILED" in safe_event.status or "BLOCKED" in safe_event.status:
                    snapshot.completed_at = now
                    if safe_event.payload.get("duration_seconds") is not None:
                        snapshot.duration_seconds = safe_event.payload.get("duration_seconds")
                snapshot.recent_events.append(safe_event)
                if len(snapshot.recent_events) > 20:
                    snapshot.recent_events = snapshot.recent_events[-20:]

            # 4. Collect targeted subscriber queues
            target_queues: set[asyncio.Queue[ExecutionEvent]] = set()

            # Queues listening to the specific project
            if clean_pid in self._project_subscribers:
                target_queues.update(self._project_subscribers[clean_pid])

            # Queues listening to the specific execution
            if clean_eid in self._execution_subscribers:
                target_queues.update(self._execution_subscribers[clean_eid])

        # 5. Broadcast to queues outside the lock (prevent deadlocks / backpressure blocks)
        for q in target_queues:
            try:
                if q.full():
                    # Backpressure: Drop oldest event if queue is full
                    try:
                        q.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                q.put_nowait(safe_event)
            except Exception as exc:
                logger.warning(f"Failed to deliver event {safe_event.event_id} to queue: {exc}")

        return safe_event

    async def subscribe(
        self,
        project_id: str,
        execution_id: str | None = None,
    ) -> asyncio.Queue[ExecutionEvent]:
        """Subscribe to live execution events for a project or specific execution."""
        clean_pid = self._normalize_id(project_id)
        queue: asyncio.Queue[ExecutionEvent] = asyncio.Queue(maxsize=DEFAULT_SUBSCRIBER_QUEUE_SIZE)

        async with self._lock:
            # Check maximum subscribers
            current_project_subs = len(self._project_subscribers.get(clean_pid, set()))
            if current_project_subs >= MAX_SUBSCRIBERS_PER_PROJECT:
                raise ValueError(
                    f"Maximum subscriber limit ({MAX_SUBSCRIBERS_PER_PROJECT}) reached for project '{clean_pid}'."
                )

            if execution_id is not None:
                clean_eid = self._normalize_id(execution_id)
                if clean_eid not in self._execution_subscribers:
                    self._execution_subscribers[clean_eid] = set()
                self._execution_subscribers[clean_eid].add(queue)
            else:
                if clean_pid not in self._project_subscribers:
                    self._project_subscribers[clean_pid] = set()
                self._project_subscribers[clean_pid].add(queue)

        return queue

    async def unsubscribe(
        self,
        queue: asyncio.Queue[ExecutionEvent],
        project_id: str,
        execution_id: str | None = None,
    ) -> None:
        """Unsubscribe and release subscriber queue."""
        clean_pid = self._normalize_id(project_id)

        async with self._lock:
            if execution_id is not None:
                clean_eid = self._normalize_id(execution_id)
                if clean_eid in self._execution_subscribers:
                    self._execution_subscribers[clean_eid].discard(queue)
                    if not self._execution_subscribers[clean_eid]:
                        del self._execution_subscribers[clean_eid]
            else:
                if clean_pid in self._project_subscribers:
                    self._project_subscribers[clean_pid].discard(queue)
                    if not self._project_subscribers[clean_pid]:
                        del self._project_subscribers[clean_pid]

    def get_events(
        self,
        project_id: str,
        execution_id: str,
        since_sequence: int = 0,
    ) -> list[ExecutionEvent]:
        """Retrieve buffered events for an execution, ensuring strict project isolation."""
        clean_pid = self._normalize_id(project_id)
        clean_eid = self._normalize_id(execution_id)

        # Check snapshot project ownership
        snapshot = self._active_snapshots.get(clean_eid)
        if snapshot and snapshot.project_id != clean_pid:
            # Cross-project access attempt
            return []

        buf = self._ring_buffers.get(clean_eid)
        if not buf:
            return []

        events: list[ExecutionEvent] = []
        for evt in buf:
            if self._normalize_id(evt.project_id) == clean_pid and evt.sequence > since_sequence:
                events.append(evt)

        return events

    def get_execution_snapshot(
        self,
        project_id: str,
        execution_id: str,
    ) -> ExecutionStateSnapshot | None:
        """Get the current state snapshot of an execution verifying project isolation."""
        clean_pid = self._normalize_id(project_id)
        clean_eid = self._normalize_id(execution_id)

        snapshot = self._active_snapshots.get(clean_eid)
        if not snapshot:
            return None

        if snapshot.project_id != clean_pid:
            # Cross-project isolation boundary enforced
            return None

        return snapshot

    def list_active_executions(self, project_id: str) -> list[ExecutionStateSnapshot]:
        """List active or recent executions for a project."""
        clean_pid = self._normalize_id(project_id)
        return [
            s for s in self._active_snapshots.values()
            if s.project_id == clean_pid
        ]

    def clear(self) -> None:
        """Clear all subscribers and buffers (for testing)."""
        self._project_subscribers.clear()
        self._execution_subscribers.clear()
        self._sequences.clear()
        self._ring_buffers.clear()
        self._active_snapshots.clear()


# Global Singleton Event Bus
_event_bus: InMemoryExecutionEventBus | None = None


def get_event_bus() -> InMemoryExecutionEventBus:
    """Return the global platform event bus singleton."""
    global _event_bus
    if _event_bus is None:
        _event_bus = InMemoryExecutionEventBus()
    return _event_bus
