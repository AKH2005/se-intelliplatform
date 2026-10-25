"""Production-Quality Google Gemini LLM Provider Implementation."""

import json
import logging
from typing import Any, TypeVar
import httpx
from pydantic import BaseModel, ValidationError

from app.agents.exceptions import ProviderError, TransientProviderError
from app.agents.providers.base import (
    AbstractLLMProvider,
    LLMRequest,
    LLMResponse,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

BASE_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(AbstractLLMProvider):
    """Production adapter for Google Gemini multimodal foundation models.
    
    Adheres strictly to the vendor-neutral AbstractLLMProvider abstraction.
    Does not expose Google API internals or raw credentials to agents.
    Uses robust async HTTP transport with strict credential isolation and error normalization.
    """

    def __init__(
        self,
        api_key: str,
        default_model: str = "gemini-2.5-flash",
        timeout: float = 30.0,
    ) -> None:
        if not api_key:
            raise ValueError("Gemini API key must be provided.")
        self.api_key = api_key
        self._default_model = default_model
        self.timeout = timeout
        self.last_usage_metadata: dict[str, Any] | None = None

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def default_model(self) -> str:
        return self._default_model


    def _get_headers(self) -> dict[str, str]:
        """Headers for Google Generative Language API with credential isolation."""
        return {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

    def _format_gemini_payload(self, request: LLMRequest, force_json: bool = False) -> dict[str, Any]:
        """Convert vendor-neutral LLMRequest to Gemini REST format."""
        system_parts = []
        contents = []

        for msg in request.messages:
            if msg.role == "system":
                system_parts.append({"text": msg.content})
            elif msg.role == "assistant":
                contents.append({"role": "model", "parts": [{"text": msg.content}]})
            else:
                contents.append({"role": "user", "parts": [{"text": msg.content}]})

        # Ensure at least one user content exists
        if not contents:
            contents.append({"role": "user", "parts": [{"text": "Hello"}]})

        generation_config: dict[str, Any] = {
            "temperature": request.temperature,
        }
        if request.max_tokens:
            generation_config["maxOutputTokens"] = request.max_tokens
        if force_json:
            generation_config["responseMimeType"] = "application/json"

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": generation_config,
        }

        if system_parts:
            payload["systemInstruction"] = {"parts": system_parts}

        return payload

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Execute a text completion request using Google Gemini."""
        model = request.model or self.default_model
        url = f"{BASE_GEMINI_URL}/{model}:generateContent"
        payload = self._format_gemini_payload(request, force_json=False)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=self._get_headers(), json=payload)
                return self._handle_gemini_response(response, model)
        except Exception as exc:
            self._handle_gemini_exception(exc)

    async def generate_structured(
        self,
        request: LLMRequest,
        response_model: type[T],
    ) -> T:
        """Execute a structured completion request validated against a Pydantic schema."""
        model = request.model or self.default_model
        url = f"{BASE_GEMINI_URL}/{model}:generateContent"

        # Schema instruction to guarantee format fidelity
        schema_json = json.dumps(response_model.model_json_schema(), indent=2)
        schema_instruction = (
            f"\n\nCRITICAL INSTRUCTION: You must respond ONLY with a valid JSON object matching "
            f"the following JSON Schema:\n{schema_json}\nDo not include any Markdown formatting, "
            f"codeblocks, or preamble. Return raw JSON only."
        )

        modified_messages = [msg.model_copy() for msg in request.messages]
        # Append to existing system prompt or prepend new system message
        system_found = False
        for msg in modified_messages:
            if msg.role == "system":
                msg.content += schema_instruction
                system_found = True
                break
        if not system_found:
            from app.agents.providers.base import LLMMessage
            modified_messages.insert(0, LLMMessage(role="system", content=f"You are a structured output assistant.{schema_instruction}"))

        modified_request = request.model_copy(update={"messages": modified_messages})
        payload = self._format_gemini_payload(modified_request, force_json=True)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=self._get_headers(), json=payload)
                llm_response = self._handle_gemini_response(response, model)
                return self._parse_and_validate(llm_response.content, response_model)
        except Exception as exc:
            self._handle_gemini_exception(exc, response_model_name=response_model.__name__)

    def _handle_gemini_response(self, response: httpx.Response, model: str) -> LLMResponse:
        """Process HTTP response and normalize non-200 status codes."""
        if response.status_code == 429:
            raise TransientProviderError(
                message="Gemini rate limit exceeded (HTTP 429).",
                provider_name=self.provider_name,
            )
        if response.status_code in (500, 502, 503, 504):
            raise TransientProviderError(
                message=f"Gemini server error (HTTP {response.status_code}). Eligible for retry.",
                provider_name=self.provider_name,
            )
        if response.status_code != 200:
            clean_error = response.text.replace(self.api_key, "[REDACTED]")
            raise ProviderError(
                message=f"Gemini API returned error (HTTP {response.status_code}): {clean_error}",
                provider_name=self.provider_name,
                transient=False,
            )

        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise ProviderError(
                message="Gemini returned an empty candidates array in response.",
                provider_name=self.provider_name,
                transient=False,
            )

        first_candidate = candidates[0]
        content_obj = first_candidate.get("content", {})
        parts = content_obj.get("parts", [])
        if not parts:
            raise ProviderError(
                message="Gemini returned no content parts in first candidate.",
                provider_name=self.provider_name,
                transient=False,
            )

        text_content = parts[0].get("text", "")
        usage_metadata = data.get("usageMetadata", {})

        raw_metadata = {
            "provider": self.provider_name,
            "model": model,
            "prompt_tokens": usage_metadata.get("promptTokenCount"),
            "completion_tokens": usage_metadata.get("candidatesTokenCount"),
            "total_tokens": usage_metadata.get("totalTokenCount"),
        }
        self.last_usage_metadata = raw_metadata

        return LLMResponse(
            content=text_content,
            raw_metadata=raw_metadata,
        )

    def _parse_and_validate(self, text: str, response_model: type[T]) -> T:
        """Strip markdown syntax fences and validate against Pydantic schema."""
        clean_text = text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        try:
            parsed_data = json.loads(clean_text)
        except json.JSONDecodeError as jde:
            raise ProviderError(
                message=f"Gemini output was not valid JSON: {jde}. Output prefix: {clean_text[:200]}",
                provider_name=self.provider_name,
                transient=False,
            ) from jde

        try:
            return response_model.model_validate(parsed_data)
        except ValidationError as ve:
            raise ProviderError(
                message=f"Gemini structured output failed Pydantic schema validation for {response_model.__name__}: {ve}",
                provider_name=self.provider_name,
                transient=False,
            ) from ve

    def _handle_gemini_exception(self, exc: Exception, response_model_name: str | None = None) -> None:
        """Map network/HTTP exceptions to platform hierarchy with credential redaction."""
        if isinstance(exc, (ProviderError, TransientProviderError)):
            raise exc

        exc_name = type(exc).__name__
        clean_msg = str(exc).replace(self.api_key, "[REDACTED]")

        if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError)):
            logger.warning(f"Gemini transient network error: {exc_name} - {clean_msg}")
            raise TransientProviderError(
                message=f"Gemini transient network error ({exc_name}): {clean_msg}",
                provider_name=self.provider_name,
            ) from exc

        logger.error(f"Gemini non-transient error: {exc_name} - {clean_msg}")
        raise ProviderError(
            message=f"Gemini provider error ({exc_name}): {clean_msg}",
            provider_name=self.provider_name,
            transient=False,
        ) from exc

    async def check_health(self) -> dict[str, Any]:
        """Perform a lightweight provider health check."""
        url = f"{BASE_GEMINI_URL}/{self.default_model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": "ping"}]}],
            "generationConfig": {"maxOutputTokens": 5},
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=self._get_headers(), json=payload)
                if resp.status_code == 200:
                    return {
                        "provider": self.provider_name,
                        "status": "healthy",
                        "model": self.default_model,
                        "reachable": True,
                    }
                return {
                    "provider": self.provider_name,
                    "status": "unhealthy",
                    "code": resp.status_code,
                    "reachable": False,
                }
        except Exception as e:
            return {
                "provider": self.provider_name,
                "status": "unreachable",
                "error": type(e).__name__,
                "reachable": False,
            }
