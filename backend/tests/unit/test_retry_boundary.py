"""Unit Tests for AgentExecutor Controlled Retry Boundary."""

import uuid
from datetime import datetime, timezone
import pytest
from pydantic import BaseModel, Field

from app.agents.base import AbstractBaseAgent
from app.agents.contracts import (
    AgentExecutionStatus,
    AgentMetadata,
    AgentType,
    ValidationResult,
)
from app.agents.exceptions import ProviderError, TransientProviderError
from app.agents.execution import AgentExecutor
from app.agents.providers.mock import MockLLMProvider
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse


class OutputModel(BaseModel):
    message: str = Field(..., min_length=2)


class ResilientAgent(AbstractBaseAgent[OutputModel]):
    def __init__(self, should_fail_validation: bool = False) -> None:
        self.should_fail_validation = should_fail_validation
        self.call_count = 0

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id="resilient-agent",
            name="Resilient Agent",
            description="Tests retry boundary",
            version="1.0.0",
            agent_type=AgentType.GENERATION,
        )

    @property
    def output_schema(self) -> type[OutputModel]:
        return OutputModel

    async def analyze(self, context, **kwargs) -> dict:
        return {}

    async def generate(self, analysis_result, provider, **kwargs) -> OutputModel:
        self.call_count += 1
        return await provider.generate_structured(None, OutputModel)

    def validate_output(self, output: OutputModel, context) -> ValidationResult:
        if self.should_fail_validation:
            return ValidationResult(is_valid=False, errors=["Business invariant violated"])
        return ValidationResult(is_valid=True)


@pytest.fixture
def mock_context() -> ProjectContextResponse:
    now = datetime.now(timezone.utc)
    return ProjectContextResponse(
        project=ProjectResponse(
            id=uuid.uuid4(),
            name="Proj",
            slug="proj",
            status="DRAFT",
            created_at=now,
            updated_at=now,
        ),
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


@pytest.mark.asyncio
async def test_retry_boundary_recovers_from_transient_error(mock_context: ProjectContextResponse):
    """Verify that TransientProviderError is retried and succeeds on recovery."""
    agent = ResilientAgent()
    provider = MockLLMProvider()
    # 1 transient error, then success
    provider.simulate_transient_failures(count=1)
    provider.register_structured_response(OutputModel(message="Success after retry"))

    executor = AgentExecutor(provider=provider, max_retries=3, retry_delay_seconds=0.0)
    result = await executor.execute(agent=agent, context=mock_context)

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.output is not None
    assert result.output.message == "Success after retry"
    # Agent was invoked twice: first attempt failed transiently, second succeeded
    assert agent.call_count == 2


@pytest.mark.asyncio
async def test_retry_boundary_never_retries_validation_failure(mock_context: ProjectContextResponse):
    """Verify that validation failures are NEVER retried and fail-fast on attempt 1."""
    agent = ResilientAgent(should_fail_validation=True)
    provider = MockLLMProvider()
    provider.register_structured_response(OutputModel(message="Structurally valid"))

    executor = AgentExecutor(provider=provider, max_retries=3, retry_delay_seconds=0.0)
    result = await executor.execute(agent=agent, context=mock_context)

    assert result.status == AgentExecutionStatus.FAILED
    assert result.error is not None
    assert result.error.error_code == "VALIDATION_FAILED"
    assert result.error.transient is False
    # Agent was invoked exactly once (no retry loop for business validation errors)
    assert agent.call_count == 1


@pytest.mark.asyncio
async def test_retry_boundary_stops_at_max_retries(mock_context: ProjectContextResponse):
    """Verify retry loop terminates at max_retries if transient failure persists."""
    agent = ResilientAgent()
    provider = MockLLMProvider()
    # 5 transient failures, but max_retries is 2
    provider.simulate_transient_failures(count=5)

    executor = AgentExecutor(provider=provider, max_retries=2, retry_delay_seconds=0.0)
    result = await executor.execute(agent=agent, context=mock_context)

    assert result.status == AgentExecutionStatus.FAILED
    assert result.error is not None
    assert result.error.transient is True
    assert agent.call_count == 2
