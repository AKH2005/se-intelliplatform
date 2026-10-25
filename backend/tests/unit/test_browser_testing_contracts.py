"""Unit Tests for Browser Testing Contracts and Verification Integration (Phase 11J - Stage 1)."""

import uuid
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.schemas.browser_testing import (
    BrowserArtifactReference,
    BrowserArtifactType,
    BrowserConsoleError,
    BrowserNetworkRecord,
    BrowserTestCaseResult,
    BrowserTestRun,
    BrowserTestStatus,
)
from app.schemas.development_version import (
    StageVerificationResult,
    VerificationRequirementLevel,
    VerificationSnapshot,
    VerificationStatus,
)


class TestBrowserArtifactReference:
    """Test BrowserArtifactReference model and path validation."""

    def test_valid_artifact_reference(self):
        ref = BrowserArtifactReference(
            artifact_type=BrowserArtifactType.SCREENSHOT,
            file_path="artifacts/screenshots/step_1.png",
            size_bytes=1024 * 50,
            content_type="image/png",
            caption="Initial page load rendering",
            step_number=1,
        )
        assert ref.artifact_type == BrowserArtifactType.SCREENSHOT
        assert ref.file_path == "artifacts/screenshots/step_1.png"
        assert ref.size_bytes == 51200
        assert ref.step_number == 1

    @pytest.mark.parametrize("bad_path", [
        "/absolute/path/screenshot.png",
        "\\absolute\\path\\screenshot.png",
        "artifacts/../../etc/passwd",
        "C:\\Windows\\screenshot.png",
        "D:screenshot.png",
    ])
    def test_reject_unsafe_artifact_paths(self, bad_path: str):
        with pytest.raises(ValidationError):
            BrowserArtifactReference(
                artifact_type=BrowserArtifactType.SCREENSHOT,
                file_path=bad_path,
            )

    def test_reject_oversized_artifact(self):
        with pytest.raises(ValidationError):
            BrowserArtifactReference(
                artifact_type=BrowserArtifactType.SCREENSHOT,
                file_path="screenshot.png",
                size_bytes=15 * 1024 * 1024,  # Exceeds 10 MB limit
            )

    def test_reject_extra_fields(self):
        with pytest.raises(ValidationError):
            BrowserArtifactReference(
                artifact_type=BrowserArtifactType.SCREENSHOT,
                file_path="screenshot.png",
                extra_field="disallowed",  # type: ignore[call-arg]
            )


class TestBrowserConsoleAndNetworkTelemetry:
    """Test console errors and network telemetry models."""

    def test_valid_console_error(self):
        err = BrowserConsoleError(
            level="error",
            message="Uncaught TypeError: Cannot read property 'map' of undefined",
            source="http://localhost:8000/static/bundle.js",
            line_number=42,
        )
        assert err.level == "error"
        assert "Cannot read property" in err.message
        assert err.line_number == 42

    def test_reject_oversized_console_message(self):
        with pytest.raises(ValidationError):
            BrowserConsoleError(message="A" * 1500)

    def test_valid_network_record(self):
        rec = BrowserNetworkRecord(
            method="POST",
            url="http://app-1234:8000/api/items",
            status_code=500,
            response_time_ms=125.4,
            failed=True,
            error_message="Internal Server Error: Database locked",
        )
        assert rec.method == "POST"
        assert rec.status_code == 500
        assert rec.failed is True

    @pytest.mark.parametrize("bad_status", [50, 99, 600, 1000])
    def test_reject_invalid_http_status_codes(self, bad_status: int):
        with pytest.raises(ValidationError):
            BrowserNetworkRecord(
                url="http://app:8000/api",
                status_code=bad_status,
            )


