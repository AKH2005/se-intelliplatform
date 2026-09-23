"""Unit tests for Phase 8.0 Test Case Generation Agent lifecycle and registry integration."""

from datetime import datetime, timezone
import uuid
import pytest

from app.agents.contracts import AgentExecutionStatus, AgentType
from app.agents.exceptions import AgentValidationError
from app.agents.execution import AgentExecutor
from app.agents.providers.mock import MockLLMProvider
from app.agents.registry import AgentRegistry, register_default_agents
from app.agents.test_case_generation.agent import TestCaseGenerationAgent
from app.agents.test_case_generation.contracts import (
    DEFAULT_TEST_CASE_LIMITATIONS,
    TestCase,
    TestCaseCoverage,
    TestCaseGenerationCandidate,
    TestCaseGenerationOutput,
    TestPriority,
    TestStep,
    TestType,
)
from app.models.requirement import RequirementPriority, RequirementStatus, RequirementType
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse
from app.schemas.requirement import RequirementResponse


@pytest.fixture
def test_case_context():
    project_id = uuid.uuid4()
    req1_id = uuid.uuid4()
    req2_id = uuid.uuid4()
    req3_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    req1 = RequirementResponse(
        id=req1_id,
        project_id=project_id,
        title="User Registration",
        description="Users must be able to register with email and password.",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.HIGH,
        status=RequirementStatus.APPROVED,
        is_archived=False,
        created_at=now,
        updated_at=now,
    )
    req2 = RequirementResponse(
        id=req2_id,
        project_id=project_id,
        title="Password Encryption",
        description="Passwords must be hashed using bcrypt before persisting.",
        type=RequirementType.NON_FUNCTIONAL,
        priority=RequirementPriority.CRITICAL,
        status=RequirementStatus.APPROVED,
        is_archived=False,
        created_at=now,
        updated_at=now,
    )
    req3 = RequirementResponse(
        id=req3_id,
        project_id=project_id,
        title="Social Login",
        description="OAuth2 login with Google.",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.LOW,
        status=RequirementStatus.DEFERRED,
        is_archived=False,
        created_at=now,
        updated_at=now,
    )

    context = ProjectContextResponse(
        project=ProjectResponse(
            id=project_id,
            name="Security Gateway",
            slug="sec-gw",
            description="Testing test case generation agent",
            is_active=True,
            created_at=now,
            updated_at=now,
        ),
        requirements=[req1, req2, req3],
        statistics=RequirementStatistics(
            total_requirements=3,
            active_requirements=2,
            functional_count=2,
            non_functional_count=0,
            constraint_count=0,
            by_priority={"HIGH": 1, "CRITICAL": 1, "LOW": 1},
            by_status={"APPROVED": 2, "DEFERRED": 1},
            completion_percentage=0.0,
        ),
        context_version=1,
        generated_at=now,
    )
    return context, req1_id, req2_id, req3_id


def test_agent_metadata():
    agent = TestCaseGenerationAgent()
    meta = agent.metadata
    assert meta.agent_id == "test-case-generation"
    assert meta.name == "Test Case Generation Agent"
    assert meta.version == "1.0.0"
    assert meta.agent_type == AgentType.GENERATION
    assert agent.output_schema == TestCaseGenerationOutput


@pytest.mark.asyncio
async def test_agent_analysis_phase(test_case_context):
    context, req1_id, req2_id, req3_id = test_case_context
    agent = TestCaseGenerationAgent()
    analysis = await agent.analyze(context)

    assert analysis["active_requirements_count"] == 2
    assert analysis["project_name"] == "Security Gateway"
    assert len(analysis["active_requirements"]) == 2
    active_ids = {str(r.id) for r in analysis["active_requirements"]}
    assert str(req1_id) in active_ids
    assert str(req2_id) in active_ids
    assert str(req3_id) not in active_ids


