"""Unit tests for BugPredictionAgent execution through AgentExecutor."""

from datetime import datetime, timezone
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.bug_prediction.agent import BugPredictionAgent
from app.agents.bug_prediction.contracts import BugPredictionOutput, DefectPredictionLabel
from app.agents.contracts import AgentExecutionStatus
from app.agents.execution import AgentExecutor
from app.agents.providers.mock import MockLLMProvider
from app.models.agent_audit import AgentExecutionAudit
from app.models.context_snapshot import ContextSnapshot
from app.models.project import Project, ProjectStatus
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse


def _sample_bug_metrics() -> dict[str, float]:
    return {
        "loc": 45.0,
        "v(g)": 7.0,
        "ev(g)": 3.0,
        "iv(g)": 4.0,
        "n": 120.0,
        "v": 650.0,
        "l": 0.05,
        "d": 20.0,
        "i": 32.5,
        "e": 13000.0,
        "b": 0.22,
        "t": 722.0,
        "lOCode": 35.0,
        "lOComment": 5.0,
        "lOBlank": 5.0,
        "locCodeAndComment": 2.0,
        "uniq_Op": 18.0,
        "uniq_Opnd": 25.0,
        "total_Op": 70.0,
        "total_Opnd": 50.0,
        "branchCount": 13.0,
    }


@pytest.mark.asyncio
async def test_bug_prediction_executor_live_context(db_session: AsyncSession):
    """Verify BugPredictionAgent executes through AgentExecutor against live context."""
    project = Project(
        name="Bug Live Project",
        slug=f"bug-live-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
        settings={"ml_bug_inputs": _sample_bug_metrics()},
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

    mock_provider = MockLLMProvider()
    agent = BugPredictionAgent()
    executor = AgentExecutor(provider=mock_provider)

    result = await executor.execute(
        agent=agent,
        context=context,
        session=db_session,
    )

    # 1. Result verification
    assert result.status == AgentExecutionStatus.COMPLETED
    assert isinstance(result.output, BugPredictionOutput)
    assert isinstance(result.output.prediction_label, DefectPredictionLabel)
    assert 0.0 <= result.output.predicted_probability <= 1.0
    assert result.output.target == "defects"
    assert result.validation.is_valid is True
    assert result.context_snapshot_id is None
    assert result.context_version is None
    assert result.started_at is not None
    assert result.completed_at is not None

    # Zero LLM calls
    assert len(mock_provider.call_history) == 0

    # 2. Database Audit Record verification
    stmt = select(AgentExecutionAudit).where(
        AgentExecutionAudit.execution_id == result.execution_id
    )
    audit = (await db_session.execute(stmt)).scalar_one_or_none()

    assert audit is not None
    assert audit.project_id == project.id
    assert audit.agent_id == "bug-prediction"
    assert audit.agent_version == "1.0.0"
    assert audit.status == AgentExecutionStatus.COMPLETED
    assert audit.context_snapshot_id is None
    assert audit.context_version is None
    assert "prediction_label" in audit.output_summary
    assert "model_provenance" in audit.output_summary


@pytest.mark.asyncio
async def test_bug_prediction_executor_snapshot_backed(db_session: AsyncSession):
    """Verify BugPredictionAgent executes with snapshot context provenance preserved."""
    project = Project(
        name="Bug Snapshot Project",
        slug=f"bug-snap-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
        settings={"ml_bug_inputs": _sample_bug_metrics()},
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    snapshot = ContextSnapshot(
        project_id=project.id,
        version=4,
        context_data={"project": {"name": project.name}},
        summary="Sprint baseline code audit",
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
        context_version=4,
        generated_at=now,
    )

    agent = BugPredictionAgent()
    executor = AgentExecutor(provider=MockLLMProvider())

    result = await executor.execute(
        agent=agent,
        context=context,
        session=db_session,
        context_snapshot_id=snapshot.id,
        context_version=snapshot.version,
    )

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.context_snapshot_id == snapshot.id
    assert result.context_version == 4

    stmt = select(AgentExecutionAudit).where(
        AgentExecutionAudit.execution_id == result.execution_id
    )
    audit = (await db_session.execute(stmt)).scalar_one_or_none()
    assert audit is not None
    assert audit.context_snapshot_id == snapshot.id
    assert audit.context_version == 4


@pytest.mark.asyncio
async def test_bug_prediction_executor_missing_features_failure(db_session: AsyncSession):
    """Verify AgentExecutor reports FAILED status and records audit on missing features."""
    project = Project(
        name="Bug Missing Features Project",
        slug=f"bug-missing-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
        settings={},  # No ml_bug_inputs
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

    agent = BugPredictionAgent()
    executor = AgentExecutor(provider=MockLLMProvider())

    result = await executor.execute(
        agent=agent,
        context=context,
        session=db_session,
    )

    assert result.status == AgentExecutionStatus.FAILED
    assert result.output is None
    assert result.error is not None
    assert result.error.error_code == "VALIDATION_FAILED"
    assert "Required ML bug prediction features are unavailable" in result.error.message

    stmt = select(AgentExecutionAudit).where(
        AgentExecutionAudit.execution_id == result.execution_id
    )
    audit = (await db_session.execute(stmt)).scalar_one_or_none()
    assert audit is not None
    assert audit.status == AgentExecutionStatus.FAILED


@pytest.mark.asyncio
async def test_bug_prediction_executor_read_only_guarantee(db_session: AsyncSession):
    """Verify BugPredictionAgent does not mutate Project entity in database."""
    initial_settings = {"ml_bug_inputs": _sample_bug_metrics()}
    project = Project(
        name="Bug ReadOnly Project",
        slug=f"bug-ro-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
        settings=initial_settings,
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

    agent = BugPredictionAgent()
    executor = AgentExecutor(provider=MockLLMProvider())

    await executor.execute(agent=agent, context=context, session=db_session)

    # Re-query project from database
    refreshed_project = (await db_session.execute(
        select(Project).where(Project.id == project.id)
    )).scalar_one()

    assert refreshed_project.name == "Bug ReadOnly Project"
    assert refreshed_project.status == ProjectStatus.IN_PROGRESS
    assert refreshed_project.settings == initial_settings
