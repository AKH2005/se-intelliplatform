"""Agent Execution Engine, Authoritative Lifecycle Orchestrator, and Audit Tracking."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, TypeVar
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.contracts import (
    AgentErrorDetail,
    AgentExecutionStatus,
    AgentResult,
    ValidationResult,
)
from app.agents.exceptions import (
    AgentError,
    AgentValidationError,
    ProviderError,
    TransientProviderError,
)
from app.agents.providers.base import AbstractLLMProvider
from app.agents.validation import DeterministicValidator
from app.schemas.context import ProjectContextResponse

logger = logging.getLogger(__name__)

OutputT = TypeVar("OutputT", bound=BaseModel)


class AgentExecutor:
    """Sole authoritative execution orchestrator for all platform agents.
    
    Owns:
    - Unique execution ID generation and lifecycle tracking
    - Authoritative lifecycle state transitions (PENDING -> RUNNING -> VALIDATING -> COMPLETED / FAILED)
    - Controlled retry policy for transient failures
    - Schema and deterministic domain validation coordination
    - Resilient error handling and normalization
    - Persistent audit recording with exact snapshot / live-context provenance
    - Production of the final structured AgentResult envelope
    """

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
        agent: Any,
        context: ProjectContextResponse,
        session: AsyncSession | None = None,
        snapshot: Any | None = None,
        context_snapshot_id: uuid.UUID | None = None,
        context_version: int | None = None,
        **kwargs: Any,
    ) -> AgentResult[OutputT]:
        """Execute an agent against canonical Project Context under authoritative executor governance.
        
        Provenance Rules:
        - Snapshot-backed execution:
            context_snapshot_id = snapshot.id (or context_snapshot_id)
            context_version = snapshot.version (or context_version)
        - Live-context execution:
            context_snapshot_id = None
            context_version = None
          (Never fabricates or assumes a version from ProjectContextResponse).
          
        Retry Policy:
        - Retries ONLY errors explicitly flagged as transient (e.g. TransientProviderError).
        - NEVER retries schema validation errors or deterministic domain rule rejections.
        """
        meta = agent.metadata
        project_id = context.project.id
        execution_id = uuid.uuid4()
        started_at = datetime.now(timezone.utc)

        # 1. Determine Context Provenance (No fabricated values)
        actual_snapshot_id: uuid.UUID | None = None
        actual_context_version: int | None = None

        if snapshot is not None:
            actual_snapshot_id = getattr(snapshot, "id", None)
            actual_context_version = getattr(snapshot, "version", None)
        elif context_snapshot_id is not None:
            actual_snapshot_id = context_snapshot_id
            actual_context_version = context_version
        else:
            # Live context execution: must explicitly remain NULL
            actual_snapshot_id = None
            actual_context_version = None

        logger.info(
            f"Commencing agent execution [{meta.agent_id} v{meta.version}] "
            f"for project [{project_id}] [exec_id={execution_id}] "
            f"provenance=[snapshot_id={actual_snapshot_id}, version={actual_context_version}]"
        )

        # 2. Authoritative Audit Record (Initial State: PENDING)
        audit_record = None
        if session is not None:
            from app.models.agent_audit import AgentExecutionAudit

            audit_record = AgentExecutionAudit(
                execution_id=execution_id,
                project_id=project_id,
                agent_id=meta.agent_id,
                agent_version=meta.version,
                status=AgentExecutionStatus.PENDING,
                context_snapshot_id=actual_snapshot_id,
                context_version=actual_context_version,
                started_at=started_at,
                metadata_payload={"provider": self.provider.provider_name},
            )
            session.add(audit_record)
            await session.commit()
            await session.refresh(audit_record)

        result: AgentResult[OutputT] | None = None

        # 3. Execution Lifecycle Loop with Controlled Retry Boundary
        for attempt in range(1, self.max_retries + 1):
            if audit_record is not None:
                audit_record.status = AgentExecutionStatus.RUNNING
                await session.commit()

            try:
                # Stage 1: Initialize
                await agent.initialize()

                # Stage 2: Analyze
                analysis_data = await agent.analyze(context, **kwargs)

                # Stage 3: Generate
                raw_output = await agent.generate(analysis_data, self.provider, **kwargs)

                # Stage 4: Validate (Schema + Deterministic Domain Validation Hook)
                if audit_record is not None:
                    audit_record.status = AgentExecutionStatus.VALIDATING
                    await session.commit()

                validated_output, validation_res = DeterministicValidator.run_pipeline(
                    raw_output=raw_output,
                    schema=agent.output_schema,
                    context=context,
                    domain_validator=agent.validate_output,
                )

                # Successful Execution Outcome
                completed_at = datetime.now(timezone.utc)
                logger.info(
                    f"Agent execution completed successfully [{meta.agent_id} v{meta.version}] "
                    f"[exec_id={execution_id}]"
                )
                result = AgentResult[OutputT](
                    execution_id=execution_id,
                    agent_id=meta.agent_id,
                    agent_version=meta.version,
                    status=AgentExecutionStatus.COMPLETED,
                    output=validated_output,
                    validation=validation_res,
                    error=None,
                    context_snapshot_id=actual_snapshot_id,
                    context_version=actual_context_version,
                    started_at=started_at,
                    completed_at=completed_at,
                    metadata={"provider": self.provider.provider_name, "attempts": attempt},
                )
                break

            except AgentValidationError as ave:
                # Deterministic validation rejection: NEVER retry
                completed_at = datetime.now(timezone.utc)
                logger.warning(
                    f"Validation failed during agent execution [{meta.agent_id}] [exec_id={execution_id}]: {ave.detail}"
                )
                result = AgentResult[OutputT](
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
                    context_snapshot_id=actual_snapshot_id,
                    context_version=actual_context_version,
                    started_at=started_at,
                    completed_at=completed_at,
                    metadata={"provider": self.provider.provider_name, "attempts": attempt},
                )
                break

            except TransientProviderError as tpe:
                # Transient error: retry if attempts remaining
                logger.warning(
                    f"Transient provider error on attempt {attempt}/{self.max_retries} "
                    f"for agent [{meta.agent_id}] [exec_id={execution_id}]: {tpe.detail}"
                )
                if attempt < self.max_retries:
                    if self.retry_delay_seconds > 0:
                        await asyncio.sleep(self.retry_delay_seconds)
                    continue

                # Max retries exhausted
                completed_at = datetime.now(timezone.utc)
                result = AgentResult[OutputT](
                    execution_id=execution_id,
                    agent_id=meta.agent_id,
                    agent_version=meta.version,
                    status=AgentExecutionStatus.FAILED,
                    output=None,
                    validation=ValidationResult(is_valid=False),
                    error=AgentErrorDetail(
                        error_code="PROVIDER_ERROR",
                        message=tpe.detail,
                        transient=True,
                    ),
                    context_snapshot_id=actual_snapshot_id,
                    context_version=actual_context_version,
                    started_at=started_at,
                    completed_at=completed_at,
                    metadata={"provider": self.provider.provider_name, "attempts": attempt},
                )
                break

            except ProviderError as pe:
                # Non-transient provider error: do not retry
                completed_at = datetime.now(timezone.utc)
                logger.error(
                    f"Non-transient provider error for agent [{meta.agent_id}] [exec_id={execution_id}]: {pe.detail}"
                )
                result = AgentResult[OutputT](
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
                    context_snapshot_id=actual_snapshot_id,
                    context_version=actual_context_version,
                    started_at=started_at,
                    completed_at=completed_at,
                    metadata={"provider": self.provider.provider_name, "attempts": attempt},
                )
                break

            except Exception as exc:
                # Unexpected failure: do not retry
                completed_at = datetime.now(timezone.utc)
                logger.exception(
                    f"Unhandled exception during agent execution [{meta.agent_id}] [exec_id={execution_id}]: {exc}"
                )
                result = AgentResult[OutputT](
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
                    context_snapshot_id=actual_snapshot_id,
                    context_version=actual_context_version,
                    started_at=started_at,
                    completed_at=completed_at,
                    metadata={"provider": self.provider.provider_name, "attempts": attempt},
                )
                break

        # Fallback safeguard in case loop exited unexpectedly
        if result is None:
            completed_at = datetime.now(timezone.utc)
            result = AgentResult[OutputT](
                execution_id=execution_id,
                agent_id=meta.agent_id,
                agent_version=meta.version,
                status=AgentExecutionStatus.FAILED,
                output=None,
                error=AgentErrorDetail(
                    error_code="UNKNOWN_ERROR",
                    message="Execution terminated without producing a result.",
                    transient=False,
                ),
                context_snapshot_id=actual_snapshot_id,
                context_version=actual_context_version,
                started_at=started_at,
                completed_at=completed_at,
                metadata={"provider": self.provider.provider_name},
            )

        # 4. Finalize Audit Record in Persistence Store
        if session is not None and audit_record is not None:
            audit_record.status = result.status
            audit_record.completed_at = result.completed_at
            if result.error is not None:
                audit_record.error_code = result.error.error_code
                audit_record.error_message = result.error.message
            if result.output is not None:
                output_dump = result.output.model_dump(mode="json")
                summary_str = f"Keys: {list(output_dump.keys())}"
                audit_record.output_summary = summary_str[:500]

            await session.commit()
            await session.refresh(audit_record)

        return result
