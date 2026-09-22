"""Unit tests for TestCaseGenerationAgent execution through AgentExecutor."""

from datetime import datetime, timezone
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.contracts import AgentExecutionStatus
from app.agents.exceptions import ProviderError
from app.agents.execution import AgentExecutor
from app.agents.providers.mock import MockLLMProvider
from app.agents.test_case_generation.agent import TestCaseGenerationAgent
from app.agents.test_case_generation.contracts import (
    DEFAULT_TEST_CASE_LIMITATIONS,
    TestCase,
    TestCaseGenerationCandidate,
    TestCaseGenerationOutput,
    TestPriority,
    TestStep,
    TestType,
)
from app.models.agent_audit import AgentExecutionAudit
from app.models.context_snapshot import ContextSnapshot
from app.models.project import Project, ProjectStatus
from app.models.requirement import Requirement, RequirementPriority, RequirementStatus, RequirementType
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse
from app.schemas.requirement import RequirementResponse


@pytest.mark.asyncio
async def test_test_case_generation_executor_live_context(db_session: AsyncSession):
    """Verify TestCaseGenerationAgent executes through AgentExecutor with live context and DB audit."""
    project = Project(
        name="Billing Engine",
        slug=f"billing-engine-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.flush()

    req = Requirement(
        project_id=project.id,
        title="Invoice Generation",
        description="Generate PDF invoices upon successful checkout.",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.HIGH,
        status=RequirementStatus.APPROVED,
    )
    db_session.add(req)
    await db_session.commit()
    await db_session.refresh(project)
    await db_session.refresh(req)

    now = datetime.now(timezone.utc)
    context = ProjectContextResponse(
        project=ProjectResponse.model_validate(project),
        requirements=[RequirementResponse.model_validate(req)],
        statistics=RequirementStatistics(
            total_requirements=1,
            active_requirements=1,
            functional_count=1,
            non_functional_count=0,
            constraint_count=0,
            completion_percentage=0.0,
        ),
        context_version=1,
        generated_at=now,
    )

    candidate = TestCaseGenerationCandidate(
        summary="Automated test suite for PDF invoice generation.",
        test_cases=[
            TestCase(
                test_case_id="TC-INV-001",
                title="Verify PDF Invoice Creation",
                description="Valid checkout creates a PDF invoice document.",
                test_type=TestType.FUNCTIONAL,
                priority=TestPriority.HIGH,
                preconditions=["Cart contains at least one item."],
                steps=[
                    TestStep(step_number=1, action="Post checkout payload", expected_behavior="Checkout returns HTTP 200"),
                    TestStep(step_number=2, action="Query invoice endpoint", expected_behavior="Invoice URL and PDF stream available"),
                ],
                expected_result="Valid PDF invoice generated and downloadable.",
                requirement_ids=[str(req.id)],
            ),
        ],
    )

    provider = MockLLMProvider()
    provider.register_structured_response(candidate)

    agent = TestCaseGenerationAgent()
    executor = AgentExecutor(provider=provider)

    result = await executor.execute(
        agent=agent,
        context=context,
        session=db_session,
    )

    # 1. Result verification
    assert result.status == AgentExecutionStatus.COMPLETED
    assert isinstance(result.output, TestCaseGenerationOutput)
    assert result.output.total_test_cases == 1
    assert result.output.coverage.total_active_requirements == 1
    assert result.output.coverage.requirements_with_tests == 1
    assert result.output.coverage.coverage_percentage == 100.0
    assert result.validation.is_valid is True
    assert result.context_snapshot_id is None
    assert result.context_version is None

    # 2. Database Audit verification
    stmt = select(AgentExecutionAudit).where(
        AgentExecutionAudit.execution_id == result.execution_id
    )
    audit = (await db_session.execute(stmt)).scalar_one_or_none()

    assert audit is not None
    assert audit.project_id == project.id
    assert audit.agent_id == "test-case-generation"
    assert audit.agent_version == "1.0.0"
    assert audit.status == AgentExecutionStatus.COMPLETED
    assert audit.context_snapshot_id is None
    assert audit.context_version is None
    assert "total_test_cases" in audit.output_summary
    assert "coverage" in audit.output_summary

    # 3. Read-only verification: project & requirement rows are untouched
    db_project = (await db_session.execute(select(Project).where(Project.id == project.id))).scalar_one()
    assert db_project.status == ProjectStatus.IN_PROGRESS

    db_req = (await db_session.execute(select(Requirement).where(Requirement.id == req.id))).scalar_one()
    assert db_req.status == RequirementStatus.APPROVED
    assert db_req.title == "Invoice Generation"


@pytest.mark.asyncio
async def test_test_case_generation_executor_snapshot_backed(db_session: AsyncSession):
    """Verify TestCaseGenerationAgent preserves snapshot provenance in executor and audit."""
    project = Project(
        name="Snapshot Testing Project",
        slug=f"snap-proj-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.flush()

    req = Requirement(
        project_id=project.id,
        title="Email Notifications",
        description="Notify users upon order confirmation.",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.MEDIUM,
        status=RequirementStatus.APPROVED,
    )
    db_session.add(req)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    snapshot = ContextSnapshot(
        project_id=project.id,
        version=2,
        context_data={"project": {"name": project.name}, "requirements": [{"id": str(req.id)}]},
    )
    db_session.add(snapshot)
    await db_session.commit()
    await db_session.refresh(project)
    await db_session.refresh(req)
    await db_session.refresh(snapshot)

    context = ProjectContextResponse(
        project=ProjectResponse.model_validate(project),
        requirements=[RequirementResponse.model_validate(req)],
        statistics=RequirementStatistics(
            total_requirements=1,
            active_requirements=1,
            functional_count=1,
            non_functional_count=0,
            constraint_count=0,
            completion_percentage=0.0,
        ),
        context_version=2,
        generated_at=now,
    )

    candidate = TestCaseGenerationCandidate(
        summary="Test suite for notification dispatch.",
        test_cases=[
            TestCase(
                test_case_id="TC-NOTIF-01",
                title="Order Confirmation Email Dispatch",
                description="Test email trigger.",
                test_type=TestType.INTEGRATION,
                priority=TestPriority.MEDIUM,
                steps=[TestStep(step_number=1, action="Trigger notification event", expected_behavior="Message placed on queue")],
                expected_result="Email queued for delivery.",
                requirement_ids=[str(req.id)],
            ),
        ],
    )

    provider = MockLLMProvider()
    provider.register_structured_response(candidate)

    agent = TestCaseGenerationAgent()
    executor = AgentExecutor(provider=provider)

    result = await executor.execute(
        agent=agent,
        context=context,
        snapshot=snapshot,
        session=db_session,
    )

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.context_snapshot_id == snapshot.id
    assert result.context_version == 2

    stmt = select(AgentExecutionAudit).where(
        AgentExecutionAudit.execution_id == result.execution_id
    )
    audit = (await db_session.execute(stmt)).scalar_one_or_none()

    assert audit is not None
    assert audit.context_snapshot_id == snapshot.id
    assert audit.context_version == 2


@pytest.mark.asyncio
async def test_test_case_generation_executor_validation_failure(db_session: AsyncSession):
    """Verify executor marks execution FAILED and logs audit when validation rejects candidate."""
    project = Project(
        name="Validation Fail Project",
        slug=f"val-fail-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    now = datetime.now(timezone.utc)
    context = ProjectContextResponse(
        project=ProjectResponse.model_validate(project),
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
        generated_at=now,
    )

    # Candidate with non-existent requirement ID
    candidate = TestCaseGenerationCandidate(
        summary="Invalid candidate with unknown req ID.",
        test_cases=[
            TestCase(
                test_case_id="TC-BAD-01",
                title="Bad Ref",
                description="Desc",
                test_type=TestType.FUNCTIONAL,
                priority=TestPriority.LOW,
                steps=[TestStep(step_number=1, action="Act", expected_behavior="Exp")],
                expected_result="Res",
                requirement_ids=[str(uuid.uuid4())],
            ),
        ],
    )

    provider = MockLLMProvider()
    provider.register_structured_response(candidate)

    agent = TestCaseGenerationAgent()
    executor = AgentExecutor(provider=provider, max_retries=2)

    result = await executor.execute(
        agent=agent,
        context=context,
        session=db_session,
    )

    assert result.status == AgentExecutionStatus.FAILED
    assert result.output is None
    assert result.error is not None
    assert result.error.error_code == "VALIDATION_FAILED"
    assert result.metadata["attempts"] == 1

    stmt = select(AgentExecutionAudit).where(
        AgentExecutionAudit.execution_id == result.execution_id
    )
    audit = (await db_session.execute(stmt)).scalar_one_or_none()

    assert audit is not None
    assert audit.status == AgentExecutionStatus.FAILED
    assert audit.error_code == "VALIDATION_FAILED"


@pytest.mark.asyncio
async def test_test_case_generation_executor_permanent_provider_failure(db_session: AsyncSession):
    """Verify executor handles permanent LLM provider failures gracefully and creates FAILED audit."""
    project = Project(
        name="Permanent Fail Project",
        slug=f"perm-fail-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    now = datetime.now(timezone.utc)
    context = ProjectContextResponse(
        project=ProjectResponse.model_validate(project),
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
        generated_at=now,
    )

    provider = MockLLMProvider()
    provider.simulate_permanent_failure(ProviderError(message="API Quota Exceeded", provider_name="mock"))

    agent = TestCaseGenerationAgent()
    executor = AgentExecutor(provider=provider, max_retries=1)

    result = await executor.execute(
        agent=agent,
        context=context,
        session=db_session,
    )

    assert result.status == AgentExecutionStatus.FAILED
    assert result.error is not None
    assert result.error.error_code == "PROVIDER_ERROR"

    stmt = select(AgentExecutionAudit).where(
        AgentExecutionAudit.execution_id == result.execution_id
    )
    audit = (await db_session.execute(stmt)).scalar_one_or_none()

    assert audit is not None
    assert audit.status == AgentExecutionStatus.FAILED
    assert audit.error_code == "PROVIDER_ERROR"
