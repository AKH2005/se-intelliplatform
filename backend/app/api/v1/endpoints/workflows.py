"""Multi-Agent Workflow Execution, Discovery & History API Endpoints.

Provides RESTful HTTP boundaries for discovering predefined multi-agent workflows,
synchronously executing them against canonical project context or immutable snapshots,
and inspecting historical execution runs.

SECURITY NOTE:
These endpoints are designed for the current trusted/local development environment
and MUST NOT be exposed unrestricted to the public internet without an authentication
and abuse/rate-limiting boundary.
"""

import asyncio
import json
import logging
import uuid
from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_optional, get_db, get_workflow_service
from app.core.database import AsyncSessionLocal
from app.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.core.rate_limit import rate_limit_workflow_execution
from app.models.project import Project
from app.models.user import User, UserRole
from app.models.workflow_execution import WorkflowExecution
from app.schemas.workflow import (
    AsyncWorkflowExecutionResponse,
    WorkflowExecuteRequest,
    WorkflowMetadataResponse,
    WorkflowResultResponse,
    WorkflowStatusPollingResponse,
)
from app.schemas.workflow_history import (
    WorkflowExecutionDetailResponse,
    WorkflowExecutionSummaryResponse,
    WorkflowHistoryListResponse,
)
from app.services.workflow_service import WorkflowService
from app.workflows.contracts import WorkflowStatus

logger = logging.getLogger(__name__)

router = APIRouter()
project_workflows_router = APIRouter()


def _create_workflow_service(session: AsyncSession) -> WorkflowService:
    """Instantiate a WorkflowService bound to a specific session."""
    from app.agents.registry import agent_registry, register_all_agents
    from app.api.dependencies import get_agent_executor
    from app.context.engine import ProjectContextEngine
    from app.workflows.coordinator import WorkflowCoordinator

    register_all_agents(agent_registry)
    context_engine = ProjectContextEngine(session=session)
    coordinator = WorkflowCoordinator(executor=get_agent_executor(), registry=agent_registry)
    return WorkflowService(
        session=session,
        context_engine=context_engine,
        coordinator=coordinator,
    )


async def _resolve_project(
    project_id: uuid.UUID,
    session: AsyncSession,
    current_user: User | None = None,
) -> Project:
    stmt = select(Project).where(Project.id == project_id)
    res = await session.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise NotFoundError("Project", str(project_id))

    is_admin = current_user is not None and (
        getattr(current_user, "role", None) == UserRole.ADMIN
        or getattr(current_user, "role", None) == UserRole.ADMIN.value
    )
    if is_admin:
        return project

    if project.owner_id is not None:
        if current_user is None or project.owner_id != current_user.id:
            raise ForbiddenError("You do not have permission to access this project.")
    else:
        from app.core.config import settings
        if settings.ENVIRONMENT in ("production", "staging"):
            raise ForbiddenError("You do not have permission to access unowned or system projects in production.")

    return project


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
    include_extensions: Annotated[bool, Query(description="Include extension workflows (code-generation, browser journeys)")] = True,
) -> list[WorkflowMetadataResponse]:
    """List all available predefined workflows."""
    workflows = service.list_workflows(include_extensions=include_extensions)
    return [service.to_metadata_response(w) for w in workflows]


# ==============================================================================
# 2. Workflow Execution Detail Endpoint (/workflows/executions/{workflow_execution_id})
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


@router.get(
    "/executions/{workflow_execution_id}/status",
    response_model=WorkflowStatusPollingResponse,
    summary="Poll workflow execution status and progress",
    description="Lightweight endpoint for periodic polling of workflow lifecycle state and completion percentage.",
)
async def get_workflow_execution_status(
    workflow_execution_id: uuid.UUID,
    service: Annotated[WorkflowService, Depends(get_workflow_service)],
) -> WorkflowStatusPollingResponse:
    """Retrieve real-time lifecycle status, progress, and error state for polling clients."""
    execution = await service.get_workflow_execution(workflow_execution_id)
    step_count = execution.step_count or 0
    completed_steps = execution.completed_steps or 0
    failed_steps = execution.failed_steps or 0
    skipped_steps = execution.skipped_steps or 0
    processed = completed_steps + failed_steps + skipped_steps

    is_term = execution.status in (
        WorkflowStatus.COMPLETED,
        WorkflowStatus.FAILED,
        WorkflowStatus.PARTIAL_SUCCESS,
    )

    if step_count > 0:
        progress = round(min(100.0, (processed / step_count) * 100), 1)
        if is_term and progress < 100.0:
            progress = 100.0
    else:
        progress = 100.0 if is_term else 10.0

    return WorkflowStatusPollingResponse(
        workflow_execution_id=execution.workflow_execution_id,
        project_id=execution.project_id,
        workflow_id=execution.workflow_id,
        workflow_version=execution.workflow_version,
        status=execution.status,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        step_count=step_count,
        completed_steps=completed_steps,
        failed_steps=failed_steps,
        skipped_steps=skipped_steps,
        progress_percentage=progress,
        is_terminal=is_term,
        errors=execution.errors or [],
        warnings=execution.warnings or [],
    )


