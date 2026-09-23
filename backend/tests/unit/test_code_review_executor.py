"""Unit tests for CodeReviewAgent execution through AgentExecutor."""

from datetime import datetime, timezone
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.code_review.agent import CodeReviewAgent
from app.agents.code_review.contracts import (
    CodeFile,
    CodeReviewCandidate,
    CodeReviewFinding,
    CodeReviewInput,
    FindingCategory,
    FindingSeverity,
    FindingSource,
)
from app.agents.contracts import AgentExecutionStatus
from app.agents.exceptions import ProviderError
from app.agents.execution import AgentExecutor
from app.agents.providers.mock import MockLLMProvider
from app.models.agent_audit import AgentExecutionAudit
from app.models.context_snapshot import ContextSnapshot
from app.models.project import Project, ProjectStatus
from app.models.requirement import Requirement, RequirementPriority, RequirementStatus, RequirementType
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse
from app.schemas.requirement import RequirementResponse


@pytest.mark.asyncio
async def test_code_review_executor_live_context(db_session: AsyncSession):
    """Verify CodeReviewAgent executes through AgentExecutor with live context and DB audit."""
    project = Project(
        name="Review Target Engine",
        slug=f"review-target-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.flush()

    req = Requirement(
        project_id=project.id,
        title="Payment Service",
        description="Process credit card payments securely.",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.CRITICAL,
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

    code = (
        "def process_payment(amount: float):\n"
        "    if amount <= 0:\n"
        "        raise ValueError('Invalid amount')\n"
        "    return True\n"
    )
    code_input = CodeReviewInput(
        files=[CodeFile(file_path="app/payment.py", language="python", content=code)]
    )

    provider = MockLLMProvider()
    candidate = CodeReviewCandidate(
        summary="Payment logic review looks solid.",
        findings=[
            CodeReviewFinding(
                finding_id="CAND-01",
                file_path="app/payment.py",
                line_start=2,
                line_end=3,
                severity=FindingSeverity.INFO,
                category=FindingCategory.CORRECTNESS,
                source=FindingSource.AI_REVIEW,
                title="Input Validation Verification",
                description="Correctly verifies that payment amount is positive.",
                evidence="if amount <= 0:\n        raise ValueError('Invalid amount')",
                recommendation="Consider adding upper boundary check for payment amounts.",
            )
        ],
    )
    provider.register_structured_response(candidate)

    agent = CodeReviewAgent()
    executor = AgentExecutor(provider=provider)

    result = await executor.execute(
        agent=agent,
        context=context,
        session=db_session,
        code_input=code_input,
    )

    # 1. Execution Result Verification
    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.output is not None
    assert result.output.agent_id == "code-review"
    assert result.output.agent_version == "1.0.0"
    assert result.output.metrics.files_analyzed_count == 1
    assert result.output.metrics.total_findings >= 1

    # 2. Audit Trail Persistence Verification
    stmt = select(AgentExecutionAudit).where(AgentExecutionAudit.execution_id == result.execution_id)
    audit_row = (await db_session.execute(stmt)).scalar_one_or_none()
    assert audit_row is not None
    assert audit_row.status == AgentExecutionStatus.COMPLETED
    assert audit_row.agent_id == "code-review"
    assert audit_row.project_id == project.id

    # 3. Privacy Invariant: Raw source code must NEVER be stored in audit records
    assert audit_row.output_summary is not None
    assert code not in audit_row.output_summary
    assert "process_payment" not in audit_row.output_summary


@pytest.mark.asyncio
async def test_code_review_executor_snapshot_provenance(db_session: AsyncSession):
    """Verify CodeReviewAgent executes with snapshot provenance correctly tracked in audit."""
    project = Project(
        name="Snapshot Target",
        slug=f"snapshot-target-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.flush()

    snapshot = ContextSnapshot(
        project_id=project.id,
        version=2,
        context_data={"project": {"name": project.name}},
        summary="Sprint 2 requirements snapshot",
    )
    db_session.add(snapshot)
    await db_session.commit()
    await db_session.refresh(snapshot)

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
        context_version=2,
        generated_at=now,
    )

    code_input = CodeReviewInput(
        files=[CodeFile(file_path="main.py", language="python", content="print('hi')\n")]
    )

    provider = MockLLMProvider()
    candidate = CodeReviewCandidate(
        summary="Review complete.",
        findings=[],
    )
    provider.register_structured_response(candidate)

    agent = CodeReviewAgent()
    executor = AgentExecutor(provider=provider)

    result = await executor.execute(
        agent=agent,
        context=context,
        session=db_session,
        snapshot=snapshot,
        code_input=code_input,
    )

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.context_snapshot_id == snapshot.id
    assert result.context_version == 2

    # Verify DB audit provenance
    stmt = select(AgentExecutionAudit).where(AgentExecutionAudit.execution_id == result.execution_id)
    audit_row = (await db_session.execute(stmt)).scalar_one_or_none()
    assert audit_row is not None
    assert audit_row.context_snapshot_id == snapshot.id
    assert audit_row.context_version == 2


@pytest.mark.asyncio
async def test_code_review_executor_transient_retry(db_session: AsyncSession):
    """Verify transient errors retry and succeed on subsequent attempt."""
    project = Project(
        name="Retry Test",
        slug=f"retry-test-{uuid.uuid4().hex[:8]}",
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

    code_input = CodeReviewInput(
        files=[CodeFile(file_path="main.py", language="python", content="x = 1\n")]
    )

    provider = MockLLMProvider()
    # Program provider to fail transiently once, then succeed
    provider.simulate_transient_failures(count=1)
    candidate = CodeReviewCandidate(summary="Retry success summary", findings=[])
    provider.register_structured_response(candidate)

    agent = CodeReviewAgent()
    executor = AgentExecutor(provider=provider, max_retries=2)

    result = await executor.execute(
        agent=agent,
        context=context,
        session=db_session,
        code_input=code_input,
    )

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.metadata["attempts"] == 2
    assert result.output is not None


@pytest.mark.asyncio
async def test_code_review_executor_validation_error_no_retry(db_session: AsyncSession):
    """Verify validation errors fail deterministically without retry."""
    project = Project(
        name="No Retry Test",
        slug=f"no-retry-{uuid.uuid4().hex[:8]}",
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

    # Missing code_input triggers AgentValidationError
    provider = MockLLMProvider()
    agent = CodeReviewAgent()
    executor = AgentExecutor(provider=provider, max_retries=3)

    result = await executor.execute(
        agent=agent,
        context=context,
        session=db_session,
        # code_input missing
    )

    assert result.status == AgentExecutionStatus.FAILED
    assert result.error is not None
    assert result.error.error_code == "VALIDATION_FAILED"
    assert result.metadata["attempts"] == 1  # Invariant: No retries on validation failure
