"""Authoritative LLM Provider Factory and Lifecycle Resolver."""

import logging
from app.agents.exceptions import AgentConfigurationError
from app.agents.providers.base import AbstractLLMProvider
from app.agents.providers.mock import MockLLMProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_llm_provider(
    provider_name: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    timeout: float | None = None,
) -> AbstractLLMProvider:
    """Resolve and instantiate the configured AbstractLLMProvider instance.
    
    Invariants:
    - Strictly adheres to configured provider name without silent fallback.
    - If 'groq' is chosen, verifies GROQ_API_KEY is configured.
    - If 'gemini' is chosen, verifies GEMINI_API_KEY is configured.
    - If 'mock' is chosen, returns deterministic mock provider.
    - Any unrecognized provider name raises an explicit AgentConfigurationError.
    """
    if provider_name is not None:
        resolved_provider = provider_name.strip().lower()
    else:
        resolved_provider = (settings.LLM_PROVIDER or "mock").strip().lower()
    req_timeout = timeout or settings.LLM_TIMEOUT

    if resolved_provider == "mock":
        return MockLLMProvider()

    if resolved_provider == "groq":
        resolved_key = api_key or settings.GROQ_API_KEY
        if not resolved_key:
            raise AgentConfigurationError(
                "Groq provider selected (LLM_PROVIDER=groq), but GROQ_API_KEY is not configured."
            )
        from app.agents.providers.groq import GroqProvider
        resolved_model = model or settings.LLM_MODEL_GROQ
        return GroqProvider(
            api_key=resolved_key,
            default_model=resolved_model,
            timeout=req_timeout,
        )

    if resolved_provider == "gemini":
        resolved_key = api_key or settings.GEMINI_API_KEY
        if not resolved_key:
            raise AgentConfigurationError(
                "Gemini provider selected (LLM_PROVIDER=gemini), but GEMINI_API_KEY is not configured."
            )
        from app.agents.providers.gemini import GeminiProvider
        resolved_model = model or settings.LLM_MODEL_GEMINI
        return GeminiProvider(
            api_key=resolved_key,
            default_model=resolved_model,
            timeout=req_timeout,
        )

    # Unknown or unsupported provider - fail fast, NO silent fallback
    raise AgentConfigurationError(
        f"Unsupported LLM provider: '{resolved_provider}'. "
        f"Supported providers in Phase 10C are: 'mock', 'groq', 'gemini'."
    )
