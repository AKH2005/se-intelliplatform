"""Testing, Multi-Tier Coverage Intelligence, and Selective Regression REST Endpoints (Phase 11L Stage 6).

Exposes:
- GET  /projects/{project_id}/testing/inventory
- GET  /projects/{project_id}/testing/coverage
- GET  /projects/{project_id}/testing/coverage/gaps
- POST /projects/{project_id}/testing/impact
- POST /projects/{project_id}/testing/regression/plan
- POST /projects/{project_id}/testing/regression/execute
"""

import logging
from typing import Annotated, Any
import uuid
from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_change_impact_service,
    get_db,
    get_development_version_service,
    get_regression_execution_service,
    get_requirement_service,
    get_selective_regression_planner,
    get_unified_test_inventory_service,
)
from app.core.exceptions import ApplicationError, ConflictError, NotFoundError, ValidationError
from app.models.project import Project
from app.models.workflow_execution import WorkflowExecution, WorkflowStatus
from app.schemas.testing import (
    ChangeImpactRequest,
    CoverageGapItem,
    CoverageGapsResponse,
    ExecuteRegressionRequest,
    PlanRegressionRequest,
)
from app.services.development_version_service import DevelopmentVersionService
from app.services.requirement_service import RequirementService
from app.testing.coverage.contracts import UnifiedCoverageReport
from app.testing.coverage.engine import UnifiedCoverageEngine
from app.testing.coverage.errors import (
    UnifiedCoverageError,
    UnifiedCoverageIsolationError,
    UnifiedCoverageValidationError,
)
from app.testing.impact.contracts import ChangeImpactReport
from app.testing.impact.errors import (
    ChangeImpactError,
    ChangeImpactIsolationError,
    ChangeImpactValidationError,
)
from app.testing.impact.service import ChangeImpactService
from app.testing.inventory.contracts import UnifiedTestInventory
from app.testing.inventory.errors import (
    UnifiedTestInventoryConflictError,
    UnifiedTestInventoryError,
    UnifiedTestInventoryIsolationError,
    UnifiedTestInventoryValidationError,
)
from app.testing.inventory.service import UnifiedTestInventoryService
from app.testing.regression.contracts import (
    RegressionExecutionResult,
    RegressionPlan,
)
from app.testing.regression.errors import (
    RegressionExecutionError,
    RegressionExecutionSafetyError,
    RegressionPlanError,
    RegressionPlanIsolationError,
    RegressionPlanValidationError,
)
from app.testing.regression.executor import RegressionExecutionService
from app.testing.regression.planner import SelectiveRegressionPlanner
from app.testing.regression.validator import RegressionPlanValidator

logger = logging.getLogger(__name__)

router = APIRouter()


async def _verify_project(session: AsyncSession, project_id: uuid.UUID) -> Project:
    """Verify project exists in DB or raise NotFoundError."""
    stmt = select(Project).where(Project.id == project_id)
    res = await session.execute(stmt)
    proj = res.scalar_one_or_none()
    if not proj:
        raise NotFoundError("Project", str(project_id))
    return proj


