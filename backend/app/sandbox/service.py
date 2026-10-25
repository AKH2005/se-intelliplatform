"""Sandbox Service Layer orchestrating validation, execution, and audit persistence."""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.code_generation.contracts import CodeGenerationOutput
from app.agents.contracts import AgentExecutionStatus
from app.core.exceptions import NotFoundError, ValidationError
from app.models.agent_audit import AgentExecutionAudit
from app.models.workflow_execution import WorkflowExecution, WorkflowStatus
from app.sandbox.base import AbstractSandboxExecutor
from app.sandbox.contracts import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
)
from app.services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)


class SandboxService:
    """Coordinates secure execution requests with artifact resolution and audit persistence."""

    def __init__(
        self,
        session: AsyncSession,
        workflow_service: WorkflowService,
        executor: AbstractSandboxExecutor,
    ) -> None:
        self.session = session
        self.workflow_service = workflow_service
        self.executor = executor

    async def get_status(self) -> dict[str, Any]:
        """Check availability and runtime diagnostics of the sandbox."""
        available = await self.executor.is_available()
        runtime_type = "docker" if "Docker" in type(self.executor).__name__ else "mock"
        image = getattr(self.executor, "image", "default")
        return {
            "available": available,
            "runtime": runtime_type,
            "image": image,
            "security_policy": {
                "network": "disabled",
                "filesystem": "read-only workspace + tmpfs",
                "capabilities": "dropped ALL",
                "privilege_escalation": "forbidden (no-new-privileges)",
                "user": "non-root (uid 2000)",
            },
        }

    async def _resolve_code_artifact(
        self,
        project_id: uuid.UUID,
        workflow_execution_id: uuid.UUID | None = None,
    ) -> tuple[CodeGenerationOutput, WorkflowExecution | None]:
        """Resolve authoritative CodeGenerationOutput from persisted workflow executions."""
        # 1. By explicit workflow execution ID
        if workflow_execution_id is not None:
            exec_record = await self.workflow_service.get_workflow_execution(workflow_execution_id)
            if exec_record.project_id != project_id:
                raise ValidationError(
                    message=f"WorkflowExecution '{workflow_execution_id}' does not belong to project '{project_id}'."
                )

            artifact_dict = exec_record.artifacts.get("code-generation") or exec_record.artifacts.get("code_generation")
            if not artifact_dict:
                raise ValidationError(
                    message=f"WorkflowExecution '{workflow_execution_id}' does not contain a 'code-generation' artifact."
                )

            try:
                code_output = CodeGenerationOutput.model_validate(artifact_dict)
            except Exception as exc:
                raise ValidationError(
                    message=f"Artifact in WorkflowExecution '{workflow_execution_id}' is not a valid CodeGenerationOutput: {exc}"
                )

            return code_output, exec_record

        # 2. Latest completed workflow execution containing code-generation
        stmt = (
            select(WorkflowExecution)
            .where(WorkflowExecution.project_id == project_id)
            .where(
                WorkflowExecution.status.in_(
                    [WorkflowStatus.COMPLETED, WorkflowStatus.PARTIAL_SUCCESS]
                )
            )
            .order_by(WorkflowExecution.started_at.desc())
        )
        result = await self.session.execute(stmt)
        executions = list(result.scalars().all())

        for ex in executions:
            artifact_dict = ex.artifacts.get("code-generation") or ex.artifacts.get("code_generation")
            if artifact_dict:
                try:
                    code_output = CodeGenerationOutput.model_validate(artifact_dict)
                    return code_output, ex
                except Exception:
                    continue

        raise ValidationError(
            message=f"No completed workflow execution with a valid code-generation artifact found for project '{project_id}'."
        )

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Execute sandboxed validation or test runner for a project artifact."""
        # 1. Verify project exists
        await self.workflow_service.context_engine._get_project(request.project_id)

        # 2. Resolve target artifact
        code_output, target_exec = await self._resolve_code_artifact(
            project_id=request.project_id,
            workflow_execution_id=request.workflow_execution_id,
        )

        effective_request = request.model_copy(
            update={
                "workflow_execution_id": target_exec.workflow_execution_id if target_exec else request.workflow_execution_id
            }
        )

        # 3. Execute in isolated sandbox
        result = await self.executor.execute(effective_request, code_output)

        # 4. Audit persistence
        completed_at = datetime.now(timezone.utc)
        started_at = completed_at - timedelta(seconds=max(result.duration_seconds, 0.001))

        audit_status = (
            AgentExecutionStatus.COMPLETED
            if result.status == ExecutionStatus.PASSED
            else AgentExecutionStatus.FAILED
        )

        audit_record = AgentExecutionAudit(
            execution_id=result.execution_id,
            project_id=request.project_id,
            agent_id="sandbox-test-runner",
            agent_version="1.0.0",
            status=audit_status,
            context_snapshot_id=target_exec.context_snapshot_id if target_exec else None,
            context_version=target_exec.context_version if target_exec else None,
            started_at=started_at,
            completed_at=completed_at,
            output_summary=(
                f"Sandbox {result.execution_type.value}: {result.status.value} "
                f"({result.tests_passed} passed, {result.tests_failed} failed, exit={result.exit_code})"
            ),
            error_code=None if result.status == ExecutionStatus.PASSED else result.status.value,
            error_message=result.stderr or (None if result.status == ExecutionStatus.PASSED else "Execution failed"),
            metadata_payload=result.model_dump(mode="json"),
        )
        self.session.add(audit_record)

        # Update WorkflowExecution with the sandbox execution result if associated
        if target_exec:
            current_artifacts = dict(target_exec.artifacts)
            current_artifacts["sandbox_execution"] = result.model_dump(mode="json")
            target_exec.artifacts = current_artifacts

        await self.session.commit()

        return result
