"""Deterministic Unit and Contract Tests for Multi-Provider LLM Foundation (Phase 10C).

Verifies:
- ProviderFactory resolution and strict error handling (no silent fallback)
- MockProvider, GroqProvider, and GeminiProvider contracts
- Structured output validation and Pydantic schema enforcement
- Normalized error classification (transient vs. non-transient)
- Security guarantees: credential redaction in logs/exceptions
- Offline execution: ZERO external API network calls or real quota consumption
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import pytest
from pydantic import BaseModel, Field

from app.agents.exceptions import (
    AgentConfigurationError,
    ProviderError,
    TransientProviderError,
)
from app.agents.providers.base import LLMMessage, LLMRequest, LLMResponse
from app.agents.providers.factory import get_llm_provider
from app.agents.providers.gemini import GeminiProvider
from app.agents.providers.groq import GroqProvider
from app.agents.providers.mock import MockLLMProvider
from app.agents.requirement_analysis.contracts import RequirementAnalysisCandidate


class SampleSchema(BaseModel):
    name: str = Field(..., description="Entity name")
    count: int = Field(..., description="Entity count")


# ==============================================================================
# 1. ProviderFactory & Configuration Tests
# ==============================================================================

def test_factory_mock_selection():
    """Mock selection returns MockLLMProvider without requiring API keys."""
    provider = get_llm_provider(provider_name="mock")
    assert isinstance(provider, MockLLMProvider)
    assert provider.provider_name == "mock"
    assert provider.default_model == "mock-model"


def test_factory_groq_selection_with_key():
    """Groq selection succeeds when api_key is provided."""
    provider = get_llm_provider(provider_name="groq", api_key="gsk-testkey12345")
    assert isinstance(provider, GroqProvider)
    assert provider.provider_name == "groq"
    assert provider.default_model in ["openai/gpt-oss-20b", "openai/gpt-oss-120b"]


def test_factory_groq_selection_missing_key():
    """Groq selection fails fast with AgentConfigurationError when key is missing."""
    with patch("app.agents.providers.factory.settings.GROQ_API_KEY", None):
        with pytest.raises(AgentConfigurationError) as exc_info:
            get_llm_provider(provider_name="groq", api_key="")
        assert "GROQ_API_KEY is not configured" in str(exc_info.value)


def test_factory_gemini_selection_with_key():
    """Gemini selection succeeds when api_key is provided."""
    provider = get_llm_provider(provider_name="gemini", api_key="AIzaSyTest12345")
    assert isinstance(provider, GeminiProvider)
    assert provider.provider_name == "gemini"
    assert provider.default_model == "gemini-2.5-flash"


def test_factory_gemini_selection_missing_key():
    """Gemini selection fails fast with AgentConfigurationError when key is missing."""
    with patch("app.agents.providers.factory.settings.GEMINI_API_KEY", None):
        with pytest.raises(AgentConfigurationError) as exc_info:
            get_llm_provider(provider_name="gemini", api_key="")
        assert "GEMINI_API_KEY is not configured" in str(exc_info.value)


def test_factory_unsupported_provider_fails_fast():
    """Unsupported provider names must fail deterministically with no silent fallback."""
    for invalid in ["openai", "cerebras", "openrouter", "unknown_vendor", ""]:
        with pytest.raises(AgentConfigurationError) as exc_info:
            get_llm_provider(provider_name=invalid)
        assert "Unsupported LLM provider" in str(exc_info.value) or "Supported providers in Phase 10C" in str(exc_info.value)


# ==============================================================================
# 2. MockProvider Invariant Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_mock_provider_canned_text():
    """MockProvider returns registered text responses sequentially."""
    provider = MockLLMProvider()
    provider.register_response("Custom canned text")

    req = LLMRequest(
        messages=[LLMMessage(role="user", content="hello")],
        model="mock-model",
    )
    resp = await provider.generate(req)
    assert resp.content == "Custom canned text"
    assert resp.raw_metadata["mock"] is True


@pytest.mark.asyncio
async def test_mock_provider_canned_structured():
    """MockProvider returns registered structured models."""
    provider = MockLLMProvider()
    candidate = RequirementAnalysisCandidate(
        summary="Test mock summary",
        ambiguities=[],
        conflicts=[],
        missing_information=[],
        refinements=[],
        scope_clarifications=[],
    )
    provider.register_structured_response(candidate)

    req = LLMRequest(
        messages=[LLMMessage(role="user", content="analyze")],
        model="mock-model",
    )
    result = await provider.generate_structured(req, RequirementAnalysisCandidate)
    assert result.summary == "Test mock summary"
    assert result.ambiguities == []



@pytest.mark.asyncio
async def test_mock_provider_transient_failure_simulation():
    """MockProvider raises TransientProviderError for programmed count."""
    provider = MockLLMProvider()
    provider.simulate_transient_failures(1)

    req = LLMRequest(
        messages=[LLMMessage(role="user", content="hi")],
        model="mock-model",
    )
    with pytest.raises(TransientProviderError):
        await provider.generate(req)

    # Subsequent call succeeds after count exhausted
    resp = await provider.generate(req)
    assert resp.content == "Mock default generation response."


# ==============================================================================
# 3. GroqProvider Offline Unit Tests (Mocked SDK)
# ==============================================================================

@pytest.mark.asyncio
async def test_groq_provider_generate_success():
    """GroqProvider correctly unpacks SDK chat completion response."""
    provider = GroqProvider(api_key="gsk-dummysecretkey123")

    mock_choice = MagicMock()
    mock_choice.message.content = "Groq generated content."
    mock_usage = MagicMock(prompt_tokens=15, completion_tokens=25, total_tokens=40)
    mock_completion = MagicMock(choices=[mock_choice], usage=mock_usage, model="openai/gpt-oss-120b")

    with patch.object(provider._client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_completion

        req = LLMRequest(
            messages=[LLMMessage(role="user", content="Explain recursion")],
            model="openai/gpt-oss-120b",
        )
        resp = await provider.generate(req)

        assert resp.content == "Groq generated content."
        assert resp.raw_metadata["provider"] == "groq"
        assert resp.raw_metadata["model"] == "openai/gpt-oss-120b"
        assert resp.raw_metadata["total_tokens"] == 40
        # Secret key MUST NOT be present in raw_metadata
        assert "gsk-dummysecretkey123" not in str(resp.raw_metadata)


@pytest.mark.asyncio
async def test_groq_provider_structured_output_success():
    """GroqProvider enforces schema and validates into Pydantic model."""
    provider = GroqProvider(api_key="gsk-dummysecretkey123")

    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({"name": "TaskModule", "count": 7})
    mock_completion = MagicMock(choices=[mock_choice], usage=None, model="openai/gpt-oss-120b")

    with patch.object(provider._client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_completion

        req = LLMRequest(
            messages=[LLMMessage(role="user", content="Return schema")],
            model="openai/gpt-oss-120b",
        )
        result = await provider.generate_structured(req, SampleSchema)

        assert isinstance(result, SampleSchema)
        assert result.name == "TaskModule"
        assert result.count == 7


@pytest.mark.asyncio
async def test_groq_provider_structured_output_markdown_fence():
    """GroqProvider strips markdown code fences before Pydantic parsing."""
    provider = GroqProvider(api_key="gsk-dummysecretkey123")

    mock_choice = MagicMock()
    mock_choice.message.content = "```json\n{\"name\": \"FencedModule\", \"count\": 3}\n```"
    mock_completion = MagicMock(choices=[mock_choice], usage=None, model="openai/gpt-oss-120b")

    with patch.object(provider._client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_completion

        req = LLMRequest(
            messages=[LLMMessage(role="user", content="Return schema")],
            model="openai/gpt-oss-120b",
        )
        result = await provider.generate_structured(req, SampleSchema)
        assert result.name == "FencedModule"
        assert result.count == 3


@pytest.mark.asyncio
async def test_groq_provider_malformed_json_raises_provider_error():
    """Malformed non-JSON output from Groq raises non-transient ProviderError."""
    provider = GroqProvider(api_key="gsk-dummysecretkey123")

    mock_choice = MagicMock()
    mock_choice.message.content = "I am sorry, but I cannot return JSON."
    mock_completion = MagicMock(choices=[mock_choice], usage=None, model="openai/gpt-oss-120b")

    with patch.object(provider._client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_completion

        req = LLMRequest(messages=[LLMMessage(role="user", content="Return JSON")], model="openai/gpt-oss-120b")
        with pytest.raises(ProviderError) as exc_info:
            await provider.generate_structured(req, SampleSchema)
        assert "not valid JSON" in str(exc_info.value)
        assert exc_info.value.transient is False


@pytest.mark.asyncio
async def test_groq_provider_pydantic_validation_error():
    """JSON output missing required schema fields raises ProviderError."""
    provider = GroqProvider(api_key="gsk-dummysecretkey123")

    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({"wrong_key": "data"})
    mock_completion = MagicMock(choices=[mock_choice], usage=None, model="openai/gpt-oss-120b")

    with patch.object(provider._client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_completion

        req = LLMRequest(messages=[LLMMessage(role="user", content="Return JSON")], model="openai/gpt-oss-120b")
        with pytest.raises(ProviderError) as exc_info:
            await provider.generate_structured(req, SampleSchema)
        assert "failed Pydantic schema validation" in str(exc_info.value)
        assert exc_info.value.transient is False


@pytest.mark.asyncio
async def test_groq_provider_secret_redaction_in_exceptions():
    """Exceptions containing the secret key must have the secret redacted."""
    secret_key = "gsk-supersecret123456789"
    provider = GroqProvider(api_key=secret_key)

    class FakeAPIError(Exception):
        pass

    with patch.object(provider._client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = FakeAPIError(f"Unauthorized with key {secret_key} on endpoint")

        req = LLMRequest(messages=[LLMMessage(role="user", content="test")], model="openai/gpt-oss-120b")
        with pytest.raises(ProviderError) as exc_info:
            await provider.generate(req)

        # Secret MUST NOT appear in the exception message
        assert secret_key not in str(exc_info.value)
        assert "[REDACTED]" in str(exc_info.value)


# ==============================================================================
# 4. GeminiProvider Offline Unit Tests (Mocked HTTPX)
# ==============================================================================

@pytest.mark.asyncio
async def test_gemini_provider_generate_success():
    """GeminiProvider correctly parses Google Generative Language v1beta REST payload."""
    secret_key = "AIzaSyDummySecretKey123"
    provider = GeminiProvider(api_key=secret_key)

    fake_response_data = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Gemini generated text."}],
                    "role": "model",
                },
                "finishReason": "STOP",
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 10,
            "candidatesTokenCount": 20,
            "totalTokenCount": 30,
        },
    }

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = fake_response_data

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        req = LLMRequest(
            messages=[LLMMessage(role="user", content="Gemini ping")],
            model="gemini-2.5-flash",
        )
        resp = await provider.generate(req)

        assert resp.content == "Gemini generated text."
        assert resp.raw_metadata["provider"] == "gemini"
        assert resp.raw_metadata["model"] == "gemini-2.5-flash"
        assert resp.raw_metadata["total_tokens"] == 30
        assert secret_key not in str(resp.raw_metadata)


@pytest.mark.asyncio
async def test_gemini_provider_structured_output_success():
    """GeminiProvider parses structured JSON and validates into Pydantic model."""
    provider = GeminiProvider(api_key="AIzaSyDummySecretKey123")

    fake_response_data = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": json.dumps({"name": "GeminiModule", "count": 12})}],
                    "role": "model",
                }
            }
        ],
        "usageMetadata": {},
    }

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = fake_response_data

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        req = LLMRequest(
            messages=[LLMMessage(role="user", content="Return structured")],
            model="gemini-2.5-flash",
        )
        result = await provider.generate_structured(req, SampleSchema)
        assert isinstance(result, SampleSchema)
        assert result.name == "GeminiModule"
        assert result.count == 12


@pytest.mark.asyncio
async def test_gemini_provider_rate_limit_transient():
    """HTTP 429 from Gemini maps to TransientProviderError for controlled retry."""
    provider = GeminiProvider(api_key="AIzaSyDummySecretKey123")

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 429
    mock_resp.text = "RESOURCE_EXHAUSTED: Rate limit exceeded"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        req = LLMRequest(messages=[LLMMessage(role="user", content="test")], model="gemini-2.5-flash")
        with pytest.raises(TransientProviderError) as exc_info:
            await provider.generate(req)
        assert "429" in str(exc_info.value)
        assert exc_info.value.transient is True


@pytest.mark.asyncio
async def test_gemini_provider_server_error_transient():
    """HTTP 503 from Gemini maps to TransientProviderError."""
    provider = GeminiProvider(api_key="AIzaSyDummySecretKey123")

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 503
    mock_resp.text = "Service Unavailable"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        req = LLMRequest(messages=[LLMMessage(role="user", content="test")], model="gemini-2.5-flash")
        with pytest.raises(TransientProviderError) as exc_info:
            await provider.generate(req)
        assert "503" in str(exc_info.value)
        assert exc_info.value.transient is True


@pytest.mark.asyncio
async def test_gemini_provider_timeout_transient():
    """httpx.TimeoutException maps to TransientProviderError."""
    provider = GeminiProvider(api_key="AIzaSyDummySecretKey123")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ReadTimeout("Connection timed out after 30.0s")

        req = LLMRequest(messages=[LLMMessage(role="user", content="test")], model="gemini-2.5-flash")
        with pytest.raises(TransientProviderError) as exc_info:
            await provider.generate(req)
        assert "timed out" in str(exc_info.value)
        assert exc_info.value.transient is True


@pytest.mark.asyncio
async def test_gemini_provider_secret_redaction_on_error():
    """Non-200 responses redacts api key from error messages."""
    secret_key = "AIzaSyPrivateSecretKey999"
    provider = GeminiProvider(api_key=secret_key)

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 400
    mock_resp.text = f"Invalid API key: {secret_key} provided."

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        req = LLMRequest(messages=[LLMMessage(role="user", content="test")], model="gemini-2.5-flash")
        with pytest.raises(ProviderError) as exc_info:
            await provider.generate(req)
        assert secret_key not in str(exc_info.value)
        assert "[REDACTED]" in str(exc_info.value)