async def _resolve_project_test_inputs(
    session: AsyncSession,
    project_id: uuid.UUID,
    version_service: DevelopmentVersionService,
    version_id: uuid.UUID | None = None,
    explicit_files_map: dict[str, str] | None = None,
) -> tuple[dict[str, str], Any, Any, Any, Any]:
    """Resolve files_map and auxiliary tier suites from development version or artifacts."""
    files_map: dict[str, str] = dict(explicit_files_map or {})
    ai_test_suite = None
    smoke_tests = None
    journey_suite = None
    resolved_version = None

    if version_id:
        resolved_version = await version_service.get_version(project_id, version_id)
    else:
        resolved_version = await version_service.get_active_version(project_id)

    if resolved_version:
        # Load files map from version if not explicitly supplied
        if not files_map:
            # Look up version entity
            from app.models.development_version import DevelopmentVersion
            stmt_v = select(DevelopmentVersion).where(
                DevelopmentVersion.id == resolved_version.version_id,
                DevelopmentVersion.project_id == project_id,
            )
            v_res = await session.execute(stmt_v)
            v_entity = v_res.scalar_one_or_none()
            if v_entity:
                files_map = await version_service._resolve_version_files_map(v_entity)

        # Inspect workflow execution artifacts for AI test suite, smoke tests, journeys
        if resolved_version.workflow_execution_id:
            stmt_wf = select(WorkflowExecution).where(
                WorkflowExecution.workflow_execution_id == resolved_version.workflow_execution_id,
                WorkflowExecution.project_id == project_id,
            )
            wf_res = await session.execute(stmt_wf)
            wf = wf_res.scalar_one_or_none()
            if wf and wf.artifacts:
                if "ai_test_suite" in wf.artifacts:
                    from app.agents.test_generation.contracts import AITestSuite
                    try:
                        ai_test_suite = AITestSuite.model_validate(wf.artifacts["ai_test_suite"])
                    except Exception as e:
                        logger.warning(f"Could not parse ai_test_suite artifact: {e}")

                if "browser_test_definitions" in wf.artifacts:
                    from app.browser.contracts import DeterministicBrowserTestDefinition
                    try:
                        smoke_tests = [
                            DeterministicBrowserTestDefinition.model_validate(item)
                            for item in wf.artifacts["browser_test_definitions"]
                        ]
                    except Exception as e:
                        logger.warning(f"Could not parse browser_test_definitions: {e}")

                if "validated_journey_suite" in wf.artifacts:
                    from app.browser.journey.contracts import ValidatedBrowserJourneySuite
                    try:
                        journey_suite = ValidatedBrowserJourneySuite.model_validate(
                            wf.artifacts["validated_journey_suite"]
                        )
                    except Exception as e:
                        logger.warning(f"Could not parse validated_journey_suite: {e}")

    # Fallback for journey_suite: check latest completed browser-journey-workflow
    if journey_suite is None:
        stmt_j = (
            select(WorkflowExecution)
            .where(
                WorkflowExecution.project_id == project_id,
                WorkflowExecution.workflow_id == "browser-journey-workflow",
                WorkflowExecution.status == WorkflowStatus.COMPLETED,
            )
            .order_by(WorkflowExecution.started_at.desc())
        )
        j_res = await session.execute(stmt_j)
        latest_j_wf = j_res.scalars().first()
        if latest_j_wf and latest_j_wf.artifacts and "validated_journey_suite" in latest_j_wf.artifacts:
            from app.browser.journey.contracts import ValidatedBrowserJourneySuite
            try:
                journey_suite = ValidatedBrowserJourneySuite.model_validate(
                    latest_j_wf.artifacts["validated_journey_suite"]
                )
            except Exception as e:
                logger.warning(f"Could not parse validated_journey_suite from workflow: {e}")

    return files_map, ai_test_suite, smoke_tests, journey_suite, resolved_version


# =============================================================================
# A. TEST INVENTORY
# =============================================================================

@router.get(
    "/inventory",
    response_model=UnifiedTestInventory,
    status_code=status.HTTP_200_OK,
    summary="Get authoritative Unified Test Inventory",
    description=(
        "Returns the complete normalized test catalog across all four platform tiers "
        "(UNIT, AI_TEST, BROWSER_SMOKE, BROWSER_JOURNEY) with bidirectional requirement traceability."
    ),
)
async def get_test_inventory(
    project_id: Annotated[uuid.UUID, Path(description="Canonical project UUID")],
    version_id: Annotated[uuid.UUID | None, Query(description="Optional development version UUID")] = None,
    strict: Annotated[bool, Query(description="Strict collision detection flag")] = True,
    session: AsyncSession = Depends(get_db),
    version_service: DevelopmentVersionService = Depends(get_development_version_service),
    inventory_service: UnifiedTestInventoryService = Depends(get_unified_test_inventory_service),
) -> UnifiedTestInventory:
    """Retrieve authoritative test inventory for the project."""
    await _verify_project(session, project_id)

    files_map, ai_suite, smoke_tests, journey_suite, _ = await _resolve_project_test_inputs(
        session=session,
        project_id=project_id,
        version_service=version_service,
        version_id=version_id,
    )

    try:
        return inventory_service.build_inventory(
            project_id=project_id,
            files_map=files_map,
            ai_test_suite=ai_suite,
            smoke_tests=smoke_tests,
            journey_suite=journey_suite,
            strict=strict,
        )
    except UnifiedTestInventoryConflictError as e:
        raise ConflictError(message=str(e))
    except (UnifiedTestInventoryIsolationError, UnifiedTestInventoryValidationError) as e:
        raise ValidationError(message=str(e))
    except UnifiedTestInventoryError as e:
        raise ApplicationError(message=str(e), status_code=500)


# =============================================================================
# B. COVERAGE INTELLIGENCE
# =============================================================================

