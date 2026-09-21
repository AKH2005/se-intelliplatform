"""Abstract Base Agent Defining Identity, Contracts, and Execution Lifecycle."""

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from pydantic import BaseModel

from app.agents.contracts import (
    AgentErrorDetail,
    AgentExecutionStatus,
    AgentMetadata,
    AgentResult,
    ValidationResult,
)
from app.agents.exceptions import AgentError, AgentValidationError, ProviderError
from app.agents.providers.base import AbstractLLMProvider
from app.agents.validation import DeterministicValidator
from app.schemas.context import ProjectContextResponse

logger = logging.getLogger(__name__)

OutputT = TypeVar("OutputT", bound=BaseModel)


class AbstractBaseAgent(ABC, Generic[OutputT]):
    """Platform-level abstract base for all software engineering intelligence agents.
    
    All future SDLC intelligence agents (Requirement Analysis, Architecture,
    Code Review, Testing, etc.) inherit from this contract, consuming the canonical
    Project Context and emitting validated, structured domain results.
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
        """Lifecycle Step 1: Pre-execution initialization hook."""
        pass

    @abstractmethod
    async def analyze(
        self,
        context: ProjectContextResponse,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Lifecycle Step 2: Extract and prepare domain-specific features from Project Context."""
        pass

    @abstractmethod
    async def generate(
        self,
        analysis_result: dict[str, Any],
        provider: AbstractLLMProvider,
        **kwargs: Any,
    ) -> OutputT:
        """Lifecycle Step 3: Invoke LLM provider to produce structured proposal adhering to output_schema."""
        pass

    def validate_output(
        self,
        output: OutputT,
        context: ProjectContextResponse,
    ) -> ValidationResult:
        """Lifecycle Step 4: Deterministic domain validation hook.
        
        Subclasses override this method to enforce authoritative business logic.
        AI is never the judge of deterministic business invariants.
        """
        return ValidationResult(is_valid=True)

    async def execute(
        self,
        context: ProjectContextResponse,
        provider: AbstractLLMProvider,
        **kwargs: Any,
    ) -> AgentResult[OutputT]:
        """Lifecycle Orchestration Boundary:
        initialize -> analyze -> generate -> validate -> complete/failed.
        """
        execution_id = uuid.uuid4()
        started_at = datetime.now(timezone.utc)
        meta = self.metadata
        context_version = context.context_version

        logger.info(
            f"Commencing agent execution [{meta.agent_id} v{meta.version}] "
            f"for project [{context.project.id}] with context v{context_version} "
            f"[exec_id={execution_id}]"
        )

        try:
            # 1. Initialize
            await self.initialize()

            # 2. Analyze
            analysis_data = await self.analyze(context, **kwargs)

            # 3. Generate
            raw_output = await self.generate(analysis_data, provider, **kwargs)

            # 4. Validate (Two-Stage: Schema + Deterministic Domain Hook)
            validated_output, validation_res = DeterministicValidator.run_pipeline(
                raw_output=raw_output,
                schema=self.output_schema,
                context=context,
                domain_validator=self.validate_output,
            )

            completed_at = datetime.now(timezone.utc)
            logger.info(
                f"Agent execution completed successfully [{meta.agent_id} v{meta.version}] "
                f"[exec_id={execution_id}]"
            )

            return AgentResult[OutputT](
                execution_id=execution_id,
                agent_id=meta.agent_id,
                agent_version=meta.version,
                status=AgentExecutionStatus.COMPLETED,
                output=validated_output,
                validation=validation_res,
                error=None,
                context_version=context_version,
                started_at=started_at,
                completed_at=completed_at,
                metadata={"provider": provider.provider_name},
            )

        except AgentValidationError as ave:
            logger.warning(
                f"Validation failed during agent execution [{meta.agent_id}] [exec_id={execution_id}]: {ave.detail}"
            )
            return AgentResult[OutputT](
                execution_id=execution_id,
                agent_id=meta.agent_id,
                agent_version=meta.version,
                status=AgentExecutionStatus.FAILED,
                output=None,
                validation=ValidationResult(is_valid=False, errors=ave.validation_errors),
                error=AgentErrorDetail(
                    error_code="VALIDATION_FAILED",
                    message=ave.detail,
                    transient=False,
                ),
                context_version=context_version,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                metadata={"provider": provider.provider_name},
            )

        except ProviderError as pe:
            logger.error(
                f"Provider error during agent execution [{meta.agent_id}] [exec_id={execution_id}]: {pe.detail}"
            )
            return AgentResult[OutputT](
                execution_id=execution_id,
                agent_id=meta.agent_id,
                agent_version=meta.version,
                status=AgentExecutionStatus.FAILED,
                output=None,
                validation=ValidationResult(is_valid=False),
                error=AgentErrorDetail(
                    error_code="PROVIDER_ERROR",
                    message=pe.detail,
                    transient=pe.transient,
                ),
                context_version=context_version,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                metadata={"provider": provider.provider_name},
            )

        except Exception as exc:
            logger.exception(
                f"Unhandled failure during agent execution [{meta.agent_id}] [exec_id={execution_id}]: {exc}"
            )
            return AgentResult[OutputT](
                execution_id=execution_id,
                agent_id=meta.agent_id,
                agent_version=meta.version,
                status=AgentExecutionStatus.FAILED,
                output=None,
                validation=ValidationResult(is_valid=False),
                error=AgentErrorDetail(
                    error_code="EXECUTION_FAILED",
                    message="An internal error occurred during agent execution.",
                    transient=False,
                ),
                context_version=context_version,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                metadata={"provider": provider.provider_name},
            )
