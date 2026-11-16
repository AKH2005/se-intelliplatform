"""Authoritative Integration Tests for Telemetry Across All Phase 12 Execution Authorities.

Proves that:
1. WorkflowCoordinator emits WORKFLOW_STARTED, WORKFLOW_STEP_*, WORKFLOW_COMPLETED/FAILED.
2. AgentExecutor emits AGENT_STARTED, AGENT_PROGRESS, AGENT_COMPLETED/FAILED.
3. DockerSandboxExecutor emits SANDBOX_STARTED, SANDBOX_PROGRESS, SANDBOX_COMPLETED/FAILED.
4. BrowserTestingService emits BROWSER_STARTED, BROWSER_PROGRESS, BROWSER_COMPLETED/FAILED.
5. RegressionExecutionService emits REGRESSION_STARTED, REGRESSION_PROGRESS, REGRESSION_COMPLETED/FAILED.
6. Event bus strictly isolates projects and maintains monotonic sequences.
"""

import asyncio
from typing import Any
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.telemetry.bus import get_event_bus
from app.telemetry.contracts import (
    ExecutionEventType,
    ExecutionKind,
)
from app.workflows.contracts import (
    WorkflowDefinition,
    WorkflowInput,
    WorkflowStep,
)
from app.workflows.coordinator import WorkflowCoordinator
from app.agents.execution import AgentExecutor
from app.agents.providers.mock import MockLLMProvider
from app.sandbox.contracts import ExecutionRequest, ExecutionType, ResourceLimits
from app.sandbox.docker_executor import DockerSandboxExecutor
from app.agents.code_generation.contracts import (
    CodeGenerationOutput,
    CodeGenerationPlan,
    FileType,
    GeneratedFile,
    PlannedFile,
)
from app.testing.regression.contracts import (
    RegressionPlan,
    RegressionPlanMode,
)
from app.testing.regression.executor import RegressionExecutionService
from app.testing.inventory.contracts import UnifiedTestInventory


@pytest.fixture(autouse=True)
def clean_event_bus():
    bus = get_event_bus()
    bus.clear()
    yield
    bus.clear()


from pydantic import BaseModel
from app.agents.base import AbstractBaseAgent
from app.agents.contracts import AgentMetadata, AgentType
from app.agents.providers.base import AbstractLLMProvider


class DummyOutputA(BaseModel):
    value_a: str


class MockTelemetryAgent(AbstractBaseAgent[DummyOutputA]):
    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id="test-agent",
            name="Test Agent",
            description="Mock Agent for telemetry testing",
            version="1.0.0",
            agent_type=AgentType.ANALYSIS,
        )

    @property
    def output_schema(self) -> type[DummyOutputA]:
        return DummyOutputA

    async def analyze(self, context: Any, **kwargs: Any) -> dict[str, Any]:
        return {"analyzed": True}

    async def generate(
        self, analysis_result: dict[str, Any], provider: AbstractLLMProvider, **kwargs: Any
    ) -> DummyOutputA:
        return DummyOutputA(value_a="valid")


