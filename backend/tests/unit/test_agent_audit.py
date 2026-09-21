"""Unit Tests for AgentExecutionAudit Database Persistence."""

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
async def test_agent_execution_audit_persistence(db_session: AsyncSession):
    """Verify that execution lifecycle persists AgentExecutionAudit record with context_version."""
    # 1. Create a persistent project
    project = Project(
        name="Audited Architecture Project",
        slug=f"audit-proj-{uuid.uuid4().hex[:8]}",
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
        context_version=12,
        generated_at=now,
    )

    agent = AuditedAgent()
    provider = MockLLMProvider()
    executor = AgentExecutor(provider=provider)

    # Execute agent with active db_session
    result = await executor.execute(
        agent=agent,
        context=context,
        session=db_session,
    )

    assert result.status == AgentExecutionStatus.COMPLETED

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
    assert audit.context_version == 12
    assert audit.started_at is not None
    assert audit.completed_at is not None
    assert audit.completed_at >= audit.started_at
    assert "architecture_style" in audit.output_summary
    assert audit.metadata_payload.get("provider") == "mock"