class TestBrowserTestCaseResult:
    """Test individual browser test case results and bounding limits."""

    def test_valid_passed_test_case(self):
        case = BrowserTestCaseResult(
            test_id="test_docs_navigation",
            name="Verify Swagger UI loads and renders endpoints",
            status=BrowserTestStatus.PASSED,
            duration_seconds=1.85,
            assertion_summary="Asserted page title contains 'FastAPI - Swagger UI'",
        )
        assert case.status == BrowserTestStatus.PASSED
        assert case.duration_seconds == 1.85
        assert case.assertion_summary is not None

    def test_valid_failed_test_case_with_evidence(self):
        screenshot = BrowserArtifactReference(
            artifact_type=BrowserArtifactType.SCREENSHOT,
            file_path="screenshots/fail_step_2.png",
        )
        console_err = BrowserConsoleError(
            message="Failed to load resource: net::ERR_CONNECTION_REFUSED",
        )
        net_err = BrowserNetworkRecord(
            url="http://app-1:8000/api/nonexistent",
            status_code=404,
            failed=True,
        )

        case = BrowserTestCaseResult(
            test_id="test_order_checkout",
            name="User checkout flow",
            status=BrowserTestStatus.FAILED,
            duration_seconds=4.2,
            failed_step="Click '#submit-order-button'",
            assertion_summary="Expected HTTP 200, received 404",
            screenshots=[screenshot],
            console_errors=[console_err],
            network_errors=[net_err],
        )
        assert case.status == BrowserTestStatus.FAILED
        assert case.failed_step == "Click '#submit-order-button'"
        assert len(case.screenshots) == 1
        assert len(case.console_errors) == 1
        assert len(case.network_errors) == 1

    def test_reject_excessive_screenshots_per_case(self):
        screenshots = [
            BrowserArtifactReference(
                artifact_type=BrowserArtifactType.SCREENSHOT,
                file_path=f"screenshot_{i}.png",
            )
            for i in range(10)  # Max is 5
        ]
        with pytest.raises(ValidationError):
            BrowserTestCaseResult(
                test_id="test_heavy",
                name="Too many screenshots",
                status=BrowserTestStatus.PASSED,
                screenshots=screenshots,
            )


class TestBrowserTestRun:
    """Test aggregate BrowserTestRun session model and validation rules."""

    def test_valid_browser_test_run(self):
        project_id = uuid.uuid4()
        version_id = uuid.uuid4()

        run = BrowserTestRun(
            project_id=project_id,
            version_id=version_id,
            status=BrowserTestStatus.PASSED,
            tests_total=2,
            tests_passed=2,
            tests_failed=0,
            tests_skipped=0,
            duration_seconds=3.4,
            summary="All 2 browser test flows completed successfully.",
        )
        assert run.project_id == project_id
        assert run.version_id == version_id
        assert run.status == BrowserTestStatus.PASSED
        assert run.tests_passed == 2

    def test_reject_passed_status_when_tests_failed_greater_than_zero(self):
        with pytest.raises(ValidationError) as exc_info:
            BrowserTestRun(
                project_id=uuid.uuid4(),
                status=BrowserTestStatus.PASSED,
                tests_total=3,
                tests_passed=2,
                tests_failed=1,
            )
        assert "cannot have status PASSED when tests_failed=1" in str(exc_info.value)

    def test_roundtrip_json_serialization(self):
        run = BrowserTestRun(
            project_id=uuid.uuid4(),
            status=BrowserTestStatus.FAILED,
            tests_total=1,
            tests_passed=0,
            tests_failed=1,
            duration_seconds=5.0,
            failure_reason="Application server returned 500 on root route.",
            summary="Browser test execution failed on 1 test case.",
        )
        dumped = run.model_dump(mode="json")
        rehydrated = BrowserTestRun.model_validate(dumped)

        assert rehydrated.run_id == run.run_id
        assert rehydrated.status == BrowserTestStatus.FAILED
        assert rehydrated.tests_failed == 1
        assert rehydrated.failure_reason == run.failure_reason


