"""Authoritative Deterministic Multi-Agent Workflow Coordinator."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.contracts import AgentErrorDetail, AgentExecutionStatus, AgentResult
from app.agents.execution import AgentExecutor
from app.agents.registry import AgentRegistry, agent_registry
from app.workflows.contracts import (
    WorkflowDefinition,
    WorkflowInput,
    WorkflowResult,
    WorkflowStatus,
    WorkflowStep,
    WorkflowStepResult,
    WorkflowStepStatus,
)
from app.workflows.pipelines import resolve_step_kwargs
from app.telemetry.contracts import EventSeverity, ExecutionEventType, ExecutionKind
from app.telemetry.publisher import ExecutionEventPublisher

logger = logging.getLogger(__name__)


class WorkflowCoordinator:
    """Sole authoritative coordinator for multi-agent workflows.

    Hierarchy Invariant:
        API / Service Layer -> WorkflowCoordinator -> AgentExecutor -> Agent

    Guarantees:
    - Never bypasses AgentExecutor: All agents are executed exclusively via AgentExecutor.
    - Zero agent-to-agent invocation: Agents remain completely unaware of each other.
    - Deterministic execution order: Evaluates steps strictly in predefined sequential order.
    - Epistemic integrity: Treats agent outputs as immutable typed artifacts. Never fabricates claims.
    - Provenance preservation: Passes identical canonical context and correlation ID to all steps.
    """

    def __init__(
        self,
        executor: AgentExecutor,
        registry: AgentRegistry | None = None,
    ) -> None:
        self.executor = executor
        self.registry = registry or agent_registry

    async def execute(
        self,
        workflow: WorkflowDefinition,
        workflow_input: WorkflowInput,
        session: AsyncSession | None = None,
        snapshot: Any | None = None,
        context_snapshot_id: uuid.UUID | None = None,
        context_version: int | None = None,
        workflow_execution_id: uuid.UUID | None = None,
    ) -> WorkflowResult:
        """Execute a predefined multi-agent workflow against canonical Project Context.

        Args:
            workflow: Declarative workflow specification with ordered steps and dependency graph.
            workflow_input: Strongly typed input containing canonical context and optional payload inputs.
            session: Optional AsyncSession for audit logging.
            snapshot: Optional ContextSnapshot instance.
            context_snapshot_id: Optional ContextSnapshot UUID.
            context_version: Optional ContextSnapshot version sequence number.
            workflow_execution_id: Optional pre-generated workflow execution correlation UUID.

        Returns:
            WorkflowResult: Structured envelope containing terminal workflow status, step outcomes,
                           and in-memory immutable artifacts.
        """
        workflow_execution_id = workflow_execution_id or uuid.uuid4()
        started_at = datetime.now(timezone.utc)
        project_id = workflow_input.context.project.id

        logger.info(
            f"Commencing workflow execution [{workflow.workflow_id} v{workflow.version}] "
            f"for project [{project_id}] [workflow_exec_id={workflow_execution_id}]"
        )

        await ExecutionEventPublisher.emit(
            event_type=ExecutionEventType.WORKFLOW_STARTED,
            project_id=project_id,
            execution_id=workflow_execution_id,
            execution_kind=ExecutionKind.WORKFLOW,
            source="WorkflowCoordinator",
            status="RUNNING",
            payload={
                "workflow_id": workflow.workflow_id,
                "workflow_version": workflow.version,
                "workflow_name": workflow.name,
                "total_steps": len(workflow.steps),
                "steps": [s.step_id for s in workflow.steps],
                "phase": f"Started {workflow.name}",
            },
        )

        step_results: list[WorkflowStepResult] = []
        artifacts: dict[str, Any] = dict(getattr(workflow_input, "initial_artifacts", {}) or {})
        step_status_map: dict[str, WorkflowStepStatus] = {
            k: WorkflowStepStatus.COMPLETED for k in artifacts if artifacts[k] is not None
        }
        errors: list[str] = []
        warnings: list[str] = []

        # Sequential deterministic step evaluation
        for step in workflow.steps:
            step_id = step.step_id
            agent_id = step.agent_id

            # 0. Check if step was already completed in pre-seeded artifacts
            if step_id in artifacts and artifacts[step_id] is not None:
                logger.info(
                    f"Step [{step_id}] already resolved in project artifacts, reusing existing outcome."
                )
                reused_res = WorkflowStepResult(
                    step_id=step_id,
                    agent_id=agent_id,
                    status=WorkflowStepStatus.COMPLETED,
                    execution_id=None,
                    agent_result=None,
                    error=None,
                    skip_reason=None,
                    started_at=started_at,
                    completed_at=datetime.now(timezone.utc),
                )
                step_results.append(reused_res)
                step_status_map[step_id] = WorkflowStepStatus.COMPLETED
                continue

            # 1. Dependency Precondition Verification
            prereq_failed = False
            prereq_fail_reason = ""
            for dep_id in step.depends_on:
                dep_status = step_status_map.get(dep_id)
                # Find dependency step definition to determine if it was mandatory
                dep_step_def = next((s for s in workflow.steps if s.step_id == dep_id), None)
                dep_required = dep_step_def.required if dep_step_def is not None else True

                if dep_status in (WorkflowStepStatus.FAILED, WorkflowStepStatus.SKIPPED):
                    if dep_required:
                        prereq_failed = True
                        prereq_fail_reason = f"Required prerequisite step '{dep_id}' was {dep_status.value}."
                        break

            if prereq_failed:
                logger.info(
                    f"Skipping step [{step_id}] in workflow [{workflow.workflow_id}]: {prereq_fail_reason}"
                )
                skipped_res = WorkflowStepResult(
                    step_id=step_id,
                    agent_id=agent_id,
                    status=WorkflowStepStatus.SKIPPED,
                    execution_id=None,
                    agent_result=None,
                    error=None,
                    skip_reason=prereq_fail_reason,
                    started_at=None,
                    completed_at=None,
                )
                step_results.append(skipped_res)
                step_status_map[step_id] = WorkflowStepStatus.SKIPPED
                warnings.append(f"Step '{step_id}' skipped: {prereq_fail_reason}")
                continue

            # 2. Artifact and Input Routing Resolution
            step_kwargs, skip_reason = resolve_step_kwargs(
                workflow_id=workflow.workflow_id,
                step=step,
                artifacts=artifacts,
                workflow_input=workflow_input,
            )

            if skip_reason is not None:
                logger.info(
                    f"Skipping step [{step_id}] in workflow [{workflow.workflow_id}]: {skip_reason}"
                )
                skipped_res = WorkflowStepResult(
                    step_id=step_id,
                    agent_id=agent_id,
                    status=WorkflowStepStatus.SKIPPED,
                    execution_id=None,
                    agent_result=None,
                    error=None,
                    skip_reason=skip_reason,
                    started_at=None,
                    completed_at=None,
                )
                step_results.append(skipped_res)
                step_status_map[step_id] = WorkflowStepStatus.SKIPPED
                warnings.append(f"Step '{step_id}' skipped: {skip_reason}")
                continue

            # 3. Agent Lookup from Registry
            from app.agents.exceptions import AgentNotFoundError

            try:
                agent = self.registry.get(agent_id)
            except AgentNotFoundError:
                agent = None

            if agent is None:
                err_msg = f"Agent '{agent_id}' required by step '{step_id}' is not registered."
                logger.error(err_msg)
                err_detail = AgentErrorDetail(
                    error_code="AGENT_NOT_FOUND",
                    message=err_msg,
                    transient=False,
                )
                failed_res = WorkflowStepResult(
                    step_id=step_id,
                    agent_id=agent_id,
                    status=WorkflowStepStatus.FAILED,
                    execution_id=None,
                    agent_result=None,
                    error=err_detail,
                    skip_reason=None,
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                )
                step_results.append(failed_res)
                step_status_map[step_id] = WorkflowStepStatus.FAILED
                errors.append(err_msg)
                continue

            # 4. Step Execution via Authoritative AgentExecutor
            step_started_at = datetime.now(timezone.utc)
            logger.info(
                f"Executing step [{step_id}] (agent: [{agent_id}]) in workflow [{workflow.workflow_id}]"
            )

            await ExecutionEventPublisher.emit(
                event_type=ExecutionEventType.WORKFLOW_STEP_STARTED,
                project_id=project_id,
                execution_id=workflow_execution_id,
                execution_kind=ExecutionKind.WORKFLOW,
                source="WorkflowCoordinator",
                status="RUNNING",
                payload={
                    "workflow_id": workflow.workflow_id,
                    "step_id": step_id,
                    "agent_id": agent_id,
                    "phase": f"Step: {step_id}",
                    "total_steps": len(workflow.steps),
                },
            )

            try:
                agent_result: AgentResult[Any] = await self.executor.execute(
                    agent=agent,
                    context=workflow_input.context,
                    session=session,
                    snapshot=snapshot,
                    context_snapshot_id=context_snapshot_id,
                    context_version=context_version,
                    workflow_execution_id=workflow_execution_id,
                    **step_kwargs,
                )
            except Exception as exc:
                step_completed_at = datetime.now(timezone.utc)
                logger.exception(
                    f"Unexpected exception executing step [{step_id}] in workflow [{workflow.workflow_id}]: {exc}"
                )
                err_detail = AgentErrorDetail(
                    error_code="WORKFLOW_STEP_EXCEPTION",
                    message=f"Step execution encountered unexpected exception: {exc}",
                    transient=False,
                )
                failed_res = WorkflowStepResult(
                    step_id=step_id,
                    agent_id=agent_id,
                    status=WorkflowStepStatus.FAILED,
                    execution_id=None,
                    agent_result=None,
                    error=err_detail,
                    skip_reason=None,
                    started_at=step_started_at,
                    completed_at=step_completed_at,
                )
                step_results.append(failed_res)
                step_status_map[step_id] = WorkflowStepStatus.FAILED
                errors.append(f"Step '{step_id}' failed: {exc}")

                await ExecutionEventPublisher.emit(
                    event_type=ExecutionEventType.WORKFLOW_STEP_FAILED,
                    project_id=project_id,
                    execution_id=workflow_execution_id,
                    execution_kind=ExecutionKind.WORKFLOW,
                    source="WorkflowCoordinator",
                    status="RUNNING",
                    severity=EventSeverity.ERROR,
                    payload={
                        "workflow_id": workflow.workflow_id,
                        "step_id": step_id,
                        "agent_id": agent_id,
                        "error": str(exc),
                        "phase": f"Failed step: {step_id}",
                    },
                )
                continue

            step_completed_at = datetime.now(timezone.utc)

            # 5. Process Step Execution Outcome
            if agent_result.status == AgentExecutionStatus.COMPLETED:
                step_res = WorkflowStepResult(
                    step_id=step_id,
                    agent_id=agent_id,
                    status=WorkflowStepStatus.COMPLETED,
                    execution_id=agent_result.execution_id,
                    agent_result=agent_result,
                    error=None,
                    skip_reason=None,
                    started_at=step_started_at,
                    completed_at=step_completed_at,
                )
                step_results.append(step_res)
                step_status_map[step_id] = WorkflowStepStatus.COMPLETED

                # Preserve immutable typed output in artifact store
                if agent_result.output is not None:
                    artifacts[step_id] = agent_result.output
                    if step_id != agent_id:
                        artifacts[agent_id] = agent_result.output

                await ExecutionEventPublisher.emit(
                    event_type=ExecutionEventType.WORKFLOW_STEP_COMPLETED,
                    project_id=project_id,
                    execution_id=workflow_execution_id,
                    execution_kind=ExecutionKind.WORKFLOW,
                    source="WorkflowCoordinator",
                    status="RUNNING",
                    payload={
                        "workflow_id": workflow.workflow_id,
                        "step_id": step_id,
                        "agent_id": agent_id,
                        "agent_execution_id": str(agent_result.execution_id) if agent_result else None,
                        "duration_seconds": round((step_completed_at - step_started_at).total_seconds(), 3),
                        "phase": f"Completed step: {step_id}",
                    },
                )
            else:
                step_res = WorkflowStepResult(
                    step_id=step_id,
                    agent_id=agent_id,
                    status=WorkflowStepStatus.FAILED,
                    execution_id=agent_result.execution_id,
                    agent_result=agent_result,
                    error=agent_result.error,
                    skip_reason=None,
                    started_at=step_started_at,
                    completed_at=step_completed_at,
                )
                step_results.append(step_res)
                step_status_map[step_id] = WorkflowStepStatus.FAILED
                err_msg = agent_result.error.message if agent_result.error else "Unknown agent execution failure"
                errors.append(f"Step '{step_id}' failed: {err_msg}")

                await ExecutionEventPublisher.emit(
                    event_type=ExecutionEventType.WORKFLOW_STEP_FAILED,
                    project_id=project_id,
                    execution_id=workflow_execution_id,
                    execution_kind=ExecutionKind.WORKFLOW,
                    source="WorkflowCoordinator",
                    status="RUNNING",
                    severity=EventSeverity.ERROR,
                    payload={
                        "workflow_id": workflow.workflow_id,
                        "step_id": step_id,
                        "agent_id": agent_id,
                        "error": err_msg,
                        "phase": f"Failed step: {step_id}",
                    },
                )

            # Optional inter-step pacing for rate-limited providers
            inter_step_delay = float(workflow_input.options.get("inter_step_delay", 0.0))
            if inter_step_delay > 0.0 and step != workflow.steps[-1]:
                await asyncio.sleep(inter_step_delay)

        # 6. Determine Deterministic Terminal Workflow Status
        final_status = self._calculate_workflow_status(workflow, step_results)
        completed_at = datetime.now(timezone.utc)

        logger.info(
            f"Workflow execution finished [{workflow.workflow_id}] status=[{final_status.value}] "
            f"completed_steps={len([s for s in step_results if s.status == WorkflowStepStatus.COMPLETED])}/"
            f"{len(workflow.steps)}"
        )

        terminal_evt = (
            ExecutionEventType.WORKFLOW_COMPLETED
            if final_status in (WorkflowStatus.COMPLETED, WorkflowStatus.PARTIAL_SUCCESS)
            else ExecutionEventType.WORKFLOW_FAILED
        )
        await ExecutionEventPublisher.emit(
            event_type=terminal_evt,
            project_id=project_id,
            execution_id=workflow_execution_id,
            execution_kind=ExecutionKind.WORKFLOW,
            source="WorkflowCoordinator",
            status=final_status.value,
            severity=EventSeverity.INFO if terminal_evt == ExecutionEventType.WORKFLOW_COMPLETED else EventSeverity.ERROR,
            payload={
                "workflow_id": workflow.workflow_id,
                "status": final_status.value,
                "duration_seconds": round((completed_at - started_at).total_seconds(), 3),
                "completed_steps": len([s for s in step_results if s.status == WorkflowStepStatus.COMPLETED]),
                "total_steps": len(workflow.steps),
                "phase": f"Workflow {final_status.value.lower()}",
            },
        )

        return WorkflowResult(
            workflow_execution_id=workflow_execution_id,
            workflow_id=workflow.workflow_id,
            workflow_version=workflow.version,
            status=final_status,
            started_at=started_at,
            completed_at=completed_at,
            step_results=step_results,
            artifacts=artifacts,
            errors=errors,
            warnings=warnings,
            metadata={
                "project_id": str(project_id),
                "total_steps": len(workflow.steps),
                "completed_steps": len([s for s in step_results if s.status == WorkflowStepStatus.COMPLETED]),
                "failed_steps": len([s for s in step_results if s.status == WorkflowStepStatus.FAILED]),
                "skipped_steps": len([s for s in step_results if s.status == WorkflowStepStatus.SKIPPED]),
            },
        )

    def _calculate_workflow_status(
        self,
        workflow: WorkflowDefinition,
        step_results: list[WorkflowStepResult],
    ) -> WorkflowStatus:
        """Deterministic status computation.

        Rules:
        1. If any required step was FAILED or SKIPPED -> FAILED.
        2. If all required steps succeeded (or no required steps exist):
           a. If ALL steps in workflow COMPLETED -> COMPLETED.
           b. If at least one step COMPLETED and some optional steps FAILED or were SKIPPED -> PARTIAL_SUCCESS.
           c. If ZERO steps completed successfully -> FAILED.
        """
        step_def_map = {s.step_id: s for s in workflow.steps}
        result_map = {r.step_id: r for r in step_results}

        # Check required steps
        for step_def in workflow.steps:
            if step_def.required:
                res = result_map.get(step_def.step_id)
                if res is None or res.status != WorkflowStepStatus.COMPLETED:
                    return WorkflowStatus.FAILED

        # Count completed vs non-completed
        completed_count = sum(1 for r in step_results if r.status == WorkflowStepStatus.COMPLETED)
        total_count = len(workflow.steps)

        if completed_count == total_count:
            return WorkflowStatus.COMPLETED

        if completed_count > 0:
            return WorkflowStatus.PARTIAL_SUCCESS

        return WorkflowStatus.FAILED