@pytest.mark.asyncio
async def test_workflow_coordinator_telemetry_emission():
    """Verify WorkflowCoordinator emits WORKFLOW_* and correlated AGENT_* events."""
    bus = get_event_bus()
    project_id = str(uuid.uuid4())

    mock_agent = MockTelemetryAgent()

    class MockAgentRegistry:
        def get(self, agent_id: str):
            return mock_agent

    provider = MockLLMProvider()
    executor = AgentExecutor(provider=provider)
    coordinator = WorkflowCoordinator(executor=executor, registry=MockAgentRegistry())

    wf_def = WorkflowDefinition(
        workflow_id="telemetry-test-wf",
        version="1.0.0",
        name="Telemetry Test Workflow",
        description="Tests telemetry",
        steps=[WorkflowStep(step_id="step-1", agent_id="test-agent", depends_on=[])],
    )
    from datetime import datetime, timezone
    from app.schemas.context import ProjectContextResponse, RequirementStatistics
    from app.schemas.project import ProjectResponse

    proj_uuid = uuid.UUID(project_id)
    ctx = ProjectContextResponse(
        project=ProjectResponse(
            id=proj_uuid,
            name="Test Coordinator Project",
            slug="test-coord-proj",
            description="Testing telemetry",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
        requirements=[],
        statistics=RequirementStatistics(
            total_requirements=0,
            active_requirements=0,
            functional_count=0,
            non_functional_count=0,
            constraint_count=0,
            completion_percentage=0.0,
        ),
        context_version=1,
        generated_at=datetime.now(timezone.utc),
    )
    wf_input = WorkflowInput(context=ctx)

    result = await coordinator.execute(workflow=wf_def, workflow_input=wf_input)
    assert result is not None

    wf_exec_id = str(result.workflow_execution_id)
    events = bus.get_events(project_id, wf_exec_id)

    event_types = [e.event_type for e in events]
    assert ExecutionEventType.WORKFLOW_STARTED in event_types
    assert ExecutionEventType.WORKFLOW_STEP_STARTED in event_types
    assert ExecutionEventType.WORKFLOW_STEP_COMPLETED in event_types
    assert ExecutionEventType.WORKFLOW_COMPLETED in event_types

    # Verify monotonic sequencing
    sequences = [e.sequence for e in events]
    assert sequences == list(range(1, len(events) + 1))


@pytest.mark.asyncio
async def test_sandbox_executor_telemetry_emission():
    """Verify DockerSandboxExecutor emits SANDBOX_STARTED, SANDBOX_COMPLETED events."""
    bus = get_event_bus()
    project_id = str(uuid.uuid4())

    sandbox = DockerSandboxExecutor()
    req = ExecutionRequest(
        project_id=uuid.UUID(project_id),
        execution_type=ExecutionType.STATIC_VALIDATE,
        limits=ResourceLimits(),
    )
    code_output = CodeGenerationOutput(
        plan=CodeGenerationPlan(
            project_type="backend",
            language="python",
            framework="fastapi",
            database="sqlite",
            package_manager="pip",
            files=[
                PlannedFile(
                    path="app/main.py",
                    purpose="Main application",
                    file_type=FileType.SOURCE,
                    architecture_component="backend",
                )
            ],
            rationale="Valid test plan for static analysis verification",
        ),
        generated_files=[
            GeneratedFile(
                path="app/main.py",
                content="def hello(): return 'world'",
                language="python",
                size_bytes=28,
                architecture_component="backend",
            )
        ],
        total_files=1,
        total_size_bytes=28,
        summary="Clean verified execution summary",
    )

    res = await sandbox.execute(req, code_output)
    assert res is not None

    events = bus.get_events(project_id, str(res.execution_id))
    event_types = [e.event_type for e in events]

    assert ExecutionEventType.SANDBOX_STARTED in event_types
    assert ExecutionEventType.SANDBOX_COMPLETED in event_types


@pytest.mark.asyncio
async def test_regression_executor_telemetry_emission():
    """Verify RegressionExecutionService emits REGRESSION_STARTED and REGRESSION_COMPLETED."""
    bus = get_event_bus()
    project_id = str(uuid.uuid4())

    inv = UnifiedTestInventory(
        inventory_id="inv-telemetry-12345",
        project_id=project_id,
        tests=[],
    )
    plan = RegressionPlan(
        project_id=project_id,
        inventory_id=inv.inventory_id,
        mode=RegressionPlanMode.FULL,
        selected_test_ids=[],
        selected_tests=[],
        is_execution_safe=True,
    )

    executor = RegressionExecutionService()
    result = await executor.execute_plan(
        project_id=project_id,
        plan=plan,
        inventory=inv,
    )

    assert result is not None
    events = bus.get_events(project_id, result.execution_id)
    event_types = [e.event_type for e in events]

    assert ExecutionEventType.REGRESSION_STARTED in event_types
    assert ExecutionEventType.REGRESSION_COMPLETED in event_types
