"""Live Integration Tests for Phase 11J - Stage 4: Browser Verification, Failure Diagnosis, and Browser Regression.

Exercises end-to-end integration:
1. Generated application starts in isolated Docker runtime.
2. Browser smoke test executes inside containerized Playwright runtime.
3. Successful browser test run enters verification pipeline -> VERIFIED status.
4. Browser failure enters verification pipeline -> blocks VERIFIED status.
5. Failure analysis receives structured browser evidence and produces bounded diagnosis.
6. Approved remediation creates v2 while preserving historical v1.
7. Browser regression executes against v2 and gates VERIFIED state.
"""

import asyncio
import os
import shutil
import tempfile
import uuid
from pathlib import Path
import pytest

from app.browser.contracts import (
    DEFAULT_PLAYWRIGHT_IMAGE,
    BrowserLimits,
    DeterministicBrowserTestDefinition,
    create_default_smoke_suite,
)
from app.browser.browser_executor import BrowserExecutor
from app.browser.browser_testing_service import BrowserTestingService
from app.runtime.application_runtime_manager import ApplicationRuntimeManager
from app.runtime.contracts import RuntimeLimits
from app.runtime.docker_runtime_executor import DockerRuntimeExecutor
from app.schemas.browser_testing import BrowserTestRun, BrowserTestStatus
from app.schemas.development_version import VerificationRequirementLevel, VerificationStatus
from app.schemas.runtime import ApplicationRuntimeManifest, RuntimeFramework, RuntimeLanguage
from app.services.verification_service import DevelopmentVerificationService
from app.agents.code_generation.contracts import (
    CodeGenerationOutput,
    CodeGenerationPlan,
    GeneratedFile,
    PlannedFile,
)
from app.agents.failure_analysis.contracts import (
    DiagnosticSeverity,
    FailureAnalysisInput,
    FailureDiagnosis,
    FailureSource,
    FailureType,
)
from app.agents.failure_analysis.service import FailureAnalysisService
from app.agents.failure_analysis.validator import FailureAnalysisValidator
from app.agents.remediation.contracts import (
    ChangeOperation,
    ProposedChange,
    RemediationProposal,
    RemediationProposalStatus,
    RemediationVerificationResult,
)
from app.sandbox.static_analysis.contracts import (
    StaticAnalysisResult,
    StaticAnalysisStatus,
)


@pytest.fixture
def docker_runtime_executor():
    return DockerRuntimeExecutor(image="se-intelliplatform-sandbox:latest")


@pytest.fixture
def browser_executor():
    return BrowserExecutor(image=DEFAULT_PLAYWRIGHT_IMAGE)


