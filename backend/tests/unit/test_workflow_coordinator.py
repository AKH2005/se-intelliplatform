"""Unit tests for WorkflowCoordinator execution, error handling, and lifecycle transitions."""

import uuid
from datetime import datetime, timezone
from typing import Any
import pytest
from pydantic import BaseModel

from app.agents.base import AbstractBaseAgent
from app.agents.contracts import (
    AgentErrorDetail,
    AgentExecutionStatus,
    AgentMetadata,
    AgentResult,
    AgentType,
    ValidationResult,
)
from app.agents.exceptions import AgentValidationError
from app.agents.execution import AgentExecutor
from app.agents.providers.base import AbstractLLMProvider
from app.agents.providers.mock import MockLLMProvider
from app.agents.registry import AgentRegistry
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
    WorkflowStepStatus,
)
from app.workflows.coordinator import WorkflowCoordinator


# Simple mock models for testing
class DummyOutputA(BaseModel):
    value_a: str


class DummyOutputB(BaseModel):
    value_b: str


class MockAgentA(AbstractBaseAgent[DummyOutputA]):
    def __init__(self, should_fail: bool = False, fail_with_validation: bool = False) -> None:
        self.should_fail = should_fail
        self.fail_with_validation = fail_with_validation
        self.received_kwargs: dict[str, Any] = {}

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id="mock-agent-a",
            name="Mock Agent A",
            description="Mock Agent A for workflow testing",
            version="1.0.0",
            agent_type=AgentType.ANALYSIS,
        )

    @property
    def output_schema(self) -> type[DummyOutputA]:
        return DummyOutputA

    async def analyze(self, context: ProjectContextResponse, **kwargs: Any) -> dict[str, Any]:
        self.received_kwargs = kwargs
        if self.fail_with_validation:
            raise AgentValidationError(
                message="Deterministic validation rejection in MockAgentA",
                validation_errors=["Validation error in agent A"],
            )
        if self.should_fail:
            raise RuntimeError("Runtime error in MockAgentA")
        return {"context": context}

    async def generate(
        self, analysis_result: dict[str, Any], provider: AbstractLLMProvider, **kwargs: Any
    ) -> DummyOutputA:
        return DummyOutputA(value_a="output_from_a")


class MockAgentB(AbstractBaseAgent[DummyOutputB]):
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.received_kwargs: dict[str, Any] = {}

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id="mock-agent-b",
            name="Mock Agent B",
            description="Mock Agent B for workflow testing",
            version="1.0.0",
            agent_type=AgentType.RECOMMENDATION,
        )

    @property
    def output_schema(self) -> type[DummyOutputB]:
        return DummyOutputB

    async def analyze(self, context: ProjectContextResponse, **kwargs: Any) -> dict[str, Any]:
        self.received_kwargs = kwargs
        if self.should_fail:
            raise RuntimeError("Runtime error in MockAgentB")
        return {"context": context}

    async def generate(
        self, analysis_result: dict[str, Any], provider: AbstractLLMProvider, **kwargs: Any
    ) -> DummyOutputB:
        return DummyOutputB(value_b="output_from_b")


