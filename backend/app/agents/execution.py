"""Agent Execution Engine, Controlled Retry Boundary, and Audit Tracking."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, TypeVar
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AbstractBaseAgent
from app.agents.contracts import (
    AgentExecutionStatus,
    AgentResult,
)
from app.agents.exceptions import AgentError, AgentValidationError, TransientProviderError
from app.agents.providers.base import AbstractLLMProvider
from app.schemas.context import ProjectContextResponse

logger = logging.getLogger(__name__)

OutputT = TypeVar("OutputT", bound=BaseModel)


class AgentExecutor:
    """Orchestrates agent execution with a controlled retry policy and persistence auditing."""

    def __init__(
        self,
        provider: AbstractLLMProvider,
        max_retries: int = 3,
        retry_delay_seconds: float = 0.0,
    ) -> None:
        self.provider = provider
        self.max_retries = max(1, max_retries)
        self.retry_delay_seconds = retry_delay_seconds

    async def execute(
        self,
        agent: AbstractBaseAgent[OutputT],
        context: ProjectContextResponse,
        session: AsyncSession | None = None,
        **kwargs: Any,
    ) -> AgentResult[OutputT]:
        """Execute an agent against the canonical Project Context with retry and audit tracking.
        
        Retry Policy:
        - Retries ONLY errors explicitly flagged as transient (e.g. TransientProviderError).
        - NEVER retries schema validation errors or deterministic domain rule rejections.
        """
        meta = agent.metadata
        context_version = context.context_version
        project_id = context.project.id
        execution_id = uuid.uuid4()
        started_at = datetime.now(timezone.utc)

        # 1. Initialize Audit Record if database session provided
        audit_record = None
        if session is not None:
            from app.models.agent_audit import AgentExecutionAudit
            audit_record = AgentExecutionAudit(
                execution_id=execution_id,
                project_id=project_id,
                agent_id=meta.agent_id,
                agent_version=meta.version,
                status=AgentExecutionStatus.PENDING,
                context_version=context_version,
                started_at=started_at,
                metadata_payload={"provider": self.provider.provider_name},
            )
            session.add(audit_record)
            await session.commit()
            await session.refresh(audit_record)

        result: AgentResult[OutputT] | None = None
        last_transient_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                if audit_record is not None:
                    audit_record.status = AgentExecutionStatus.RUNNING
                    await session.commit()  # type: ignore[union-attr]

                # Execute the agent lifecycle
                result = await agent.execute(
                    context=context,
                    provider=self.provider,
                    **kwargs,
                )
                # Overwrite execution_id to match tracked audit ID
                result.execution_id = execution_id

                # If result failed due to a transient provider error, trigger retry
                if (
                    result.status == AgentExecutionStatus.FAILED
                    and result.error is not None
                    and result.error.transient
                ):
                    if attempt < self.max_retries:
                        logger.warning(
                            f"Transient failure on attempt {attempt}/{self.max_retries} for agent [{meta.agent_id}]: "
                            f"{result.error.message}. Retrying..."
                        )
                        if self.retry_delay_seconds > 0:
                            await asyncio.sleep(self.retry_delay_seconds)
                        continue

                # Non-transient result (Success or non-transient failure like validation)
                break

            except TransientProviderError as tpe:
                last_transient_error = tpe
                logger.warning(
                    f"Transient provider exception on attempt {attempt}/{self.max_retries} "
                    f"for agent [{meta.agent_id}]: {tpe.detail}"
                )
                if attempt < self.max_retries:
                    if self.retry_delay_seconds > 0:
                        await asyncio.sleep(self.retry_delay_seconds)
                    continue

        # If loop completed without a structured result (due to unhandled transient loop)
        if result is None:
            result = AgentResult[OutputT](
                execution_id=execution_id,
                agent_id=meta.agent_id,
                agent_version=meta.version,
                status=AgentExecutionStatus.FAILED,
                output=None,
                error=None,
                context_version=context_version,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                metadata={"provider": self.provider.provider_name, "error": str(last_transient_error)},
            )

        # 2. Finalize Audit Record in Persistence Store
        if session is not None and audit_record is not None:
            audit_record.status = result.status
            audit_record.completed_at = result.completed_at
            if result.error is not None:
                audit_record.error_code = result.error.error_code
                audit_record.error_message = result.error.message
            if result.output is not None:
                # Sanitized brief summary of output (no full prompt or secrets)
                output_dump = result.output.model_dump(mode="json")
                summary_str = f"Keys: {list(output_dump.keys())}"
                audit_record.output_summary = summary_str[:500]

            await session.commit()
            await session.refresh(audit_record)

        return result
