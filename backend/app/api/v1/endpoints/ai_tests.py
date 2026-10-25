"""AI-Generated Testing API Endpoints: Generation, Retrieval, and Ephemeral Sandbox Execution."""

import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Path, status
from pydantic import BaseModel, ConfigDict, Field

from app.agents.test_generation.contracts import (
    AITestExecutionResult,
    AITestSuite,
    TestCategory,
)
from app.agents.test_generation.service import AITestService
from app.api.dependencies import get_ai_test_service

router = APIRouter()


class GenerateAITestsRequest(BaseModel):
    """Payload to trigger AI test generation against verified code artifact."""

    model_config = ConfigDict(extra="forbid")

    workflow_execution_id: uuid.UUID | None = Field(
        default=None,
        description="Optional specific workflow execution to test. Defaults to latest.",
    )
    allowed_categories: list[TestCategory] | None = Field(
        default=None,
        description="Optional subset of test categories to focus on.",
    )


class ExecuteAITestsRequest(BaseModel):
    """Payload to execute an AI test suite inside the ephemeral Docker sandbox."""

    model_config = ConfigDict(extra="forbid")

    workflow_execution_id: uuid.UUID | None = Field(
        default=None,
        description="Optional workflow execution UUID. Defaults to latest.",
    )
    timeout_seconds: int = Field(
        default=30,
        ge=5,
        le=60,
        description="Execution timeout in seconds.",
    )


@router.post(
    "/generate",
    response_model=AITestSuite,
    status_code=status.HTTP_201_CREATED,
    summary="Generate structured pytest tests for generated software",
    description=(
        "Analyzes verified code generation artifact, requirements, and static analysis "
        "to produce structured, deterministically validated pytest tests. "
        "The original software artifact remains completely unchanged."
    ),
)
async def generate_tests(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    service: Annotated[AITestService, Depends(get_ai_test_service)],
    request: GenerateAITestsRequest | None = None,
) -> AITestSuite:
    """Generate, validate, and compile an authoritative AI test suite."""
    wf_id = request.workflow_execution_id if request else None
    categories = request.allowed_categories if request else None

    return await service.generate_tests(
        project_id=project_id,
        workflow_execution_id=wf_id,
        allowed_categories=categories,
    )


@router.get(
    "/latest",
    response_model=AITestSuite | None,
    status_code=status.HTTP_200_OK,
    summary="Get latest AI test suite for project",
    description="Retrieves the most recently generated AI test suite from project workflow artifacts.",
)
async def get_latest_test_suite(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    service: Annotated[AITestService, Depends(get_ai_test_service)],
) -> AITestSuite | None:
    """Retrieve the latest AI test suite for the project, if one exists."""
    return await service.get_latest_test_suite(project_id=project_id)


@router.get(
    "/{suite_id}",
    response_model=AITestSuite,
    status_code=status.HTTP_200_OK,
    summary="Retrieve AI test suite by ID",
    description="Fetches a specific generated test suite by its unique identifier.",
)
async def get_test_suite(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    suite_id: Annotated[uuid.UUID, Path(description="Suite UUID")],
    service: Annotated[AITestService, Depends(get_ai_test_service)],
) -> AITestSuite:
    """Retrieve an existing AI test suite."""
    return await service.get_test_suite(
        project_id=project_id,
        suite_id=suite_id,
    )


@router.post(
    "/{suite_id}/execute",
    response_model=AITestExecutionResult,
    status_code=status.HTTP_200_OK,
    summary="Execute AI test suite in isolated ephemeral sandbox",
    description=(
        "Executes validated AI tests inside the hardened Docker sandbox with network disabled. "
        "Generated tests run ephemerally alongside original code without mutating the application artifact. "
        "Does NOT trigger autonomous remediation loops."
    ),
)
async def execute_tests(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    suite_id: Annotated[uuid.UUID, Path(description="Suite UUID")],
    service: Annotated[AITestService, Depends(get_ai_test_service)],
    request: ExecuteAITestsRequest | None = None,
) -> AITestExecutionResult:
    """Execute AI test suite in ephemeral sandbox."""
    wf_id = request.workflow_execution_id if request else None
    timeout = request.timeout_seconds if request else 30

    return await service.execute_tests(
        project_id=project_id,
        suite_id=suite_id,
        timeout_seconds=timeout,
        workflow_execution_id=wf_id,
    )


# ==============================================================================
# Phase 11G: AI Test Failure Analysis
# ==============================================================================

from app.agents.failure_analysis.contracts import FailureDiagnosis, FailureSource
from app.agents.failure_analysis.service import FailureAnalysisService
from app.api.dependencies import get_failure_analysis_service


class AnalyzeAITestFailureRequest(BaseModel):
    """Payload to trigger AI test failure analysis."""

    model_config = ConfigDict(extra="forbid")

    workflow_execution_id: uuid.UUID | None = Field(
        default=None,
        description="Optional workflow execution UUID. Defaults to latest.",
    )


@router.post(
    "/{suite_id}/analyze-failure",
    response_model=FailureDiagnosis,
    status_code=status.HTTP_200_OK,
    summary="Analyze AI test failure using authoritative FailureAnalysisAgent",
    description=(
        "Collects deterministic AI test execution failure evidence and invokes the "
        "authoritative FailureAnalysisAgent. Produces a structured conceptual diagnosis "
        "without mutating code or automatically initiating remediation."
    ),
)
async def analyze_ai_test_failure(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    suite_id: Annotated[uuid.UUID, Path(description="Suite UUID")],
    failure_service: Annotated[FailureAnalysisService, Depends(get_failure_analysis_service)],
    request: AnalyzeAITestFailureRequest | None = None,
) -> FailureDiagnosis:
    """Analyze AI test failure using authoritative FailureAnalysisAgent."""
    wf_id = request.workflow_execution_id if request else None

    return await failure_service.analyze_failure(
        project_id=project_id,
        workflow_execution_id=wf_id,
        force=True,
        failure_source=FailureSource.AI_TEST,
    )
