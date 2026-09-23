"""Unit tests for ExplainabilityAgent execution through AgentExecutor."""

from datetime import datetime, timezone
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.contracts import AgentExecutionStatus
from app.agents.exceptions import ProviderError
from app.agents.execution import AgentExecutor
from app.agents.explainability.agent import ExplainabilityAgent
from app.agents.explainability.contracts import (
    ClaimType,
    EngineeringInsight,
    ExplainabilityCandidate,
    ExplainabilityInput,
    ExplainabilityOutput,
    InsightCategory,
    SourceReference,
)
from app.agents.providers.mock import MockLLMProvider
from app.agents.risk_prediction.contracts import (
    RiskLevel,
    RiskModelProvenance,
    RiskPredictionOutput,
)
from app.models.agent_audit import AgentExecutionAudit
from app.models.context_snapshot import ContextSnapshot
from app.models.project import Project, ProjectStatus
from app.models.requirement import Requirement, RequirementPriority, RequirementStatus, RequirementType
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse
from app.schemas.requirement import RequirementResponse


@pytest.fixture
def sample_risk_output():
    return RiskPredictionOutput(
        predicted_risk_score=6.8,
        risk_level=RiskLevel.HIGH,
        feature_summary={"active_requirements_count": 5},
        model_provenance=RiskModelProvenance(
            model_name="risk_ridge_v1",
            model_version="1.0.0",
            algorithm="Ridge",
            training_dataset="risk_data.csv",
            feature_schema_version="1.0.0",
            artifact_checksum="abc123checksum",
        ),
        summary="High risk predicted based on requirements density.",
        limitations=["Trained on 585 historical projects."],
    )


