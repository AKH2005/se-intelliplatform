"""Unit Tests for AbstractLLMProvider and MockLLMProvider."""

import pytest
from pydantic import BaseModel, Field

from app.agents.exceptions import ProviderError, TransientProviderError
from app.agents.providers.base import LLMMessage, LLMRequest
from app.agents.providers.mock import MockLLMProvider


class SampleStructuredDTO(BaseModel):
    summary: str = Field(default="Default summary")
    count: int = Field(default=1)


@pytest.mark.asyncio
async def test_mock_provider_text_generation():
    """Verify mock provider generates queued text and tracks history."""
    provider = MockLLMProvider()
    provider.register_response("Custom generated text response.")

    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Analyze context")],
        model="mock-v1",
    )
    response = await provider.generate(request)

    assert response.content == "Custom generated text response."
    assert len(provider.call_history) == 1
    assert provider.call_history[0].model == "mock-v1"


@pytest.mark.asyncio
async def test_mock_provider_structured_generation():
    """Verify mock provider returns structured Pydantic model directly."""
    provider = MockLLMProvider()
    expected_model = SampleStructuredDTO(summary="Explicit Model Output", count=99)
    provider.register_structured_response(expected_model)

    request = LLMRequest(
        messages=[LLMMessage(role="user", content="Generate structured plan")],
        model="mock-v1",
    )
    output = await provider.generate_structured(request, SampleStructuredDTO)

    assert output.summary == "Explicit Model Output"
    assert output.count == 99


@pytest.mark.asyncio
async def test_mock_provider_transient_failure_simulation():
    """Verify mock provider raises TransientProviderError for configured number of calls."""
    provider = MockLLMProvider()
    provider.simulate_transient_failures(count=2)
    provider.register_response("Eventual success")

    request = LLMRequest(messages=[LLMMessage(role="user", content="Test")], model="mock-v1")

    # First call: transient error
    with pytest.raises(TransientProviderError) as exc1:
        await provider.generate(request)
    assert exc1.value.transient is True

    # Second call: transient error
    with pytest.raises(TransientProviderError) as exc2:
        await provider.generate(request)
    assert exc2.value.transient is True

    # Third call: success
    res = await provider.generate(request)
    assert res.content == "Eventual success"


@pytest.mark.asyncio
async def test_mock_provider_permanent_failure_simulation():
    """Verify mock provider raises permanent ProviderError."""
    provider = MockLLMProvider()
    provider.simulate_permanent_failure(ProviderError("Permanent API crash", provider_name="mock", transient=False))

    request = LLMRequest(messages=[LLMMessage(role="user", content="Test")], model="mock-v1")

    with pytest.raises(ProviderError) as exc:
        await provider.generate(request)
    assert exc.value.transient is False
    assert "Permanent API crash" in str(exc.value)
