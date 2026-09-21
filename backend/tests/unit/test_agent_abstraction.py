"""Unit Tests for AbstractBaseAgent Lifecycle and Result Envelopes."""

from typing import Any
import pytest
from pydantic import BaseModel, Field

from app.agents.base import AbstractBaseAgent
from app.agents.contracts import (
    AgentExecutionStatus,
    AgentMetadata,
    AgentType,
    ValidationResult,
)
from app.agents.providers.mock import MockLLMProvider
from app.schemas.context import (
    ProjectContextResponse,
    RequirementStatistics,
)
from app.schemas.project import ProjectResponse


# Test DTO models
class MockAgentOutput(BaseModel):
    summary: str = Field(..., min_length=3)
    score: int = Field(..., ge=0, le=100)


class SampleTestAgent(AbstractBaseAgent[MockAgentOutput]):
    """Concrete test agent implementation for framework verification."""

    def __init__(self, should_fail_domain_validation: bool = False) -> None:
        self.should_fail_domain_validation = should_fail_domain_validation
        self.initialized = False

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id="test-sample-agent",
            name="Sample Test Agent",
            description="Agent for testing framework lifecycle",
            version="1.0.0",
            agent_type=AgentType.ANALYSIS,
        )

    @property
    def output_schema(self) -> type[MockAgentOutput]:
        return MockAgentOutput

    async def initialize(self) -> None:
        self.initialized = True

    async def analyze(self, context: ProjectContextResponse, **kwargs: Any) -> dict[str, Any]:
        return {
            "req_count": context.statistics.total_requirements,
            "project_slug": context.project.slug,
        }

    async def generate(
        self,
        analysis_result: dict[str, Any],
        provider: MockLLMProvider,  # type: ignore[override]
        **kwargs: Any,
    ) -> MockAgentOutput:
        # Request generation from provider
        return await provider.generate_structured(
            request=None,  # MockLLMProvider can use canned structured output
            response_model=self.output_schema,
        )

    def validate_output(
        self,
        output: MockAgentOutput,
        context: ProjectContextResponse,
    ) -> ValidationResult:
        if self.should_fail_domain_validation:
            return ValidationResult(
                is_valid=False,
                errors=["Domain business invariant failed: score exceeds threshold."],
            )
        return ValidationResult(is_valid=True)


@pytest.fixture
def mock_context() -> ProjectContextResponse:
    """Provide a mock ProjectContextResponse."""
    import uuid
    from datetime import datetime, timezone
    return ProjectContextResponse(
        project=ProjectResponse(
            id=uuid.uuid4(),
            name="Test Project",
            slug="test-proj",
            status="DRAFT",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
        requirements=[],
        statistics=RequirementStatistics(
            total_requirements=5,
            active_requirements=3,
            functional_count=2,
            non_functional_count=1,
            constraint_count=0,
            completion_percentage=33.33,
        ),
        context_version=4,
        generated_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_agent_successful_execution_lifecycle(mock_context: ProjectContextResponse):
    """Verify full successful lifecycle: initialize -> analyze -> generate -> validate -> complete."""
    agent = SampleTestAgent()
    provider = MockLLMProvider()
    provider.register_structured_response(MockAgentOutput(summary="Analysis complete", score=85))

    result = await agent.execute(context=mock_context, provider=provider)

    assert agent.initialized is True
    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.output is not None
    assert result.output.summary == "Analysis complete"
    assert result.output.score == 85
    assert result.validation.is_valid is True
    assert result.error is None
    assert result.context_version == 4
    assert result.agent_id == "test-sample-agent"
    assert result.agent_version == "1.0.0"


@pytest.mark.asyncio
async def test_agent_deterministic_validation_failure(mock_context: ProjectContextResponse):
    """Verify domain validation failure transitions lifecycle to FAILED."""
    agent = SampleTestAgent(should_fail_domain_validation=True)
    provider = MockLLMProvider()
    provider.register_structured_response(MockAgentOutput(summary="High score", score=99))

    result = await agent.execute(context=mock_context, provider=provider)

    assert result.status == AgentExecutionStatus.FAILED
    assert result.output is None
    assert result.validation.is_valid is False
    assert "score exceeds threshold" in result.validation.errors[0]
    assert result.error is not None
    assert result.error.error_code == "VALIDATION_FAILED"
    assert result.context_version == 4


@pytest.mark.asyncio
async def test_agent_provider_failure(mock_context: ProjectContextResponse):
    """Verify provider exception results in FAILED result with error details."""
    agent = SampleTestAgent()
    provider = MockLLMProvider()
    from app.agents.exceptions import ProviderError
    provider.simulate_permanent_failure(ProviderError("Provider unavailable", provider_name="mock"))

    result = await agent.execute(context=mock_context, provider=provider)

    assert result.status == AgentExecutionStatus.FAILED
    assert result.output is None
    assert result.error is not None
    assert result.error.error_code == "PROVIDER_ERROR"
    assert "Provider unavailable" in result.error.message
