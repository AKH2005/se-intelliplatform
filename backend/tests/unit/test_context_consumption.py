"""Unit Tests for Canonical Project Context Consumption."""

import uuid
from datetime import datetime, timezone
import pytest
from pydantic import BaseModel

from app.agents.base import AbstractBaseAgent
from app.agents.contracts import AgentMetadata, AgentType
from app.agents.providers.mock import MockLLMProvider
from app.models.requirement import RequirementPriority, RequirementStatus, RequirementType
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse
from app.schemas.requirement import RequirementResponse


class ContextConsumerOutput(BaseModel):
    consumed_version: int
    active_count: int
    first_req_title: str


class ContextTestingAgent(AbstractBaseAgent[ContextConsumerOutput]):
    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id="context-testing-agent",
            name="Context Testing Agent",
            description="Tests canonical context consumption",
            version="1.0.0",
            agent_type=AgentType.ANALYSIS,
        )

    @property
    def output_schema(self) -> type[ContextConsumerOutput]:
        return ContextConsumerOutput

    async def analyze(self, context: ProjectContextResponse, **kwargs) -> dict:
        first_title = context.requirements[0].title if context.requirements else "None"
        return {
            "consumed_version": context.context_version,
            "active_count": context.statistics.active_requirements,
            "first_req_title": first_title,
        }

    async def generate(self, analysis_result: dict, provider, **kwargs) -> ContextConsumerOutput:
        return ContextConsumerOutput(**analysis_result)


@pytest.mark.asyncio
async def test_agent_consumes_canonical_context():
    """Verify that agent consumes canonical Phase 2 ProjectContextResponse without schema duplication."""
    project_id = uuid.uuid4()
    req_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    context = ProjectContextResponse(
        project=ProjectResponse(
            id=project_id,
            name="FinTech Microservices",
            slug="fintech-ms",
            status="IN_PROGRESS",
            created_at=now,
            updated_at=now,
        ),
        requirements=[
            RequirementResponse(
                id=req_id,
                project_id=project_id,
                title="PCI-DSS Compliance",
                description="Tokenize all card data.",
                type=RequirementType.CONSTRAINT,
                priority=RequirementPriority.CRITICAL,
                status=RequirementStatus.APPROVED,
                is_archived=False,
                created_at=now,
                updated_at=now,
            )
        ],
        statistics=RequirementStatistics(
            total_requirements=1,
            active_requirements=1,
            functional_count=0,
            non_functional_count=0,
            constraint_count=1,
            completion_percentage=0.0,
        ),
        context_version=7,
        generated_at=now,
    )

    agent = ContextTestingAgent()
    provider = MockLLMProvider()

    result = await agent.execute(context=context, provider=provider)

    assert result.status.value == "COMPLETED"
    assert result.context_version == 7
    assert result.output is not None
    assert result.output.consumed_version == 7
    assert result.output.active_count == 1
    assert result.output.first_req_title == "PCI-DSS Compliance"