@router.get(
    "/executions/{workflow_execution_id}/stream",
    summary="Stream workflow execution progress in real-time via SSE",
    description="Server-Sent Events (SSE) stream emitting progress updates until terminal lifecycle status.",
)
async def stream_workflow_execution(
    workflow_execution_id: uuid.UUID,
) -> StreamingResponse:
    """Stream live workflow execution progress events using Server-Sent Events."""
    async def event_generator():
        for _ in range(120):  # Stream for up to 120 seconds
            async with AsyncSessionLocal() as sse_session:
                stmt = select(WorkflowExecution).where(
                    WorkflowExecution.workflow_execution_id == workflow_execution_id
                )
                res = await sse_session.execute(stmt)
                execution = res.scalar_one_or_none()
                if execution:
                    step_count = execution.step_count or 0
                    completed_steps = execution.completed_steps or 0
                    failed_steps = execution.failed_steps or 0
                    skipped_steps = execution.skipped_steps or 0
                    processed = completed_steps + failed_steps + skipped_steps
                    is_term = execution.status in (
                        WorkflowStatus.COMPLETED,
                        WorkflowStatus.FAILED,
                        WorkflowStatus.PARTIAL_SUCCESS,
                    )
                    progress = (
                        round(min(100.0, (processed / step_count) * 100), 1)
                        if step_count > 0
                        else (100.0 if is_term else 10.0)
                    )

                    status_str = execution.status.value if hasattr(execution.status, "value") else str(execution.status)
                    payload = {
                        "workflow_execution_id": str(execution.workflow_execution_id),
                        "status": status_str,
                        "progress_percentage": progress,
                        "completed_steps": completed_steps,
                        "step_count": step_count,
                        "is_terminal": is_term,
                    }
                    yield f"event: progress\ndata: {json.dumps(payload)}\n\n"
                    if is_term:
                        yield f"event: completed\ndata: {json.dumps(payload)}\n\n"
                        break
            await asyncio.sleep(1.0)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ==============================================================================
# 3. Workflow Definition Detail Endpoint (/workflows/{workflow_id})
# ==============================================================================

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
# 4. Workflow Execution Endpoints (/workflows/{workflow_id}/execute and execute-async)
# ==============================================================================

@router.post(
    "/{workflow_id}/execute",
    response_model=WorkflowResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute a multi-agent workflow synchronously",
    description=(
        "Synchronously executes a predefined multi-agent workflow against canonical project context "
        "or an immutable historical snapshot. Creates a persistent audit record and returns the authoritative "
        "structured WorkflowResult envelope."
    ),
    dependencies=[Depends(rate_limit_workflow_execution)],
)
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecuteRequest,
    service: Annotated[WorkflowService, Depends(get_workflow_service)],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> WorkflowResultResponse:
    """Synchronously execute a multi-agent workflow against project context."""
    await _resolve_project(request.project_id, session, current_user)
    result = await service.execute_workflow(workflow_id=workflow_id, request=request)
    return WorkflowResultResponse.from_workflow_result(result)


@router.post(
    "/{workflow_id}/execute-async",
    response_model=AsyncWorkflowExecutionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Execute a multi-agent workflow asynchronously",
    description=(
        "Dispatches multi-agent workflow execution in a background task. Immediately returns tracking "
        "UUID and polling/streaming URLs for real-time progress monitoring."
    ),
    dependencies=[Depends(rate_limit_workflow_execution)],
)
async def execute_workflow_async(
    workflow_id: str,
    request: WorkflowExecuteRequest,
    background_tasks: BackgroundTasks,
    service: Annotated[WorkflowService, Depends(get_workflow_service)],
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> AsyncWorkflowExecutionResponse:
    """Trigger an asynchronous multi-agent workflow run."""
    await _resolve_project(request.project_id, session, current_user)
    # Ensure workflow definition is valid
    service.get_workflow(workflow_id)

    execution_id = uuid.uuid4()

    async def _run_in_background(exec_id: uuid.UUID) -> None:
        async with AsyncSessionLocal() as bg_session:
            bg_service = _create_workflow_service(bg_session)
            try:
                await bg_service.execute_workflow(
                    workflow_id=workflow_id,
                    request=request,
                    preallocated_execution_id=exec_id,
                )
            except Exception as exc:
                logger.exception(
                    f"Background execution of workflow '{workflow_id}' failed: {exc}"
                )

    background_tasks.add_task(_run_in_background, execution_id)

    return AsyncWorkflowExecutionResponse(
        workflow_execution_id=execution_id,
        project_id=request.project_id,
        workflow_id=workflow_id,
        status=WorkflowStatus.RUNNING,
        status_url=f"/api/v1/workflows/executions/{execution_id}/status",
        stream_url=f"/api/v1/workflows/executions/{execution_id}/stream",
    )


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
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Page limit")] = 20,
    offset: Annotated[int, Query(ge=0, description="Page offset")] = 0,
    workflow_id: Annotated[str | None, Query(description="Filter by workflow ID")] = None,
    status: Annotated[WorkflowStatus | None, Query(description="Filter by execution status")] = None,
) -> WorkflowHistoryListResponse:
    """Retrieve paginated workflow execution history for a given project."""
    await _resolve_project(project_id, session, current_user)
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
