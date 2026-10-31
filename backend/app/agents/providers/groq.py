"""Production-Quality Groq LLM Provider Implementation."""

import json
import logging
import re
from typing import Any, AsyncGenerator, TypeVar
from pydantic import BaseModel, ValidationError

from app.agents.exceptions import ProviderError, TransientProviderError
from app.agents.providers.base import (
    AbstractLLMProvider,
    LLMRequest,
    LLMResponse,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class GroqProvider(AbstractLLMProvider):
    """Production adapter for Groq Cloud fast inference engine.
    
    Adheres strictly to the vendor-neutral AbstractLLMProvider abstraction.
    Does not expose Groq SDK internals or raw credentials to agents.
    """

    def __init__(
        self,
        api_key: str,
        default_model: str = "openai/gpt-oss-20b",
        timeout: float = 30.0,
    ) -> None:
        if not api_key:
            raise ValueError("Groq API key must be provided.")
        self.api_key = api_key
        self._default_model = default_model
        self.timeout = timeout
        self.last_usage_metadata: dict[str, Any] | None = None
        
        # Lazy client initialization with zero internal blocking retries
        from groq import AsyncGroq
        self._client = AsyncGroq(api_key=api_key, timeout=timeout, max_retries=0)

    @property
    def provider_name(self) -> str:
        return "groq"

    @property
    def default_model(self) -> str:
        return self._default_model


    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Execute a text completion request using Groq inference."""
        model = request.model or self.default_model
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        try:
            response = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

            choice = response.choices[0]
            content = choice.message.content or ""
            usage = response.usage

            raw_metadata = {
                "provider": self.provider_name,
                "model": response.model or model,
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            }
            self.last_usage_metadata = raw_metadata

            return LLMResponse(content=content, raw_metadata=raw_metadata)

        except Exception as exc:
            self._handle_groq_exception(exc)

    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Execute a text completion stream using Groq inference."""
        model = request.model or self.default_model
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        try:
            stream = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as exc:
            self._handle_groq_exception(exc)

    async def generate_structured(
        self,
        request: LLMRequest,
        response_model: type[T],
    ) -> T:
        """Execute a structured completion request validated against a Pydantic schema."""
        model = request.model or self.default_model
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        # Ensure schema enforcement instructions exist in messages
        schema_json = json.dumps(response_model.model_json_schema(), separators=(",", ":"))
        schema_instruction = (
            f"\n\nCRITICAL INSTRUCTION: You must respond ONLY with a valid JSON object matching "
            f"the following JSON Schema:\n{schema_json}\nDo not include any Markdown formatting, "
            f"codeblocks, or preamble. Return raw JSON only."
        )

        # Append schema instruction to the system message or first user message
        if messages and messages[0]["role"] == "system":
            messages[0]["content"] += schema_instruction
        else:
            messages.insert(0, {"role": "system", "content": f"You are a structured output assistant.{schema_instruction}"})

        try:
            response = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens or 3500,
                response_format={"type": "json_object"},
            )

            raw_text = response.choices[0].message.content or ""
            usage = response.usage
            self.last_usage_metadata = {
                "provider": self.provider_name,
                "model": response.model or model,
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            }
            return self._parse_and_validate(raw_text, response_model)

        except Exception as exc:
            # Check if Groq returned a json_validate_failed error containing 'failed_generation'
            failed_gen = None
            if hasattr(exc, "body") and isinstance(exc.body, dict):
                error_obj = exc.body.get("error", {})
                if isinstance(error_obj, dict):
                    failed_gen = error_obj.get("failed_generation")
            elif hasattr(exc, "response") and hasattr(exc.response, "json"):
                try:
                    err_json = exc.response.json()
                    failed_gen = err_json.get("error", {}).get("failed_generation")
                except Exception:
                    pass

            if failed_gen and isinstance(failed_gen, str):
                try:
                    return self._parse_and_validate(failed_gen, response_model)
                except Exception:
                    pass

            # Fallback for json_validate_failed or tool_use_failed: try non-json_object mode chat completion
            err_str = str(exc).lower()
            if "json_validate_failed" in err_str or "tool_use_failed" in err_str:
                try:
                    fallback_msgs = list(messages)
                    fallback_msgs.append({
                        "role": "system",
                        "content": "IMPORTANT: Do NOT invoke any tools or call functions. Respond ONLY with a valid JSON object matching the required schema.",
                    })
                    fallback_response = await self._client.chat.completions.create(
                        model=model,
                        messages=fallback_msgs,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens or 1500,
                    )
                    fallback_text = fallback_response.choices[0].message.content or ""
                    return self._parse_and_validate(fallback_text, response_model)
                except Exception:
                    pass

            self._handle_groq_exception(exc, response_model_name=response_model.__name__)

    def _parse_and_validate(self, text: str, response_model: type[T]) -> T:
        """Clean markdown wrapping and validate parsed JSON into Pydantic model."""
        clean_text = text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        parsed_data = None
        try:
            parsed_data = json.loads(clean_text)
        except json.JSONDecodeError:
            # Fallback: extract the outermost JSON object if preamble/postamble exists
            match = re.search(r"(\{[\s\S]*\})", text)
            if match:
                try:
                    parsed_data = json.loads(match.group(1))
                except json.JSONDecodeError as jde:
                    raise ProviderError(
                        message=f"Groq output was not valid JSON: {jde}. Raw output prefix: {clean_text[:200]}",
                        provider_name=self.provider_name,
                        transient=False,
                    ) from jde
            else:
                raise ProviderError(
                    message=f"Groq output was not valid JSON and no JSON object was found. Raw output prefix: {clean_text[:200]}",
                    provider_name=self.provider_name,
                    transient=False,
                )

        try:
            return response_model.model_validate(parsed_data)
        except ValidationError as ve:
            raise ProviderError(
                message=f"Groq structured output failed Pydantic schema validation for {response_model.__name__}: {ve}",
                provider_name=self.provider_name,
                transient=False,
            ) from ve

    def _handle_groq_exception(self, exc: Exception, response_model_name: str | None = None) -> None:
        """Map Groq SDK exceptions to platform exception hierarchy."""
        if isinstance(exc, (ProviderError, TransientProviderError)):
            raise exc

        exc_name = type(exc).__name__
        msg = str(exc)

        # Sanitize message to ensure no authorization or key information leaks
        sanitized_msg = msg.replace(self.api_key, "[REDACTED]")

        # Rate limits, timeouts, and network connection drops are transient
        is_rate_limit = (
            exc_name in ("RateLimitError", "APIConnectionError", "APITimeoutError")
            or "rate limit" in msg.lower()
            or "rate_limit" in msg.lower()
            or "too many requests" in msg.lower()
            or getattr(exc, "status_code", None) in (429, 503)
        )
        if is_rate_limit:
            retry_after: float | None = None
            if hasattr(exc, "response") and hasattr(getattr(exc, "response"), "headers"):
                retry_header = getattr(exc.response, "headers", {}).get("retry-after")
                if retry_header:
                    try:
                        retry_after = float(retry_header)
                    except ValueError:
                        pass
            if retry_after is None:
                m = re.search(r"try again in ([\d.]+)s", msg, re.IGNORECASE)
                if m:
                    try:
                        retry_after = float(m.group(1))
                    except ValueError:
                        pass

            retry_msg = f"Groq API rate limit or transient error ({exc_name}): {sanitized_msg}."
            if retry_after is not None:
                retry_msg += f" Retry guidance: please wait {retry_after:.1f}s before retrying."

            logger.warning(f"Groq transient failure: {exc_name} - {sanitized_msg} (retry_after={retry_after}s)")
            extra_payload = {
                "retry_after": retry_after,
                "is_rate_limit": True,
                "tier_boundary": "8,000 TPM",
            }
            raise TransientProviderError(
                message=retry_msg,
                provider_name=self.provider_name,
                extra=extra_payload,
            ) from exc

        # Authentication, model not found, invalid request are non-transient
        logger.error(f"Groq non-transient failure: {exc_name} - {sanitized_msg}")
        raise ProviderError(
            message=f"Groq provider error ({exc_name}): {sanitized_msg}",
            provider_name=self.provider_name,
            transient=False,
        ) from exc

    async def check_health(self) -> dict[str, Any]:
        """Perform a lightweight provider health check."""
        try:
            response = await self._client.chat.completions.create(
                model=self.default_model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return {
                "provider": self.provider_name,
                "status": "healthy",
                "model": self.default_model,
                "reachable": True,
            }
        except Exception as e:
            return {
                "provider": self.provider_name,
                "status": "unhealthy",
                "error": type(e).__name__,
                "reachable": False,
            }
