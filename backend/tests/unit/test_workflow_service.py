"""Unit Tests for Workflow Schemas and WorkflowService Integration."""

import uuid
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.code_review.contracts import CodeFile, CodeReviewInput
from app.agents.registry import register_default_agents
from app.core.exceptions import NotFoundError, ValidationError
from app.models.project import Project
from app.schemas.workflow import (
    WorkflowExecuteRequest,
    WorkflowMetadataResponse,
    WorkflowResultResponse,
    WorkflowStepResultResponse,
)


@pytest.fixture(autouse=True)
def ensure_default_agents():
    """Ensure all default agents are registered before running tests."""
    register_default_agents()

from app.services.context_engine import ProjectContextEngine
from app.services.workflow_service import WorkflowService
from app.workflows.contracts import (
    WorkflowResult,
    WorkflowStatus,
    WorkflowStepResult,
    WorkflowStepStatus,
)
from app.workflows.coordinator import WorkflowCoordinator
from app.workflows.pipelines import (
    WORKFLOW_COMPREHENSIVE_AUDIT_ID,
    WORKFLOW_PROJECT_ESTIMATION_ID,
    WORKFLOW_SOFTWARE_DESIGN_ID,
)


# ==============================================================================
# 1. Schema Validation Tests
# ==============================================================================

def test_workflow_execute_request_valid():
    """Verify valid request passes schema validation."""
    pid = uuid.uuid4()
    req = WorkflowExecuteRequest(
        project_id=pid,
        options={"fail_fast": True},
    )
    assert req.project_id == pid
    assert req.options == {"fail_fast": True}
    assert req.snapshot_id is None
    assert req.snapshot_version is None


def test_workflow_execute_request_forbidden_extra_fields():
    """Verify extra unrecognized fields are rejected."""
    with pytest.raises(PydanticValidationError) as exc_info:
        WorkflowExecuteRequest.model_validate(
            {
                "project_id": str(uuid.uuid4()),
                "unauthorized_field": "exploit",
            }
        )
    assert "extra_forbidden" in str(exc_info.value)


def test_workflow_execute_request_unsupported_options():
    """Verify options with unknown keys are rejected."""
    with pytest.raises(PydanticValidationError) as exc_info:
        WorkflowExecuteRequest(
            project_id=uuid.uuid4(),
            options={"speculative_option": "value"},
        )
    assert "Unsupported workflow execution option" in str(exc_info.value)


def test_workflow_execute_request_mutually_exclusive_snapshots():
    """Verify providing both snapshot_id and snapshot_version is rejected."""
    with pytest.raises(PydanticValidationError) as exc_info:
        WorkflowExecuteRequest(
            project_id=uuid.uuid4(),
            snapshot_id=uuid.uuid4(),
            snapshot_version=1,
        )
    assert "Cannot specify both 'snapshot_id' and 'snapshot_version'" in str(exc_info.value)


def test_workflow_execute_request_invalid_code_review_input():
    """Verify invalid code review inputs (e.g. path traversal) are rejected at schema gate."""
    with pytest.raises(PydanticValidationError) as exc_info:
        WorkflowExecuteRequest(
            project_id=uuid.uuid4(),
            code_review_input=CodeReviewInput(
                files=[
                    CodeFile(
                        file_path="../../etc/passwd",
                        language="python",
                        content="print('insecure')",
                    )
                ]
            ),
        )
    assert "Invalid code_review_input" in str(exc_info.value)


def test_workflow_result_response_serialization():
    """Verify domain WorkflowResult transforms into clean WorkflowResultResponse."""
    exec_id = uuid.uuid4()
    step_exec_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    domain_res = WorkflowResult(
        workflow_execution_id=exec_id,
        workflow_id=WORKFLOW_SOFTWARE_DESIGN_ID,
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        started_at=now,
        completed_at=now,
        step_results=[
            WorkflowStepResult(
                step_id="step-1",
                agent_id="requirement-analysis",
                status=WorkflowStepStatus.COMPLETED,
                execution_id=step_exec_id,
                started_at=now,
                completed_at=now,
            )
        ],
        artifacts={"step-1": {"analysis": "passed"}},
        metadata={"total_steps": 1},
    )

    api_res = WorkflowResultResponse.from_workflow_result(domain_res)
    assert api_res.workflow_execution_id == exec_id
    assert api_res.status == WorkflowStatus.COMPLETED
    assert len(api_res.step_results) == 1
    assert api_res.step_results[0].step_id == "step-1"
    assert api_res.step_results[0].execution_id == step_exec_id
    assert api_res.artifacts == {"step-1": {"analysis": "passed"}}


# ==============================================================================
# 2. Service Unit Tests
# ==============================================================================

