"""Multi-Agent Workflow Execution & Discovery API Endpoints.

Provides RESTful HTTP boundaries for discovering predefined multi-agent workflows
and synchronously executing them against canonical project context or immutable snapshots.

SECURITY NOTE:
These endpoints are designed for the current trusted/local development environment
and MUST NOT be exposed unrestricted to the public internet without an authentication
and abuse/rate-limiting boundary.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_workflow_service
from app.schemas.workflow import (
    WorkflowExecuteRequest,
    WorkflowMetadataResponse,
    WorkflowResultResponse,
)
from app.services.workflow_service import WorkflowService

router = APIRouter()


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


@router.post(
    "/{workflow_id}/execute",
    response_model=WorkflowResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute a multi-agent workflow",
    description=(
        "Synchronously executes a predefined multi-agent workflow against canonical project context "
        "or an immutable historical snapshot. Returns the authoritative structured WorkflowResult envelope."
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