@router.get(
    "/coverage",
    response_model=UnifiedCoverageReport,
    status_code=status.HTTP_200_OK,
    summary="Get unified multi-tier requirement coverage",
    description=(
        "Calculates and returns deterministic requirement-level coverage across all four tiers "
        "as a mathematical set union against active requirements."
    ),
)
async def get_coverage_report(
    project_id: Annotated[uuid.UUID, Path(description="Canonical project UUID")],
    version_id: Annotated[uuid.UUID | None, Query(description="Optional development version UUID")] = None,
    session: AsyncSession = Depends(get_db),
    version_service: DevelopmentVersionService = Depends(get_development_version_service),
    requirement_service: RequirementService = Depends(get_requirement_service),
    inventory_service: UnifiedTestInventoryService = Depends(get_unified_test_inventory_service),
) -> UnifiedCoverageReport:
    """Calculate deterministic multi-tier coverage for the project."""
    await _verify_project(session, project_id)

    files_map, ai_suite, smoke_tests, journey_suite, _ = await _resolve_project_test_inputs(
        session=session,
        project_id=project_id,
        version_service=version_service,
        version_id=version_id,
    )

    try:
        inventory = inventory_service.build_inventory(
            project_id=project_id,
            files_map=files_map,
            ai_test_suite=ai_suite,
            smoke_tests=smoke_tests,
            journey_suite=journey_suite,
            strict=False,
        )
        reqs, _ = await requirement_service.list_requirements(project_id=project_id, limit=1000)

        return UnifiedCoverageEngine.compute_coverage(
            active_requirements=reqs,
            inventory=inventory,
            project_id=project_id,
        )
    except (UnifiedCoverageIsolationError, UnifiedCoverageValidationError) as e:
        raise ValidationError(message=str(e))
    except UnifiedCoverageError as e:
        raise ApplicationError(message=str(e), status_code=500)


# =============================================================================
# C. COVERAGE GAPS
# =============================================================================

@router.get(
    "/coverage/gaps",
    response_model=CoverageGapsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get requirement coverage gaps",
    description=(
        "Derives and returns active requirements lacking authoritative test coverage "
        "across all testing tiers, derived purely from UnifiedCoverageReport."
    ),
)
async def get_coverage_gaps(
    project_id: Annotated[uuid.UUID, Path(description="Canonical project UUID")],
    version_id: Annotated[uuid.UUID | None, Query(description="Optional development version UUID")] = None,
    session: AsyncSession = Depends(get_db),
    version_service: DevelopmentVersionService = Depends(get_development_version_service),
    requirement_service: RequirementService = Depends(get_requirement_service),
    inventory_service: UnifiedTestInventoryService = Depends(get_unified_test_inventory_service),
) -> CoverageGapsResponse:
    """Derive coverage gaps from the authoritative UnifiedCoverageReport."""
    await _verify_project(session, project_id)

    files_map, ai_suite, smoke_tests, journey_suite, _ = await _resolve_project_test_inputs(
        session=session,
        project_id=project_id,
        version_service=version_service,
        version_id=version_id,
    )

    try:
        inventory = inventory_service.build_inventory(
            project_id=project_id,
            files_map=files_map,
            ai_test_suite=ai_suite,
            smoke_tests=smoke_tests,
            journey_suite=journey_suite,
            strict=False,
        )
        reqs, _ = await requirement_service.list_requirements(project_id=project_id, limit=1000)

        report = UnifiedCoverageEngine.compute_coverage(
            active_requirements=reqs,
            inventory=inventory,
            project_id=project_id,
        )

        # Derive gaps strictly from the UnifiedCoverageReport
        gap_items: list[CoverageGapItem] = []
        for req_id in report.combined_uncovered_requirement_ids:
            trace = report.requirement_traceability.get(req_id)
            if trace:
                tier_names = [t.value if hasattr(t, "value") else str(t) for t in trace.covering_tiers]
                all_tests: list[str] = []
                for tests in trace.tests_by_tier.values():
                    all_tests.extend(tests)
                gap_items.append(
                    CoverageGapItem(
                        requirement_id=req_id,
                        covering_tiers=tier_names,
                        available_test_ids=sorted(list(set(all_tests))),
                        tests_by_tier=trace.tests_by_tier,
                    )
                )
            else:
                gap_items.append(CoverageGapItem(requirement_id=req_id))

        tier_summary = {
            tier: summary.uncovered_requirement_count
            for tier, summary in report.tier_coverages.items()
        }

        return CoverageGapsResponse(
            project_id=report.project_id,
            total_active_requirements=report.total_active_requirements,
            uncovered_count=report.combined_uncovered_count,
            uncovered_requirement_ids=report.combined_uncovered_requirement_ids,
            gaps=gap_items,
            tier_uncovered_summary=tier_summary,
            calculated_at=report.calculated_at,
            metadata=report.metadata,
        )
    except (UnifiedCoverageIsolationError, UnifiedCoverageValidationError) as e:
        raise ValidationError(message=str(e))
    except UnifiedCoverageError as e:
        raise ApplicationError(message=str(e), status_code=500)


