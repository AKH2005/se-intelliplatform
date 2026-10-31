"""Deterministic Mock LLM Provider for Isolated Testing."""

import json
from typing import Any, AsyncGenerator, TypeVar
from pydantic import BaseModel

from app.agents.exceptions import ProviderError, TransientProviderError
from app.agents.providers.base import (
    AbstractLLMProvider,
    LLMRequest,
    LLMResponse,
)

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(AbstractLLMProvider):
    """Deterministic, zero-cost LLM provider implementation for local tests.
    
    Permits registering canned structured models, arbitrary text responses, or
    programmable failure modes without external network calls or secrets.
    """

    def __init__(self) -> None:
        self._canned_responses: list[str] = []
        self._canned_structured: list[BaseModel] = []
        self.call_history: list[LLMRequest] = []
        self.transient_error_counter: int = 0
        self.permanent_error: Exception | None = None

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def default_model(self) -> str:
        return getattr(self, "_default_model", "mock-model")

    @property
    def last_usage_metadata(self) -> dict[str, Any] | None:
        return {
            "provider": self.provider_name,
            "model": "mock-model",
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
        }


    def register_response(self, text: str) -> None:
        """Queue a string response to be returned on subsequent generate calls."""
        self._canned_responses.append(text)

    def register_structured_response(self, model: BaseModel) -> None:
        """Queue a Pydantic model response for generate_structured calls."""
        self._canned_structured.append(model)

    def simulate_transient_failures(self, count: int) -> None:
        """Instruct provider to raise TransientProviderError for the next N calls."""
        self.transient_error_counter = count

    def simulate_permanent_failure(self, exc: Exception | None) -> None:
        """Instruct provider to continuously raise the provided exception."""
        self.permanent_error = exc

    def reset(self) -> None:
        """Clear queued responses, errors, and invocation history."""
        self._canned_responses.clear()
        self._canned_structured.clear()
        self.call_history.clear()
        self.transient_error_counter = 0
        self.permanent_error = None

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Return queued text or raise programmed failure."""
        self.call_history.append(request)

        if self.permanent_error:
            raise self.permanent_error

        if self.transient_error_counter > 0:
            self.transient_error_counter -= 1
            raise TransientProviderError(
                message="Mock transient rate limit or network error.",
                provider_name=self.provider_name,
            )

        if self._canned_responses:
            content = self._canned_responses.pop(0)
        else:
            content = "Mock default generation response."

        return LLMResponse(
            content=content,
            raw_metadata={"mock": True, "model": request.model, "tokens": 42},
        )

    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream chunks by simulating progressive token generation for tests."""
        response = await self.generate(request)
        words = response.content.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")

    async def generate_structured(
        self,
        request: LLMRequest,
        response_model: type[T],
    ) -> T:
        """Return queued Pydantic model or construct model from queued text/defaults."""
        self.call_history.append(request)

        if self.permanent_error:
            raise self.permanent_error

        if self.transient_error_counter > 0:
            self.transient_error_counter -= 1
            raise TransientProviderError(
                message="Mock transient rate limit during structured generation.",
                provider_name=self.provider_name,
            )

        if self._canned_structured:
            for idx, candidate in enumerate(self._canned_structured):
                if isinstance(candidate, response_model):
                    return self._canned_structured.pop(idx)

            model_inst = self._canned_structured.pop(0)
            if isinstance(model_inst, response_model):
                return model_inst
            # If dictionary or mismatch, try to validate into expected model
            if isinstance(model_inst, BaseModel):
                return response_model.model_validate(model_inst.model_dump())


        if self._canned_responses:
            raw_json = self._canned_responses.pop(0)
            try:
                parsed = json.loads(raw_json)
                return response_model.model_validate(parsed)
            except Exception as exc:
                raise ProviderError(
                    message=f"Mock response could not be parsed into {response_model.__name__}: {exc}",
                    provider_name=self.provider_name,
                ) from exc

        # Fallback: attempt to instantiate response_model with defaults if possible
        try:
            return response_model()
        except Exception as exc:
            if response_model.__name__ == "AssistantResponseSchema":
                return response_model(  # type: ignore
                    message="Mock assistant response based on verified project context.",
                    suggested_action=None,
                )
            raise ProviderError(
                message=f"No mock response configured for structured model {response_model.__name__}.",
                provider_name=self.provider_name,
            ) from exc

