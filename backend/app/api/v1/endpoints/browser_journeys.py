"""Browser Journey REST API Endpoints for Phase 11K (Stage 5).

Exposes project-scoped browser journey generation, validation, adaptation,
execution, and historical artifact retrieval backed by BrowserJourneyService.
Enforces strict project isolation, authentication/authorization boundaries,
and read-only outcome inspection. Directly calling LLM providers, Playwright,
Docker, or running arbitrary shell commands is strictly prohibited.
"""

import logging
import uuid
from typing import Annotated
from fastapi import APIRouter, Body, Depends, Path, Query, status

from app.api.dependencies import get_browser_journey_service
from app.schemas.browser_journeys import (
    BrowserJourneyWorkflowResponse,
    GenerateBrowserJourneysRequest,
)
from app.services.browser_journey_service import BrowserJourneyService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "",
    response_model=BrowserJourneyWorkflowResponse,
    status_code=status.HTTP_200_OK,
    summary="Synthesize, validate, adapt, and execute browser journeys",
    description=(
        "Triggers the Stage 4 intelligent browser journey workflow for an authorized project. "
        "Coordinates candidate generation via WorkflowCoordinator and AgentExecutor, deterministic "
        "validation, deterministic adaptation, containerized execution via BrowserTestingService, "
        "and persists the authoritative execution record. Direct Playwright or Docker calls are strictly forbidden."
    ),
)
@router.post(
    "/",
    response_model=BrowserJourneyWorkflowResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def generate_browser_journeys(
    project_id: Annotated[uuid.UUID, Path(description="Target project UUID")],
    service: Annotated[BrowserJourneyService, Depends(get_browser_journey_service)],
    request: GenerateBrowserJourneysRequest = Body(default_factory=GenerateBrowserJourneysRequest),
) -> BrowserJourneyWorkflowResponse:
    """Generate, validate, adapt, and execute browser journeys for a project."""
    logger.info(
        f"Received browser journey generation request for project [{project_id}] "
        f"[version_id={request.development_version_id}, execute_tests={request.execute_browser_tests}]"
    )

    res = await service.generate_and_execute_journeys(
        project_id=project_id,
        version_id=request.development_version_id,
        execute_browser_tests=request.execute_browser_tests,
        max_journeys=request.max_journeys,
    )
    return BrowserJourneyWorkflowResponse.from_result(res)


@router.get(
    "/latest",
    response_model=BrowserJourneyWorkflowResponse,
    status_code=status.HTTP_200_OK,
    summary="Get latest browser journey workflow execution result",
    description=(
        "Retrieves the most recent persisted browser journey workflow run and validated artifacts for the project. "
        "Strictly READ_ONLY: does not rerun the workflow, regenerate journeys, or invoke Playwright."
    ),
)
async def get_latest_browser_journey_result(
    project_id: Annotated[uuid.UUID, Path(description="Target project UUID")],
    service: Annotated[BrowserJourneyService, Depends(get_browser_journey_service)],
) -> BrowserJourneyWorkflowResponse:
    """Retrieve the latest browser journey workflow outcome for a project."""
    execution = await service.get_latest_workflow_result(project_id=project_id)
    return BrowserJourneyWorkflowResponse.from_workflow_execution(execution)


@router.get(
    "/{workflow_execution_id}",
    response_model=BrowserJourneyWorkflowResponse,
    status_code=status.HTTP_200_OK,
    summary="Get browser journey workflow execution result by UUID",
    description=(
        "Retrieves the authoritative persisted execution record for a specific browser journey workflow run. "
        "Enforces strict project isolation: cross-project access is rejected with HTTP 404. "
        "Strictly READ_ONLY: does not rerun the workflow, regenerate journeys, or invoke Playwright."
    ),
)
async def get_browser_journey_result_by_id(
    project_id: Annotated[uuid.UUID, Path(description="Target project UUID")],
    workflow_execution_id: Annotated[uuid.UUID, Path(description="Workflow execution correlation UUID")],
    service: Annotated[BrowserJourneyService, Depends(get_browser_journey_service)],
) -> BrowserJourneyWorkflowResponse:
    """Retrieve a specific browser journey workflow run by correlation UUID."""
    execution = await service.get_workflow_result(
        project_id=project_id,
        workflow_execution_id=workflow_execution_id,
    )
    return BrowserJourneyWorkflowResponse.from_workflow_execution(execution)


@router.get(
    "",
    response_model=list[BrowserJourneyWorkflowResponse],
    status_code=status.HTTP_200_OK,
    summary="List historical browser journey workflow executions",
    description="Returns paginated browser journey workflow executions for an authorized project.",
)
@router.get(
    "/",
    response_model=list[BrowserJourneyWorkflowResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def list_browser_journey_results(
    project_id: Annotated[uuid.UUID, Path(description="Target project UUID")],
    service: Annotated[BrowserJourneyService, Depends(get_browser_journey_service)],
    limit: Annotated[int, Query(ge=1, le=100, description="Page limit")] = 20,
    offset: Annotated[int, Query(ge=0, description="Page offset")] = 0,
) -> list[BrowserJourneyWorkflowResponse]:
    """List historical browser journey workflow executions for a project."""
    records, _ = await service.list_workflow_results(
        project_id=project_id,
        limit=limit,
        offset=offset,
    )
    return [BrowserJourneyWorkflowResponse.from_workflow_execution(r) for r in records]