class TestVerificationSnapshotIntegration:
    """Test VerificationSnapshot compatibility and browser_validation stage support."""

    @pytest.fixture
    def sample_base_stages(self):
        """Generate sample passing baseline stages for static_analysis, sandbox, ai_tests, and failure_analysis."""
        return {
            "static_analysis": StageVerificationResult(
                stage="static_analysis",
                requirement_level=VerificationRequirementLevel.REQUIRED,
                status=VerificationStatus.PASSED,
                details="Zero linting or AST syntax errors.",
                error_count=0,
                warning_count=0,
                blocking_issues=[],
            ),
            "sandbox_execution": StageVerificationResult(
                stage="sandbox_execution",
                requirement_level=VerificationRequirementLevel.REQUIRED,
                status=VerificationStatus.PASSED,
                details="All 4 sandbox unit tests passed.",
                error_count=0,
                warning_count=0,
                blocking_issues=[],
            ),
            "ai_tests": StageVerificationResult(
                stage="ai_tests",
                requirement_level=VerificationRequirementLevel.OPTIONAL,
                status=VerificationStatus.NOT_RUN,
                details="No AI tests generated for this version.",
                error_count=0,
                warning_count=0,
                blocking_issues=[],
            ),
            "failure_analysis": StageVerificationResult(
                stage="failure_analysis",
                requirement_level=VerificationRequirementLevel.NOT_APPLICABLE,
                status=VerificationStatus.PASSED,
                details="No active failure diagnoses.",
                error_count=0,
                warning_count=0,
                blocking_issues=[],
            ),
        }

    def test_verification_snapshot_without_browser_validation_backwards_compatible(self, sample_base_stages):
        """Existing 4-stage snapshot works seamlessly when browser_validation is omitted."""
        snapshot = VerificationSnapshot(
            verification_status=VerificationStatus.PASSED,
            is_verified=True,
            summary="All required checks passed cleanly.",
            **sample_base_stages,
        )
        assert snapshot.browser_validation is None
        assert snapshot.is_verified is True
        assert snapshot.verification_status == VerificationStatus.PASSED

        # Roundtrip JSON test
        data = snapshot.model_dump(mode="json")
        assert "browser_validation" in data
        assert data["browser_validation"] is None
        rehydrated = VerificationSnapshot.model_validate(data)
        assert rehydrated.browser_validation is None

    def test_verification_snapshot_with_browser_validation_passed(self, sample_base_stages):
        """Snapshot supports browser_validation as 5th stage with PASSED status."""
        browser_stage = StageVerificationResult(
            stage="browser_validation",
            requirement_level=VerificationRequirementLevel.REQUIRED,
            status=VerificationStatus.PASSED,
            details="All 3 browser end-to-end user flows passed successfully.",
            error_count=0,
            warning_count=0,
            blocking_issues=[],
        )

        snapshot = VerificationSnapshot(
            verification_status=VerificationStatus.PASSED,
            is_verified=True,
            summary="All 5 verification stages passed including browser validation.",
            browser_validation=browser_stage,
            **sample_base_stages,
        )
        assert snapshot.browser_validation is not None
        assert snapshot.browser_validation.stage == "browser_validation"
        assert snapshot.browser_validation.status == VerificationStatus.PASSED
        assert snapshot.browser_validation.requirement_level == VerificationRequirementLevel.REQUIRED

        # Roundtrip JSON test
        data = snapshot.model_dump(mode="json")
        rehydrated = VerificationSnapshot.model_validate(data)
        assert rehydrated.browser_validation is not None
        assert rehydrated.browser_validation.status == VerificationStatus.PASSED

    def test_verification_snapshot_with_browser_validation_failed(self, sample_base_stages):
        """Snapshot correctly represents a FAILED browser_validation stage."""
        browser_stage = StageVerificationResult(
            stage="browser_validation",
            requirement_level=VerificationRequirementLevel.REQUIRED,
            status=VerificationStatus.FAILED,
            details="Application server raised HTTP 500 during browser checkout flow.",
            error_count=1,
            warning_count=0,
            blocking_issues=["Browser assertion failed: expected 200, got 500"],
        )

        snapshot = VerificationSnapshot(
            verification_status=VerificationStatus.FAILED,
            is_verified=False,
            summary="Verification failed: browser validation encountered 1 blocking issue.",
            browser_validation=browser_stage,
            **sample_base_stages,
        )
        assert snapshot.is_verified is False
        assert snapshot.verification_status == VerificationStatus.FAILED
        assert snapshot.browser_validation is not None
        assert snapshot.browser_validation.status == VerificationStatus.FAILED
        assert len(snapshot.browser_validation.blocking_issues) == 1

    def test_verification_snapshot_with_browser_validation_not_run(self, sample_base_stages):
        """Snapshot supports OPTIONAL or NOT_APPLICABLE browser_validation when tests are not configured."""
        browser_stage = StageVerificationResult(
            stage="browser_validation",
            requirement_level=VerificationRequirementLevel.OPTIONAL,
            status=VerificationStatus.NOT_RUN,
            details="No browser test suite configured for this version.",
            error_count=0,
            warning_count=0,
            blocking_issues=[],
        )

        snapshot = VerificationSnapshot(
            verification_status=VerificationStatus.PASSED,
            is_verified=True,
            summary="Verification passed without optional browser validation.",
            browser_validation=browser_stage,
            **sample_base_stages,
        )
        assert snapshot.browser_validation is not None
        assert snapshot.browser_validation.status == VerificationStatus.NOT_RUN
        assert snapshot.browser_validation.requirement_level == VerificationRequirementLevel.OPTIONAL
        assert snapshot.is_verified is True
