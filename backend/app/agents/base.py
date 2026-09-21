"""Abstract Base Agent Defining Identity, Contracts, and Execution Hooks."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar
from pydantic import BaseModel

from app.agents.contracts import (
    AgentMetadata,
    AgentResult,
    ValidationResult,
)
from app.agents.providers.base import AbstractLLMProvider
from app.schemas.context import ProjectContextResponse

logger = logging.getLogger(__name__)

OutputT = TypeVar("OutputT", bound=BaseModel)


class AbstractBaseAgent(ABC, Generic[OutputT]):
    """Platform-level abstract base for all software engineering intelligence agents.
    
    All future SDLC intelligence agents (Requirement Analysis, Architecture,
    Code Review, Testing, etc.) inherit from this contract, consuming the canonical
    Project Context and emitting validated, structured domain results.
    
    Architectural Authority Invariant:
    `AbstractBaseAgent` owns ONLY agent-specific domain behavior hooks:
      - `initialize`: Pre-execution setup
      - `analyze`: Context feature extraction
      - `generate`: Structured LLM generation
      - `validate_output`: Deterministic domain invariants
      
    Execution orchestration, lifecycle state transitions, retry loops, audit logging,
    and error handling are STRICTLY owned by `AgentExecutor`.
    """

    @property
    @abstractmethod
    def metadata(self) -> AgentMetadata:
        """Deterministic identity and capability metadata."""
        pass

    @property
    @abstractmethod
    def output_schema(self) -> type[OutputT]:
        """Pydantic model representing the expected structured output."""
        pass

    async def initialize(self) -> None:
        """Lifecycle Hook 1: Pre-execution initialization hook."""
        pass

    @abstractmethod
    async def analyze(
        self,
        context: ProjectContextResponse,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Lifecycle Hook 2: Extract and prepare domain-specific features from Project Context."""
        pass

    @abstractmethod
    async def generate(
        self,
        analysis_result: dict[str, Any],
        provider: AbstractLLMProvider,
        **kwargs: Any,
    ) -> OutputT:
        """Lifecycle Hook 3: Invoke LLM provider to produce structured proposal adhering to output_schema."""
        pass

    def validate_output(
        self,
        output: OutputT,
        context: ProjectContextResponse,
    ) -> ValidationResult:
        """Lifecycle Hook 4: Deterministic domain validation hook.
        
        Subclasses override this method to enforce authoritative business logic.
        AI is never the judge of deterministic business invariants.
        """
        return ValidationResult(is_valid=True)

    async def execute(
        self,
        context: ProjectContextResponse,
        provider: AbstractLLMProvider,
        session: Any = None,
        snapshot: Any = None,
        context_snapshot_id: Any = None,
        context_version: Any = None,
        **kwargs: Any,
    ) -> AgentResult[OutputT]:
        """Convenience delegation to authoritative AgentExecutor.
        
        Guarantees single execution authority across the platform.
        """
        from app.agents.execution import AgentExecutor

        executor = AgentExecutor(provider=provider)
        return await executor.execute(
            agent=self,
            context=context,
            session=session,
            snapshot=snapshot,
            context_snapshot_id=context_snapshot_id,
            context_version=context_version,
            **kwargs,
        )
