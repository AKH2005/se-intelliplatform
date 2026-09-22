"""Unit tests for TimelinePredictionAgent execution through AgentExecutor."""

from datetime import datetime, timezone
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.contracts import AgentExecutionStatus
from app.agents.execution import AgentExecutor
from app.agents.providers.mock import MockLLMProvider
from app.agents.timeline_prediction.agent import TimelinePredictionAgent
from app.agents.timeline_prediction.contracts import TimelinePredictionOutput
from app.models.agent_audit import AgentExecutionAudit
from app.models.context_snapshot import ContextSnapshot
from app.models.project import Project, ProjectStatus
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse


@pytest.mark.asyncio
async def test_timeline_prediction_executor_live_context(db_session: AsyncSession):
    """Verify TimelinePredictionAgent executes through AgentExecutor against live context."""
    project = Project(
        name="Timeline Live Project",
        slug=f"timeline-live-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
        settings={
            "ml_timeline_inputs": {
                "afp": 650.0,
                "input_count": 70.0,
                "output_count": 50.0,
                "enquiry_count": 35.0,
                "file_count": 30.0,
                "interface_count": 20.0,
                "resource_level": 3,
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

    agent = TimelinePredictionAgent()
    executor = AgentExecutor(provider=MockLLMProvider())

    result = await executor.execute(
        agent=agent,
        context=context,
        session=db_session,
    )

    # 1. Result verification
    assert result.status == AgentExecutionStatus.COMPLETED
    assert isinstance(result.output, TimelinePredictionOutput)
    assert result.output.predicted_duration_months > 0.0
    assert result.output.target == "Duration"
    assert result.output.target_unit == "months"
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
    assert audit.agent_id == "timeline-prediction"
    assert audit.agent_version == "1.0.0"
    assert audit.status == AgentExecutionStatus.COMPLETED
    assert audit.context_snapshot_id is None
    assert audit.context_version is None
    assert "predicted_duration_months" in audit.output_summary
    assert "model_provenance" in audit.output_summary


@pytest.mark.asyncio
async def test_timeline_prediction_executor_snapshot_backed(db_session: AsyncSession):
    """Verify TimelinePredictionAgent executes with snapshot context provenance preserved."""
    project = Project(
        name="Timeline Snapshot Project",
        slug=f"timeline-snap-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
        settings={
            "ml_timeline_inputs": {
                "afp": 250.0,
                "input_count": 25.0,
                "output_count": 15.0,
                "enquiry_count": 10.0,
                "file_count": 8.0,
                "interface_count": 4.0,
                "resource_level": 1,
            }
        },
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    snapshot = ContextSnapshot(
        project_id=project.id,
        version=3,
        context_data={"project": {"name": project.name}},
        summary="Sprint planning baseline",
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
        context_version=3,
        generated_at=now,
    )

    agent = TimelinePredictionAgent()
    executor = AgentExecutor(provider=MockLLMProvider())

    result = await executor.execute(
        agent=agent,
        context=context,
        snapshot=snapshot,
        session=db_session,
    )

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.context_snapshot_id == snapshot.id
    assert result.context_version == 3

    stmt = select(AgentExecutionAudit).where(
        AgentExecutionAudit.execution_id == result.execution_id
    )
    audit = (await db_session.execute(stmt)).scalar_one_or_none()

    assert audit is not None
    assert audit.context_snapshot_id == snapshot.id
    assert audit.context_version == 3


@pytest.mark.asyncio
async def test_timeline_prediction_executor_missing_features_failure(db_session: AsyncSession):
    """Verify executor catches TimelineFeatureUnavailableError without retrying and records FAILED status."""
    project = Project(
        name="Incomplete Timeline Project",
        slug=f"timeline-fail-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
        settings={},  # Missing required timeline features
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

    agent = TimelinePredictionAgent()
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