@pytest.fixture
def sample_context() -> ProjectContextResponse:
    project_id = uuid.uuid4()
    req_id = uuid.uuid4()
    return ProjectContextResponse(
        project=ProjectResponse(
            id=project_id,
            name="Test Coordinator Project",
            slug="test-coordinator-project",
            description="Testing workflow coordinator",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
        requirements=[
            RequirementResponse(
                id=req_id,
                project_id=project_id,
                title="System Auth",
                description="User shall authenticate securely",
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


class TestWorkflowCoordinator:
    @pytest.mark.asyncio
    async def test_successful_two_step_workflow(self, sample_context: ProjectContextResponse) -> None:
        agent_a = MockAgentA()
        agent_b = MockAgentB()

        registry = AgentRegistry()
        registry.register(agent_a)
        registry.register(agent_b)

        provider = MockLLMProvider()
        executor = AgentExecutor(provider=provider)
        coordinator = WorkflowCoordinator(executor=executor, registry=registry)

        workflow = WorkflowDefinition(
            workflow_id="test-success-workflow",
            version="1.0.0",
            name="Two Step Success",
            description="Testing two sequential successful steps",
            steps=[
                WorkflowStep(step_id="step-a", agent_id="mock-agent-a", required=True),
                WorkflowStep(
                    step_id="step-b",
                    agent_id="mock-agent-b",
                    required=True,
                    depends_on=["step-a"],
                ),
            ],
        )

        wf_input = WorkflowInput(context=sample_context)
        res = await coordinator.execute(workflow, wf_input)

        assert res.status == WorkflowStatus.COMPLETED
        assert len(res.step_results) == 2
        assert res.step_results[0].status == WorkflowStepStatus.COMPLETED
        assert res.step_results[1].status == WorkflowStepStatus.COMPLETED

        # Check artifact storage
        assert "step-a" in res.artifacts
        assert res.artifacts["step-a"].value_a == "output_from_a"
        assert "step-b" in res.artifacts
        assert res.artifacts["step-b"].value_b == "output_from_b"

        # Check workflow execution id was passed to agent kwargs
        assert "workflow_execution_id" in agent_a.received_kwargs
        assert agent_a.received_kwargs["workflow_execution_id"] == res.workflow_execution_id
        assert agent_b.received_kwargs["workflow_execution_id"] == res.workflow_execution_id

    @pytest.mark.asyncio
    async def test_mandatory_step_failure_halts_dependent_step(
        self, sample_context: ProjectContextResponse
    ) -> None:
        agent_a = MockAgentA(should_fail=True)
        agent_b = MockAgentB()

        registry = AgentRegistry()
        registry.register(agent_a)
        registry.register(agent_b)

        provider = MockLLMProvider()
        executor = AgentExecutor(provider=provider)
        coordinator = WorkflowCoordinator(executor=executor, registry=registry)

        workflow = WorkflowDefinition(
            workflow_id="test-mandatory-fail",
            version="1.0.0",
            name="Mandatory Failure Test",
            description="Step A fails and Step B is skipped",
            steps=[
                WorkflowStep(step_id="step-a", agent_id="mock-agent-a", required=True),
                WorkflowStep(
                    step_id="step-b",
                    agent_id="mock-agent-b",
                    required=True,
                    depends_on=["step-a"],
                ),
            ],
        )

        wf_input = WorkflowInput(context=sample_context)
        res = await coordinator.execute(workflow, wf_input)

        assert res.status == WorkflowStatus.FAILED
        assert res.step_results[0].status == WorkflowStepStatus.FAILED
        assert res.step_results[1].status == WorkflowStepStatus.SKIPPED
        assert "Required prerequisite step 'step-a' was FAILED" in (res.step_results[1].skip_reason or "")
        assert "step-a" not in res.artifacts
        assert "step-b" not in res.artifacts

    @pytest.mark.asyncio
    async def test_optional_step_failure_permits_partial_success(
        self, sample_context: ProjectContextResponse
    ) -> None:
        agent_a = MockAgentA()
        agent_b = MockAgentB(should_fail=True)

        registry = AgentRegistry()
        registry.register(agent_a)
        registry.register(agent_b)

        provider = MockLLMProvider()
        executor = AgentExecutor(provider=provider)
        coordinator = WorkflowCoordinator(executor=executor, registry=registry)

        workflow = WorkflowDefinition(
            workflow_id="test-optional-fail",
            version="1.0.0",
            name="Optional Failure Test",
            description="Step A succeeds, Step B fails optionally",
            steps=[
                WorkflowStep(step_id="step-a", agent_id="mock-agent-a", required=True),
                WorkflowStep(
                    step_id="step-b",
                    agent_id="mock-agent-b",
                    required=False,
                    depends_on=["step-a"],
                ),
            ],
        )

        wf_input = WorkflowInput(context=sample_context)
        res = await coordinator.execute(workflow, wf_input)

        assert res.status == WorkflowStatus.PARTIAL_SUCCESS
        assert res.step_results[0].status == WorkflowStepStatus.COMPLETED
        assert res.step_results[1].status == WorkflowStepStatus.FAILED
        assert "step-a" in res.artifacts
        assert "step-b" not in res.artifacts

    @pytest.mark.asyncio
    async def test_agent_not_found_handled_gracefully(
        self, sample_context: ProjectContextResponse
    ) -> None:
        registry = AgentRegistry()  # Empty registry
        provider = MockLLMProvider()
        executor = AgentExecutor(provider=provider)
        coordinator = WorkflowCoordinator(executor=executor, registry=registry)

        workflow = WorkflowDefinition(
            workflow_id="test-missing-agent",
            version="1.0.0",
            name="Missing Agent Test",
            description="Agent is not in registry",
            steps=[
                WorkflowStep(step_id="step-missing", agent_id="non-existent-agent", required=True),
            ],
        )

        wf_input = WorkflowInput(context=sample_context)
        res = await coordinator.execute(workflow, wf_input)

        assert res.status == WorkflowStatus.FAILED
        assert res.step_results[0].status == WorkflowStepStatus.FAILED
        assert res.step_results[0].error is not None
        assert res.step_results[0].error.error_code == "AGENT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_validation_error_is_terminal_and_not_retried(
        self, sample_context: ProjectContextResponse
    ) -> None:
        agent_a = MockAgentA(fail_with_validation=True)

        registry = AgentRegistry()
        registry.register(agent_a)

        provider = MockLLMProvider()
        executor = AgentExecutor(provider=provider, max_retries=3)
        coordinator = WorkflowCoordinator(executor=executor, registry=registry)

        workflow = WorkflowDefinition(
            workflow_id="test-val-error",
            version="1.0.0",
            name="Validation Error Test",
            description="Deterministic validation error must be terminal",
            steps=[
                WorkflowStep(step_id="step-a", agent_id="mock-agent-a", required=True),
            ],
        )

        wf_input = WorkflowInput(context=sample_context)
        res = await coordinator.execute(workflow, wf_input)

        assert res.status == WorkflowStatus.FAILED
        assert res.step_results[0].status == WorkflowStepStatus.FAILED
        assert res.step_results[0].agent_result is not None
        assert res.step_results[0].agent_result.error is not None
        assert res.step_results[0].agent_result.error.error_code == "VALIDATION_FAILED"
        # Verify attempt count in metadata is 1 (never retried)
        assert res.step_results[0].agent_result.metadata.get("attempts") == 1

    @pytest.mark.asyncio
    async def test_provenance_and_snapshot_preserved_across_all_steps(
        self, sample_context: ProjectContextResponse
    ) -> None:
        agent_a = MockAgentA()
        agent_b = MockAgentB()

        registry = AgentRegistry()
        registry.register(agent_a)
        registry.register(agent_b)

        provider = MockLLMProvider()
        executor = AgentExecutor(provider=provider)
        coordinator = WorkflowCoordinator(executor=executor, registry=registry)

        workflow = WorkflowDefinition(
            workflow_id="test-provenance-workflow",
            version="1.0.0",
            name="Provenance Test Workflow",
            description="Testing provenance across all steps",
            steps=[
                WorkflowStep(step_id="step-a", agent_id="mock-agent-a", required=True),
                WorkflowStep(step_id="step-b", agent_id="mock-agent-b", required=True),
            ],
        )

        fake_snapshot_id = uuid.uuid4()
        fake_context_version = 42

        wf_input = WorkflowInput(context=sample_context)
        res = await coordinator.execute(
            workflow=workflow,
            workflow_input=wf_input,
            context_snapshot_id=fake_snapshot_id,
            context_version=fake_context_version,
        )

        assert res.status == WorkflowStatus.COMPLETED
        for step_res in res.step_results:
            assert step_res.agent_result is not None
            # Context snapshot provenance must match exact passed snapshot ID and version
            assert step_res.agent_result.context_snapshot_id == fake_snapshot_id
            assert step_res.agent_result.context_version == fake_context_version

    @pytest.mark.asyncio
    async def test_all_optional_steps_fail_leads_to_workflow_failure(
        self, sample_context: ProjectContextResponse
    ) -> None:
        agent_a = MockAgentA(should_fail=True)
        agent_b = MockAgentB(should_fail=True)

        registry = AgentRegistry()
        registry.register(agent_a)
        registry.register(agent_b)

        provider = MockLLMProvider()
        executor = AgentExecutor(provider=provider)
        coordinator = WorkflowCoordinator(executor=executor, registry=registry)

        workflow = WorkflowDefinition(
            workflow_id="test-all-fail-workflow",
            version="1.0.0",
            name="All Fail Workflow",
            description="Workflow where every step is optional but all fail",
            steps=[
                WorkflowStep(step_id="step-a", agent_id="mock-agent-a", required=False),
                WorkflowStep(step_id="step-b", agent_id="mock-agent-b", required=False),
            ],
        )

        wf_input = WorkflowInput(context=sample_context)
        res = await coordinator.execute(workflow, wf_input)

        # When all steps fail (even if optional), 0 steps succeeded -> FAILED
        assert res.status == WorkflowStatus.FAILED
        assert res.step_results[0].status == WorkflowStepStatus.FAILED
        assert res.step_results[1].status == WorkflowStepStatus.FAILED
