"""Integration Tests for Phase 11F: AI Test Generation & Ephemeral Sandbox Execution API."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.code_generation.contracts import (
    CodeGenerationOutput,
    CodeGenerationPlan,
    GeneratedFile,
    PlannedFile,
)
from app.agents.execution import AgentExecutor
from app.agents.providers.mock import MockLLMProvider
from app.agents.test_generation.contracts import (
    AITestSuiteCandidate,
    GeneratedTestCandidate,
    TestCategory,
)
from app.api.dependencies import get_agent_executor, get_sandbox_executor
from app.main import app
from app.models.project import Project, ProjectStatus
from app.models.workflow_execution import WorkflowExecution, WorkflowStatus
from app.sandbox.base import AbstractSandboxExecutor
from app.sandbox.contracts import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    ExecutionType,
)


@pytest.fixture
def mock_agent_and_sandbox_dependencies():
    """Mock LLM provider returning a valid AITestSuiteCandidate and mock sandbox."""
    mock_prov = MockLLMProvider()
    canned_suite = AITestSuiteCandidate(
        summary="Automated unit test suite for calculator module",
        tests=[
            GeneratedTestCandidate(
                test_id="TEST-001",
                name="test_calculator_addition",
                description="Verifies add function with positive integers",
                category="HAPPY_PATH",
                target_file="app/calculator.py",
                target_symbol="add",
                requirement_ids=[],
                architecture_component="CalculatorService",
                rationale="Ensures basic arithmetic works",
                code="def test_calculator_addition():\n    from app.calculator import add\n    assert add(2, 3) == 5\n",
                expected_behavior="Returns 5",
            ),
            GeneratedTestCandidate(
                test_id="TEST-002",
                name="test_calculator_zero_division",
                description="Verifies divide function raises ValueError on zero",
                category="ERROR_HANDLING",
                target_file="app/calculator.py",
                target_symbol="divide",
                requirement_ids=[],
                architecture_component="CalculatorService",
                rationale="Ensures error handling for zero division",
                code="def test_calculator_zero_division():\n    import pytest\n    from app.calculator import divide\n    with pytest.raises(ValueError):\n        divide(10, 0)\n",
                expected_behavior="Raises ValueError",
            ),
        ],
    )
    mock_prov.register_structured_response(canned_suite)
    executor = AgentExecutor(provider=mock_prov)

    class MockSandbox(AbstractSandboxExecutor):
        def __init__(self):
            self.execute_calls = []

        async def is_available(self) -> bool:
            return True

        async def execute(self, request, code_output):
            self.execute_calls.append((request, code_output))
            return ExecutionResult(
                execution_id=uuid.uuid4(),
                project_id=request.project_id,
                execution_type=request.execution_type,
                status=ExecutionStatus.PASSED,
                exit_code=0,
                stdout=(
                    "tests/test_ai_generated.py::test_calculator_addition PASSED [ 50%]\n"
                    "tests/test_ai_generated.py::test_calculator_zero_division PASSED [100%]\n"
                    "2 passed in 0.08s"
                ),
                stderr="",
                duration_seconds=0.08,
                tests_passed=2,
                tests_failed=0,
                tests_total=2,
            )

    sandbox = MockSandbox()

    app.dependency_overrides[get_agent_executor] = lambda: executor
    app.dependency_overrides[get_sandbox_executor] = lambda: sandbox

    yield executor, sandbox

    app.dependency_overrides.pop(get_agent_executor, None)
    app.dependency_overrides.pop(get_sandbox_executor, None)


async def _seed_test_project_and_artifact(session: AsyncSession) -> tuple[Project, WorkflowExecution]:
    """Seed project and workflow execution with a valid CodeGenerationOutput artifact."""
    project = Project(
        name="AI Testing Sandbox Project",
        slug=f"ai-testing-proj-{uuid.uuid4().hex[:8]}",
        description="Integration testing for AI Test Generation",
        status=ProjectStatus.IN_PROGRESS,
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)

    code_output = CodeGenerationOutput(
        plan=CodeGenerationPlan(
            project_type="backend-service",
            language="python",
            framework="fastapi",
            database="sqlite",
            package_manager="pip",
            files=[
                PlannedFile(
                    path="app/calculator.py",
                    purpose="Calculator operations",
                    file_type="SOURCE",
                    requirement_ids=[],
                    dependencies=[],
                )
            ],
            rationale="Modular calculation engine",
        ),
        generated_files=[
            GeneratedFile(
                path="app/calculator.py",
                content=(
                    "def add(a, b):\n"
                    "    return a + b\n\n"
                    "def divide(a, b):\n"
                    "    if b == 0:\n"
                    "        raise ValueError('Cannot divide by zero')\n"
                    "    return a / b\n"
                ),
                language="python",
                size_bytes=105,
                requirement_ids=[],
            )
        ],
        total_files=1,
        total_size_bytes=105,
        summary="Single-file calculation service",
    )

    wf_exec = WorkflowExecution(
        workflow_execution_id=uuid.uuid4(),
        project_id=project.id,
        workflow_id="code_generation",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        artifacts={"code_generation": code_output.model_dump(mode="json")},
    )
    session.add(wf_exec)
    await session.commit()
    await session.refresh(wf_exec)

    return project, wf_exec


# ==============================================================================
# Integration Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_generate_ai_tests_success(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_agent_and_sandbox_dependencies,
):
    """POST /tests/ai/generate produces an authoritative validated AITestSuite."""
    project, wf_exec = await _seed_test_project_and_artifact(db_session)

    resp = await client.post(
        f"/api/v1/projects/{project.id}/tests/ai/generate",
        json={"workflow_execution_id": str(wf_exec.workflow_execution_id)},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "suite_id" in data
    assert data["test_count"] == 2
    assert "tests/test_ai_generated.py" in data["test_files"]
    assert "test_calculator_addition" in data["tests"][0]["name"]

    # Verify persisted in database artifacts
    await db_session.refresh(wf_exec)
    assert "ai_test_suite" in wf_exec.artifacts
    assert wf_exec.artifacts["ai_test_suite"]["suite_id"] == data["suite_id"]


@pytest.mark.asyncio
async def test_generate_ai_tests_missing_code_artifact(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """POST /tests/ai/generate rejects execution if no code generation artifact exists."""
    project = Project(
        name="Empty Project",
        slug=f"empty-proj-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    wf_exec = WorkflowExecution(
        workflow_execution_id=uuid.uuid4(),
        project_id=project.id,
        workflow_id="code_generation",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        artifacts={},
    )
    db_session.add(wf_exec)
    await db_session.commit()

    resp = await client.post(f"/api/v1/projects/{project.id}/tests/ai/generate")
    assert resp.status_code in [400, 422]


@pytest.mark.asyncio
async def test_get_latest_ai_test_suite(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_agent_and_sandbox_dependencies,
):
    """GET /tests/ai/latest returns the most recent test suite."""
    project, wf_exec = await _seed_test_project_and_artifact(db_session)

    gen_resp = await client.post(f"/api/v1/projects/{project.id}/tests/ai/generate")
    assert gen_resp.status_code == 201
    created_suite = gen_resp.json()

    get_resp = await client.get(f"/api/v1/projects/{project.id}/tests/ai/latest")
    assert get_resp.status_code == 200
    fetched_suite = get_resp.json()
    assert fetched_suite["suite_id"] == created_suite["suite_id"]


@pytest.mark.asyncio
async def test_get_ai_test_suite_by_id(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_agent_and_sandbox_dependencies,
):
    """GET /tests/ai/{suite_id} returns the specific test suite."""
    project, wf_exec = await _seed_test_project_and_artifact(db_session)

    gen_resp = await client.post(f"/api/v1/projects/{project.id}/tests/ai/generate")
    suite_id = gen_resp.json()["suite_id"]

    get_resp = await client.get(f"/api/v1/projects/{project.id}/tests/ai/{suite_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["suite_id"] == suite_id


@pytest.mark.asyncio
async def test_execute_ai_tests_success(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_agent_and_sandbox_dependencies,
):
    """POST /tests/ai/{suite_id}/execute runs validated tests in ephemeral sandbox and preserves original artifact."""
    project, wf_exec = await _seed_test_project_and_artifact(db_session)
    original_files_count = len(wf_exec.artifacts["code_generation"]["generated_files"])

    gen_resp = await client.post(f"/api/v1/projects/{project.id}/tests/ai/generate")
    suite_id = gen_resp.json()["suite_id"]

    exec_resp = await client.post(
        f"/api/v1/projects/{project.id}/tests/ai/{suite_id}/execute",
        json={"timeout_seconds": 25},
    )
    assert exec_resp.status_code == 200
    data = exec_resp.json()
    assert data["status"] == "PASSED"
    assert data["tests_passed"] == 2
    assert len(data["test_results"]) == 2
    assert data["test_results"][0]["status"] == "PASSED"

    # CRITICAL VERIFICATION: Original code generation artifact remains unchanged
    await db_session.refresh(wf_exec)
    assert len(wf_exec.artifacts["code_generation"]["generated_files"]) == original_files_count
    assert "tests/test_ai_generated.py" not in [
        f["path"] for f in wf_exec.artifacts["code_generation"]["generated_files"]
    ]

    # Verify execution result is recorded in artifacts
    assert "ai_test_execution" in wf_exec.artifacts
    assert wf_exec.artifacts["ai_test_execution"]["suite_id"] == suite_id


@pytest.mark.asyncio
async def test_execute_nonexistent_suite(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_agent_and_sandbox_dependencies,
):
    """POST /tests/ai/{suite_id}/execute returns 404 for unknown suite."""
    project, _ = await _seed_test_project_and_artifact(db_session)
    random_id = str(uuid.uuid4())

    resp = await client.post(f"/api/v1/projects/{project.id}/tests/ai/{random_id}/execute")
    assert resp.status_code == 404
