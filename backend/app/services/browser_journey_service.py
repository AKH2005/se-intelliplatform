"""Browser Journey Domain Service for Phase 11K (Stage 5).

Acts as the authoritative domain boundary between REST APIs / Assistant Engineering Actions
and the Stage 4 BrowserJourneyWorkflowOrchestrator.
Enforces project authorization, persistent WorkflowExecution lifecycle recording,
and strictly read-only result inspection.

INVARIANTS:
1. Never executes agents or LLMs directly (delegates strictly to BrowserJourneyWorkflowOrchestrator).
2. Never invokes Playwright, Docker, or shell commands directly.
3. Enforces project boundary isolation: cross-project lookups raise NotFoundError.
4. Read methods are strictly READ_ONLY (zero workflow execution, zero LLM calls).
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.browser.browser_testing_service import BrowserTestingService
from app.browser.journey.contracts import (
    BoundedRouteInfo,
    BrowserJourneyWorkflowResult,
    BrowserJourneyWorkflowStatus,
)
from app.browser.journey.orchestrator import BrowserJourneyWorkflowOrchestrator
from app.core.exceptions import NotFoundError, ValidationError
from app.models.project import Project
from app.models.workflow_execution import WorkflowExecution, WorkflowStatus
from app.schemas.browser_journeys import (
    BrowserJourneyWorkflowResponse,
    GenerateBrowserJourneysRequest,
)
from app.schemas.runtime import ApplicationRuntimeManifest
from app.services.context_engine import ProjectContextEngine
from app.services.development_version_service import DevelopmentVersionService
from app.services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)


class BrowserJourneyService:
    """Authoritative domain service for managing browser journey generation and execution runs."""

    def __init__(
        self,
        session: AsyncSession,
        context_engine: ProjectContextEngine,
        version_service: DevelopmentVersionService,
        browser_testing_service: BrowserTestingService,
        workflow_service: WorkflowService,
        orchestrator: BrowserJourneyWorkflowOrchestrator | None = None,
    ) -> None:
        self.session = session
        self.context_engine = context_engine
        self.version_service = version_service
        self.browser_testing_service = browser_testing_service
        self.workflow_service = workflow_service
        self._orchestrator = orchestrator

    async def _verify_project_exists(self, project_id: uuid.UUID) -> None:
        """Verify project exists in database or raise RFC 7807 NotFoundError."""
        stmt = select(Project.id).where(Project.id == project_id)
        res = await self.session.execute(stmt)
        if not res.scalar_one_or_none():
            raise NotFoundError("Project", str(project_id))

    def _get_orchestrator(self) -> BrowserJourneyWorkflowOrchestrator:
        """Retrieve injected orchestrator or construct standard domain instance."""
        if self._orchestrator:
            return self._orchestrator
        return BrowserJourneyWorkflowOrchestrator(
            coordinator=self.workflow_service.coordinator,
            browser_service=self.browser_testing_service,
            context_engine=self.context_engine,
        )

    async def generate_and_execute_journeys(
        self,
        project_id: uuid.UUID,
        version_id: uuid.UUID | None = None,
        execute_browser_tests: bool = True,
        max_journeys: int = 10,
        workflow_execution_id: uuid.UUID | None = None,
    ) -> BrowserJourneyWorkflowResult:
        """Execute Stage 4 workflow and persist the authoritative WorkflowExecution audit record.

        Args:
            project_id: Target project UUID.
            version_id: Optional specific development version UUID.
            execute_browser_tests: Whether to execute container browser smoke tests.
            max_journeys: Maximum candidate journeys (bounded).
            workflow_execution_id: Optional pre-allocated correlation UUID.

        Returns:
            Authoritative BrowserJourneyWorkflowResult.
        """
        await self._verify_project_exists(project_id)

        # 1. Resolve Target Version and Runtime Metadata
        target_version = None
        manifest: ApplicationRuntimeManifest | None = None
        routes: list[BoundedRouteInfo] = []
        file_manifest: list[str] = []

        if version_id:
            target_version = await self.version_service.get_version(project_id, version_id)
            if not target_version:
                raise NotFoundError("DevelopmentVersion", str(version_id))
        else:
            target_version = await self.version_service.get_active_version(project_id)
            if not target_version:
                version_list = await self.version_service.list_versions(project_id)
                if version_list.items:
                    target_version = version_list.items[-1]

        if target_version:
            raw_manifest = getattr(target_version, "runtime_manifest", None)
            if raw_manifest:
                try:
                    manifest = ApplicationRuntimeManifest.model_validate(raw_manifest)
                except Exception as m_err:
                    raise ValidationError(f"Invalid runtime manifest for version '{target_version.version_id}': {m_err}")
            else:
                manifest = await self.version_service.resolve_runtime_manifest(project_id, target_version.version_id)
            if target_version.files_manifest:
                file_manifest = [f.path for f in target_version.files_manifest]

        # 2. Build Canonical Project Context
        context = await self.context_engine.generate_context(project_id)

        # 3. Create persistent WorkflowExecution record in RUNNING state
        exec_id = workflow_execution_id or uuid.uuid4()
        started_at = datetime.now(timezone.utc)

        execution_record = WorkflowExecution(
            workflow_execution_id=exec_id,
            project_id=project_id,
            workflow_id="browser-journey-workflow",
            workflow_version="1.0.0",
            status=WorkflowStatus.RUNNING,
            context_snapshot_id=None,
            context_version=None,
            started_at=started_at,
            step_count=1,
            completed_steps=0,
            failed_steps=0,
            skipped_steps=0,
            artifacts={},
            errors=[],
            warnings=[],
            metadata_payload={
                "project_id": str(project_id),
                "version_id": str(target_version.version_id) if target_version else None,
                "version_number": target_version.version_number if target_version else None,
                "workflow_id": "browser-journey-workflow",
            },
        )
        self.session.add(execution_record)
        await self.session.commit()
        await self.session.refresh(execution_record)

        # 4. Invoke Stage 4 Orchestrator
        orchestrator = self._get_orchestrator()
        generation_input = orchestrator.build_generation_input(
            context=context,
            authoritative_routes=routes or None,
            runtime_manifest=manifest,
            development_version_id=target_version.version_id if target_version else None,
            version_number=target_version.version_number if target_version else None,
            max_journeys=max_journeys,
            file_manifest=file_manifest,
        )
        try:
            result = await orchestrator.execute_workflow(
                context=context,
                generation_input=generation_input,
                authoritative_routes=routes or None,
                runtime_manifest=manifest,
                execute_browser_tests=execute_browser_tests,
                workflow_execution_id=exec_id,
                session=self.session,
            )
        except Exception as unhandled_err:
            logger.error(
                f"Unhandled exception in BrowserJourneyWorkflowOrchestrator for project [{project_id}]: {unhandled_err}",
                exc_info=True,
            )
            execution_record.status = WorkflowStatus.FAILED
            execution_record.completed_at = datetime.now(timezone.utc)
            execution_record.errors = [str(unhandled_err)]
            await self.session.commit()
            raise

        # 5. Persist Terminal Outcome to WorkflowExecution
        execution_record.status = (
            WorkflowStatus.COMPLETED
            if result.status == BrowserJourneyWorkflowStatus.COMPLETED
            else WorkflowStatus.FAILED
        )
        execution_record.completed_at = result.completed_at
        execution_record.artifacts = result.artifacts
        execution_record.errors = result.errors
        execution_record.metadata_payload = {
            "project_id": str(project_id),
            "version_id": str(target_version.version_id) if target_version else None,
            "version_number": target_version.version_number if target_version else None,
            "workflow_status": result.status.value,
            "stage_reached": result.stage_reached,
            "journey_count": len(result.candidate_suite.journeys) if result.candidate_suite else 0,
            "validation_passed": result.validation_outcome.is_valid if result.validation_outcome else False,
            "coverage_percentage": result.coverage_report.coverage_percentage if result.coverage_report else None,
            "covered_requirement_ids": result.coverage_report.covered_requirement_ids if result.coverage_report else [],
            "uncovered_requirement_ids": result.coverage_report.uncovered_requirement_ids if result.coverage_report else [],
            "test_definitions_count": len(result.test_definitions) if result.test_definitions else 0,
            "browser_tests_executed": result.browser_test_run is not None,
            "duration_seconds": result.duration_seconds,
        }

        await self.session.commit()
        await self.session.refresh(execution_record)

        return result

    async def get_workflow_result(
        self,
        project_id: uuid.UUID,
        workflow_execution_id: uuid.UUID,
    ) -> WorkflowExecution:
        """Retrieve persisted WorkflowExecution audit record with strict project isolation.

        Raises:
            NotFoundError: If the execution does not exist OR belongs to another project.
        """
        await self._verify_project_exists(project_id)

        stmt = select(WorkflowExecution).where(
            WorkflowExecution.workflow_execution_id == workflow_execution_id,
            WorkflowExecution.project_id == project_id,
        )
        res = await self.session.execute(stmt)
        record = res.scalar_one_or_none()

        if not record:
            raise NotFoundError("BrowserJourneyWorkflow", str(workflow_execution_id))

        return record

    async def get_latest_workflow_result(
        self,
        project_id: uuid.UUID,
    ) -> WorkflowExecution:
        """Retrieve the most recent browser journey workflow execution for the project.

        Raises:
            NotFoundError: If no browser journey executions exist for this project.
        """
        await self._verify_project_exists(project_id)

        stmt = (
            select(WorkflowExecution)
            .where(
                WorkflowExecution.project_id == project_id,
                WorkflowExecution.workflow_id == "browser-journey-workflow",
            )
            .order_by(
                WorkflowExecution.started_at.desc(),
                WorkflowExecution.workflow_execution_id.desc(),
            )
            .limit(1)
        )
        res = await self.session.execute(stmt)
        record = res.scalar_one_or_none()

        if not record:
            raise NotFoundError(
                "BrowserJourneyWorkflow",
                f"No browser journey workflow executions found for project {project_id}.",
            )

        return record

    async def list_workflow_results(
        self,
        project_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[WorkflowExecution], int]:
        """List paginated browser journey workflow executions for a project."""
        await self._verify_project_exists(project_id)

        base_stmt = select(WorkflowExecution).where(
            WorkflowExecution.project_id == project_id,
            WorkflowExecution.workflow_id == "browser-journey-workflow",
        )

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        paged_stmt = (
            base_stmt.order_by(
                WorkflowExecution.started_at.desc(),
                WorkflowExecution.workflow_execution_id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        records = list((await self.session.execute(paged_stmt)).scalars().all())

        return records, total
