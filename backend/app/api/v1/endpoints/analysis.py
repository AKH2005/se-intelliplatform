"""Static Analysis API Endpoints."""

import uuid
from typing import Annotated, Any
from fastapi import APIRouter, Depends, Path, status
from sqlalchemy import select

from app.api.dependencies import get_static_analysis_service
from app.core.exceptions import NotFoundError
from app.models.agent_audit import AgentExecutionAudit
from app.sandbox.static_analysis.contracts import (
    StaticAnalysisRequest,
    StaticAnalysisResult,
)
from app.sandbox.static_analysis.service import StaticAnalysisService

router = APIRouter()


@router.post(
    "/static",
    response_model=StaticAnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Run deterministic static analysis on generated project artifact",
    description=(
        "Executes a multi-stage static analysis pipeline (security check, AST parsing, "
        "import/dependency analysis, test discovery, and containerized Ruff linting) "
        "on a verified code generation artifact."
    ),
)
async def run_static_analysis(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    request: StaticAnalysisRequest,
    service: Annotated[StaticAnalysisService, Depends(get_static_analysis_service)],
) -> StaticAnalysisResult:
    """Execute static analysis on project code artifact."""
    if request.project_id != project_id:
        request = request.model_copy(update={"project_id": project_id})

    return await service.analyze(request)


@router.get(
    "/static/{analysis_id}",
    response_model=StaticAnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Get persisted static analysis result by analysis ID",
    description="Retrieves a historical static analysis execution outcome from the persistent audit trail.",
)
async def get_static_analysis_result(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    analysis_id: Annotated[uuid.UUID, Path(description="Analysis UUID")],
    service: Annotated[StaticAnalysisService, Depends(get_static_analysis_service)],
) -> StaticAnalysisResult:
    """Retrieve persisted static analysis report."""
    stmt = (
        select(AgentExecutionAudit)
        .where(AgentExecutionAudit.project_id == project_id)
        .where(AgentExecutionAudit.execution_id == analysis_id)
        .where(AgentExecutionAudit.agent_id == "static-analysis-runner")
    )
    res = await service.session.execute(stmt)
    record = res.scalar_one_or_none()

    if not record or not record.metadata_payload:
        raise NotFoundError(resource_type="StaticAnalysisResult", identifier=analysis_id)

    return StaticAnalysisResult.model_validate(record.metadata_payload)


# ==============================================================================
# Failure Analysis Endpoints (Phase 11D)
# ==============================================================================

from pydantic import BaseModel, ConfigDict, Field
from app.agents.failure_analysis.contracts import FailureDiagnosis, FailureSource
from app.agents.failure_analysis.service import FailureAnalysisService
from app.api.dependencies import get_failure_analysis_service


class FailureAnalysisApiRequest(BaseModel):
    """Request payload for triggering Failure Analysis."""

    model_config = ConfigDict(extra="forbid")

    workflow_execution_id: uuid.UUID | None = Field(
        default=None,
        description="Optional workflow execution UUID to analyze. Defaults to latest execution.",
    )
    force: bool = Field(
        default=False,
        description="Force AI failure analysis even if execution and static checks passed with zero errors.",
    )
    failure_source: FailureSource | None = Field(
        default=None,
        description="Optional failure source filter (e.g. AI_TEST, SANDBOX, STATIC_ANALYSIS).",
    )


@router.post(
    "/failure",
    response_model=FailureDiagnosis,
    status_code=status.HTTP_200_OK,
    summary="Run AI failure analysis and diagnostic reasoning",
    description=(
        "Consumes deterministic execution and static analysis evidence to formulate "
        "a grounded, structured root-cause failure diagnosis."
    ),
)
async def run_failure_analysis(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    request: FailureAnalysisApiRequest,
    service: Annotated[FailureAnalysisService, Depends(get_failure_analysis_service)],
) -> FailureDiagnosis:
    """Execute failure analysis on project execution and static analysis artifacts."""
    return await service.analyze_failure(
        project_id=project_id,
        workflow_execution_id=request.workflow_execution_id,
        force=request.force,
        failure_source=request.failure_source,
    )


@router.get(
    "/failure/{diagnosis_id}",
    response_model=FailureDiagnosis,
    status_code=status.HTTP_200_OK,
    summary="Get persisted failure diagnosis by diagnosis ID",
    description="Retrieves a historical failure diagnosis from the audit trail.",
)
async def get_failure_diagnosis(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    diagnosis_id: Annotated[uuid.UUID, Path(description="Diagnosis UUID")],
    service: Annotated[FailureAnalysisService, Depends(get_failure_analysis_service)],
) -> FailureDiagnosis:
    """Retrieve persisted failure diagnosis."""
    # 1. Resolve from WorkflowExecution artifacts
    from app.models.workflow_execution import WorkflowExecution
    stmt_wf = (
        select(WorkflowExecution)
        .where(WorkflowExecution.project_id == project_id)
        .order_by(WorkflowExecution.started_at.desc())
    )
    wf_res = await service.session.execute(stmt_wf)
    for wf in wf_res.scalars().all():
        for key in ("failure_analysis", "ai_test_failure_analysis"):
            fa_dict = wf.artifacts.get(key)
            if fa_dict and (
                fa_dict.get("diagnosis_id") == str(diagnosis_id)
                or str(wf.workflow_execution_id) == str(diagnosis_id)
            ):
                return FailureDiagnosis.model_validate(fa_dict)

    # 2. Fallback to AgentExecutionAudit
    stmt = (
        select(AgentExecutionAudit)
        .where(AgentExecutionAudit.project_id == project_id)
        .where(AgentExecutionAudit.execution_id == diagnosis_id)
        .where(AgentExecutionAudit.agent_id == "failure-analysis")
    )
    res = await service.session.execute(stmt)
    record = res.scalar_one_or_none()

    if record and record.metadata_payload and "failure_type" in record.metadata_payload:
        return FailureDiagnosis.model_validate(record.metadata_payload)

    raise NotFoundError(resource_type="FailureDiagnosis", identifier=diagnosis_id)