@pytest.mark.asyncio
async def test_agent_successful_generation(test_case_context):
    context, req1_id, req2_id, _ = test_case_context
    agent = TestCaseGenerationAgent()
    provider = MockLLMProvider()

    candidate = TestCaseGenerationCandidate(
        summary="Automated suite for registration and password hashing.",
        test_cases=[
            TestCase(
                test_case_id="TC-AUTH-01",
                title="Successful Email Registration",
                description="Register with valid email and password.",
                test_type=TestType.FUNCTIONAL,
                priority=TestPriority.HIGH,
                preconditions=["Database is reachable."],
                steps=[
                    TestStep(step_number=1, action="Post registration payload", expected_behavior="HTTP 201 Created"),
                    TestStep(step_number=2, action="Query database for user", expected_behavior="User row exists"),
                ],
                expected_result="User registered successfully.",
                requirement_ids=[str(req1_id)],
            ),
            TestCase(
                test_case_id="TC-AUTH-02",
                title="Bcrypt Password Hashing Verification",
                description="Ensure persisted password hash uses bcrypt format.",
                test_type=TestType.SECURITY,
                priority=TestPriority.CRITICAL,
                preconditions=["User registered."],
                steps=[
                    TestStep(step_number=1, action="Fetch password_hash from DB", expected_behavior="Hash begins with $2b$"),
                ],
                expected_result="Password is not stored in plaintext.",
                requirement_ids=[str(req2_id)],
            ),
        ],
    )
    provider.register_structured_response(candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.COMPLETED
    output = result.output
    assert isinstance(output, TestCaseGenerationOutput)
    assert output.total_test_cases == 2
    assert len(output.test_cases) == 2
    assert output.coverage.total_active_requirements == 2
    assert output.coverage.requirements_with_tests == 2
    assert output.coverage.requirements_without_tests == 0
    assert output.coverage.coverage_percentage == 100.0
    assert len(output.limitations) >= 3


@pytest.mark.asyncio
async def test_agent_partial_coverage_calculation(test_case_context):
    context, req1_id, req2_id, _ = test_case_context
    agent = TestCaseGenerationAgent()
    provider = MockLLMProvider()

    # Candidate only tests req1, leaving req2 untested
    candidate = TestCaseGenerationCandidate(
        summary="Partial test suite covering only registration.",
        test_cases=[
            TestCase(
                test_case_id="TC-AUTH-01",
                title="Registration Only Test",
                description="Register with email.",
                test_type=TestType.FUNCTIONAL,
                priority=TestPriority.HIGH,
                steps=[
                    TestStep(step_number=1, action="Post valid email", expected_behavior="201 Created"),
                ],
                expected_result="User created.",
                requirement_ids=[str(req1_id)],
            ),
        ],
    )
    provider.register_structured_response(candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.COMPLETED
    output = result.output
    assert output.total_test_cases == 1
    assert output.coverage.total_active_requirements == 2
    assert output.coverage.requirements_with_tests == 1
    assert output.coverage.requirements_without_tests == 1
    assert output.coverage.coverage_percentage == 50.0


@pytest.mark.asyncio
async def test_agent_validation_failure_on_invalid_candidate(test_case_context):
    context, _, _, _ = test_case_context
    agent = TestCaseGenerationAgent()
    provider = MockLLMProvider()

    # Candidate with non-existent requirement ID
    fake_id = str(uuid.uuid4())
    candidate = TestCaseGenerationCandidate(
        summary="Invalid candidate.",
        test_cases=[
            TestCase(
                test_case_id="TC-INV-01",
                title="Invalid Req ID",
                description="Ref non-existent req.",
                test_type=TestType.FUNCTIONAL,
                priority=TestPriority.LOW,
                steps=[TestStep(step_number=1, action="Action", expected_behavior="Behavior")],
                expected_result="Result",
                requirement_ids=[fake_id],
            ),
        ],
    )
    provider.register_structured_response(candidate)

    executor = AgentExecutor(provider=provider)
    result = await executor.execute(agent=agent, context=context)

    assert result.status == AgentExecutionStatus.FAILED
    assert result.error is not None
    assert result.error.error_code == "VALIDATION_FAILED"
    assert "references non-existent requirement ID" in result.error.message



def test_registry_integration():
    registry = AgentRegistry()
    register_default_agents(registry)

    assert registry.has("test-case-generation")
    agent = registry.get("test-case-generation")
    assert isinstance(agent, TestCaseGenerationAgent)
    assert agent.metadata.agent_id == "test-case-generation"
    assert len(registry.list_agents()) == 9

    # Idempotent registration
    register_default_agents(registry)
    assert len(registry.list_agents()) == 9
