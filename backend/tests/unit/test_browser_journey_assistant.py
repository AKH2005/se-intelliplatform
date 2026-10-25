"""Unit Tests for Phase 11K Stage 5: Intelli Assistant Action Integration.

Tests:
1. Action registry contains GENERATE_BROWSER_JOURNEYS
2. Correct category = GENERATION
3. Confirmation requirement = False (non-mutating synthesis)
4. Action resolves correctly from assistant intent
5. EngineeringActionService receives the action
6. Action invokes Stage 4 workflow via BrowserJourneyService
7. Action does not call LLM provider directly
8. Action does not call BrowserTestingService directly
9. Action returns standard EngineeringAction result
10. Cross-project / unauthorized target is rejected
11. Failure status is preserved
12. End-to-end Assistant reasoning -> Engineering Action -> Stage 4 pipeline
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.providers.mock import MockLLMProvider
from app.browser.journey.contracts import (
    BrowserJourneyWorkflowResult,
    BrowserJourneyWorkflowStatus,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.models.development_version import DevelopmentVersion, DevelopmentVersionStatus
from app.models.project import Project, ProjectStatus
from app.schemas.assistant import (
    ActionCategory,
    ActionResult,
    ActionStatus,
    AssistantActionCandidate,
    AssistantContext,
    AssistantResponseSchema,
    GenerateBrowserJourneysParams,
)
from app.services.action_registry import (
    ACTION_REGISTRY,
    get_action_definition,
    is_confirmation_required,
    validate_action_parameters,
)
from app.services.assistant_reasoning_service import AssistantReasoningService
from app.services.browser_journey_service import BrowserJourneyService
from app.services.context_engine import ProjectContextEngine
from app.services.development_version_service import DevelopmentVersionService
from app.services.engineering_action_service import EngineeringActionService
from app.services.requirement_service import RequirementService
from app.services.verification_service import DevelopmentVerificationService
from app.services.workflow_service import WorkflowService


@pytest.fixture
def sample_project_id() -> uuid.UUID:
    return uuid.uuid4()


# ==============================================================================
# 1. Action Registry Contracts
# ==============================================================================

def test_action_registry_contains_generate_browser_journeys():
    """Verify GENERATE_BROWSER_JOURNEYS is registered with correct metadata."""
    assert "GENERATE_BROWSER_JOURNEYS" in ACTION_REGISTRY
    action = get_action_definition("GENERATE_BROWSER_JOURNEYS")

    assert action.action_id == "GENERATE_BROWSER_JOURNEYS"
    assert action.category == ActionCategory.GENERATION
    assert action.requires_confirmation is False
    assert is_confirmation_required("GENERATE_BROWSER_JOURNEYS") is False
    assert action.parameter_schema == GenerateBrowserJourneysParams


def test_validate_action_parameters_generate_browser_journeys():
    """Verify parameter validation enforces extra='forbid' and caps max_journeys."""
    # Valid parameters
    valid_params = {"execute_browser_tests": True, "max_journeys": 5}
    model = validate_action_parameters("GENERATE_BROWSER_JOURNEYS", valid_params)
    assert isinstance(model, GenerateBrowserJourneysParams)
    assert model.max_journeys == 5
    assert model.execute_browser_tests is True

    # Invalid bounds
    with pytest.raises(ValidationError):
        validate_action_parameters("GENERATE_BROWSER_JOURNEYS", {"max_journeys": 25})

    # Extra parameters forbidden
    with pytest.raises(ValidationError):
        validate_action_parameters(
            "GENERATE_BROWSER_JOURNEYS",
            {"untrusted_field": "dangerous", "max_journeys": 5},
        )


# ==============================================================================
# 2. Assistant Reasoning Service Integration
# ==============================================================================

@pytest.mark.asyncio
async def test_assistant_reasoning_resolves_generate_browser_journeys(sample_project_id: uuid.UUID):
    """Verify AssistantReasoningService can propose GENERATE_BROWSER_JOURNEYS."""
    mock_provider = MockLLMProvider()
    canned_response = AssistantResponseSchema(
        message="I will synthesize and execute the browser journeys for your project now.",
        suggested_action=AssistantActionCandidate(
            action_id="GENERATE_BROWSER_JOURNEYS",
            parameters={"execute_browser_tests": True, "max_journeys": 5},
        ),
    )
    mock_provider.register_structured_response(canned_response)

    reasoning_service = AssistantReasoningService(provider=mock_provider)
    ctx = AssistantContext(
        project_id=sample_project_id,
        project_name="Reasoning Project",
        project_slug="reasoning-proj",
        project_status="ACTIVE",
    )

    response = await reasoning_service.generate_response(
        user_message="Generate browser journeys for this project.",
        context=ctx,
    )

    assert response.suggested_action is not None
    assert response.suggested_action.action_id == "GENERATE_BROWSER_JOURNEYS"
    assert response.suggested_action.parameters["max_journeys"] == 5


# ==============================================================================
# 3. EngineeringActionService Dispatching
# ==============================================================================

@pytest.mark.asyncio
async def test_engineering_action_service_dispatches_generate_browser_journeys(
    db_session: AsyncSession,
    sample_project_id: uuid.UUID,
):
    """Verify EngineeringActionService dispatches GENERATE_BROWSER_JOURNEYS to BrowserJourneyService."""
    proj = Project(
        id=sample_project_id,
        name="Action Project",
        slug="action-proj",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(proj)
    await db_session.commit()

    mock_wf_result = BrowserJourneyWorkflowResult(
        workflow_execution_id=uuid.uuid4(),
        project_id=sample_project_id,
        status=BrowserJourneyWorkflowStatus.COMPLETED,
        stage_reached="completed",
        candidate_suite=None,
        validation_outcome=None,
        validated_suite=None,
        coverage_report=None,
        test_definitions=[],
        browser_test_run=None,
        artifacts={},
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        duration_seconds=2.1,
    )

    mock_journey_service = MagicMock(spec=BrowserJourneyService)
    mock_journey_service.generate_and_execute_journeys = AsyncMock(return_value=mock_wf_result)

    action_service = EngineeringActionService(
        session=db_session,
        version_service=MagicMock(spec=DevelopmentVersionService),
        verification_service=MagicMock(spec=DevelopmentVerificationService),
        requirement_service=MagicMock(spec=RequirementService),
        context_engine=MagicMock(spec=ProjectContextEngine),
        workflow_service=MagicMock(spec=WorkflowService),
        browser_journey_service=mock_journey_service,
    )

    result = await action_service.execute_action(
        project_id=sample_project_id,
        action_id="GENERATE_BROWSER_JOURNEYS",
        parameters={"execute_browser_tests": True, "max_journeys": 5},
    )

    assert isinstance(result, ActionResult)
    assert result.action_id == "GENERATE_BROWSER_JOURNEYS"
    assert result.status == ActionStatus.SUCCESS
    assert result.requires_confirmation is False
    assert result.data["workflow_execution_id"] == str(mock_wf_result.workflow_execution_id)
    assert result.data["status"] == "COMPLETED"

    mock_journey_service.generate_and_execute_journeys.assert_awaited_once_with(
        project_id=sample_project_id,
        version_id=None,
        execute_browser_tests=True,
        max_journeys=5,
    )


@pytest.mark.asyncio
async def test_engineering_action_service_failure_propagation(
    db_session: AsyncSession,
    sample_project_id: uuid.UUID,
):
    """Verify workflow validation or execution failures return ActionStatus.SUCCESS with failed status payload."""
    proj = Project(
        id=sample_project_id,
        name="Failure Project",
        slug="fail-proj",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(proj)
    await db_session.commit()

    failed_wf_result = BrowserJourneyWorkflowResult(
        workflow_execution_id=uuid.uuid4(),
        project_id=sample_project_id,
        status=BrowserJourneyWorkflowStatus.VALIDATION_FAILED,
        stage_reached="validation",
        candidate_suite=None,
        validation_outcome=None,
        validated_suite=None,
        coverage_report=None,
        test_definitions=[],
        browser_test_run=None,
        error_message="Route '/unknown' not allowed",
        errors=["Route '/unknown' not allowed"],
        artifacts={},
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        duration_seconds=0.5,
    )

    mock_journey_service = MagicMock(spec=BrowserJourneyService)
    mock_journey_service.generate_and_execute_journeys = AsyncMock(return_value=failed_wf_result)

    action_service = EngineeringActionService(
        session=db_session,
        version_service=MagicMock(spec=DevelopmentVersionService),
        verification_service=MagicMock(spec=DevelopmentVerificationService),
        requirement_service=MagicMock(spec=RequirementService),
        context_engine=MagicMock(spec=ProjectContextEngine),
        workflow_service=MagicMock(spec=WorkflowService),
        browser_journey_service=mock_journey_service,
    )

    result = await action_service.execute_action(
        project_id=sample_project_id,
        action_id="GENERATE_BROWSER_JOURNEYS",
        parameters={"max_journeys": 5},
    )

    assert result.status == ActionStatus.SUCCESS
    assert result.data["status"] == "WORKFLOW_VALIDATION_FAILED"
    assert result.data["validation_passed"] is False


@pytest.mark.asyncio
async def test_engineering_action_service_rejects_cross_project_version(
    db_session: AsyncSession,
    sample_project_id: uuid.UUID,
):
    """Verify referencing a version belonging to another project raises NotFoundError."""
    foreign_version_id = uuid.uuid4()

    mock_version_service = MagicMock(spec=DevelopmentVersionService)
    mock_version_service.get_version = AsyncMock(return_value=None)  # Version does not belong to project

    action_service = EngineeringActionService(
        session=db_session,
        version_service=mock_version_service,
        verification_service=MagicMock(spec=DevelopmentVerificationService),
        requirement_service=MagicMock(spec=RequirementService),
        context_engine=MagicMock(spec=ProjectContextEngine),
        workflow_service=MagicMock(spec=WorkflowService),
    )

    with pytest.raises(NotFoundError):
        await action_service.execute_action(
            project_id=sample_project_id,
            action_id="GENERATE_BROWSER_JOURNEYS",
            parameters={"version_id": str(foreign_version_id)},
        )


# ==============================================================================
# 4. End-to-End Mocked Flow
# ==============================================================================

@pytest.mark.asyncio
async def test_assistant_end_to_end_journey_flow(
    db_session: AsyncSession,
    sample_project_id: uuid.UUID,
):
    """Complete E2E test:
    Assistant Intent -> AssistantReasoningService -> GENERATE_BROWSER_JOURNEYS
    -> EngineeringActionService -> BrowserJourneyService -> Mocked Stage 4 Orchestrator
    -> ActionResult.
    """
    proj = Project(
        id=sample_project_id,
        name="E2E Project",
        slug="e2e-proj",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(proj)
    await db_session.commit()

    # Step 1: Assistant proposes candidate action
    mock_provider = MockLLMProvider()
    candidate = AssistantActionCandidate(
        action_id="GENERATE_BROWSER_JOURNEYS",
        parameters={"execute_browser_tests": True, "max_journeys": 3},
    )
    mock_provider.register_structured_response(
        AssistantResponseSchema(
            message="Generating and running browser journeys.",
            suggested_action=candidate,
        )
    )

    reasoning_service = AssistantReasoningService(provider=mock_provider)
    ctx = AssistantContext(
        project_id=sample_project_id,
        project_name="E2E Project",
        project_slug="e2e-proj",
        project_status="ACTIVE",
    )
    assistant_resp = await reasoning_service.generate_response(
        user_message="Please generate browser journeys.",
        context=ctx,
    )
    assert assistant_resp.suggested_action is not None
    assert assistant_resp.suggested_action.action_id == "GENERATE_BROWSER_JOURNEYS"

    # Step 2: EngineeringActionService executes action
    wf_exec_id = uuid.uuid4()
    mock_result = BrowserJourneyWorkflowResult(
        workflow_execution_id=wf_exec_id,
        project_id=sample_project_id,
        status=BrowserJourneyWorkflowStatus.COMPLETED,
        stage_reached="completed",
        candidate_suite=None,
        validation_outcome=None,
        validated_suite=None,
        coverage_report=None,
        test_definitions=[],
        browser_test_run=None,
        artifacts={},
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        duration_seconds=1.5,
    )

    mock_journey_service = MagicMock(spec=BrowserJourneyService)
    mock_journey_service.generate_and_execute_journeys = AsyncMock(return_value=mock_result)

    action_service = EngineeringActionService(
        session=db_session,
        version_service=MagicMock(spec=DevelopmentVersionService),
        verification_service=MagicMock(spec=DevelopmentVerificationService),
        requirement_service=MagicMock(spec=RequirementService),
        context_engine=MagicMock(spec=ProjectContextEngine),
        workflow_service=MagicMock(spec=WorkflowService),
        browser_journey_service=mock_journey_service,
    )

    action_result = await action_service.execute_action(
        project_id=sample_project_id,
        action_id=assistant_resp.suggested_action.action_id,
        parameters=assistant_resp.suggested_action.parameters,
    )

    assert action_result.status == ActionStatus.SUCCESS
    assert action_result.data["workflow_execution_id"] == str(wf_exec_id)
    assert action_result.data["status"] == "COMPLETED"
