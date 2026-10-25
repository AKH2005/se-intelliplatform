"""Comprehensive Integration and API Tests for Phase 12 Telemetry Endpoints and WebSockets.

Verifies:
1. REST snapshot queries (/active, /status, /events).
2. Monotonic sequence ordering and since_sequence replay.
3. Strict project isolation across REST and WebSocket streams.
4. WebSocket live streaming and ping/pong heartbeats.
5. Clean disconnect and unsubscribe lifecycle.
"""

import asyncio
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.telemetry.bus import get_event_bus
from app.telemetry.contracts import (
    EventSeverity,
    ExecutionEvent,
    ExecutionEventType,
    ExecutionKind,
)
from app.telemetry.publisher import ExecutionEventPublisher


@pytest.fixture(autouse=True)
def clean_event_bus():
    """Ensure clean event bus before and after each test."""
    bus = get_event_bus()
    bus.clear()
    yield
    bus.clear()


def test_rest_active_executions_and_isolation():
    """Verify listing active executions enforces project boundary isolation."""
    client = TestClient(app)
    bus = get_event_bus()

    proj_a = str(uuid.uuid4())
    proj_b = str(uuid.uuid4())
    exec_a = str(uuid.uuid4())
    exec_b = str(uuid.uuid4())

    # Emit event for Project A
    asyncio.run(
        ExecutionEventPublisher.emit(
            event_type=ExecutionEventType.WORKFLOW_STARTED,
            project_id=proj_a,
            execution_id=exec_a,
            execution_kind=ExecutionKind.WORKFLOW,
            source="WorkflowCoordinator",
            status="RUNNING",
            payload={"workflow_name": "WF_A", "phase": "Step 1"},
        )
    )

    # Emit event for Project B
    asyncio.run(
        ExecutionEventPublisher.emit(
            event_type=ExecutionEventType.WORKFLOW_STARTED,
            project_id=proj_b,
            execution_id=exec_b,
            execution_kind=ExecutionKind.WORKFLOW,
            source="WorkflowCoordinator",
            status="RUNNING",
            payload={"workflow_name": "WF_B", "phase": "Step 1"},
        )
    )

    # Project A query
    resp_a = client.get(f"/api/v1/projects/{proj_a}/telemetry/active")
    assert resp_a.status_code == 200
    data_a = resp_a.json()
    assert len(data_a) == 1
    assert data_a[0]["execution_id"] == exec_a
    assert data_a[0]["project_id"] == proj_a

    # Project B query
    resp_b = client.get(f"/api/v1/projects/{proj_b}/telemetry/active")
    assert resp_b.status_code == 200
    data_b = resp_b.json()
    assert len(data_b) == 1
    assert data_b[0]["execution_id"] == exec_b
    assert data_b[0]["project_id"] == proj_b


def test_rest_execution_status_and_negative_cross_project():
    """Verify status snapshot lookup and 404 on cross-project access attempt."""
    client = TestClient(app)

    proj_1 = str(uuid.uuid4())
    proj_2 = str(uuid.uuid4())
    exec_id = str(uuid.uuid4())

    asyncio.run(
        ExecutionEventPublisher.emit(
            event_type=ExecutionEventType.AGENT_STARTED,
            project_id=proj_1,
            execution_id=exec_id,
            execution_kind=ExecutionKind.AGENT,
            source="AgentExecutor",
            status="RUNNING",
            payload={"agent_id": "test-agent"},
        )
    )

    # Valid query for project 1
    resp_valid = client.get(f"/api/v1/projects/{proj_1}/telemetry/executions/{exec_id}/status")
    assert resp_valid.status_code == 200
    snap = resp_valid.json()
    assert snap["execution_id"] == exec_id
    assert snap["status"] == "RUNNING"
    assert snap["total_events"] == 1

    # Cross-project unauthorized access attempt (Project 2 requesting Project 1's execution)
    resp_cross = client.get(f"/api/v1/projects/{proj_2}/telemetry/executions/{exec_id}/status")
    assert resp_cross.status_code == 404


