"""Schemas for General AI Chat and Guided App Planning."""

from typing import Any, Literal
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Conversational turn message."""

    role: Literal["system", "user", "assistant"] = Field(..., description="Message author role")
    content: str = Field(..., min_length=1, description="Text content of the message")


class GeneralChatRequest(BaseModel):
    """Request payload for the Global AI Assistant."""

    message: str = Field(..., min_length=1, description="User prompt or question")
    conversation_history: list[ChatMessage] = Field(
        default_factory=list,
        description="Prior conversation history turns",
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional client state metadata (active mode, selected project, etc.)",
    )


class GeneralChatResponse(BaseModel):
    """Response returned by the Global AI Assistant."""

    response: str = Field(..., description="AI response text in markdown format")
    provider: str = Field(..., description="Underlying LLM provider used")
    model: str = Field(..., description="Model identifier used for generation")


class AppRequirementItem(BaseModel):
    """Synthesized requirement item for guided project creation."""

    title: str = Field(..., description="Short requirement title")
    description: str = Field(..., description="Detailed description")
    type: Literal["FUNCTIONAL", "NON_FUNCTIONAL"] = Field(default="FUNCTIONAL")
    priority: Literal["HIGH", "MEDIUM", "LOW"] = Field(default="HIGH")


class GuidedAppPlanRequest(BaseModel):
    """Request payload for synthesizing application blueprint."""

    prompt: str = Field(..., min_length=3, description="User's natural language project description")


class GuidedAppPlanResponse(BaseModel):
    """Synthesized blueprint for a new application."""

    name: str = Field(..., description="Proposed application name")
    slug: str = Field(..., description="URL-friendly slug")
    description: str = Field(..., description="Refined project description")
    requirements: list[AppRequirementItem] = Field(default_factory=list)
    suggested_features: list[str] = Field(default_factory=list)
