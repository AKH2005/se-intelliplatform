"""Unit tests for RiskPredictionAgent execution through AgentExecutor."""

from datetime import datetime, timezone
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.contracts import AgentExecutionStatus
from app.agents.execution import AgentExecutor
from app.agents.providers.mock import MockLLMProvider
from app.agents.risk_prediction.agent import RiskPredictionAgent
from app.agents.risk_prediction.contracts import RiskPredictionOutput
from app.models.agent_audit import AgentExecutionAudit
from app.models.context_snapshot import ContextSnapshot
from app.models.project import Project, ProjectStatus
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse


@pytest.mark.asyncio
async def test_risk_prediction_executor_live_context(db_session: AsyncSession):
    """Verify RiskPredictionAgent executes through AgentExecutor against live context."""
    project = Project(
        name="Risk Live Project",
        slug=f"risk-live-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
        settings={
            "ml_risk_inputs": {
                "project_size": "Large",
                "team_experience_level": "Medium",
                "estimated_effort_hours": 1500.0,
                "complexity_level": "High",
                "requirement_stability": "Unstable",
            }
        },
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
            by_priority={},
            by_status={},
            completion_percentage=0.0,
        ),
        context_version=1,
        generated_at=now,
    )

    agent = RiskPredictionAgent()
    executor = AgentExecutor(provider=MockLLMProvider())

    result = await executor.execute(
        agent=agent,
        context=context,
        session=db_session,
    )

    # 1. Result verification
    assert result.status == AgentExecutionStatus.COMPLETED
    assert isinstance(result.output, RiskPredictionOutput)
    assert 1.0 <= result.output.predicted_risk_score <= 10.0
    assert result.validation.is_valid is True
    assert result.context_snapshot_id is None
    assert result.context_version is None
    assert result.started_at is not None
    assert result.completed_at is not None

    # 2. Database Audit Record verification
    stmt = select(AgentExecutionAudit).where(
        AgentExecutionAudit.execution_id == result.execution_id
    )
    audit = (await db_session.execute(stmt)).scalar_one_or_none()

    assert audit is not None
    assert audit.project_id == project.id
    assert audit.agent_id == "risk-prediction"
    assert audit.agent_version == "1.0.0"
    assert audit.status == AgentExecutionStatus.COMPLETED
    assert audit.context_snapshot_id is None
    assert audit.context_version is None
    assert "predicted_risk_score" in audit.output_summary
    assert "model_provenance" in audit.output_summary
    assert "limitations" in audit.output_summary


@pytest.mark.asyncio
async def test_risk_prediction_executor_snapshot_backed(db_session: AsyncSession):
    """Verify RiskPredictionAgent executes with snapshot context provenance preserved."""
    project = Project(
        name="Risk Snapshot Project",
        slug=f"risk-snap-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
        settings={
            "ml_risk_inputs": {
                "project_size": "Small",
                "team_experience_level": "High",
                "estimated_effort_hours": 300.0,
                "complexity_level": "Low",
                "requirement_stability": "Stable",
            }
        },
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    snapshot = ContextSnapshot(
        project_id=project.id,
        version=5,
        context_data={"project": {"name": project.name}},
        summary="Milestone freeze",
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
            by_priority={},
            by_status={},
            completion_percentage=0.0,
        ),
        context_version=5,
        generated_at=now,
    )

    agent = RiskPredictionAgent()
    executor = AgentExecutor(provider=MockLLMProvider())

    result = await executor.execute(
        agent=agent,
        context=context,
        snapshot=snapshot,
        session=db_session,
    )

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.context_snapshot_id == snapshot.id
    assert result.context_version == 5

    stmt = select(AgentExecutionAudit).where(
        AgentExecutionAudit.execution_id == result.execution_id
    )
    audit = (await db_session.execute(stmt)).scalar_one_or_none()

    assert audit is not None
    assert audit.context_snapshot_id == snapshot.id
    assert audit.context_version == 5


@pytest.mark.asyncio
async def test_risk_prediction_executor_missing_features_failure(db_session: AsyncSession):
    """Verify executor catches MLFeatureUnavailableError without retrying and records FAILED status."""
    project = Project(
        name="Incomplete Settings Project",
        slug=f"risk-fail-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
        settings={},  # Missing required ML features
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
            by_priority={},
            by_status={},
            completion_percentage=0.0,
        ),
        context_version=1,
        generated_at=now,
    )

    agent = RiskPredictionAgent()
    executor = AgentExecutor(provider=MockLLMProvider(), max_retries=3)

    result = await executor.execute(
        agent=agent,
        context=context,
        session=db_session,
    )

    # Must fail immediately without retrying
    assert result.status == AgentExecutionStatus.FAILED
    assert result.output is None
    assert result.error is not None
    assert result.error.error_code == "VALIDATION_FAILED"
    assert result.metadata["attempts"] == 1

    # Verify audit record reflects FAILED status
    stmt = select(AgentExecutionAudit).where(
        AgentExecutionAudit.execution_id == result.execution_id
    )
    audit = (await db_session.execute(stmt)).scalar_one_or_none()

    assert audit is not None
    assert audit.status == AgentExecutionStatus.FAILED
    assert audit.error_code == "VALIDATION_FAILED"