# =============================================================================
# D. CHANGE IMPACT
# =============================================================================

@router.post(
    "/impact",
    response_model=ChangeImpactReport,
    status_code=status.HTTP_200_OK,
    summary="Analyze change impact from modifications or version diff",
    description=(
        "Analyzes source code changes through static AST dependency graphing to determine "
        "transitively affected files, tests, and requirements."
    ),
)
async def analyze_impact(
    project_id: Annotated[uuid.UUID, Path(description="Canonical project UUID")],
    body: ChangeImpactRequest,
    session: AsyncSession = Depends(get_db),
    version_service: DevelopmentVersionService = Depends(get_development_version_service),
    requirement_service: RequirementService = Depends(get_requirement_service),
    inventory_service: UnifiedTestInventoryService = Depends(get_unified_test_inventory_service),
    impact_service: ChangeImpactService = Depends(get_change_impact_service),
) -> ChangeImpactReport:
    """Analyze static change impact for the project."""
    await _verify_project(session, project_id)

    # 1. Resolve Changed Files and Files Map
    changed_files = body.changed_files
    files_map = body.files_map

    if body.base_version_id and body.target_version_id:
        # Validate isolation for both versions
        await version_service.get_version(project_id, body.base_version_id)
        target_ver = await version_service.get_version(project_id, body.target_version_id)

        if not changed_files:
            comparison = await version_service.compare_versions(
                project_id=project_id,
                from_version_id=body.base_version_id,
                to_version_id=body.target_version_id,
            )
            changed_files = [
                f.file_path for f in (comparison.files_modified + comparison.files_added + comparison.files_removed)
            ]

        if not files_map:
            from app.models.development_version import DevelopmentVersion
            stmt_v = select(DevelopmentVersion).where(
                DevelopmentVersion.id == target_ver.version_id,
                DevelopmentVersion.project_id == project_id,
            )
            v_res = await session.execute(stmt_v)
            v_entity = v_res.scalar_one_or_none()
            if v_entity:
                files_map = await version_service._resolve_version_files_map(v_entity)

    # Fallback to active version files if still not resolved
    if not files_map:
        files_map, _, _, _, _ = await _resolve_project_test_inputs(
            session=session,
            project_id=project_id,
            version_service=version_service,
            version_id=body.target_version_id,
        )

    if changed_files is None:
        raise ValidationError("Either changed_files or base_version_id and target_version_id must be provided.")

    # 2. Build Inventory
    files_map_resolved, ai_suite, smoke_tests, journey_suite, _ = await _resolve_project_test_inputs(
        session=session,
        project_id=project_id,
        version_service=version_service,
        version_id=body.target_version_id,
        explicit_files_map=files_map,
    )
    inventory = inventory_service.build_inventory(
        project_id=project_id,
        files_map=files_map_resolved,
        ai_test_suite=ai_suite,
        smoke_tests=smoke_tests,
        journey_suite=journey_suite,
        strict=False,
    )

    # 3. Retrieve Active Requirement IDs
    reqs, _ = await requirement_service.list_requirements(project_id=project_id, limit=1000)
    active_ids = [str(r.id) for r in reqs if not getattr(r, "is_archived", False)]

    # 4. Analyze Change Impact
    try:
        return impact_service.analyze_change_impact(
            project_id=project_id,
            changed_files=changed_files,
            files_map=files_map_resolved,
            inventory=inventory,
            active_requirement_ids=active_ids,
        )
    except (ChangeImpactIsolationError, ChangeImpactValidationError) as e:
        raise ValidationError(message=str(e))
    except ChangeImpactError as e:
        raise ApplicationError(message=str(e), status_code=500)


# =============================================================================
# E. REGRESSION PLAN
# =============================================================================

