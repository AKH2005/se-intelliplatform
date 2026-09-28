"""Workflow Service Layer.

Provides application-level coordination between HTTP API endpoints,
canonical ProjectContextEngine state resolution, and the deterministic
WorkflowCoordinator engine.
"""

import logging
import uuid
from collections.abc import Callable
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.context_snapshot import ContextSnapshot
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
)
from app.workflows.coordinator import WorkflowCoordinator
from app.workflows.pipelines import (
    WORKFLOW_COMPREHENSIVE_AUDIT_ID,
    WORKFLOW_PROJECT_ESTIMATION_ID,
    WORKFLOW_SOFTWARE_DESIGN_ID,
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

    def __init__(
        self,
        session: AsyncSession,
        context_engine: ProjectContextEngine,
        coordinator: WorkflowCoordinator,
    ) -> None:
        self.session = session
        self.context_engine = context_engine
        self.coordinator = coordinator

    def list_workflows(self) -> list[WorkflowDefinition]:
        """Return all registered predefined workflow definitions in deterministic order."""
        return [builder() for builder in self.PREDEFINED_WORKFLOWS.values()]

    def get_workflow(self, workflow_id: str) -> WorkflowDefinition:
        """Retrieve a specific predefined workflow definition by ID or raise NotFoundError."""
        builder = self.PREDEFINED_WORKFLOWS.get(workflow_id)
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
    ) -> WorkflowResult:
        """Resolve context, construct WorkflowInput, and delegate execution to coordinator.

        Args:
            workflow_id: Predefined workflow identifier.
            request: Validated API execution request payload.

        Returns:
            Authoritative WorkflowResult from WorkflowCoordinator.
        """
        workflow = self.get_workflow(workflow_id)

        context, snapshot, snapshot_id, snapshot_version = await self._resolve_context(
            project_id=request.project_id,
            snapshot_id=request.snapshot_id,
            snapshot_version=request.snapshot_version,
        )

        workflow_input = WorkflowInput(
            context=context,
            code_review_input=request.code_review_input,
            explainability_target_scope=request.explainability_target_scope,
            explainability_user_query=request.explainability_user_query,
            options=request.options,
        )

        logger.info(
            f"Invoking WorkflowCoordinator for [{workflow_id}] on project [{request.project_id}] "
            f"(snapshot_id={snapshot_id}, version={snapshot_version})"
        )

        result = await self.coordinator.execute(
            workflow=workflow,
            workflow_input=workflow_input,
            session=self.session,
            snapshot=snapshot,
            context_snapshot_id=snapshot_id,
            context_version=snapshot_version,
        )

        return result