DEFAULT_ML_SETTINGS = {
    "ml_risk_inputs": {
        "project_size": "Medium",
        "team_experience_level": "High",
        "estimated_effort_hours": 950.0,
        "complexity_level": "High",
        "requirement_stability": "Moderate",
    },
    "ml_timeline_inputs": {
        "afp": 480.0,
        "input_count": 55.0,
        "output_count": 40.0,
        "enquiry_count": 30.0,
        "file_count": 25.0,
        "interface_count": 15.0,
        "resource_level": 2,
    },
    "ml_bug_inputs": {
        "loc": 45.0,
        "v(g)": 7.0,
        "ev(g)": 3.0,
        "iv(g)": 4.0,
        "n": 120.0,
        "v": 650.0,
        "l": 0.05,
        "d": 20.0,
        "i": 32.5,
        "e": 13000.0,
        "b": 0.22,
        "t": 722.0,
        "lOCode": 35.0,
        "lOComment": 5.0,
        "lOBlank": 5.0,
        "locCodeAndComment": 2.0,
        "uniq_Op": 15.0,
        "uniq_Opnd": 25.0,
        "total_Op": 60.0,
        "total_Opnd": 40.0,
        "branchCount": 12.0,
    },
}


@pytest.fixture
async def sample_project(db_session: AsyncSession) -> Project:
    """Create a sample project entity with ML features configured."""
    proj = Project(
        name="Workflow Test Project",
        slug=f"wf-test-{uuid.uuid4().hex[:8]}",
        description="Project for workflow service unit tests",
        settings=DEFAULT_ML_SETTINGS,
    )
    db_session.add(proj)
    await db_session.commit()
    await db_session.refresh(proj)
    return proj



@pytest.fixture
def workflow_service(db_session: AsyncSession) -> WorkflowService:
    """Instantiate a real WorkflowService backed by the test DB session."""
    from app.agents.execution import AgentExecutor
    from app.agents.registry import agent_registry
    from app.api.dependencies import build_default_mock_provider

    context_engine = ProjectContextEngine(session=db_session)
    executor = AgentExecutor(provider=build_default_mock_provider())
    coordinator = WorkflowCoordinator(executor=executor, registry=agent_registry)

    return WorkflowService(
        session=db_session,
        context_engine=context_engine,
        coordinator=coordinator,
    )



@pytest.mark.asyncio
async def test_list_and_get_predefined_workflows(workflow_service: WorkflowService):
    """Verify listing and retrieving predefined workflows."""
    workflows = workflow_service.list_workflows()
    assert len(workflows) == 3
    ids = {w.workflow_id for w in workflows}
    assert WORKFLOW_SOFTWARE_DESIGN_ID in ids
    assert WORKFLOW_PROJECT_ESTIMATION_ID in ids
    assert WORKFLOW_COMPREHENSIVE_AUDIT_ID in ids

    # Valid get
    wf = workflow_service.get_workflow(WORKFLOW_SOFTWARE_DESIGN_ID)
    assert wf.workflow_id == WORKFLOW_SOFTWARE_DESIGN_ID

    # Invalid get raises NotFoundError
    with pytest.raises(NotFoundError) as exc_info:
        workflow_service.get_workflow("non-existent-pipeline")
    assert "Workflow" in str(exc_info.value)


@pytest.mark.asyncio
async def test_to_metadata_response(workflow_service: WorkflowService):
    """Verify internal workflow definitions map to safe discovery schemas."""
    wf = workflow_service.get_workflow(WORKFLOW_COMPREHENSIVE_AUDIT_ID)
    meta = workflow_service.to_metadata_response(wf)

    assert meta.workflow_id == WORKFLOW_COMPREHENSIVE_AUDIT_ID
    assert meta.step_count == 9
    assert "project_id" in meta.required_inputs
    assert "code_review_input" in meta.optional_inputs
    assert "explainability_user_query" in meta.optional_inputs
    assert len(meta.steps) == 9
    assert meta.steps[0].step_id == "requirement-analysis"


@pytest.mark.asyncio
async def test_execute_workflow_live_context(
    workflow_service: WorkflowService,
    sample_project: Project,
):
    """Verify workflow executes against live canonical context."""
    req = WorkflowExecuteRequest(project_id=sample_project.id)
    result = await workflow_service.execute_workflow(
        workflow_id=WORKFLOW_PROJECT_ESTIMATION_ID,
        request=req,
    )

    assert result.workflow_id == WORKFLOW_PROJECT_ESTIMATION_ID
    assert result.status in (WorkflowStatus.COMPLETED, WorkflowStatus.PARTIAL_SUCCESS)
    assert len(result.step_results) == 3
    assert result.metadata["project_id"] == str(sample_project.id)


