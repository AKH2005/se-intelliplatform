"""Multi-Agent Workflow Execution, Discovery & History API Endpoints.

Provides RESTful HTTP boundaries for discovering predefined multi-agent workflows,
synchronously executing them against canonical project context or immutable snapshots,
and inspecting historical execution runs.

SECURITY NOTE:
These endpoints are designed for the current trusted/local development environment
and MUST NOT be exposed unrestricted to the public internet without an authentication
and abuse/rate-limiting boundary.
"""

import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_workflow_service
from app.schemas.workflow import (
    WorkflowExecuteRequest,
    WorkflowMetadataResponse,
    WorkflowResultResponse,
)
from app.schemas.workflow_history import (
    WorkflowExecutionDetailResponse,
    WorkflowExecutionSummaryResponse,
    WorkflowHistoryListResponse,
)
from app.services.workflow_service import WorkflowService
from app.workflows.contracts import WorkflowStatus

router = APIRouter()
project_workflows_router = APIRouter()


# ==============================================================================
# 1. Workflow Pipeline Discovery Endpoints (/workflows)
# ==============================================================================

@router.get(
    "",
    response_model=list[WorkflowMetadataResponse],
    summary="List available workflow pipelines",
    description=(
        "Returns declarative discovery metadata for all predefined multi-agent workflows. "
        "Exposes step graphs, dependency relationships, and input requirements without executing pipelines."
    ),
)
async def list_workflows(
    service: Annotated[WorkflowService, Depends(get_workflow_service)],
) -> list[WorkflowMetadataResponse]:
    """List all available predefined workflows."""
    workflows = service.list_workflows()
    return [service.to_metadata_response(w) for w in workflows]


@router.get(
    "/{workflow_id}",
    response_model=WorkflowMetadataResponse,
    summary="Get workflow definition details",
    description=(
        "Retrieves detailed declarative metadata, ordered steps, and dependency invariants "
        "for a specific predefined workflow pipeline."
    ),
)
async def get_workflow(
    workflow_id: str,
    service: Annotated[WorkflowService, Depends(get_workflow_service)],
) -> WorkflowMetadataResponse:
    """Get metadata for a specific predefined workflow by ID."""
    workflow = service.get_workflow(workflow_id)
    return service.to_metadata_response(workflow)


# ==============================================================================
# 2. Workflow Execution Endpoint (/workflows/{workflow_id}/execute)
# ==============================================================================

@router.post(
    "/{workflow_id}/execute",
    response_model=WorkflowResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute a multi-agent workflow",
    description=(
        "Synchronously executes a predefined multi-agent workflow against canonical project context "
        "or an immutable historical snapshot. Creates a persistent audit record and returns the authoritative "
        "structured WorkflowResult envelope."
    ),
)
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecuteRequest,
    service: Annotated[WorkflowService, Depends(get_workflow_service)],
) -> WorkflowResultResponse:
    """Synchronously execute a multi-agent workflow against project context."""
    result = await service.execute_workflow(workflow_id=workflow_id, request=request)
    return WorkflowResultResponse.from_workflow_result(result)


# ==============================================================================
# 3. Workflow Execution Detail Endpoint (/workflows/executions/{workflow_execution_id})
# ==============================================================================

@router.get(
    "/executions/{workflow_execution_id}",
    response_model=WorkflowExecutionDetailResponse,
    summary="Get workflow execution run detail",
    description=(
        "Retrieves the authoritative persisted execution record for a multi-agent workflow run, "
        "including terminal status, step counts, validated domain artifacts, and sanitized metadata."
    ),
)
async def get_workflow_execution_detail(
    workflow_execution_id: uuid.UUID,
    service: Annotated[WorkflowService, Depends(get_workflow_service)],
) -> WorkflowExecutionDetailResponse:
    """Retrieve detailed persisted outcome for a specific workflow execution."""
    execution = await service.get_workflow_execution(workflow_execution_id)
    return WorkflowExecutionDetailResponse.from_orm_model(execution)


# ==============================================================================
# 4. Project-Scoped Workflow History (/projects/{project_id}/workflows/history)
# ==============================================================================

@project_workflows_router.get(
    "/history",
    response_model=WorkflowHistoryListResponse,
    summary="List project workflow execution history",
    description=(
        "Returns a paginated list of historical workflow execution summaries for a project, "
        "ordered newest first. Supports optional filtering by workflow_id and execution status."
    ),
)
async def list_project_workflow_history(
    project_id: uuid.UUID,
    service: Annotated[WorkflowService, Depends(get_workflow_service)],
    limit: Annotated[int, Query(ge=1, le=100, description="Page limit")] = 20,
    offset: Annotated[int, Query(ge=0, description="Page offset")] = 0,
    workflow_id: Annotated[str | None, Query(description="Filter by workflow ID")] = None,
    status: Annotated[WorkflowStatus | None, Query(description="Filter by execution status")] = None,
) -> WorkflowHistoryListResponse:
    """Retrieve paginated workflow execution history for a given project."""
    records, total = await service.list_project_workflow_history(
        project_id=project_id,
        limit=limit,
        offset=offset,
        workflow_id=workflow_id,
        status=status,
    )
    items = [WorkflowExecutionSummaryResponse.from_orm_model(rec) for rec in records]
    return WorkflowHistoryListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )
