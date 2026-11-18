"""Workflow Service Layer.

Provides application-level coordination between HTTP API endpoints,
canonical ProjectContextEngine state resolution, and the deterministic
WorkflowCoordinator engine.
"""

import asyncio
import inspect
import logging
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.context_snapshot import ContextSnapshot
from app.models.workflow_execution import WorkflowExecution
from app.schemas.context import ProjectContextResponse
from app.schemas.workflow import (
    WorkflowExecuteRequest,
    WorkflowMetadataResponse,
    WorkflowStepMetadata,
)
from app.services.context_engine import ProjectContextEngine
from app.workflows.contracts import (
    WorkflowDefinition,
    WorkflowInput,
    WorkflowResult,
    WorkflowStatus,
    WorkflowStepStatus,
)
from app.workflows.coordinator import WorkflowCoordinator
from app.workflows.pipelines import (
    WORKFLOW_COMPREHENSIVE_AUDIT_ID,
    WORKFLOW_PROJECT_ESTIMATION_ID,
    WORKFLOW_SOFTWARE_DESIGN_ID,
    WORKFLOW_CODE_GENERATION_ID,
    WORKFLOW_BROWSER_JOURNEY_ID,
    build_browser_journey_workflow,
    build_code_generation_workflow,
    build_comprehensive_audit_workflow,
    build_project_estimation_workflow,
    build_software_design_workflow,
)

logger = logging.getLogger(__name__)


class WorkflowService:
    """Application-level service orchestrating workflow execution and discovery.

    Hierarchy Invariant:
        API Endpoint -> WorkflowService -> ProjectContextEngine -> DB
                                       -> WorkflowCoordinator -> AgentExecutor -> Agent

    Guarantees:
    - Never executes agents directly: delegates exclusively to WorkflowCoordinator.
    - Resolves canonical context through ProjectContextEngine.
    - Preserves deterministic live vs snapshot context provenance.
    - Performs strict validation on context-to-snapshot targeting.
    """

    PREDEFINED_WORKFLOWS: dict[str, Callable[[], WorkflowDefinition]] = {
        WORKFLOW_SOFTWARE_DESIGN_ID: build_software_design_workflow,
        WORKFLOW_PROJECT_ESTIMATION_ID: build_project_estimation_workflow,
        WORKFLOW_COMPREHENSIVE_AUDIT_ID: build_comprehensive_audit_workflow,
    }

    EXTENSION_WORKFLOWS: dict[str, Callable[[], WorkflowDefinition]] = {
        WORKFLOW_CODE_GENERATION_ID: build_code_generation_workflow,
        WORKFLOW_BROWSER_JOURNEY_ID: build_browser_journey_workflow,
    }

    _active_project_builds: set[uuid.UUID] = set()
    _build_locks_mutex: asyncio.Lock = asyncio.Lock()

    def __init__(
        self,
        session: AsyncSession,
        context_engine: ProjectContextEngine,
        coordinator: WorkflowCoordinator,
    ) -> None:
        self.session = session
        self.context_engine = context_engine
        self.coordinator = coordinator

    def list_workflows(self, include_extensions: bool = False) -> list[WorkflowDefinition]:
        """Return registered predefined workflow definitions in deterministic order."""
        workflows = [builder() for builder in self.PREDEFINED_WORKFLOWS.values()]
        if include_extensions:
            workflows.extend(builder() for builder in self.EXTENSION_WORKFLOWS.values())
        return workflows

    def get_workflow(self, workflow_id: str) -> WorkflowDefinition:
        """Retrieve a specific workflow definition by ID or raise NotFoundError."""
        builder = self.PREDEFINED_WORKFLOWS.get(workflow_id) or self.EXTENSION_WORKFLOWS.get(workflow_id)
        if builder is None:
            raise NotFoundError(resource_type="Workflow", identifier=workflow_id)
        return builder()

    def to_metadata_response(self, workflow: WorkflowDefinition) -> WorkflowMetadataResponse:
        """Convert an internal WorkflowDefinition into a safe discovery schema."""
        step_agent_ids = {s.agent_id for s in workflow.steps}

        required_inputs = ["project_id"]
        optional_inputs = ["snapshot_id", "snapshot_version", "options"]

        if "code-review" in step_agent_ids:
            optional_inputs.append("code_review_input")
        if "explainability-insights" in step_agent_ids:
            optional_inputs.extend(["explainability_target_scope", "explainability_user_query"])

        steps_metadata = [
            WorkflowStepMetadata(
                step_id=s.step_id,
                agent_id=s.agent_id,
                required=s.required,
                depends_on=s.depends_on,
                description=s.description,
            )
            for s in workflow.steps
        ]

        return WorkflowMetadataResponse(
            workflow_id=workflow.workflow_id,
            version=workflow.version,
            name=workflow.name,
            description=workflow.description,
            step_count=len(workflow.steps),
            steps=steps_metadata,
            required_inputs=required_inputs,
            optional_inputs=optional_inputs,
        )

    async def _resolve_context(
        self,
        project_id: uuid.UUID,
        snapshot_id: uuid.UUID | None = None,
        snapshot_version: int | None = None,
    ) -> tuple[ProjectContextResponse, Any | None, uuid.UUID | None, int | None]:
        """Resolve canonical ProjectContextResponse and provenance parameters.

        Returns:
            tuple of (canonical_context, snapshot_model, context_snapshot_id, context_version)
        """
        # 1. Verify target project exists (raises NotFoundError if invalid)
        await self.context_engine._get_project(project_id)

        # 2. Mutually exclusive check
        if snapshot_id is not None and snapshot_version is not None:
            raise ValidationError(
                message="Cannot specify both 'snapshot_id' and 'snapshot_version'. Provide at most one."
            )

        # 3. Snapshot by UUID
        if snapshot_id is not None:
            statement = select(ContextSnapshot).where(ContextSnapshot.id == snapshot_id)
            result = await self.session.execute(statement)
            snapshot = result.scalar_one_or_none()
            if not snapshot:
                raise NotFoundError(resource_type="ContextSnapshot", identifier=snapshot_id)

            if snapshot.project_id != project_id:
                raise ValidationError(
                    message=f"ContextSnapshot '{snapshot_id}' does not belong to project '{project_id}'."
                )

            context = ProjectContextResponse.model_validate(snapshot.context_data)
            return context, snapshot, snapshot.id, snapshot.version

        # 4. Snapshot by integer version
        if snapshot_version is not None:
            snapshot = await self.context_engine.get_snapshot_by_version(
                project_id=project_id, version=snapshot_version
            )
            context = ProjectContextResponse.model_validate(snapshot.context_data)
            return context, snapshot, snapshot.id, snapshot.version

        # 5. Live canonical context (Default)
        context = await self.context_engine.generate_context(project_id=project_id)
        return context, None, None, None

    async def execute_workflow(
        self,
        workflow_id: str,
        request: WorkflowExecuteRequest,
        preallocated_execution_id: uuid.UUID | None = None,
    ) -> WorkflowResult:
        """Resolve context, construct WorkflowInput, and delegate execution to coordinator.

        Lifecycle:
        1. Resolve canonical project context and provenance.
        2. Pre-generate workflow_execution_id correlation UUID.
        3. Create initial persistent WorkflowExecution record (status: RUNNING).
        4. Delegate to WorkflowCoordinator.
        5. Update WorkflowExecution record with terminal status, step counts, errors, and validated artifacts.
        6. Commit and return authoritative WorkflowResult.

        Args:
            workflow_id: Predefined workflow identifier.
            request: Validated API execution request payload.

        Returns:
            Authoritative WorkflowResult from WorkflowCoordinator.
        """
        workflow = self.get_workflow(workflow_id)

        # Concurrency & Duplicate Build Protection
        async with self._build_locks_mutex:
            if request.project_id in self._active_project_builds:
                target_project = await self.context_engine._get_project(request.project_id)
                raise ConflictError(
                    f"A build is already in progress for project '{target_project.name}'. Please wait for it to complete."
                )

            stmt_active_run = select(WorkflowExecution).where(
                WorkflowExecution.project_id == request.project_id,
                WorkflowExecution.status == WorkflowStatus.RUNNING,
            )
            res_active_run = await self.session.execute(stmt_active_run)
            active_run = None
            if hasattr(res_active_run, "scalars"):
                sc = res_active_run.scalars()
                if hasattr(sc, "first"):
                    first_val = sc.first()
                    active_run = await first_val if inspect.isawaitable(first_val) else first_val
            if active_run:
                target_project = await self.context_engine._get_project(request.project_id)
                raise ConflictError(
                    f"A build is already in progress for project '{target_project.name}'. Please wait for it to complete."
                )

            self._active_project_builds.add(request.project_id)

        try:
            context, snapshot, snapshot_id, snapshot_version = await self._resolve_context(
                project_id=request.project_id,
                snapshot_id=request.snapshot_id,
                snapshot_version=request.snapshot_version,
            )

            # Populate upstream artifacts from prior successful workflows (e.g. software-design-workflow)
            initial_artifacts: dict[str, Any] = {}
            stmt_prev = (
                select(WorkflowExecution)
                .where(
                    WorkflowExecution.project_id == request.project_id,
                    WorkflowExecution.status == WorkflowStatus.COMPLETED,
                )
                .order_by(WorkflowExecution.completed_at.desc())
            )
            prev_res = await self.session.execute(stmt_prev)
            prev_sc = prev_res.scalars() if hasattr(prev_res, "scalars") else None
            raw_prev_list = prev_sc.all() if hasattr(prev_sc, "all") else []
            prev_list = await raw_prev_list if inspect.isawaitable(raw_prev_list) else raw_prev_list
            for prev_exec in (prev_list or []):
                if prev_exec.workflow_id == workflow.workflow_id:
                    # Do not reuse deliverables from a previous run of the same workflow;
                    # a re-run of this workflow must execute its own steps freshly.
                    continue
                if prev_exec.artifacts:
                    for k, v in prev_exec.artifacts.items():
                        if k not in initial_artifacts:
                            initial_artifacts[k] = v

            workflow_input = WorkflowInput(
                context=context,
                code_review_input=request.code_review_input,
                explainability_target_scope=request.explainability_target_scope,
                explainability_user_query=request.explainability_user_query,
                options=request.options,
                initial_artifacts=initial_artifacts,
            )

            workflow_execution_id = preallocated_execution_id or uuid.uuid4()
            started_at = datetime.now(timezone.utc)

            # 3. Create persistent WorkflowExecution record in RUNNING state
            execution_record = WorkflowExecution(
                workflow_execution_id=workflow_execution_id,
                project_id=request.project_id,
                workflow_id=workflow.workflow_id,
                workflow_version=workflow.version,
                status=WorkflowStatus.RUNNING,
                context_snapshot_id=snapshot_id,
                context_version=snapshot_version,
                started_at=started_at,
                step_count=len(workflow.steps),
                completed_steps=0,
                failed_steps=0,
                skipped_steps=0,
                artifacts={},
                errors=[],
                warnings=[],
                metadata_payload={
                    "project_id": str(request.project_id),
                    "context_provenance": "snapshot" if snapshot_id or snapshot_version else "live",
                    "options": request.options,
                },
            )
            self.session.add(execution_record)
            await self.session.commit()
            await self.session.refresh(execution_record)

            logger.info(
                f"Invoking WorkflowCoordinator for [{workflow_id}] on project [{request.project_id}] "
                f"(snapshot_id={snapshot_id}, version={snapshot_version}) [exec_id={workflow_execution_id}]"
            )

            # 4. Delegate to WorkflowCoordinator with failure safety
            try:
                result = await self.coordinator.execute(
                    workflow=workflow,
                    workflow_input=workflow_input,
                    session=self.session,
                    snapshot=snapshot,
                    context_snapshot_id=snapshot_id,
                    context_version=snapshot_version,
                    workflow_execution_id=workflow_execution_id,
                )
            except Exception as exc:
                logger.exception(
                    f"Workflow execution [{workflow_id}] crashed unexpectedly "
                    f"[workflow_exec_id={workflow_execution_id}]: {exc}"
                )
                execution_record.status = WorkflowStatus.FAILED
                execution_record.completed_at = datetime.now(timezone.utc)
                execution_record.errors = [f"Unexpected execution failure: {str(exc)}"]
                try:
                    await self.session.commit()
                except Exception as commit_exc:
                    logger.error(f"Failed to record FAILED workflow status in DB: {commit_exc}")
                raise

            # 5. Serialize validated domain artifacts
            serialized_artifacts: dict[str, Any] = {}
            for k, v in result.artifacts.items():
                if hasattr(v, "model_dump"):
                    serialized_artifacts[k] = v.model_dump(mode="json")
                else:
                    serialized_artifacts[k] = v

            completed_count = sum(1 for s in result.step_results if s.status == WorkflowStepStatus.COMPLETED)
            failed_count = sum(1 for s in result.step_results if s.status == WorkflowStepStatus.FAILED)
            skipped_count = sum(1 for s in result.step_results if s.status == WorkflowStepStatus.SKIPPED)

            # 6. Update terminal execution state
            execution_record.status = result.status
            execution_record.completed_at = result.completed_at
            execution_record.completed_steps = completed_count
            execution_record.failed_steps = failed_count
            execution_record.skipped_steps = skipped_count
            execution_record.artifacts = serialized_artifacts
            execution_record.errors = result.errors
            execution_record.warnings = result.warnings
            execution_record.metadata_payload = {
                "project_id": str(request.project_id),
                "context_provenance": "snapshot" if snapshot_id or snapshot_version else "live",
                "total_steps": len(workflow.steps),
                "completed_steps": completed_count,
                "failed_steps": failed_count,
                "skipped_steps": skipped_count,
                "options": request.options,
            }

            await self.session.commit()
            await self.session.refresh(execution_record)

            # 7. Automatically register DevelopmentVersion for successful code generation
            if workflow.workflow_id == "code-generation-workflow" and result.status in (
                WorkflowStatus.COMPLETED,
                WorkflowStatus.PARTIAL_SUCCESS,
            ):
                has_code = "code-generation" in result.artifacts or "code_generation" in result.artifacts
                if has_code:
                    try:
                        from app.services.development_version_service import DevelopmentVersionService
                        dev_service = DevelopmentVersionService(self.session)
                        key = "code-generation" if "code-generation" in result.artifacts else "code_generation"
                        await dev_service.register_version_from_workflow(
                            project_id=request.project_id,
                            workflow_execution_id=workflow_execution_id,
                            artifact_key=key,
                            source_reason="INITIAL_GENERATION",
                        )
                    except Exception as reg_exc:
                        logger.warning(
                            f"Could not automatically register DevelopmentVersion for execution {workflow_execution_id}: {reg_exc}"
                        )

            return result
        finally:
            async with self._build_locks_mutex:
                self._active_project_builds.discard(request.project_id)


    async def list_project_workflow_history(
        self,
        project_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        workflow_id: str | None = None,
        status: WorkflowStatus | None = None,
    ) -> tuple[list[WorkflowExecution], int]:
        """Retrieve paginated workflow execution history for a specific project.

        Args:
            project_id: Target project UUID.
            limit: Maximum number of records to return.
            offset: Pagination offset.
            workflow_id: Optional filter by workflow definition ID.
            status: Optional filter by WorkflowStatus enum.

        Returns:
            tuple of (list[WorkflowExecution], total_count)
        """
        # 1. Verify target project exists (raises NotFoundError if invalid)
        await self.context_engine._get_project(project_id)

        # 2. Build filtered select query
        statement = select(WorkflowExecution).where(WorkflowExecution.project_id == project_id)
        if workflow_id:
            statement = statement.where(WorkflowExecution.workflow_id == workflow_id)
        if status:
            statement = statement.where(WorkflowExecution.status == status)

        # 3. Count total matching records
        count_stmt = select(func.count()).select_from(statement.subquery())
        total_res = await self.session.execute(count_stmt)
        total = total_res.scalar_one()

        # 4. Fetch ordered and paginated items (newest first, tie-break by execution UUID)
        paged_stmt = (
            statement.order_by(
                WorkflowExecution.started_at.desc(),
                WorkflowExecution.workflow_execution_id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(paged_stmt)
        records = list(result.scalars().all())

        return records, total

    async def get_workflow_execution(
        self,
        workflow_execution_id: uuid.UUID,
    ) -> WorkflowExecution:
        """Retrieve a persisted workflow execution by correlation UUID or raise NotFoundError.

        Args:
            workflow_execution_id: Workflow execution UUID.

        Returns:
            WorkflowExecution ORM entity.
        """
        statement = select(WorkflowExecution).where(
            WorkflowExecution.workflow_execution_id == workflow_execution_id
        )
        result = await self.session.execute(statement)
        execution = result.scalar_one_or_none()
        if execution is None:
            raise NotFoundError(
                resource_type="WorkflowExecution",
                identifier=workflow_execution_id,
            )
        return execution