@router.post(
    "/regression/plan",
    response_model=RegressionPlan,
    status_code=status.HTTP_200_OK,
    summary="Generate deterministic selective regression plan",
    description=(
        "Plans regression execution by mapping Stage 3 ChangeImpactReport against "
        "Stage 2 UnifiedCoverageReport and Stage 1 UnifiedTestInventory. "
        "Validates deterministic ordering and safety rules."
    ),
)
async def plan_regression(
    project_id: Annotated[uuid.UUID, Path(description="Canonical project UUID")],
    body: PlanRegressionRequest,
    session: AsyncSession = Depends(get_db),
    version_service: DevelopmentVersionService = Depends(get_development_version_service),
    requirement_service: RequirementService = Depends(get_requirement_service),
    inventory_service: UnifiedTestInventoryService = Depends(get_unified_test_inventory_service),
    impact_service: ChangeImpactService = Depends(get_change_impact_service),
    planner: SelectiveRegressionPlanner = Depends(get_selective_regression_planner),
) -> RegressionPlan:
    """Generate a validated selective regression plan."""
    await _verify_project(session, project_id)

    # 1. Resolve Files and Inventory
    files_map, ai_suite, smoke_tests, journey_suite, _ = await _resolve_project_test_inputs(
        session=session,
        project_id=project_id,
        version_service=version_service,
        version_id=body.target_version_id,
    )
    inventory = inventory_service.build_inventory(
        project_id=project_id,
        files_map=files_map,
        ai_test_suite=ai_suite,
        smoke_tests=smoke_tests,
        journey_suite=journey_suite,
        strict=False,
    )

    # 2. Resolve Change Impact Report
    impact_report = body.impact_report
    if impact_report is None:
        changed_files = body.changed_files
        if not changed_files and body.base_version_id and body.target_version_id:
            comparison = await version_service.compare_versions(
                project_id=project_id,
                from_version_id=body.base_version_id,
                to_version_id=body.target_version_id,
            )
            changed_files = [
                f.file_path for f in (comparison.files_modified + comparison.files_added + comparison.files_removed)
            ]
        elif not changed_files:
            changed_files = list(files_map.keys())

        reqs, _ = await requirement_service.list_requirements(project_id=project_id, limit=1000)
        active_ids = [str(r.id) for r in reqs if not getattr(r, "is_archived", False)]

        try:
            impact_report = impact_service.analyze_change_impact(
                project_id=project_id,
                changed_files=changed_files,
                files_map=files_map,
                inventory=inventory,
                active_requirement_ids=active_ids,
            )
        except (ChangeImpactIsolationError, ChangeImpactValidationError) as e:
            raise ValidationError(message=str(e))

    # 3. Resolve Coverage Report
    coverage_report = body.coverage_report
    if coverage_report is None:
        reqs, _ = await requirement_service.list_requirements(project_id=project_id, limit=1000)
        try:
            coverage_report = UnifiedCoverageEngine.compute_coverage(
                active_requirements=reqs,
                inventory=inventory,
                project_id=project_id,
            )
        except Exception as e:
            logger.warning(f"Could not compute coverage report for regression planning: {e}")

    # 4. Plan Regression
    try:
        plan = planner.plan_regression(
            project_id=project_id,
            inventory=inventory,
            impact_report=impact_report,
            coverage_report=coverage_report,
            mode=body.mode,
            auto_broaden=body.auto_broaden,
            base_version_id=str(body.base_version_id) if body.base_version_id else None,
            target_version_id=str(body.target_version_id) if body.target_version_id else None,
            metadata=body.metadata,
        )
        return plan
    except (RegressionPlanIsolationError, RegressionPlanValidationError) as e:
        raise ValidationError(message=str(e))
    except RegressionPlanError as e:
        raise ApplicationError(message=str(e), status_code=500)


# =============================================================================
# F. REGRESSION EXECUTION
# =============================================================================

