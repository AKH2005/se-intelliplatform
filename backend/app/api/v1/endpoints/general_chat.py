"""Global AI Assistant & Conversational Guidance API Endpoints."""

import json
import logging
import re
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from app.agents.exceptions import ProviderError, TransientProviderError
from app.agents.providers.base import LLMMessage, LLMRequest
from app.agents.providers.factory import get_llm_provider
from app.api.dependencies import get_current_user_optional
from app.models.user import User
from app.schemas.general_chat import (
    AppRequirementItem,
    GeneralChatRequest,
    GeneralChatResponse,
    GuidedAppPlanRequest,
    GuidedAppPlanResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

GLOBAL_ASSISTANT_SYSTEM_PROMPT = """You are the Global AI Assistant for SE IntelliPlatform, an autonomous software engineering platform.

Your primary responsibilities:
1. Provide helpful, conversational, and accurate answers to general software engineering questions, programming concepts, architecture patterns, debugging challenges, and computer science topics.
2. Guide users on how to use SE IntelliPlatform effectively:
   - User Mode: A welcoming, conversational environment for beginners and creators to explore ideas, learn concepts, discover platform tools, and create applications through guided steps.
   - Developer Mode: A professional development environment with Code Studio (Monaco multi-file editor), IntelliAssist (project-aware code generation and diff review), isolated Docker previews (port 8001), and testing intelligence.
   - Header Mode Switcher: Users can toggle between User Mode and Developer Mode at any time without losing active projects or login sessions.
   - Code Studio: Inspect and edit source files directly with syntax validation and diff viewing.
   - Live Preview: Real application running in an isolated Docker sandbox on port 8001 with restart controls.
   - IntelliAssist: Project-aware developer in Developer Mode that evaluates the active project, proposes multi-file diffs, and modifies code with developer confirmation.
3. Be conversational, clear, approachable, and professional. Use markdown formatting with code blocks, bullet points, and headers where helpful.
"""

GUIDED_PLAN_SYSTEM_PROMPT = """You are an expert software architect and requirements engineer.
Given a user's description of an application they want to build, synthesize a structured project blueprint.

Return ONLY a valid JSON object matching this schema:
{
  "name": "Concise Application Name",
  "slug": "url-friendly-slug",
  "description": "2-3 sentences summarizing the application purpose and value.",
  "requirements": [
    {
      "title": "Requirement title",
      "description": "Specific requirement detail",
      "type": "FUNCTIONAL",
      "priority": "HIGH"
    }
  ],
  "suggested_features": ["Feature 1", "Feature 2", "Feature 3"]
}

Rules:
- Generate 3 to 6 high-value requirements (mix of FUNCTIONAL and NON_FUNCTIONAL).
- Ensure valid JSON with no markdown wrapping or backticks.
"""


def _slugify(text: str) -> str:
    """Generate a clean URL slug from text."""
    clean = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[-\s]+", "-", clean)[:40] or "new-app"


@router.post(
    "",
    response_model=GeneralChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with the Global AI Assistant",
    description="Conversational endpoint for general questions, learning, and platform guidance.",
)
async def chat_with_assistant(
    request: GeneralChatRequest,
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> GeneralChatResponse:
    """Process a conversational turn with the Global AI Assistant."""
    try:
        provider = get_llm_provider()
    except Exception as exc:
        logger.error(f"Failed to initialize LLM provider: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Assistant service is currently configuring or unavailable.",
        ) from exc

    # Assemble conversation context
    messages: list[LLMMessage] = [
        LLMMessage(role="system", content=GLOBAL_ASSISTANT_SYSTEM_PROMPT)
    ]

    # Include recent conversation turns (up to 8 messages to stay within budget)
    if request.conversation_history:
        for item in request.conversation_history[-8:]:
            if item.content.strip():
                messages.append(LLMMessage(role=item.role, content=item.content.strip()))

    # Append the user's latest query
    messages.append(LLMMessage(role="user", content=request.message.strip()))

    llm_req = LLMRequest(
        messages=messages,
        model=provider.default_model,
        temperature=0.7,
        metadata={"user_id": str(current_user.id) if current_user else None},
    )

    try:
        res = await provider.generate(llm_req)
        return GeneralChatResponse(
            response=res.content,
            provider=provider.provider_name,
            model=provider.default_model,
        )
    except (ProviderError, TransientProviderError) as p_err:
        logger.warning(f"LLM Provider error during chat: {p_err}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI service provider encountered an issue: {str(p_err)}",
        ) from p_err
    except Exception as exc:
        logger.error(f"Unexpected error in general chat: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the assistant response.",
        ) from exc


@router.post(
    "/guided-app-plan",
    response_model=GuidedAppPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Synthesize guided application blueprint from prompt",
    description="Analyzes an idea prompt and produces structured requirements and naming.",
)
async def create_guided_app_plan(
    request: GuidedAppPlanRequest,
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> GuidedAppPlanResponse:
    """Synthesize a structured application blueprint from natural language."""
    try:
        provider = get_llm_provider()
    except Exception as exc:
        logger.error(f"Failed to initialize LLM provider: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI Assistant service is currently configuring or unavailable: {exc}",
        ) from exc

    llm_req = LLMRequest(
        messages=[
            LLMMessage(role="system", content=GUIDED_PLAN_SYSTEM_PROMPT),
            LLMMessage(
                role="user",
                content=f"Synthesize an application blueprint for: {request.prompt.strip()}",
            ),
        ],
        model=provider.default_model,
        temperature=0.3,
    )

    import asyncio
    try:
        # Enforce 28s provider timeout so backend always responds before client's 45s timeout
        res = await asyncio.wait_for(provider.generate(llm_req), timeout=28.0)
    except asyncio.TimeoutError as t_err:
        logger.warning(f"AI planning request timed out waiting for provider {provider.provider_name}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI planning request timed out waiting for AI provider response. Please try again.",
        ) from t_err
    except (TransientProviderError,) as tp_err:
        logger.warning(f"LLM Transient error during guided-app-plan: {tp_err}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service provider is temporarily busy or rate-limited: {str(tp_err)}. Please wait a moment and try again.",
        ) from tp_err
    except (ProviderError,) as p_err:
        logger.error(f"LLM Provider error during guided-app-plan: {p_err}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI service provider encountered an issue: {str(p_err)}",
        ) from p_err
    except Exception as exc:
        logger.error(f"Unexpected error in guided app plan generation: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating application blueprint: {str(exc)}",
        ) from exc

    raw_text = res.content.strip()

    # Clean any potential markdown code fence markers
    if raw_text.startswith("```"):
        raw_text = re.sub(r"^```[a-zA-Z]*\n?", "", raw_text)
        raw_text = re.sub(r"\n?```$", "", raw_text).strip()

    # Try extracting JSON object if surrounded by preamble/postamble
    match = re.search(r"(\{[\s\S]*\})", raw_text)
    if match:
        raw_json = match.group(1)
    else:
        raw_json = raw_text

    try:
        parsed = json.loads(raw_json)
        reqs = [
            AppRequirementItem(
                title=r.get("title", "Core Feature"),
                description=r.get("description", ""),
                type=r.get("type", "FUNCTIONAL"),
                priority=r.get("priority", "HIGH"),
            )
            for r in parsed.get("requirements", [])
        ]

        name = parsed.get("name", "New Application")
        slug = parsed.get("slug") or _slugify(name)
        description = parsed.get("description", request.prompt.strip())
        features = parsed.get("suggested_features", [])

        return GuidedAppPlanResponse(
            name=name,
            slug=slug,
            description=description,
            requirements=reqs,
            suggested_features=features,
        )
    except Exception as parse_exc:
        logger.info(f"Model output was not valid JSON ({parse_exc}), synthesizing blueprint directly from prompt")
        # Synthesize directly from the user's prompt text (never hijacking into an unrelated template)
        words = request.prompt.strip().split()
        title_words = words[:4]
        name = " ".join(title_words).title() or "Custom Application"
        slug = _slugify(name)

        return GuidedAppPlanResponse(
            name=name,
            slug=slug,
            description=request.prompt.strip(),
            requirements=[
                AppRequirementItem(
                    title="User Interface & Interactive Navigation",
                    description=f"Modern, responsive interface tailored for {name}.",
                    type="FUNCTIONAL",
                    priority="HIGH",
                ),
                AppRequirementItem(
                    title="Data Management & Core Operations",
                    description=f"Standardized state management and persistent data handling for {name}.",
                    type="FUNCTIONAL",
                    priority="HIGH",
                ),
                AppRequirementItem(
                    title="Real-Time Verification & Preview",
                    description="Continuous feedback and live runtime integration on SE IntelliPlatform.",
                    type="NON_FUNCTIONAL",
                    priority="HIGH",
                ),
            ],
            suggested_features=["Interactive Dashboard", "Search & Filtering", "Audit & Reporting"],
        )
