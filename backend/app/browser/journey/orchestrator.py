"""Intelligent Browser Journey Generation Orchestrator (Phase 11K - Stage 4).

Connects the validated browser journey components into an authoritative, deterministic
platform workflow:

    Authoritative Project Context
            │
            ▼
    BrowserJourneyGenerationInput
            │
            ▼
    WorkflowCoordinator
            │
            ▼
    AgentExecutor
            │
            ▼
    BrowserJourneyGenerationAgent
            │
            ▼
    BrowserJourneySuiteCandidate
            │
            ▼
    BrowserJourneyValidator
            │
            ├── FAIL → WORKFLOW_VALIDATION_FAILED (execution stops)
            │
            ▼
    ValidatedBrowserJourneySuite
            │
            ▼
    BrowserJourneyAdapter
            │
            ├── FAIL → WORKFLOW_ADAPTATION_FAILED (execution stops)
            │
            ▼
    DeterministicBrowserTestDefinition[]
            │
            ▼
    BrowserTestingService
            │
            ▼
    Phase 11J Isolated Browser Container Runtime
            │
            ▼
    BrowserTestRun
            │
            ├── FAIL → WORKFLOW_BROWSER_EXECUTION_FAILED (optional FailureAnalysisAgent)
            │
            ▼
    WorkflowExecution Artifacts (Full Traceability Chain Preserved)

ARCHITECTURAL INVARIANTS:
1. AgentExecutor remains the sole single-agent execution authority.
2. WorkflowCoordinator remains the sole multi-agent coordination authority.
3. BrowserTestingService remains the sole browser test execution authority.
4. Unvalidated candidates NEVER reach the adapter or BrowserTestingService.
5. Zero raw Playwright/Python/JS code generation.
6. Zero direct LLM provider calls (Groq/Gemini called strictly via AgentExecutor).
7. Zero direct Docker/Playwright execution in this orchestrator.
8. Zero automatic remediation or repair loops.
9. Zero DevelopmentVersion mutation.
"""

import logging
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.contracts import AgentExecutionStatus, AgentResult
from app.agents.failure_analysis.agent import FailureAnalysisAgent
from app.agents.failure_analysis.contracts import FailureDiagnosis
from app.agents.browser_journey.contracts import (
    BoundedRequirementInfo,
    BoundedRouteInfo,
    BrowserJourneyGenerationInput,
    BrowserJourneySuiteCandidate,
    JourneyCategory,
    MAX_JOURNEYS_PER_SUITE,
)
from app.browser.contracts import (
    BrowserLimits,
    DeterministicBrowserTestDefinition,
)
from app.browser.browser_testing_service import BrowserTestingService
from app.browser.journey.adapter import BrowserJourneyAdapter
from app.browser.journey.contracts import (
    BrowserJourneyWorkflowResult,
    BrowserJourneyWorkflowStatus,
    ValidatedBrowserJourneySuite,
    ValidationContext,
    ValidationOutcome,
)
from app.browser.journey.errors import BrowserJourneyAdaptationError
from app.browser.journey.validator import BrowserJourneyValidator
from app.schemas.browser_testing import BrowserTestRun, BrowserTestStatus
from app.schemas.context import ProjectContextResponse
from app.schemas.runtime import ApplicationRuntimeManifest
from app.workflows.contracts import WorkflowInput, WorkflowStatus
from app.workflows.coordinator import WorkflowCoordinator
from app.workflows.pipelines import build_browser_journey_workflow

logger = logging.getLogger(__name__)


