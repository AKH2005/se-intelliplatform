"""Unit Tests for Phase 12 Telemetry Contracts, Event Bus, Redaction & Publisher."""

import asyncio
import pytest
from app.telemetry.bus import InMemoryExecutionEventBus, get_event_bus
from app.telemetry.contracts import (
    EventSeverity,
    ExecutionEvent,
    ExecutionEventType,
    ExecutionKind,
    MAX_SUBSCRIBERS_PER_PROJECT,
)
from app.telemetry.publisher import ExecutionEventPublisher
from app.telemetry.redaction import sanitize_event_payload


@pytest.mark.asyncio
async def test_telemetry_event_model():
    """Verify ExecutionEvent schema validation, defaults, and monotonic sequencing."""
    evt = ExecutionEvent(
        event_type=ExecutionEventType.WORKFLOW_STARTED,
        project_id="proj-123",
        execution_id="exec-456",
        correlation_id="corr-789",
        execution_kind=ExecutionKind.WORKFLOW,
        source="WorkflowCoordinator",
        status="RUNNING",
        sequence=1,
        payload={"step_count": 3},
    )
    assert evt.event_id is not None
    assert evt.sequence == 1
    assert evt.severity == EventSeverity.INFO
    assert evt.payload["step_count"] == 3

    # Extra fields forbidden
    with pytest.raises(Exception):
        ExecutionEvent(
            event_type=ExecutionEventType.WORKFLOW_STARTED,
            project_id="proj-123",
            execution_id="exec-456",
            correlation_id="corr-789",
            execution_kind=ExecutionKind.WORKFLOW,
            source="WorkflowCoordinator",
            status="RUNNING",
            sequence=1,
            invalid_field="not_allowed",  # type: ignore
        )


def test_secret_redaction():
    """Verify sensitive fields and credentials are redacted in payloads."""
    raw_payload = {
        "user": "developer",
        "api_key": "secret-key-123",
        "nested": {
            "password": "my_password",
            "db_token": "bearer-token",
            "public_info": "safe_value",
        },
        "safe_list": ["val1", {"client_secret": "hidden"}],
    }
    sanitized = sanitize_event_payload(raw_payload)
    assert sanitized["user"] == "developer"
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["nested"]["password"] == "[REDACTED]"
    assert sanitized["nested"]["db_token"] == "[REDACTED]"
    assert sanitized["nested"]["public_info"] == "safe_value"
    assert sanitized["safe_list"][1]["client_secret"] == "[REDACTED]"


@pytest.mark.asyncio
async def test_event_bus_publish_and_subscribe():
    """Verify event bus delivers events to project and execution subscribers."""
    bus = InMemoryExecutionEventBus()
    project_id = "proj-alpha"
    exec_id = "exec-beta"

    proj_queue = await bus.subscribe(project_id)
    exec_queue = await bus.subscribe(project_id, execution_id=exec_id)

    evt = ExecutionEvent(
        event_type=ExecutionEventType.WORKFLOW_STARTED,
        project_id=project_id,
        execution_id=exec_id,
        correlation_id="corr-1",
        execution_kind=ExecutionKind.WORKFLOW,
        source="WorkflowCoordinator",
        status="RUNNING",
        sequence=1,
        payload={"workflow_id": "test-wf"},
    )

    published = await bus.publish(evt)
    assert published.event_id == evt.event_id

    # Both project and execution queues should receive it
    received_proj = await asyncio.wait_for(proj_queue.get(), timeout=1.0)
    received_exec = await asyncio.wait_for(exec_queue.get(), timeout=1.0)

    assert received_proj.execution_id == exec_id
    assert received_exec.execution_id == exec_id

    # Snapshot check
    snap = bus.get_execution_snapshot(project_id, exec_id)
    assert snap is not None
    assert snap.status == "RUNNING"
    assert snap.total_events == 1

    # Cleanup
    await bus.unsubscribe(proj_queue, project_id)
    await bus.unsubscribe(exec_queue, project_id, execution_id=exec_id)


@pytest.mark.asyncio
async def test_event_bus_project_isolation():
    """Verify that subscriber for Project A does NOT receive events from Project B."""
    bus = InMemoryExecutionEventBus()

    queue_a = await bus.subscribe("proj-a")
    queue_b = await bus.subscribe("proj-b")

    evt_a = ExecutionEvent(
        event_type=ExecutionEventType.AGENT_STARTED,
        project_id="proj-a",
        execution_id="exec-a1",
        correlation_id="corr-a",
        execution_kind=ExecutionKind.AGENT,
        source="AgentExecutor",
        status="RUNNING",
        sequence=1,
    )
    await bus.publish(evt_a)

    # Queue A should get it
    received_a = await asyncio.wait_for(queue_a.get(), timeout=1.0)
    assert received_a.project_id == "proj-a"

    # Queue B should receive nothing
    assert queue_b.empty()

    # Replay isolation: project B cannot fetch project A events
    replayed = bus.get_events("proj-b", "exec-a1")
    assert len(replayed) == 0

    await bus.unsubscribe(queue_a, "proj-a")
    await bus.unsubscribe(queue_b, "proj-b")


@pytest.mark.asyncio
async def test_execution_publisher_safe_emit():
    """Verify ExecutionEventPublisher safely handles emission and sequence numbering."""
    bus = get_event_bus()
    bus.clear()

    project_id = "proj-pub"
    exec_id = "exec-pub-1"

    queue = await bus.subscribe(project_id)

    evt1 = await ExecutionEventPublisher.emit(
        event_type=ExecutionEventType.WORKFLOW_STARTED,
        project_id=project_id,
        execution_id=exec_id,
        execution_kind=ExecutionKind.WORKFLOW,
        source="WorkflowCoordinator",
        status="RUNNING",
        payload={"step": "init"},
    )
    assert evt1 is not None
    assert evt1.sequence == 1

    evt2 = await ExecutionEventPublisher.emit(
        event_type=ExecutionEventType.WORKFLOW_COMPLETED,
        project_id=project_id,
        execution_id=exec_id,
        execution_kind=ExecutionKind.WORKFLOW,
        source="WorkflowCoordinator",
        status="COMPLETED",
        payload={"duration_seconds": 1.25},
    )
    assert evt2 is not None
    assert evt2.sequence == 2

    # Verify monotonic ordering in subscriber queue
    q_evt1 = await queue.get()
    q_evt2 = await queue.get()
    assert q_evt1.sequence == 1
    assert q_evt2.sequence == 2

    await bus.unsubscribe(queue, project_id)
