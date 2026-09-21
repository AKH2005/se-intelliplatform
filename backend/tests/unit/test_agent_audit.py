"""Unit Tests for AgentExecutionAudit Database Persistence and Provenance."""

import uuid
from datetime import datetime, timezone
import pytest
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AbstractBaseAgent
from app.agents.contracts import (
    AgentExecutionStatus,
    AgentMetadata,
    AgentType,
)
from app.agents.execution import AgentExecutor
from app.agents.providers.mock import MockLLMProvider
from app.models.agent_audit import AgentExecutionAudit
from app.models.context_snapshot import ContextSnapshot
from app.models.project import Project, ProjectStatus
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse


class AuditOutputModel(BaseModel):
    architecture_style: str = "modular_monolith"


class AuditedAgent(AbstractBaseAgent[AuditOutputModel]):
    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id="audited-agent",
            name="Audited Agent",
            description="Agent for testing audit logging",
            version="1.2.0",
            agent_type=AgentType.ARCHITECTURE,
        )

    @property
    def output_schema(self) -> type[AuditOutputModel]:
        return AuditOutputModel

    async def analyze(self, context, **kwargs) -> dict:
        return {}

    async def generate(self, analysis_result, provider, **kwargs) -> AuditOutputModel:
        return AuditOutputModel()


@pytest.mark.asyncio
async def test_agent_execution_audit_live_context_persistence(db_session: AsyncSession):
    """Verify that live-context execution persists AgentExecutionAudit with NULL context_snapshot_id and NULL context_version (no fabrication)."""
    # 1. Create a persistent project
    project = Project(
        name="Live Context Architecture Project",
        slug=f"audit-live-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    now = datetime.now(timezone.utc)
    # context has a context_version counter, but it is NOT snapshot-backed
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
        context_version=12,
        generated_at=now,
    )

    agent = AuditedAgent()
    provider = MockLLMProvider()
    executor = AgentExecutor(provider=provider)

    # Execute agent against live context with active db_session
    result = await executor.execute(
        agent=agent,
        context=context,
        session=db_session,
    )

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.context_snapshot_id is None
    assert result.context_version is None

    # Query audit record from database
    stmt = select(AgentExecutionAudit).where(
        AgentExecutionAudit.execution_id == result.execution_id
    )
    res = await db_session.execute(stmt)
    audit = res.scalar_one_or_none()

    assert audit is not None
    assert audit.project_id == project.id
    assert audit.agent_id == "audited-agent"
    assert audit.agent_version == "1.2.0"
    assert audit.status == AgentExecutionStatus.COMPLETED
    # Provenance must be NULL for live-context: never fabricate or infer context_version
    assert audit.context_snapshot_id is None
    assert audit.context_version is None
    assert audit.started_at is not None
    assert audit.completed_at is not None
    assert audit.completed_at >= audit.started_at
    assert "architecture_style" in audit.output_summary
    assert audit.metadata_payload.get("provider") == "mock"


@pytest.mark.asyncio
async def test_agent_execution_audit_snapshot_backed_persistence(db_session: AsyncSession):
    """Verify that snapshot-backed execution persists actual snapshot UUID and actual version."""
    project = Project(
        name="Snapshot Backed Project",
        slug=f"audit-snap-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create an actual snapshot in the database
    snapshot = ContextSnapshot(
        project_id=project.id,
        version=5,
        context_data={"project": {"name": project.name}, "requirements": []},
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
        context_version=5,
        generated_at=now,
    )

    agent = AuditedAgent()
    provider = MockLLMProvider()
    executor = AgentExecutor(provider=provider)

    # Execute agent with explicit snapshot backing
    result = await executor.execute(
        agent=agent,
        context=context,
        session=db_session,
        snapshot=snapshot,
    )

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.context_snapshot_id == snapshot.id
    assert result.context_version == 5

    # Query audit record from database
    stmt = select(AgentExecutionAudit).where(
        AgentExecutionAudit.execution_id == result.execution_id
    )
    res = await db_session.execute(stmt)
    audit = res.scalar_one_or_none()

    assert audit is not None
    assert audit.project_id == project.id
    assert audit.context_snapshot_id == snapshot.id
    assert audit.context_version == 5
    assert audit.status == AgentExecutionStatus.COMPLETED
