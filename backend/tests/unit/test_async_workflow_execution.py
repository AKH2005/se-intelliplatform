"""Unit tests for Asynchronous Workflow Execution, Polling, and Streaming."""

import json
import uuid
from datetime import datetime, timezone
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.api.v1.endpoints.workflows import (
    execute_workflow_async,
    get_workflow_execution_status,
    stream_workflow_execution,
)
from app.models.workflow_execution import WorkflowExecution
from app.schemas.workflow import (
    AsyncWorkflowExecutionResponse,
    WorkflowExecuteRequest,
    WorkflowStatusPollingResponse,
)
from app.workflows.contracts import WorkflowStatus


def test_async_workflow_schemas():
    """Verify AsyncWorkflowExecutionResponse and WorkflowStatusPollingResponse construct properly."""
    exec_id = uuid.uuid4()
    proj_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    async_res = AsyncWorkflowExecutionResponse(
        workflow_execution_id=exec_id,
        project_id=proj_id,
        workflow_id="software-design-workflow",
        status=WorkflowStatus.RUNNING,
        status_url=f"/api/v1/workflows/executions/{exec_id}/status",
        stream_url=f"/api/v1/workflows/executions/{exec_id}/stream",
    )
    assert async_res.workflow_execution_id == exec_id
    assert async_res.status == WorkflowStatus.RUNNING
    assert "status" in async_res.status_url

    poll_res = WorkflowStatusPollingResponse(
        workflow_execution_id=exec_id,
        project_id=proj_id,
        workflow_id="software-design-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.RUNNING,
        started_at=now,
        step_count=4,
        completed_steps=2,
        failed_steps=0,
        skipped_steps=0,
        progress_percentage=50.0,
        is_terminal=False,
    )
    assert poll_res.progress_percentage == 50.0
    assert poll_res.is_terminal is False


@pytest.mark.asyncio
async def test_get_workflow_execution_status_endpoint():
    """Verify get_workflow_execution_status calculates progress percentage and terminal state."""
    exec_id = uuid.uuid4()
    proj_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    execution = WorkflowExecution(
        workflow_execution_id=exec_id,
        project_id=proj_id,
        workflow_id="software-design-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        started_at=now,
        completed_at=now,
        step_count=4,
        completed_steps=4,
        failed_steps=0,
        skipped_steps=0,
        errors=[],
        warnings=[],
    )

    mock_service = MagicMock()
    mock_service.get_workflow_execution = AsyncMock(return_value=execution)

    res = await get_workflow_execution_status(exec_id, service=mock_service)
    assert res.workflow_execution_id == exec_id
    assert res.status == WorkflowStatus.COMPLETED
    assert res.progress_percentage == 100.0
    assert res.is_terminal is True


@pytest.mark.asyncio
async def test_execute_workflow_async_endpoint():
    """Verify execute_workflow_async validates workflow and queues background task."""
    workflow_id = "software-design-workflow"
    project_id = uuid.uuid4()
    request = WorkflowExecuteRequest(project_id=project_id)

    mock_service = MagicMock()
    mock_service.get_workflow.return_value = MagicMock()

    mock_session = AsyncMock()
    mock_background_tasks = MagicMock()

    # Mock _resolve_project to succeed
    with patch("app.api.v1.endpoints.workflows._resolve_project", AsyncMock()):
        response = await execute_workflow_async(
            workflow_id=workflow_id,
            request=request,
            background_tasks=mock_background_tasks,
            service=mock_service,
            session=mock_session,
            current_user=None,
        )

        assert response.workflow_id == workflow_id
        assert response.project_id == project_id
        assert response.status == WorkflowStatus.RUNNING
        assert str(response.workflow_execution_id) in response.status_url
        assert str(response.workflow_execution_id) in response.stream_url
        # Background task must be added
        mock_background_tasks.add_task.assert_called_once()