@pytest.mark.asyncio
async def test_explainability_executor_live_context(db_session: AsyncSession, sample_risk_output):
    """Verify ExplainabilityAgent executes through AgentExecutor with live context and DB audit."""
    project = Project(
        name="Explainability Live Engine",
        slug=f"explain-live-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.flush()

    req = Requirement(
        project_id=project.id,
        title="Transaction Isolation",
        description="Must implement SERIALIZABLE isolation level.",
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

    candidate = ExplainabilityCandidate(
        summary="Live explainability synthesis for transaction isolation scope.",
        insights=[
            EngineeringInsight(
                insight_id="RAW-01",
                category=InsightCategory.RISK,
                title="Transaction Concurrency Risk Impact",
                summary="Ridge regression model risk score correlates with strict isolation.",
                explanation="Enforcing SERIALIZABLE isolation increases lock contention risks according to model signals.",
                source_references=[
                    SourceReference(
                        agent_id="risk-prediction",
                        source_entity_id="risk_ridge_v1",
                        source_field="predicted_risk_score",
                        claim_type=ClaimType.FACT,
                    )
                ],
                suggested_actions=["Consider READ COMMITTED with optimistic concurrency control."],
            )
        ],
    )

    provider = MockLLMProvider()
    provider.register_structured_response(candidate)

    agent = ExplainabilityAgent()
    executor = AgentExecutor(provider=provider)

    inp = ExplainabilityInput(
        risk_prediction=sample_risk_output,
        target_scope="Database Concurrency",
        user_query="How does transaction isolation affect risk?",
    )

    result = await executor.execute(
        agent=agent,
        context=context,
        session=db_session,
        explainability_input=inp,
    )

    # 1. Verify result structure
    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.error is None
    assert isinstance(result.output, ExplainabilityOutput)
    assert result.output.agent_id == "explainability-insights"
    assert result.output.metrics.total_insights == 1
    assert result.output.insights[0].insight_id == "INSIGHT-001"

    # 2. Verify DB audit trail
    stmt = select(AgentExecutionAudit).where(
        AgentExecutionAudit.execution_id == result.execution_id,
    )
    res = await db_session.execute(stmt)
    audit = res.scalars().first()
    assert audit is not None
    assert audit.status == AgentExecutionStatus.COMPLETED
    assert audit.agent_id == "explainability-insights"
    assert audit.project_id == project.id
    assert audit.completed_at is not None
    assert audit.error_code is None


@pytest.mark.asyncio
async def test_explainability_executor_snapshot_context(db_session: AsyncSession, sample_risk_output):
    """Verify ExplainabilityAgent executes using a stored ContextSnapshot."""
    project = Project(
        name="Snapshot Explain Engine",
        slug=f"snapshot-explain-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.flush()

    snapshot = ContextSnapshot(
        project_id=project.id,
        version=2,
        context_data={"project": {"name": project.name}},
        summary="Sprint 2 explainability snapshot",
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

    candidate = ExplainabilityCandidate(
        summary="Synthesis on frozen context snapshot.",
        insights=[
            EngineeringInsight(
                insight_id="RAW-01",
                category=InsightCategory.RISK,
                title="Historical Risk Benchmark",
                summary="Grounded in frozen snapshot.",
                explanation="Model evaluation on snapshot baseline.",
                source_references=[
                    SourceReference(
                        agent_id="risk-prediction",
                        source_entity_id="risk_ridge_v1",
                        source_field="predicted_risk_score",
                        claim_type=ClaimType.FACT,
                    )
                ],
            )
        ],
    )

    provider = MockLLMProvider()
    provider.register_structured_response(candidate)

    agent = ExplainabilityAgent()
    executor = AgentExecutor(provider=provider)

    inp = ExplainabilityInput(risk_prediction=sample_risk_output)

    result = await executor.execute(
        agent=agent,
        context=context,
        session=db_session,
        explainability_input=inp,
        context_snapshot_id=snapshot.id,
    )

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.output.metrics.total_insights == 1

    # Verify audit recorded context_snapshot_id
    stmt = select(AgentExecutionAudit).where(
        AgentExecutionAudit.execution_id == result.execution_id,
    )
    res = await db_session.execute(stmt)
    audit = res.scalars().first()
    assert audit is not None
    assert audit.context_snapshot_id == snapshot.id


@pytest.mark.asyncio
async def test_explainability_executor_retry_behavior(db_session: AsyncSession, sample_risk_output):
    """Verify AgentExecutor retries on transient errors for ExplainabilityAgent."""
    project = Project(
        name="Retry Explain Engine",
        slug=f"retry-explain-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.commit()

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

    candidate = ExplainabilityCandidate(
        summary="Explainability recovered after transient retry.",
        insights=[
            EngineeringInsight(
                insight_id="RAW-RETRY",
                category=InsightCategory.RISK,
                title="Recovered Risk Explanation",
                summary="Successful response after retry.",
                explanation="Transient provider network hiccup was automatically retried.",
                source_references=[
                    SourceReference(
                        agent_id="risk-prediction",
                        source_entity_id="risk_ridge_v1",
                        source_field="predicted_risk_score",
                        claim_type=ClaimType.FACT,
                    )
                ],
            )
        ],
    )

    provider = MockLLMProvider()
    provider.simulate_transient_failures(count=1)
    provider.register_structured_response(candidate)

    agent = ExplainabilityAgent()
    executor = AgentExecutor(provider=provider, max_retries=2)

    inp = ExplainabilityInput(risk_prediction=sample_risk_output)

    result = await executor.execute(
        agent=agent,
        context=context,
        session=db_session,
        explainability_input=inp,
    )

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.metadata["attempts"] == 2
    assert result.output.insights[0].insight_id == "INSIGHT-001"


@pytest.mark.asyncio
async def test_explainability_executor_all_phantom_fails_without_retry(
    db_session: AsyncSession, sample_risk_output
):
    """Verify that candidate with only phantom references fails deterministically in AgentExecutor without retry."""
    project = Project(
        name="Phantom Fail Engine",
        slug=f"phantom-fail-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.commit()

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

    candidate = ExplainabilityCandidate(
        summary="Phantom candidate.",
        insights=[
            EngineeringInsight(
                insight_id="RAW-PHANTOM",
                category=InsightCategory.CODE_REVIEW,
                title="Phantom Title",
                summary="Phantom Summary",
                explanation="Phantom Explanation",
                source_references=[
                    SourceReference(
                        agent_id="code-review",  # Unsupplied!
                        source_entity_id="CR-999",
                        source_field="severity",
                        claim_type=ClaimType.FACT,
                    )
                ],
            )
        ],
    )

    provider = MockLLMProvider()
    provider.register_structured_response(candidate)

    agent = ExplainabilityAgent()
    executor = AgentExecutor(provider=provider, max_retries=2)

    inp = ExplainabilityInput(risk_prediction=sample_risk_output)

    result = await executor.execute(
        agent=agent,
        context=context,
        session=db_session,
        explainability_input=inp,
    )

    # Invariant: Must fail with FAILED status and error code VALIDATION_FAILED
    assert result.status == AgentExecutionStatus.FAILED
    assert result.output is None
    assert result.error is not None
    assert result.error.error_code == "VALIDATION_FAILED"
    assert result.error.transient is False
    assert result.metadata["attempts"] == 1  # Never retry deterministic validation failure

    # Verify audit recorded FAILED
    stmt = select(AgentExecutionAudit).where(
        AgentExecutionAudit.execution_id == result.execution_id,
    )
    res = await db_session.execute(stmt)
    audit = res.scalars().first()
    assert audit is not None
    assert audit.status == AgentExecutionStatus.FAILED
    assert audit.error_code == "VALIDATION_FAILED"