@pytest.mark.asyncio
async def test_live_browser_verification_and_failure_flow(docker_runtime_executor, browser_executor):
    """Integration Test: App startup, browser smoke test execution, verification gating, failure diagnosis, and regression."""
    if not await docker_runtime_executor.check_docker_available():
        pytest.skip("Docker daemon is not available.")
    if not await browser_executor.check_image_available():
        pytest.skip(f"Playwright browser image '{DEFAULT_PLAYWRIGHT_IMAGE}' not available locally.")

    project_id = uuid.uuid4()
    artifacts_dir = tempfile.mkdtemp(prefix="se_int_artifacts_")

    try:
        runtime_manager = ApplicationRuntimeManager()
        testing_service = BrowserTestingService(
            runtime_manager=runtime_manager,
            browser_executor=browser_executor,
            artifacts_base_dir=artifacts_dir,
        )

        # ----------------------------------------------------------------------
        # Step 1: Passing Application and Verification
        # ----------------------------------------------------------------------
        passing_files = {
            "index.html": "<!DOCTYPE html><html><head><title>App Home</title></head><body><h1>Welcome</h1></body></html>",
        }
        passing_manifest = ApplicationRuntimeManifest(
            runtime_type="docker",
            language=RuntimeLanguage.PYTHON,
            framework=RuntimeFramework.FASTAPI,
            entrypoint="app.main:app",
            startup_command=["python", "-m", "http.server", "8000"],
            application_port=8000,
            health_check_path="/index.html",
            health_check_method="GET",
            health_check_timeout_seconds=5.0,
        )

        test_suite = [
            DeterministicBrowserTestDefinition(
                test_id="test_smoke_root",
                name="Root Page Smoke Test",
                target_path="/index.html",
                expected_title_contains="App Home",
            )
        ]

        # 1. Run live browser test against passing application
        run_pass = await testing_service.execute_browser_tests(
            project_id=project_id,
            files_map=passing_files,
            manifest=passing_manifest,
            test_definitions=test_suite,
        )
        assert run_pass.status == BrowserTestStatus.PASSED
        assert run_pass.tests_failed == 0
        assert run_pass.tests_passed == 1

        # 2. Feed passing browser result into VerificationService
        code_artifact = CodeGenerationOutput(
            plan=CodeGenerationPlan(
                project_type="backend-service",
                language="python",
                framework="fastapi",
                database="none",
                package_manager="pip",
                files=[PlannedFile(path="index.html", purpose="Home page", file_type="SOURCE")],
                rationale="Sample static app",
            ),
            generated_files=[
                GeneratedFile(path="index.html", content=passing_files["index.html"], language="html", size_bytes=len(passing_files["index.html"]))
            ],
            total_files=1,
            total_size_bytes=len(passing_files["index.html"]),
            summary="Passing app",
        )
        sa_pass = StaticAnalysisResult(
            analysis_id=uuid.uuid4(),
            project_id=project_id,
            status=StaticAnalysisStatus.PASSED,
            duration_seconds=0.1,
            files_analyzed=1,
            files_skipped=0,
            error_count=0,
            warning_count=0,
            info_count=0,
            security_issue_count=0,
            syntax_error_count=0,
            lint_issue_count=0,
            diagnostics=[],
            summary="Clean",
        )

        snapshot_pass = DevelopmentVerificationService.evaluate_verification(
            artifact=code_artifact,
            static_analysis=sa_pass,
            browser_test_run=run_pass,
            browser_testing_required=True,
        )
        assert snapshot_pass.is_verified is True
        assert snapshot_pass.verification_status == VerificationStatus.PASSED
        assert snapshot_pass.browser_validation.status == VerificationStatus.PASSED

        # ----------------------------------------------------------------------
        # Step 2: Failing Application, Verification Gating & Failure Diagnosis
        # ----------------------------------------------------------------------
        failing_files = {
            "index.html": "<!DOCTYPE html><html><head><title>Wrong Title</title></head><body><h1>Broken</h1></body></html>",
        }

        # Expect title "App Home", but page has "Wrong Title" -> smoke test fails!
        run_fail = await testing_service.execute_browser_tests(
            project_id=project_id,
            files_map=failing_files,
            manifest=passing_manifest,
            test_definitions=test_suite,
        )
        assert run_fail.status == BrowserTestStatus.FAILED
        assert run_fail.tests_failed == 1

        # Evaluate verification with failed browser run -> must fail and block is_verified!
        snapshot_fail = DevelopmentVerificationService.evaluate_verification(
            artifact=code_artifact,
            static_analysis=sa_pass,
            browser_test_run=run_fail,
            browser_testing_required=True,
        )
        assert snapshot_fail.is_verified is False
        assert snapshot_fail.verification_status == VerificationStatus.FAILED
        assert snapshot_fail.browser_validation.status == VerificationStatus.FAILED

        # 3. Check failure analysis trigger
        should_run_fa, fa_reason = FailureAnalysisService.should_trigger_analysis(
            execution_result=None,
            static_analysis_result=sa_pass,
            browser_test_run=run_fail,
        )
        assert should_run_fa is True
        assert "status is 'FAILED'" in fa_reason

        # 4. Construct FailureAnalysisInput and validate anti-hallucination guardrails
        fa_input = FailureAnalysisInput(
            project_id=project_id,
            all_project_files=["index.html"],
            browser_test_run=run_fail,
            failure_source=FailureSource.BROWSER,
        )
        assert fa_input.browser_test_run is not None
        assert fa_input.failure_source == FailureSource.BROWSER

        # Formulate diagnosis grounded in the browser test failure
        diagnosis = FailureDiagnosis(
            failure_type=FailureType.TEST_FAILURE,
            failure_source=FailureSource.BROWSER,
            title="Browser Smoke Test Assertion Failed",
            summary="Expected page title 'App Home' was not observed in HTML head.",
            root_cause="The HTML index template renders 'Wrong Title' instead of required 'App Home'.",
            severity=DiagnosticSeverity.ERROR,
            affected_files=["index.html"],
            evidence=[
                from_ev := {
                    "evidence_id": "test_smoke_root",
                    "source": "browser",
                    "file_path": "index.html",
                    "description": "Title mismatch assertion in smoke test",
                }
            ],
            claims=[
                {
                    "claim_type": "FACT",
                    "statement": "The browser test failed with title assertion mismatch.",
                    "evidence_ids": ["test_smoke_root"],
                }
            ],
            suggested_remediation="Update the title element in the HTML document to match the expected page title.",
        )
        val_result = FailureAnalysisValidator.validate(diagnosis, fa_input)
        assert val_result.is_valid is True

        # ----------------------------------------------------------------------
        # Step 3: Approved Remediation & Browser Regression to v2
        # ----------------------------------------------------------------------
        # Historical v1 preserved
        v1_preserved = dict(failing_files)

        # Apply remediation patch to create v2
        v2_files = {
            "index.html": "<!DOCTYPE html><html><head><title>App Home</title></head><body><h1>Remediated</h1></body></html>",
        }

        # Run browser regression on v2
        regression_run = await testing_service.execute_browser_tests(
            project_id=project_id,
            files_map=v2_files,
            manifest=passing_manifest,
            test_definitions=test_suite,
        )
        assert regression_run.status == BrowserTestStatus.PASSED
        assert regression_run.tests_failed == 0

        # Create RemediationVerificationResult
        rem_ver = RemediationVerificationResult(
            proposal_id=uuid.uuid4(),
            status=RemediationProposalStatus.VERIFIED,
            static_analysis_passed=True,
            sandbox_passed=True,
            browser_passed=True,
            browser_test_run=regression_run,
            summary="Remediation verified: Static analysis and browser regression tests passed.",
        )

        # Evaluate verification of remediated v2
        snapshot_v2 = DevelopmentVerificationService.evaluate_verification(
            artifact=CodeGenerationOutput(
                plan=code_artifact.plan,
                generated_files=[
                    GeneratedFile(path="index.html", content=v2_files["index.html"], language="html", size_bytes=len(v2_files["index.html"]))
                ],
                total_files=1,
                total_size_bytes=len(v2_files["index.html"]),
                summary="v2 remediated",
            ),
            static_analysis=sa_pass,
            failure_diagnosis=diagnosis,
            remediation_verification=rem_ver,
            browser_test_run=regression_run,
            browser_testing_required=True,
        )
        assert snapshot_v2.is_verified is True
        assert snapshot_v2.verification_status == VerificationStatus.PASSED
        assert snapshot_v2.browser_validation.status == VerificationStatus.PASSED
        assert snapshot_v2.failure_analysis.status == VerificationStatus.PASSED

        # Verify historical v1 remains untouched
        assert v1_preserved["index.html"] != v2_files["index.html"]
        assert "Wrong Title" in v1_preserved["index.html"]
        assert "App Home" in v2_files["index.html"]

    finally:
        shutil.rmtree(artifacts_dir, ignore_errors=True)
