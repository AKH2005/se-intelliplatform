"""Request and Response Schemas for Browser Journey Workflow API (Phase 11K Stage 5).

Provides strongly-typed, sanitized DTOs for client communication without exposing
internal engine models, secrets, container IDs, or filesystem paths.
"""

import uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.browser.journey.contracts import (
    BrowserJourneyWorkflowResult,
    BrowserJourneyWorkflowStatus,
)
from app.models.workflow_execution import WorkflowExecution
from app.schemas.browser_testing import BrowserTestStatus


class GenerateBrowserJourneysRequest(BaseModel):
    """Payload to trigger browser journey synthesis, validation, adaptation, and execution."""

    model_config = ConfigDict(extra="forbid")

    development_version_id: uuid.UUID | None = Field(
        default=None,
        description="Optional target development version UUID. Defaults to active version if not specified.",
    )
    execute_browser_tests: bool = Field(
        default=True,
        description="Whether to execute generated journeys in the isolated browser container runtime.",
    )
    max_journeys: int = Field(
        default=10,
        ge=1,
        le=10,
        description="Maximum number of candidate journeys to generate (capped at 10).",
    )


class BrowserJourneyWorkflowResponse(BaseModel):
    """Public, stable response representation of a browser journey workflow run."""

    model_config = ConfigDict(extra="forbid")

    workflow_execution_id: uuid.UUID = Field(
        ...,
        description="Correlation UUID of the workflow execution",
    )
    project_id: uuid.UUID = Field(
        ...,
        description="Target project UUID",
    )
    status: str = Field(
        ...,
        description="Final deterministic workflow outcome status (e.g. COMPLETED, WORKFLOW_GENERATION_FAILED, WORKFLOW_VALIDATION_FAILED, WORKFLOW_ADAPTATION_FAILED, WORKFLOW_BROWSER_EXECUTION_FAILED)",
    )
    stage_reached: str = Field(
        ...,
        description="Deepest pipeline stage reached: 'generation', 'validation', 'adaptation', 'browser_execution', 'completed'",
    )
    journey_count: int = Field(
        default=0,
        description="Number of candidate journeys generated",
    )
    validation_passed: bool = Field(
        default=False,
        description="Whether candidate journey suite passed all deterministic validation checks",
    )
    coverage_percentage: float | None = Field(
        default=None,
        description="Requirement coverage percentage computed deterministically by Stage 2 engine",
    )
    covered_requirement_ids: list[str] = Field(
        default_factory=list,
        description="Authoritative requirement IDs covered by validated journeys",
    )
    uncovered_requirement_ids: list[str] = Field(
        default_factory=list,
        description="Authoritative requirement IDs not covered by validated journeys",
    )
    test_definitions_count: int = Field(
        default=0,
        description="Number of adapted deterministic browser test definitions",
    )
    browser_tests_executed: bool = Field(
        default=False,
        description="Whether browser container tests were executed",
    )
    browser_tests_passed: bool | None = Field(
        default=None,
        description="Whether all browser container tests passed (None if not executed)",
    )
    browser_test_run_id: uuid.UUID | None = Field(
        default=None,
        description="Correlation UUID of the BrowserTestRun if executed",
    )
    failure_reason: str | None = Field(
        default=None,
        description="Primary human-readable error description if workflow did not complete successfully",
    )
    failure_diagnosis: dict[str, Any] | None = Field(
        default=None,
        description="Serialized diagnostic root cause analysis produced by FailureAnalysisAgent if browser tests failed",
    )
    artifacts: dict[str, Any] = Field(
        default_factory=dict,
        description="Serialized workflow execution artifacts preserving the traceability chain",
    )
    started_at: datetime = Field(
        ...,
        description="Timestamp when workflow run commenced (UTC)",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Timestamp when workflow run finished (UTC)",
    )
    duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Elapsed duration in seconds",
    )

    @classmethod
    def from_result(cls, res: BrowserJourneyWorkflowResult) -> "BrowserJourneyWorkflowResponse":
        """Transform a live Stage 4 BrowserJourneyWorkflowResult domain object into an API response DTO."""
        journey_count = len(res.candidate_suite.journeys) if res.candidate_suite else 0
        validation_passed = res.validation_outcome.is_valid if res.validation_outcome else False
        coverage_pct = res.coverage_report.coverage_percentage if res.coverage_report else None
        cov_ids = res.coverage_report.covered_requirement_ids if res.coverage_report else []
        uncov_ids = res.coverage_report.uncovered_requirement_ids if res.coverage_report else []
        test_defs_count = len(res.test_definitions) if res.test_definitions else 0
        executed = res.browser_test_run is not None
        passed = (res.browser_test_run.status == BrowserTestStatus.PASSED) if res.browser_test_run else None
        run_id = res.browser_test_run.run_id if res.browser_test_run else None
        fa_dict = res.failure_diagnosis.model_dump(mode="json") if res.failure_diagnosis else None

        return cls(
            workflow_execution_id=res.workflow_execution_id,
            project_id=res.project_id,
            status=res.status.value,
            stage_reached=res.stage_reached,
            journey_count=journey_count,
            validation_passed=validation_passed,
            coverage_percentage=coverage_pct,
            covered_requirement_ids=cov_ids,
            uncovered_requirement_ids=uncov_ids,
            test_definitions_count=test_defs_count,
            browser_tests_executed=executed,
            browser_tests_passed=passed,
            browser_test_run_id=run_id,
            failure_reason=res.error_message,
            failure_diagnosis=fa_dict,
            artifacts=res.artifacts,
            started_at=res.started_at,
            completed_at=res.completed_at,
            duration_seconds=res.duration_seconds,
        )

    @classmethod
    def from_workflow_execution(cls, execution: WorkflowExecution) -> "BrowserJourneyWorkflowResponse":
        """Transform a persisted WorkflowExecution ORM entity into an API response DTO."""
        artifacts = execution.artifacts or {}
        metadata = execution.metadata_payload or {}

        validation_art = artifacts.get("browser_journey_validation") or {}
        suite_art = artifacts.get("browser_journey_suite") or {}
        browser_run_art = artifacts.get("browser_test_run") or {}
        fa_art = artifacts.get("failure_analysis")

        cov_art = validation_art.get("coverage_report") or {}
        coverage_pct = cov_art.get("coverage_percentage")
        cov_ids = cov_art.get("covered_requirement_ids") or []
        uncov_ids = cov_art.get("uncovered_requirement_ids") or []

        journeys_list = suite_art.get("journeys") or []
        journey_count = metadata.get("journey_count", len(journeys_list))
        validation_passed = metadata.get("validation_passed", validation_art.get("is_valid", False))
        test_defs_count = metadata.get("test_definitions_count", len(journeys_list))

        executed = bool(browser_run_art)
        run_status = browser_run_art.get("status")
        passed = (run_status == "PASSED") if run_status else None
        run_id_val = browser_run_art.get("run_id")
        run_id = uuid.UUID(str(run_id_val)) if run_id_val else None

        status_val = metadata.get("workflow_status", execution.status.value)
        stage_reached = metadata.get("stage_reached", "completed" if execution.status.value == "COMPLETED" else "unknown")

        err_msg = execution.errors[0] if execution.errors else None
        duration = metadata.get("duration_seconds", 0.0)

        return cls(
            workflow_execution_id=execution.workflow_execution_id,
            project_id=execution.project_id,
            status=status_val,
            stage_reached=stage_reached,
            journey_count=journey_count,
            validation_passed=validation_passed,
            coverage_percentage=coverage_pct,
            covered_requirement_ids=cov_ids,
            uncovered_requirement_ids=uncov_ids,
            test_definitions_count=test_defs_count,
            browser_tests_executed=executed,
            browser_tests_passed=passed,
            browser_test_run_id=run_id,
            failure_reason=err_msg,
            failure_diagnosis=fa_art,
            artifacts=artifacts,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            duration_seconds=duration,
        )