class BrowserJourneyWorkflowOrchestrator:
    """Deterministic orchestrator for AI-powered browser user journey workflows."""

    def __init__(
        self,
        coordinator: WorkflowCoordinator,
        browser_service: BrowserTestingService | None = None,
        failure_analysis_agent: FailureAnalysisAgent | None = None,
        context_engine: Any = None,
    ) -> None:
        self.coordinator = coordinator
        self.browser_service = browser_service or BrowserTestingService()
        self.failure_analysis_agent = failure_analysis_agent
        self.context_engine = context_engine

    @classmethod
    def build_generation_input(
        cls,
        context: ProjectContextResponse,
        authoritative_routes: list[str] | list[BoundedRouteInfo] | None = None,
        runtime_manifest: ApplicationRuntimeManifest | None = None,
        development_version_id: uuid.UUID | None = None,
        version_number: int | None = None,
        max_journeys: int = 5,
        target_categories: list[JourneyCategory] | None = None,
        file_manifest: list[str] | None = None,
        architecture_components: list[str] | None = None,
    ) -> BrowserJourneyGenerationInput:
        """Construct authoritative, bounded generation input from canonical ProjectContextResponse.

        Extracts ONLY active requirements and discovered/declared routes.
        Sanitizes file manifests to exclude secrets, credentials, environment files, and binaries.
        """
        # 1. Bounded active requirements
        req_infos: list[BoundedRequirementInfo] = []
        if context.requirements:
            for r in context.requirements:
                is_arch = getattr(r, "is_archived", False)
                status = getattr(r, "status", None)
                status_val = status.value if hasattr(status, "value") else str(status)

                # Only include active, actionable requirements
                if not is_arch and status_val in {"DRAFT", "APPROVED", "IMPLEMENTED"}:
                    cat_val = None
                    if hasattr(r, "category") and r.category:
                        cat_val = r.category.value if hasattr(r.category, "value") else str(r.category)
                    req_infos.append(
                        BoundedRequirementInfo(
                            id=str(r.id),
                            title=getattr(r, "title", f"Requirement {r.id}"),
                            description=getattr(r, "description", "") or "",
                            category=cat_val,
                        )
                    )

        # 2. Normalized application routes
        route_infos: list[BoundedRouteInfo] = []
        seen_paths: set[str] = set()

        if authoritative_routes:
            for r in authoritative_routes:
                if isinstance(r, BoundedRouteInfo):
                    if r.path not in seen_paths:
                        route_infos.append(r)
                        seen_paths.add(r.path)
                elif isinstance(r, str):
                    clean_path = r.strip()
                    if clean_path:
                        if not clean_path.startswith("/"):
                            clean_path = "/" + clean_path
                        if clean_path not in seen_paths:
                            route_infos.append(BoundedRouteInfo(path=clean_path, method="GET"))
                            seen_paths.add(clean_path)

        if runtime_manifest:
            if runtime_manifest.health_check_path and runtime_manifest.health_check_path not in seen_paths:
                route_infos.append(BoundedRouteInfo(path=runtime_manifest.health_check_path, method="GET", name="Health Check"))
                seen_paths.add(runtime_manifest.health_check_path)
            for default_p in ["/", "/docs", "/openapi.json"]:
                if default_p not in seen_paths:
                    route_infos.append(BoundedRouteInfo(path=default_p, method="GET"))
                    seen_paths.add(default_p)

        if not route_infos:
            route_infos.append(BoundedRouteInfo(path="/", method="GET", name="Root", description="Default root route"))

        # 3. Architecture components
        arch_comps: list[str] = []
        if architecture_components:
            arch_comps = [str(c) for c in architecture_components[:20]]
        elif hasattr(context, "architecture") and getattr(context, "architecture", None):
            arch_obj = context.architecture
            if hasattr(arch_obj, "components") and isinstance(arch_obj.components, list):
                arch_comps = [c.name for c in arch_obj.components if hasattr(c, "name")][:20]

        # 4. Sanitized file manifest (no secrets, .env, binaries, traversal)
        clean_files: list[str] = []
        if file_manifest:
            for f in file_manifest:
                fn = f.strip().replace("\\", "/")
                # Defensive exclusion of sensitive patterns
                if any(bad in fn.lower() for bad in (".env", "secret", "password", "key", "token", "credential")):
                    continue
                if any(fn.lower().endswith(ext) for ext in (".pyc", ".png", ".jpg", ".webp", ".so", ".bin")):
                    continue
                if ".." in fn:
                    continue
                clean_files.append(fn)
                if len(clean_files) >= 50:
                    break

        bounded_max_journeys = min(max(int(max_journeys), 1), MAX_JOURNEYS_PER_SUITE)
        categories = target_categories or list(JourneyCategory)

        return BrowserJourneyGenerationInput(
            project_id=context.project.id,
            project_name=getattr(context.project, "name", "Application Under Test"),
            development_version_id=development_version_id,
            version_number=version_number,
            requirements=req_infos,
            routes=route_infos,
            architecture_components=arch_comps,
            file_manifest=clean_files,
            max_journeys=bounded_max_journeys,
            target_categories=categories,
        )

    async def execute_workflow(
        self,
        context: ProjectContextResponse,
        generation_input: BrowserJourneyGenerationInput | None = None,
        authoritative_routes: list[str] | list[BoundedRouteInfo] | None = None,
        runtime_manifest: ApplicationRuntimeManifest | None = None,
        files_map: dict[str, str] | None = None,
        limits: BrowserLimits | None = None,
        execute_browser_tests: bool = True,
        workflow_execution_id: uuid.UUID | None = None,
        session: AsyncSession | None = None,
    ) -> BrowserJourneyWorkflowResult:
        """Execute the end-to-end Browser Journey Generation and Testing Workflow.

        Pipeline Stages:
        1. Context & Input Preparation
        2. Generation (via WorkflowCoordinator -> AgentExecutor -> BrowserJourneyGenerationAgent)
        3. Deterministic Validation (BrowserJourneyValidator)
        4. Deterministic Adaptation (BrowserJourneyAdapter)
        5. Browser Testing Execution (BrowserTestingService via isolated Playwright container)
        6. Outcome Analysis & Traceability (FailureAnalysisAgent if browser tests fail)
        """
        workflow_execution_id = workflow_execution_id or uuid.uuid4()
        started_at = datetime.now(timezone.utc)
        start_time = time.monotonic()
        project_id = context.project.id

        artifacts: dict[str, Any] = {}
        errors: list[str] = []

        logger.info(
            f"Commencing Browser Journey Workflow for project [{project_id}] "
            f"[workflow_execution_id={workflow_execution_id}]"
        )

        # ----------------------------------------------------------------------
        # STAGE 1: Build Authoritative Generation Input
        # ----------------------------------------------------------------------
        if generation_input is None:
            generation_input = self.build_generation_input(
                context=context,
                authoritative_routes=authoritative_routes,
                runtime_manifest=runtime_manifest,
            )
        artifacts["browser_journey_input"] = generation_input.model_dump(mode="json")

        # ----------------------------------------------------------------------
        # STAGE 2: Execute Generation via WorkflowCoordinator -> AgentExecutor
        # ----------------------------------------------------------------------
        wf_input = WorkflowInput(
            context=context,
            browser_journey_input=generation_input,
        )
        wf_def = build_browser_journey_workflow()

        wf_result = await self.coordinator.execute(
            workflow=wf_def,
            workflow_input=wf_input,
            session=session,
            workflow_execution_id=workflow_execution_id,
        )

        if wf_result.status != WorkflowStatus.COMPLETED:
            err_msg = wf_result.errors[0] if wf_result.errors else "Browser journey generation failed."
            errors.extend(wf_result.errors or [err_msg])
            duration = round(time.monotonic() - start_time, 3)
            logger.warning(
                f"Browser journey generation failed for project [{project_id}]: {err_msg}"
            )
            return BrowserJourneyWorkflowResult(
                workflow_execution_id=workflow_execution_id,
                project_id=project_id,
                status=BrowserJourneyWorkflowStatus.GENERATION_FAILED,
                stage_reached="generation",
                generation_input=generation_input,
                error_message=err_msg,
                errors=errors,
                artifacts=artifacts,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                duration_seconds=duration,
            )

        candidate = wf_result.artifacts.get("browser-journey-generation")
        if candidate is None or not isinstance(candidate, BrowserJourneySuiteCandidate):
            err_msg = "No valid BrowserJourneySuiteCandidate produced by generation agent."
            errors.append(err_msg)
            duration = round(time.monotonic() - start_time, 3)
            return BrowserJourneyWorkflowResult(
                workflow_execution_id=workflow_execution_id,
                project_id=project_id,
                status=BrowserJourneyWorkflowStatus.GENERATION_FAILED,
                stage_reached="generation",
                generation_input=generation_input,
                error_message=err_msg,
                errors=errors,
                artifacts=artifacts,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                duration_seconds=duration,
            )

        artifacts["browser_journey_generation"] = candidate.model_dump(mode="json")

        # ----------------------------------------------------------------------
        # STAGE 3: Deterministic Validation Gate (BrowserJourneyValidator)
        # ----------------------------------------------------------------------
        val_context = ValidationContext.from_project_context(
            context=context,
            authoritative_routes=authoritative_routes or [r.path for r in generation_input.routes],
            runtime_manifest=runtime_manifest,
        )
        validated_suite, outcome = BrowserJourneyValidator.validate(candidate, val_context)
        artifacts["browser_journey_validation"] = outcome.model_dump(mode="json")

        if not outcome.is_valid or validated_suite is None:
            err_msg = f"Browser journey validation failed with {len(outcome.errors)} error(s)."
            errors.extend(outcome.error_messages or [err_msg])
            duration = round(time.monotonic() - start_time, 3)
            logger.warning(
                f"Browser journey validation gate blocked execution for project [{project_id}]: {outcome.error_messages}"
            )
            return BrowserJourneyWorkflowResult(
                workflow_execution_id=workflow_execution_id,
                project_id=project_id,
                status=BrowserJourneyWorkflowStatus.VALIDATION_FAILED,
                stage_reached="validation",
                generation_input=generation_input,
                candidate_suite=candidate,
                validation_outcome=outcome,
                error_message=err_msg,
                errors=errors,
                artifacts=artifacts,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                duration_seconds=duration,
            )

        artifacts["browser_journey_suite"] = validated_suite.model_dump(mode="json")

        # ----------------------------------------------------------------------
        # STAGE 4: Deterministic Adaptation (BrowserJourneyAdapter)
        # ----------------------------------------------------------------------
        try:
            test_definitions = BrowserJourneyAdapter.adapt(validated_suite)
        except (BrowserJourneyAdaptationError, ValueError, TypeError) as adapt_err:
            err_msg = f"Browser journey adaptation failed: {adapt_err}"
            errors.append(err_msg)
            duration = round(time.monotonic() - start_time, 3)
            logger.error(f"Browser journey adaptation error for project [{project_id}]: {adapt_err}")
            return BrowserJourneyWorkflowResult(
                workflow_execution_id=workflow_execution_id,
                project_id=project_id,
                status=BrowserJourneyWorkflowStatus.ADAPTATION_FAILED,
                stage_reached="adaptation",
                generation_input=generation_input,
                candidate_suite=candidate,
                validation_outcome=outcome,
                validated_suite=validated_suite,
                coverage_report=validated_suite.coverage_report,
                error_message=err_msg,
                errors=errors,
                artifacts=artifacts,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                duration_seconds=duration,
            )

        # If browser container execution was not requested (e.g. generate-and-validate only)
        if not execute_browser_tests:
            duration = round(time.monotonic() - start_time, 3)
            return BrowserJourneyWorkflowResult(
                workflow_execution_id=workflow_execution_id,
                project_id=project_id,
                status=BrowserJourneyWorkflowStatus.COMPLETED,
                stage_reached="adaptation",
                generation_input=generation_input,
                candidate_suite=candidate,
                validation_outcome=outcome,
                validated_suite=validated_suite,
                coverage_report=validated_suite.coverage_report,
                test_definitions=test_definitions,
                artifacts=artifacts,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                duration_seconds=duration,
            )

        # ----------------------------------------------------------------------
        # STAGE 5: Browser Container Execution (BrowserTestingService)
        # ----------------------------------------------------------------------
        try:
            browser_test_run = await self.browser_service.execute_validated_browser_journey_suite(
                suite=validated_suite,
                limits=limits,
                files_map=files_map,
                manifest=runtime_manifest,
                version_id=generation_input.development_version_id,
            )
            artifacts["browser_test_run"] = browser_test_run.model_dump(mode="json")
        except Exception as exec_err:
            err_msg = f"Browser container execution failed with exception: {exec_err}"
            errors.append(err_msg)
            duration = round(time.monotonic() - start_time, 3)
            logger.exception(f"Unexpected browser execution failure for project [{project_id}]: {exec_err}")
            return BrowserJourneyWorkflowResult(
                workflow_execution_id=workflow_execution_id,
                project_id=project_id,
                status=BrowserJourneyWorkflowStatus.BROWSER_EXECUTION_FAILED,
                stage_reached="browser_execution",
                generation_input=generation_input,
                candidate_suite=candidate,
                validation_outcome=outcome,
                validated_suite=validated_suite,
                coverage_report=validated_suite.coverage_report,
                test_definitions=test_definitions,
                error_message=err_msg,
                errors=errors,
                artifacts=artifacts,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                duration_seconds=duration,
            )

        # ----------------------------------------------------------------------
        # STAGE 6: Outcome Evaluation & Failure Analysis Integration
        # ----------------------------------------------------------------------
        is_browser_pass = (
            browser_test_run.status == BrowserTestStatus.PASSED
            and getattr(browser_test_run, "tests_failed", 0) == 0
        )

        failure_diagnosis: FailureDiagnosis | None = None

        if not is_browser_pass:
            # Trigger FailureAnalysisAgent if available
            if self.failure_analysis_agent and hasattr(self.coordinator, "executor"):
                try:
                    fa_result = await self.coordinator.executor.execute(
                        agent=self.failure_analysis_agent,
                        context=context,
                        session=session,
                        browser_test_run=browser_test_run,
                        failure_source="BROWSER_TEST",
                        workflow_execution_id=workflow_execution_id,
                    )
                    if fa_result.status == AgentExecutionStatus.COMPLETED and fa_result.output:
                        failure_diagnosis = fa_result.output
                        artifacts["failure_analysis"] = failure_diagnosis.model_dump()
                except Exception as fa_err:
                    logger.warning(
                        f"FailureAnalysisAgent encountered advisory exception on browser failure: {fa_err}"
                    )

            err_msg = (
                browser_test_run.failure_reason
                or browser_test_run.summary
                or "Browser test run failed."
            )
            errors.append(err_msg)
            duration = round(time.monotonic() - start_time, 3)

            return BrowserJourneyWorkflowResult(
                workflow_execution_id=workflow_execution_id,
                project_id=project_id,
                status=BrowserJourneyWorkflowStatus.BROWSER_EXECUTION_FAILED,
                stage_reached="browser_execution",
                generation_input=generation_input,
                candidate_suite=candidate,
                validation_outcome=outcome,
                validated_suite=validated_suite,
                coverage_report=validated_suite.coverage_report,
                test_definitions=test_definitions,
                browser_test_run=browser_test_run,
                failure_diagnosis=failure_diagnosis,
                error_message=err_msg,
                errors=errors,
                artifacts=artifacts,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                duration_seconds=duration,
            )

        # ----------------------------------------------------------------------
        # STAGE 7: Terminal Success
        # ----------------------------------------------------------------------
        duration = round(time.monotonic() - start_time, 3)
        logger.info(
            f"Browser Journey Workflow completed successfully for project [{project_id}] in {duration}s"
        )

        return BrowserJourneyWorkflowResult(
            workflow_execution_id=workflow_execution_id,
            project_id=project_id,
            status=BrowserJourneyWorkflowStatus.COMPLETED,
            stage_reached="completed",
            generation_input=generation_input,
            candidate_suite=candidate,
            validation_outcome=outcome,
            validated_suite=validated_suite,
            coverage_report=validated_suite.coverage_report,
            test_definitions=test_definitions,
            browser_test_run=browser_test_run,
            failure_diagnosis=None,
            artifacts=artifacts,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            duration_seconds=duration,
        )