@router.post(
    "/regression/execute",
    response_model=RegressionExecutionResult,
    status_code=status.HTTP_200_OK,
    summary="Execute validated selective regression plan",
    description=(
        "Executes a validated selective regression test plan across unit, AI, "
        "and browser test tiers using existing execution authorities (Docker sandbox, Playwright). "
        "Strictly validates the plan with RegressionPlanValidator before running."
    ),
)
async def execute_regression(
    project_id: Annotated[uuid.UUID, Path(description="Canonical project UUID")],
    body: ExecuteRegressionRequest,
    session: AsyncSession = Depends(get_db),
    version_service: DevelopmentVersionService = Depends(get_development_version_service),
    requirement_service: RequirementService = Depends(get_requirement_service),
    inventory_service: UnifiedTestInventoryService = Depends(get_unified_test_inventory_service),
    impact_service: ChangeImpactService = Depends(get_change_impact_service),
    planner: SelectiveRegressionPlanner = Depends(get_selective_regression_planner),
    executor: RegressionExecutionService = Depends(get_regression_execution_service),
) -> RegressionExecutionResult:
    """Execute a validated regression plan for the project."""
    await _verify_project(session, project_id)

    files_map, ai_suite, smoke_tests, journey_suite, resolved_version = await _resolve_project_test_inputs(
        session=session,
        project_id=project_id,
        version_service=version_service,
        version_id=body.target_version_id,
    )
    inventory = inventory_service.build_inventory(
        project_id=project_id,
        files_map=files_map,
        ai_test_suite=ai_suite,
        smoke_tests=smoke_tests,
        journey_suite=journey_suite,
        strict=False,
    )

    # 1. Resolve or Generate Plan
    plan: RegressionPlan | None = body.plan
    if plan is None:
        changed_files = body.changed_files
        if not changed_files and body.base_version_id and body.target_version_id:
            comparison = await version_service.compare_versions(
                project_id=project_id,
                from_version_id=body.base_version_id,
                to_version_id=body.target_version_id,
            )
            changed_files = [
                f.file_path for f in (comparison.files_modified + comparison.files_added + comparison.files_removed)
            ]
        elif not changed_files:
            changed_files = list(files_map.keys())

        reqs, _ = await requirement_service.list_requirements(project_id=project_id, limit=1000)
        active_ids = [str(r.id) for r in reqs if not getattr(r, "is_archived", False)]

        try:
            impact_report = impact_service.analyze_change_impact(
                project_id=project_id,
                changed_files=changed_files,
                files_map=files_map,
                inventory=inventory,
                active_requirement_ids=active_ids,
            )
            coverage_report = UnifiedCoverageEngine.compute_coverage(
                active_requirements=reqs,
                inventory=inventory,
                project_id=project_id,
            )
            plan = planner.plan_regression(
                project_id=project_id,
                inventory=inventory,
                impact_report=impact_report,
                coverage_report=coverage_report,
                mode=body.mode,
                auto_broaden=body.auto_broaden,
                base_version_id=str(body.base_version_id) if body.base_version_id else None,
                target_version_id=str(body.target_version_id) if body.target_version_id else None,
            )
        except (ChangeImpactIsolationError, ChangeImpactValidationError, RegressionPlanIsolationError, RegressionPlanValidationError) as e:
            raise ValidationError(message=str(e))

    # 2. Strict Project Boundary Enforcement on Plan
    if str(plan.project_id).strip().lower() != str(project_id).strip().lower():
        raise ValidationError(
            f"RegressionPlan belongs to project '{plan.project_id}', not authorized for '{project_id}'."
        )

    # 3. Deterministic Plan Validation
    validator = RegressionPlanValidator()
    try:
        validator.validate(plan, inventory)
    except (RegressionPlanIsolationError, RegressionPlanValidationError) as e:
        raise ValidationError(message=str(e))

    # 4. Resolve Runtime Manifest if available
    manifest = None
    if resolved_version:
        raw_manifest = getattr(resolved_version, "runtime_manifest", None)
        if raw_manifest:
            from app.schemas.runtime import ApplicationRuntimeManifest
            try:
                manifest = ApplicationRuntimeManifest.model_validate(raw_manifest)
            except Exception as e:
                raise ValidationError(f"Invalid runtime manifest: {e}")
        else:
            manifest = await version_service.resolve_runtime_manifest(project_id, resolved_version.version_id)

    # 5. Execute Plan via Stage 5 RegressionExecutionService
    try:
        return await executor.execute_plan(
            project_id=project_id,
            plan=plan,
            inventory=inventory,
            files_map=files_map,
            application_manifest=manifest,
            skip_browser_tests=body.skip_browser_tests,
            browser_base_url=body.browser_base_url,
            execution_timeout_seconds=body.execution_timeout_seconds,
        )
    except RegressionExecutionSafetyError as e:
        raise ValidationError(message=str(e))
    except RegressionExecutionError as e:
        raise ApplicationError(message=str(e), status_code=500)
