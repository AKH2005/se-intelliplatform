"""Unit tests for Workflow Orchestration Contracts, Enums, and Definitions."""

import uuid
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.agents.contracts import AgentErrorDetail, AgentExecutionStatus, AgentResult
from app.agents.code_review.contracts import CodeFile, CodeReviewInput
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse
from app.schemas.requirement import (
    RequirementPriority,
    RequirementResponse,
    RequirementStatus,
    RequirementType,
)
from app.workflows.contracts import (
    WorkflowDefinition,
    WorkflowInput,
    WorkflowResult,
    WorkflowStatus,
    WorkflowStep,
    WorkflowStepResult,
    WorkflowStepStatus,
)


@pytest.fixture
def sample_context() -> ProjectContextResponse:
    project_id = uuid.uuid4()
    req_id = uuid.uuid4()
    return ProjectContextResponse(
        project=ProjectResponse(
            id=project_id,
            name="Test Workflow Project",
            slug="test-workflow-project",
            description="Testing workflow contracts",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
        requirements=[
            RequirementResponse(
                id=req_id,
                project_id=project_id,
                title="System Login",
                description="User shall authenticate securely via OAuth2",
                type=RequirementType.FUNCTIONAL,
                priority=RequirementPriority.HIGH,
                status=RequirementStatus.APPROVED,
                is_archived=False,
                version=1,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        ],
        statistics=RequirementStatistics(
            total_requirements=1,
            active_requirements=1,
            functional_count=1,
            non_functional_count=0,
            constraint_count=0,
            completion_percentage=0.0,
        ),
        context_version=1,
        generated_at=datetime.now(timezone.utc),
    )


class TestWorkflowContracts:
    def test_workflow_enums(self) -> None:
        assert WorkflowStatus.PENDING == "PENDING"
        assert WorkflowStatus.RUNNING == "RUNNING"
        assert WorkflowStatus.COMPLETED == "COMPLETED"
        assert WorkflowStatus.PARTIAL_SUCCESS == "PARTIAL_SUCCESS"
        assert WorkflowStatus.FAILED == "FAILED"

        assert WorkflowStepStatus.PENDING == "PENDING"
        assert WorkflowStepStatus.RUNNING == "RUNNING"
        assert WorkflowStepStatus.COMPLETED == "COMPLETED"
        assert WorkflowStepStatus.FAILED == "FAILED"
        assert WorkflowStepStatus.SKIPPED == "SKIPPED"

    def test_workflow_step_creation(self) -> None:
        step = WorkflowStep(
            step_id="step-1",
            agent_id="requirement-analysis",
            required=True,
            depends_on=[],
            description="Analyze requirements",
        )
        assert step.step_id == "step-1"
        assert step.agent_id == "requirement-analysis"
        assert step.required is True
        assert step.depends_on == []
        assert step.description == "Analyze requirements"

        # Immutability check
        with pytest.raises(ValidationError):
            step.step_id = "step-2"  # type: ignore

    def test_workflow_definition_validation(self) -> None:
        valid_def = WorkflowDefinition(
            workflow_id="test-pipeline",
            version="1.0.0",
            name="Test Pipeline",
            description="Valid workflow test definition",
            steps=[
                WorkflowStep(step_id="step-1", agent_id="requirement-analysis"),
                WorkflowStep(
                    step_id="step-2",
                    agent_id="architecture-recommendation",
                    required=False,
                    depends_on=["step-1"],
                ),
            ],
        )
        assert valid_def.workflow_id == "test-pipeline"
        assert len(valid_def.steps) == 2

    def test_workflow_definition_duplicate_step_id_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Duplicate step_id 'step-1'"):
            WorkflowDefinition(
                workflow_id="test-dup-steps",
                version="1.0.0",
                name="Duplicate Step Test",
                description="Testing duplicate step rejection",
                steps=[
                    WorkflowStep(step_id="step-1", agent_id="requirement-analysis"),
                    WorkflowStep(step_id="step-1", agent_id="architecture-recommendation"),
                ],
            )

    def test_workflow_definition_self_dependency_rejected(self) -> None:
        with pytest.raises(ValidationError, match="cannot depend on itself"):
            WorkflowDefinition(
                workflow_id="test-self-dep",
                version="1.0.0",
                name="Self Dependency Test",
                description="Testing self dependency rejection",
                steps=[
                    WorkflowStep(
                        step_id="step-1",
                        agent_id="requirement-analysis",
                        depends_on=["step-1"],
                    ),
                ],
            )

    def test_workflow_definition_forward_or_missing_dependency_rejected(self) -> None:
        # Step-1 depends on step-2 which appears AFTER it
        with pytest.raises(ValidationError, match="not defined prior to it"):
            WorkflowDefinition(
                workflow_id="test-forward-dep",
                version="1.0.0",
                name="Forward Dependency Test",
                description="Testing forward dependency rejection",
                steps=[
                    WorkflowStep(
                        step_id="step-1",
                        agent_id="requirement-analysis",
                        depends_on=["step-2"],
                    ),
                    WorkflowStep(step_id="step-2", agent_id="architecture-recommendation"),
                ],
            )

        # Non-existent dependency
        with pytest.raises(ValidationError, match="not defined prior to it"):
            WorkflowDefinition(
                workflow_id="test-missing-dep",
                version="1.0.0",
                name="Missing Dependency Test",
                description="Testing missing dependency rejection",
                steps=[
                    WorkflowStep(
                        step_id="step-1",
                        agent_id="requirement-analysis",
                        depends_on=["non-existent-step"],
                    ),
                ],
            )

    def test_workflow_input_creation(self, sample_context: ProjectContextResponse) -> None:
        code_input = CodeReviewInput(
            files=[CodeFile(file_path="main.py", language="python", content="print('hello')")]
        )
        wf_input = WorkflowInput(
            context=sample_context,
            code_review_input=code_input,
            explainability_target_scope="auth",
            explainability_user_query="Why is this required?",
            options={"dry_run": False},
        )
        assert wf_input.context.project.name == "Test Workflow Project"
        assert wf_input.code_review_input is not None
        assert len(wf_input.code_review_input.files) == 1
        assert wf_input.explainability_target_scope == "auth"
        assert wf_input.explainability_user_query == "Why is this required?"
        assert wf_input.options["dry_run"] is False

    def test_workflow_step_result_and_workflow_result(self) -> None:
        exec_id = uuid.uuid4()
        step_res = WorkflowStepResult(
            step_id="step-1",
            agent_id="requirement-analysis",
            status=WorkflowStepStatus.COMPLETED,
            execution_id=exec_id,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )
        assert step_res.step_id == "step-1"
        assert step_res.status == WorkflowStepStatus.COMPLETED
        assert step_res.execution_id == exec_id

        wf_exec_id = uuid.uuid4()
        wf_res = WorkflowResult(
            workflow_execution_id=wf_exec_id,
            workflow_id="test-workflow",
            workflow_version="1.0.0",
            status=WorkflowStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            step_results=[step_res],
            artifacts={"step-1": {"dummy": "data"}},
            errors=[],
            warnings=[],
            metadata={"test": True},
        )
        assert wf_res.workflow_execution_id == wf_exec_id
        assert wf_res.status == WorkflowStatus.COMPLETED
        assert len(wf_res.step_results) == 1
        assert wf_res.artifacts["step-1"] == {"dummy": "data"}

        dump = wf_res.model_dump(mode="json")
        assert dump["workflow_id"] == "test-workflow"
        assert dump["status"] == "COMPLETED"