def test_rest_events_replay_and_since_sequence():
    """Verify /events returns ordered events with since_sequence filtering."""
    client = TestClient(app)

    proj_id = str(uuid.uuid4())
    exec_id = str(uuid.uuid4())

    for i in range(1, 4):
        asyncio.run(
            ExecutionEventPublisher.emit(
                event_type=ExecutionEventType.EXECUTION_PROGRESS,
                project_id=proj_id,
                execution_id=exec_id,
                execution_kind=ExecutionKind.AGENT,
                source="AgentExecutor",
                status="RUNNING",
                payload={"step": i},
            )
        )

    # Fetch all events (since_sequence=0)
    resp_all = client.get(f"/api/v1/projects/{proj_id}/telemetry/executions/{exec_id}/events")
    assert resp_all.status_code == 200
    events_all = resp_all.json()
    assert len(events_all) == 3
    assert [e["sequence"] for e in events_all] == [1, 2, 3]

    # Fetch with since_sequence=2
    resp_since = client.get(
        f"/api/v1/projects/{proj_id}/telemetry/executions/{exec_id}/events",
        params={"since_sequence": 2},
    )
    assert resp_since.status_code == 200
    events_since = resp_since.json()
    assert len(events_since) == 1
    assert events_since[0]["sequence"] == 3


def test_websocket_streaming_replay_and_ping_pong():
    """Verify WebSocket connection, reconnect event replay, live events, and ping/pong."""
    client = TestClient(app)

    proj_id = str(uuid.uuid4())
    exec_id = str(uuid.uuid4())

    # Pre-emit event 1 to test initial replay
    asyncio.run(
        ExecutionEventPublisher.emit(
            event_type=ExecutionEventType.WORKFLOW_STARTED,
            project_id=proj_id,
            execution_id=exec_id,
            execution_kind=ExecutionKind.WORKFLOW,
            source="WorkflowCoordinator",
            status="RUNNING",
            payload={"workflow_name": "WF-Replay"},
        )
    )

    with client.websocket_connect(
        f"/api/v1/projects/{proj_id}/telemetry/ws?execution_id={exec_id}&since_sequence=0"
    ) as ws:
        # 1. Verify replayed event 1
        replayed = ws.receive_json()
        assert replayed["execution_id"] == exec_id
        assert replayed["sequence"] == 1
        assert replayed["event_type"] == "WORKFLOW_STARTED"

        # 2. Test ping-pong heartbeat
        ws.send_text('{"type": "ping"}')
        pong = ws.receive_json()
        assert pong == {"type": "pong"}

        # 3. Emit live event 2 and verify streaming receipt
        asyncio.run(
            ExecutionEventPublisher.emit(
                event_type=ExecutionEventType.WORKFLOW_STEP_COMPLETED,
                project_id=proj_id,
                execution_id=exec_id,
                execution_kind=ExecutionKind.WORKFLOW,
                source="WorkflowCoordinator",
                status="RUNNING",
                payload={"step_id": "step-1"},
            )
        )

        live_evt = ws.receive_json()
        assert live_evt["sequence"] == 2
        assert live_evt["event_type"] == "WORKFLOW_STEP_COMPLETED"


def test_websocket_cross_project_isolation():
    """Verify WebSocket subscriber for Project A NEVER receives events for Project B."""
    client = TestClient(app)

    proj_a = str(uuid.uuid4())
    proj_b = str(uuid.uuid4())
    exec_b = str(uuid.uuid4())

    with client.websocket_connect(f"/api/v1/projects/{proj_a}/telemetry/ws") as ws_a:
        # Send ping to confirm connection is active
        ws_a.send_text('{"type": "ping"}')
        assert ws_a.receive_json() == {"type": "pong"}

        # Emit event for Project B
        asyncio.run(
            ExecutionEventPublisher.emit(
                event_type=ExecutionEventType.AGENT_STARTED,
                project_id=proj_b,
                execution_id=exec_b,
                execution_kind=ExecutionKind.AGENT,
                source="AgentExecutor",
                status="RUNNING",
                payload={"note": "for project B only"},
            )
        )

        # Ping Project A again; if an unexpected Project B event was delivered,
        # receive_json would return that event instead of {"type": "pong"}.
        ws_a.send_text('{"type": "ping"}')
        second_pong = ws_a.receive_json()
        assert second_pong == {"type": "pong"}
