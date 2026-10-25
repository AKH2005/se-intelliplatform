"""Deterministic Verification Service for Phase 11H.

Evaluates multi-stage verification state across static analysis, containerized
sandbox execution, AI test execution, and failure diagnosis resolution.

Guarantees:
- Purely deterministic rules: zero LLM calculation of verification status.
- Enforces distinction between REQUIRED and OPTIONAL verification stages.
- Re-run / refresh only computes status without mutating code artifacts.
"""

import logging
from typing import Any

from app.agents.code_generation.contracts import CodeGenerationOutput
from app.agents.failure_analysis.contracts import FailureDiagnosis
from app.agents.remediation.contracts import RemediationVerificationResult
from app.agents.test_generation.contracts import AITestExecutionResult, AITestSuite
from app.sandbox.contracts import ExecutionResult, ExecutionStatus
from app.sandbox.static_analysis.contracts import DiagnosticSeverity, StaticAnalysisResult
from app.schemas.development_version import (
    StageVerificationResult,
    VerificationRequirementLevel,
    VerificationSnapshot,
    VerificationStatus,
)

logger = logging.getLogger(__name__)


class DevelopmentVerificationService:
    """Deterministic verification orchestrator and aggregator."""

    @staticmethod
    def has_test_files(artifact: CodeGenerationOutput | None) -> bool:
        """Determine if generated project contains test suite files."""
        if not artifact or not artifact.generated_files:
            return False
        for f in artifact.generated_files:
            p = f.path.lower()
            if p.startswith("tests/") or p.startswith("test/") or "/tests/" in p:
                return True
            if p.endswith("_test.py") or p.endswith("test_.py") or p.startswith("test_"):
                return True
        return False

    @classmethod
    def evaluate_verification(
        cls,
        artifact: CodeGenerationOutput | None,
        static_analysis: StaticAnalysisResult | None = None,
        sandbox_execution: ExecutionResult | None = None,
        ai_test_suite: AITestSuite | None = None,
        ai_test_execution: AITestExecutionResult | None = None,
        failure_diagnosis: FailureDiagnosis | None = None,
        remediation_verification: RemediationVerificationResult | None = None,
        browser_test_run: Any | None = None,
        browser_testing_required: bool = False,
    ) -> VerificationSnapshot:
        """Deterministically aggregate verification across all SDLC stages."""
        blocking_issues: list[str] = []

        # 1. Static Analysis (ALWAYS REQUIRED)
        if static_analysis is None:
            sa_level = VerificationRequirementLevel.REQUIRED
            sa_status = VerificationStatus.FAILED
            sa_details = "Static analysis was never executed for this artifact."
            sa_errors = 1
            sa_warnings = 0
            sa_blocking = ["Missing mandatory static analysis report"]
            blocking_issues.extend(sa_blocking)
        elif static_analysis.error_count > 0 or static_analysis.security_issue_count > 0:
            sa_level = VerificationRequirementLevel.REQUIRED
            sa_status = VerificationStatus.FAILED
            sa_details = (
                f"Static analysis failed with {static_analysis.error_count} error(s) "
                f"and {static_analysis.security_issue_count} security issue(s)."
            )
            sa_errors = static_analysis.error_count + static_analysis.security_issue_count
            sa_warnings = static_analysis.warning_count
            sa_blocking = [
                f"Static analysis finding: {d.code} at {d.file_path}:{d.line}"
                for d in static_analysis.diagnostics
                if d.severity in (DiagnosticSeverity.CRITICAL, DiagnosticSeverity.ERROR)
            ]
            blocking_issues.extend(sa_blocking or [sa_details])
        else:
            sa_level = VerificationRequirementLevel.REQUIRED
            sa_status = VerificationStatus.PASSED
            sa_details = f"Static analysis passed with 0 errors and {static_analysis.warning_count} warnings."
            sa_errors = 0
            sa_warnings = static_analysis.warning_count
            sa_blocking = []

        sa_stage = StageVerificationResult(
            stage="static_analysis",
            requirement_level=sa_level,
            status=sa_status,
            details=sa_details,
            error_count=sa_errors,
            warning_count=sa_warnings,
            blocking_issues=sa_blocking,
        )

        # 2. Sandbox Execution (REQUIRED if project scaffold contains test files)
        project_has_tests = cls.has_test_files(artifact)
        if project_has_tests:
            sb_level = VerificationRequirementLevel.REQUIRED
            if sandbox_execution is None:
                sb_status = VerificationStatus.FAILED
                sb_details = "Sandbox tests were not executed for project containing test files."
                sb_blocking = ["Mandatory sandbox tests were not executed"]
                sb_errors = 1
                blocking_issues.extend(sb_blocking)
            else:
                status_val = (
                    sandbox_execution.status.value
                    if hasattr(sandbox_execution.status, "value")
                    else str(sandbox_execution.status)
                )
                if (
                    status_val != "PASSED"
                    or sandbox_execution.exit_code != 0
                    or sandbox_execution.tests_failed > 0
                ):
                    sb_status = VerificationStatus.FAILED
                    sb_details = (
                        f"Sandbox execution failed (status='{status_val}', "
                        f"exit_code={sandbox_execution.exit_code}, "
                        f"failed={sandbox_execution.tests_failed}/{sandbox_execution.tests_total})."
                    )
                    sb_blocking = [sb_details]
                    sb_errors = max(1, sandbox_execution.tests_failed)
                    blocking_issues.extend(sb_blocking)
                else:
                    sb_status = VerificationStatus.PASSED
                    sb_details = f"All {sandbox_execution.tests_passed} sandbox tests passed."
                    sb_blocking = []
                    sb_errors = 0
        else:
            sb_level = VerificationRequirementLevel.NOT_APPLICABLE
            sb_status = VerificationStatus.NOT_RUN
            sb_details = "No unit test files present in scaffold manifest."
            sb_blocking = []
            sb_errors = 0

        sb_stage = StageVerificationResult(
            stage="sandbox_execution",
            requirement_level=sb_level,
            status=sb_status,
            details=sb_details,
            error_count=sb_errors,
            warning_count=0,
            blocking_issues=sb_blocking,
        )

        # 3. AI-Generated Tests (REQUIRED if an AI test suite was generated)
        if ai_test_suite is not None and getattr(ai_test_suite, "test_count", 0) > 0:
            ai_level = VerificationRequirementLevel.REQUIRED
            if ai_test_execution is None:
                ai_status = VerificationStatus.FAILED
                ai_details = "AI test suite was generated but execution results are missing."
                ai_blocking = ["Mandatory AI test execution was not performed"]
                ai_errors = 1
                blocking_issues.extend(ai_blocking)
            else:
                ai_status_val = (
                    ai_test_execution.status.value
                    if hasattr(ai_test_execution.status, "value")
                    else str(ai_test_execution.status)
                )
                if (
                    ai_status_val != "PASSED"
                    or getattr(ai_test_execution, "exit_code", 0) != 0
                    or getattr(ai_test_execution, "tests_failed", 0) > 0
                ):
                    ai_status = VerificationStatus.FAILED
                    ai_details = (
                        f"AI test execution failed (status='{ai_status_val}', "
                        f"failed={ai_test_execution.tests_failed}/{ai_test_execution.tests_total})."
                    )
                    ai_blocking = [ai_details]
                    ai_errors = max(1, ai_test_execution.tests_failed)
                    blocking_issues.extend(ai_blocking)
                else:
                    ai_status = VerificationStatus.PASSED
                    ai_details = f"All {ai_test_execution.tests_passed} AI-generated tests passed."
                    ai_blocking = []
                    ai_errors = 0
        else:
            ai_level = VerificationRequirementLevel.OPTIONAL
            ai_status = VerificationStatus.NOT_RUN
            ai_details = "No AI test suite generated for this version."
            ai_blocking = []
            ai_errors = 0

        ai_stage = StageVerificationResult(
            stage="ai_tests",
            requirement_level=ai_level,
            status=ai_status,
            details=ai_details,
            error_count=ai_errors,
            warning_count=0,
            blocking_issues=ai_blocking,
        )

        # 4. Failure Analysis (Diagnostic reasoning & root-cause verification)
        fa_level = VerificationRequirementLevel.NOT_APPLICABLE
        fa_status = VerificationStatus.NOT_RUN
        fa_details = "No failure diagnoses recorded."
        fa_blocking: list[str] = []
        fa_errors = 0

        if failure_diagnosis is not None:
            # Check if diagnosis represents a real failure vs confirmed clean state
            is_real_failure = (
                failure_diagnosis.severity in (DiagnosticSeverity.CRITICAL, DiagnosticSeverity.ERROR)
                and "No Failure Detected" not in failure_diagnosis.title
            )
            if is_real_failure:
                fa_level = VerificationRequirementLevel.REQUIRED
                # FailureAnalysis is read-only diagnostic infrastructure.
                # Valid diagnosis passes failure_analysis without requiring remediation.
                is_structurally_valid = bool(
                    getattr(failure_diagnosis, "diagnosis_id", None)
                    and getattr(failure_diagnosis, "title", None)
                    and getattr(failure_diagnosis, "failure_type", None)
                    and getattr(failure_diagnosis, "root_cause", None)
                )
                if is_structurally_valid:
                    fa_status = VerificationStatus.PASSED
                    rem_info = ""
                    if remediation_verification is not None:
                        rem_resolved = (
                            remediation_verification.static_analysis_passed
                            and remediation_verification.sandbox_passed
                            and (getattr(remediation_verification, "browser_passed", None) is not False)
                        )
                        rem_info = f" (Remediation verification: resolved={rem_resolved})"
                    fa_details = (
                        f"Failure diagnosis validated: '{failure_diagnosis.title}' "
                        f"({failure_diagnosis.failure_type.value}, severity={failure_diagnosis.severity.value})."
                        f"{rem_info}"
                    )
                    fa_blocking = []
                    fa_errors = 0
                else:
                    fa_status = VerificationStatus.FAILED
                    fa_details = (
                        f"Malformed failure diagnosis for '{failure_diagnosis.title}': "
                        "Missing mandatory diagnostic attributes."
                    )
                    fa_blocking = [fa_details]
                    fa_errors = 1
                    blocking_issues.extend(fa_blocking)
            else:
                fa_level = VerificationRequirementLevel.NOT_APPLICABLE
                fa_status = VerificationStatus.PASSED
                fa_details = "Diagnostic reasoning confirmed no failure detected."
        else:
            fa_level = VerificationRequirementLevel.NOT_APPLICABLE
            fa_status = VerificationStatus.NOT_RUN
            fa_details = "No failure diagnoses recorded."

        fa_stage = StageVerificationResult(
            stage="failure_analysis",
            requirement_level=fa_level,
            status=fa_status,
            details=fa_details,
            error_count=fa_errors,
            warning_count=0,
            blocking_issues=fa_blocking,
        )

        # 5. Browser Validation (REQUIRED if browser suite / runtime manifest is configured)
        is_browser_configured = browser_testing_required or (browser_test_run is not None)
        if is_browser_configured:
            br_level = VerificationRequirementLevel.REQUIRED
            if browser_test_run is None:
                br_status = VerificationStatus.FAILED
                br_details = "Browser validation was required for this version but was not executed."
                br_blocking = ["Mandatory browser validation was not executed"]
                br_errors = 1
                blocking_issues.extend(br_blocking)
            else:
                status_val = (
                    browser_test_run.status.value
                    if hasattr(browser_test_run.status, "value")
                    else str(browser_test_run.status)
                )
                tests_failed = getattr(browser_test_run, "tests_failed", 0)
                tests_total = getattr(browser_test_run, "tests_total", 0)
                tests_passed = getattr(browser_test_run, "tests_passed", 0)
                failure_reason = getattr(browser_test_run, "failure_reason", None)
                summary_msg = getattr(browser_test_run, "summary", "")

                if (
                    status_val != "PASSED"
                    or tests_failed > 0
                    or status_val in ("FAILED", "TIMEOUT", "STARTUP_FAILED", "BROWSER_ERROR", "RESOURCE_LIMIT", "VALIDATION_ERROR")
                ):
                    br_status = VerificationStatus.FAILED
                    err_reason = failure_reason or summary_msg or f"Browser tests failed ({tests_failed}/{tests_total})."
                    br_details = (
                        f"Browser validation failed (status='{status_val}', "
                        f"failed={tests_failed}/{tests_total}): {err_reason}"
                    )
                    br_blocking = [br_details]
                    br_errors = max(1, tests_failed)
                    blocking_issues.extend(br_blocking)
                else:
                    br_status = VerificationStatus.PASSED
                    br_details = f"All {tests_passed} browser smoke test(s) passed successfully."
                    br_blocking = []
                    br_errors = 0
        else:
            br_level = VerificationRequirementLevel.NOT_APPLICABLE
            br_status = VerificationStatus.NOT_RUN
            br_details = "No browser test suite or application runtime configured for this version."
            br_blocking = []
            br_errors = 0

        br_stage = StageVerificationResult(
            stage="browser_validation",
            requirement_level=br_level,
            status=br_status,
            details=br_details,
            error_count=br_errors,
            warning_count=0,
            blocking_issues=br_blocking,
        )

        # 6. Aggregate Verdict
        is_verified = len(blocking_issues) == 0 and sa_status == VerificationStatus.PASSED
        if is_verified:
            overall_status = VerificationStatus.PASSED
            summary = (
                "Verification passed: All required static analysis, sandbox tests, "
                "browser tests, and diagnostic checks satisfied."
            )
        else:
            overall_status = VerificationStatus.FAILED
            summary = f"Verification failed with {len(blocking_issues)} issue(s): {'; '.join(blocking_issues[:3])}"

        return VerificationSnapshot(
            verification_status=overall_status,
            is_verified=is_verified,
            summary=summary,
            static_analysis=sa_stage,
            sandbox_execution=sb_stage,
            ai_tests=ai_stage,
            failure_analysis=fa_stage,
            browser_validation=br_stage,
        )
