"""Authoritative Real-Time Execution Telemetry API Endpoints for Phase 12.

Provides REST snapshots and WebSocket streaming for execution telemetry,
strictly isolated by project_id with reconnect replay and backpressure safeguards.
"""

import asyncio
import json
import logging
import uuid
from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    Path,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from starlette.websockets import WebSocketState

from app.telemetry.bus import get_event_bus
from app.telemetry.contracts import ExecutionEvent, ExecutionStateSnapshot

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/active",
    response_model=list[ExecutionStateSnapshot],
    summary="List active or recent executions for a project",
)
async def list_active_executions(
    project_id: str = Path(..., description="Project UUID"),
) -> list[ExecutionStateSnapshot]:
    """Return all active or recent executions for the specified project."""
    bus = get_event_bus()
    return bus.list_active_executions(project_id)


@router.get(
    "/executions/{execution_id}/status",
    response_model=ExecutionStateSnapshot,
    summary="Get execution state snapshot",
)
async def get_execution_status(
    project_id: str = Path(..., description="Project UUID"),
    execution_id: str = Path(..., description="Execution UUID"),
) -> ExecutionStateSnapshot:
    """Retrieve current state snapshot for an execution, ensuring project isolation."""
    bus = get_event_bus()
    snapshot = bus.get_execution_snapshot(project_id, execution_id)
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution '{execution_id}' not found or access denied.",
        )
    return snapshot


@router.get(
    "/executions/{execution_id}/events",
    response_model=list[ExecutionEvent],
    summary="Get buffered execution events for replay",
)
async def get_execution_events(
    project_id: str = Path(..., description="Project UUID"),
    execution_id: str = Path(..., description="Execution UUID"),
    since_sequence: int = Query(0, ge=0, description="Retrieve events with sequence greater than this"),
) -> list[ExecutionEvent]:
    """Retrieve ordered execution events since a specific sequence number."""
    bus = get_event_bus()
    return bus.get_events(project_id, execution_id, since_sequence=since_sequence)


@router.websocket("/ws")
async def telemetry_websocket(
    websocket: WebSocket,
    project_id: str = Path(..., description="Project UUID"),
    execution_id: str | None = Query(None, description="Optional Execution UUID filter"),
    since_sequence: int = Query(0, ge=0, description="Sequence offset for reconnect replay"),
) -> None:
    """WebSocket endpoint for real-time execution event streaming.

    Features:
    - Guaranteed project boundary isolation.
    - Automatic replay of buffered events starting from since_sequence.
    - Non-blocking push for newly published execution events.
    - Heartbeat ping-pong support.
    - Guaranteed cleanup on client disconnect.
    """
    await websocket.accept()

    bus = get_event_bus()
    queue = None

    try:
        # 1. Subscribe to event bus
        queue = await bus.subscribe(project_id=project_id, execution_id=execution_id)

        # 2. Replay buffered events since requested sequence
        if execution_id:
            historical_events = bus.get_events(
                project_id=project_id,
                execution_id=execution_id,
                since_sequence=since_sequence,
            )
            for evt in historical_events:
                await websocket.send_json(evt.model_dump(mode="json"))

        # 3. Stream live events and handle incoming client messages
        async def client_listener() -> None:
            """Listen for client heartbeats or control messages."""
            try:
                while True:
                    data = await websocket.receive_text()
                    try:
                        parsed = json.loads(data)
                        if parsed.get("type") == "ping":
                            await websocket.send_json({"type": "pong"})
                    except Exception:
                        pass
            except (WebSocketDisconnect, asyncio.CancelledError):
                pass

        client_task = asyncio.create_task(client_listener())

        try:
            while True:
                # Wait for next event from queue
                event = await queue.get()
                # Strict double-check on project isolation
                if str(event.project_id).strip().lower() == str(project_id).strip().lower():
                    await websocket.send_json(event.model_dump(mode="json"))
        finally:
            client_task.cancel()
            try:
                await client_task
            except asyncio.CancelledError:
                pass

    except (WebSocketDisconnect, asyncio.CancelledError):
        logger.debug(
            f"Telemetry WebSocket disconnected or cancelled for project [{project_id}]"
        )
    except Exception as exc:
        logger.warning(f"Telemetry WebSocket error for project [{project_id}]: {exc}")
    finally:
        if queue is not None:
            try:
                await asyncio.shield(
                    bus.unsubscribe(
                        queue,
                        project_id=project_id,
                        execution_id=execution_id,
                    )
                )
            except (Exception, asyncio.CancelledError):
                pass

        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.close()
        except (Exception, asyncio.CancelledError):
            pass