@pytest.mark.asyncio
async def test_execute_workflow_snapshot_by_version(
    workflow_service: WorkflowService,
    sample_project: Project,
):
    """Verify workflow executes against a versioned immutable snapshot."""
    # Create snapshot v1
    snapshot = await workflow_service.context_engine.create_snapshot(
        project_id=sample_project.id,
        summary="Milestone 1 snapshot",
    )
    assert snapshot.version == 1

    req = WorkflowExecuteRequest(
        project_id=sample_project.id,
        snapshot_version=1,
    )
    result = await workflow_service.execute_workflow(
        workflow_id=WORKFLOW_PROJECT_ESTIMATION_ID,
        request=req,
    )

    assert result.workflow_id == WORKFLOW_PROJECT_ESTIMATION_ID
    assert result.status in (WorkflowStatus.COMPLETED, WorkflowStatus.PARTIAL_SUCCESS)


@pytest.mark.asyncio
async def test_execute_workflow_snapshot_by_id(
    workflow_service: WorkflowService,
    sample_project: Project,
):
    """Verify workflow executes against a snapshot identified by UUID."""
    snapshot = await workflow_service.context_engine.create_snapshot(
        project_id=sample_project.id,
        summary="UUID test snapshot",
    )

    req = WorkflowExecuteRequest(
        project_id=sample_project.id,
        snapshot_id=snapshot.id,
    )
    result = await workflow_service.execute_workflow(
        workflow_id=WORKFLOW_PROJECT_ESTIMATION_ID,
        request=req,
    )

    assert result.workflow_id == WORKFLOW_PROJECT_ESTIMATION_ID
    assert result.status in (WorkflowStatus.COMPLETED, WorkflowStatus.PARTIAL_SUCCESS)


@pytest.mark.asyncio
async def test_execute_workflow_nonexistent_project_raises_404(
    workflow_service: WorkflowService,
):
    """Verify non-existent project raises NotFoundError."""
    req = WorkflowExecuteRequest(project_id=uuid.uuid4())
    with pytest.raises(NotFoundError) as exc_info:
        await workflow_service.execute_workflow(
            workflow_id=WORKFLOW_PROJECT_ESTIMATION_ID,
            request=req,
        )
    assert "Project" in str(exc_info.value)


@pytest.mark.asyncio
async def test_execute_workflow_nonexistent_snapshot_id_raises_404(
    workflow_service: WorkflowService,
    sample_project: Project,
):
    """Verify non-existent snapshot UUID raises NotFoundError."""
    req = WorkflowExecuteRequest(
        project_id=sample_project.id,
        snapshot_id=uuid.uuid4(),
    )
    with pytest.raises(NotFoundError) as exc_info:
        await workflow_service.execute_workflow(
            workflow_id=WORKFLOW_PROJECT_ESTIMATION_ID,
            request=req,
        )
    assert "ContextSnapshot" in str(exc_info.value)


@pytest.mark.asyncio
async def test_execute_workflow_nonexistent_snapshot_version_raises_404(
    workflow_service: WorkflowService,
    sample_project: Project,
):
    """Verify non-existent snapshot version raises NotFoundError."""
    req = WorkflowExecuteRequest(
        project_id=sample_project.id,
        snapshot_version=999,
    )
    with pytest.raises(NotFoundError) as exc_info:
        await workflow_service.execute_workflow(
            workflow_id=WORKFLOW_PROJECT_ESTIMATION_ID,
            request=req,
        )
    assert "ContextSnapshot" in str(exc_info.value)


@pytest.mark.asyncio
async def test_execute_workflow_snapshot_project_mismatch_raises_validation_error(
    workflow_service: WorkflowService,
    sample_project: Project,
    db_session: AsyncSession,
):
    """Verify snapshot belonging to another project is deterministically rejected."""
    # Create another project and its snapshot
    other_proj = Project(
        name="Other Project",
        slug=f"other-proj-{uuid.uuid4().hex[:8]}",
    )
    db_session.add(other_proj)
    await db_session.commit()
    await db_session.refresh(other_proj)

    other_snapshot = await workflow_service.context_engine.create_snapshot(
        project_id=other_proj.id,
        summary="Other project snapshot",
    )

    # Attempt to use other_snapshot on sample_project
    req = WorkflowExecuteRequest(
        project_id=sample_project.id,
        snapshot_id=other_snapshot.id,
    )
    with pytest.raises(ValidationError) as exc_info:
        await workflow_service.execute_workflow(
            workflow_id=WORKFLOW_PROJECT_ESTIMATION_ID,
            request=req,
        )
    assert "does not belong to project" in str(exc_info.value)
