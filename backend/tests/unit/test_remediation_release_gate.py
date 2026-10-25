"""Unit and Regression Tests for SE IntelliPlatform Final Release Gate Remediation.

Explicitly verifies:
- BLOCKER 1: DevelopmentVersion runtime_manifest safe resolution in:
    A. Regression Execution
    B. Browser Journey Execution
    C. Assistant execute_regression_tests action
    D. Controlled error handling for missing/malformed runtime manifests (no AttributeError)
- BLOCKER 2: Remediation Verification Status:
    1. Remediation creates a new DevelopmentVersion
    2. The new version contains authoritative verification snapshot
    3. Status becomes VERIFIED when verification genuinely passes
    4. A failed verification remains FAILED_VERIFICATION
    5. Deployment accepts genuinely VERIFIED versions
    6. Promotion gates continue enforcing existing rules
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.agents.code_generation.contracts import (
    CodeGenerationOutput,
    CodeGenerationPlan,
    FileType,
    GeneratedFile,
    PlannedFile,
)
from app.sandbox.static_analysis.contracts import DiagnosticSeverity, StaticAnalysisResult, StaticAnalysisStatus
from app.schemas.runtime import ApplicationRuntimeManifest, create_default_fastapi_manifest
from app.agents.failure_analysis.contracts import (
    FailureDiagnosis,
    FailureType,
)
from app.agents.remediation.contracts import (
    ChangeOperation,
    ProposedChange,
    RemediationProposal,
    RemediationProposalStatus,
    RemediationVerificationResult,
    RiskLevel,
)
from app.agents.remediation.service import RemediationService
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.development_version import DevelopmentVersion, DevelopmentVersionStatus
from app.models.environment import EnvironmentType, DeploymentStatus
from app.models.project import Project, ProjectStatus
from app.models.requirement import Requirement, RequirementPriority, RequirementStatus, RequirementType
from app.models.workflow_execution import WorkflowExecution, WorkflowStatus
from app.sandbox.contracts import ExecutionResult, ExecutionStatus, ExecutionType
from app.sandbox.static_analysis.contracts import StaticAnalysisResult
from app.schemas.assistant import ActionStatus
from app.schemas.development_version import DevelopmentVersionResponse, VerificationSnapshot
from app.schemas.runtime import ApplicationRuntimeManifest
from app.services.development_version_service import DevelopmentVersionService
from app.services.engineering_action_service import EngineeringActionService
from app.services.environment_service import EnvironmentService
from app.services.browser_journey_service import BrowserJourneyService
from app.testing.inventory.contracts import (
    DiscoveryProvenance,
    TestTier,
    UnifiedTestDefinition,
    UnifiedTestInventory,
)
from app.testing.regression.contracts import (
    RegressionExecutionResult,
    RegressionExecutionStatus,
    RegressionPlan,
    RegressionPlanMode,
    SelectedTest,
)


@pytest.fixture
async def sample_project(db_session: AsyncSession) -> Project:
    proj = Project(
        name="Release Gate Project",
        slug="release-gate-proj",
        status=ProjectStatus.IN_PROGRESS,
        settings={},
    )
    db_session.add(proj)
    await db_session.flush()
    return proj


@pytest.fixture
async def sample_requirement(db_session: AsyncSession, sample_project: Project) -> Requirement:
    req = Requirement(
        project_id=sample_project.id,
        title="Sample Requirement",
        description="Verify user endpoints",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.HIGH,
        status=RequirementStatus.APPROVED,
    )
    db_session.add(req)
    await db_session.flush()
    return req


def make_code_output(has_bug: bool = False) -> CodeGenerationOutput:
    code = (
        "def test_example():\n    assert False\n"
        if has_bug
        else "def test_example():\n    assert True\n"
    )
    main_code = "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\ndef root():\n    return {'status': 'ok'}\n"
    files = [
        GeneratedFile(
            path="app/main.py",
            content=main_code,
            language="python",
            size_bytes=len(main_code),
            architecture_component="backend-service",
            requirement_ids=[],
        ),
        GeneratedFile(
            path="tests/test_main.py",
            content=code,
            language="python",
            size_bytes=len(code),
            architecture_component="testing",
            requirement_ids=[],
        ),
    ]
    plan = CodeGenerationPlan(
        project_type="backend-service",
        language="python",
        framework="fastapi",
        database="postgresql",
        package_manager="pip",
        files=[
            PlannedFile(
                path="app/main.py",
                purpose="Main API",
                file_type=FileType.SOURCE,
                architecture_component="backend-service",
            ),
            PlannedFile(
                path="tests/test_main.py",
                purpose="Tests",
                file_type=FileType.SOURCE,
                architecture_component="testing",
            ),
        ],
        rationale="Scaffold code output",
    )
    return CodeGenerationOutput(
        plan=plan,
        generated_files=files,
        total_files=len(files),
        total_size_bytes=sum(f.size_bytes for f in files),
        summary="Scaffold code",
    )


@pytest.fixture
async def sample_workflow_and_version(
    db_session: AsyncSession, sample_project: Project
) -> tuple[WorkflowExecution, DevelopmentVersion]:
    exec_id = uuid.uuid4()
    code_out = make_code_output(has_bug=False)
    raw_manifest = create_default_fastapi_manifest().model_dump(mode="json")

    wf = WorkflowExecution(
        workflow_execution_id=exec_id,
        project_id=sample_project.id,
        workflow_id="code-generation-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        step_count=1,
        completed_steps=1,
        failed_steps=0,
        skipped_steps=0,
        artifacts={
            "code-generation": code_out.model_dump(mode="json"),
            "runtime_manifest": raw_manifest,
        },
        errors=[],
    )
    db_session.add(wf)
    await db_session.flush()

    dev_service = DevelopmentVersionService(session=db_session)
    ver = await dev_service.register_version_from_workflow(
        project_id=sample_project.id,
        workflow_execution_id=exec_id,
        artifact_key="code-generation",
        source_reason="INITIAL_GENERATION",
    )
    await db_session.commit()
    await db_session.refresh(ver)
    return wf, ver


# =============================================================================
# BLOCKER 1 TESTS: runtime_manifest MISMATCH REMEDIATION
# =============================================================================

@pytest.mark.asyncio
async def test_blocker1_dev_version_response_has_no_runtime_manifest_attr(
    sample_project: Project,
    sample_workflow_and_version: tuple[WorkflowExecution, DevelopmentVersion],
    db_session: AsyncSession,
):
    """Confirm DevelopmentVersionResponse schema maintains contract without fake runtime_manifest."""
    _, ver = sample_workflow_and_version
    dev_service = DevelopmentVersionService(session=db_session)
    response_dto = await dev_service.get_version(sample_project.id, ver.id)

    assert isinstance(response_dto, DevelopmentVersionResponse)
    assert not hasattr(response_dto, "runtime_manifest")
    assert getattr(response_dto, "runtime_manifest", None) is None


@pytest.mark.asyncio
async def test_blocker1_resolve_runtime_manifest_from_version_service(
    sample_project: Project,
    sample_workflow_and_version: tuple[WorkflowExecution, DevelopmentVersion],
    db_session: AsyncSession,
):
    """Test authoritative resolution of ApplicationRuntimeManifest via DevelopmentVersionService."""
    _, ver = sample_workflow_and_version
    dev_service = DevelopmentVersionService(session=db_session)

    manifest = await dev_service.resolve_runtime_manifest(sample_project.id, ver.id)
    assert manifest is not None
    assert isinstance(manifest, ApplicationRuntimeManifest)
    assert manifest.application_port == 8000
    assert manifest.entrypoint == "app.main:app"


@pytest.mark.asyncio
async def test_blocker1_assistant_execute_regression_tests_works_with_version(
    sample_project: Project,
    sample_workflow_and_version: tuple[WorkflowExecution, DevelopmentVersion],
    sample_requirement: Requirement,
    db_session: AsyncSession,
):
    """Test Assistant EXECUTE_REGRESSION action succeeds with target_version_id without AttributeError."""
    _, ver = sample_workflow_and_version
    mock_executor = AsyncMock()
    mock_executor.execute_plan.return_value = RegressionExecutionResult(
        execution_id="exec-gate-001",
        project_id=str(sample_project.id).lower(),
        inventory_id="inv-gate-001",
        mode=RegressionPlanMode.SELECTIVE,
        status=RegressionExecutionStatus.PASSED,
        passed_tests=1,
        total_tests=1,
        duration_seconds=0.05,
    )

    from app.services.requirement_service import RequirementService
    version_svc = DevelopmentVersionService(session=db_session)
    req_svc = RequirementService(session=db_session)
    action_service = EngineeringActionService(
        session=db_session,
        version_service=version_svc,
        verification_service=MagicMock(),
        requirement_service=req_svc,
        context_engine=MagicMock(),
        workflow_service=MagicMock(),
        regression_executor=mock_executor,
    )

    result = await action_service.execute_action(
        action_id="EXECUTE_REGRESSION",
        parameters={
            "target_version_id": str(ver.id),
            "mode": "SELECTIVE",
            "changed_files": ["app/main.py"],
        },
        project_id=sample_project.id,
    )

    assert result.status == ActionStatus.SUCCESS
    assert result.action_id == "EXECUTE_REGRESSION"
    assert result.data["status"] == "PASSED"
    # Ensure executor was called and manifest was resolved
    assert mock_executor.execute_plan.called
    call_kwargs = mock_executor.execute_plan.call_args.kwargs
    assert call_kwargs["application_manifest"] is not None
    assert isinstance(call_kwargs["application_manifest"], ApplicationRuntimeManifest)


@pytest.mark.asyncio
async def test_blocker1_browser_journey_execution_with_development_version(
    sample_project: Project,
    sample_workflow_and_version: tuple[WorkflowExecution, DevelopmentVersion],
    db_session: AsyncSession,
):
    """Test BrowserJourneyService resolves version and file manifest without AttributeError."""
    _, ver = sample_workflow_and_version
    mock_context_engine = MagicMock()
    mock_context_engine.generate_context = AsyncMock()
    mock_context = MagicMock()
    mock_context.project.id = sample_project.id
    mock_context.project.name = "Release Gate Test Project"
    mock_context.requirements = []
    mock_context_engine.generate_context.return_value = mock_context

    mock_orchestrator = MagicMock()
    mock_result = MagicMock()
    mock_result.status.value = "COMPLETED"
    mock_result.completed_at = datetime.now(timezone.utc)
    mock_result.artifacts = {"browser_journey_input": {}}
    mock_result.errors = []
    mock_result.stage_reached = "EXECUTION"
    mock_result.candidate_suite = MagicMock(journeys=[])
    mock_result.validation_outcome = MagicMock(is_valid=True)
    mock_result.coverage_report = MagicMock(coverage_percentage=100.0, covered_requirement_ids=[], uncovered_requirement_ids=[])
    mock_result.test_definitions = []
    mock_result.browser_test_run = None
    mock_result.duration_seconds = 1.0

    mock_orchestrator.execute_workflow = AsyncMock(return_value=mock_result)

    version_svc = DevelopmentVersionService(session=db_session)
    journey_service = BrowserJourneyService(
        session=db_session,
        context_engine=mock_context_engine,
        version_service=version_svc,
        browser_testing_service=MagicMock(),
        workflow_service=MagicMock(),
        orchestrator=mock_orchestrator,
    )

    res = await journey_service.generate_and_execute_journeys(
        project_id=sample_project.id,
        version_id=ver.id,
        execute_browser_tests=False,
    )

    assert res.status.value == "COMPLETED"
    assert mock_orchestrator.execute_workflow.called
    call_kwargs = mock_orchestrator.execute_workflow.call_args.kwargs
    assert call_kwargs["runtime_manifest"] is not None
    assert isinstance(call_kwargs["runtime_manifest"], ApplicationRuntimeManifest)


@pytest.mark.asyncio
async def test_blocker1_malformed_runtime_manifest_produces_controlled_validation_error(
    sample_project: Project,
    db_session: AsyncSession,
):
    """Test that a malformed runtime manifest produces a controlled ValidationError, not AttributeError/HTTP 500."""
    exec_id = uuid.uuid4()
    code_out = make_code_output(has_bug=False)
    # Prohibited port 22 (SSH) violates ApplicationRuntimeManifest invariants
    malformed_manifest = {
        "runtime_type": "docker",
        "language": "python",
        "framework": "fastapi",
        "entrypoint": "app.main:app",
        "startup_command": ["python", "-m", "uvicorn", "app.main:app"],
        "application_port": 22,
        "health_check_path": "/",
    }

    wf = WorkflowExecution(
        workflow_execution_id=exec_id,
        project_id=sample_project.id,
        workflow_id="code-generation-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        step_count=1,
        completed_steps=1,
        failed_steps=0,
        skipped_steps=0,
        artifacts={
            "code-generation": code_out.model_dump(mode="json"),
            "runtime_manifest": malformed_manifest,
        },
        errors=[],
    )
    db_session.add(wf)
    await db_session.flush()

    dev_service = DevelopmentVersionService(session=db_session)
    ver = await dev_service.register_version_from_workflow(
        project_id=sample_project.id,
        workflow_execution_id=exec_id,
        artifact_key="code-generation",
        source_reason="INITIAL_GENERATION",
    )
    await db_session.commit()

    # Resolving malformed manifest must raise controlled ValidationError, NEVER AttributeError
    with pytest.raises(ValidationError) as exc_info:
        await dev_service.resolve_runtime_manifest(sample_project.id, ver.id)
    assert "Invalid runtime manifest" in str(exc_info.value)


# =============================================================================
# BLOCKER 2 TESTS: REMEDIATION VERIFICATION STATUS & DEPLOYMENT GATE
# =============================================================================

@pytest.mark.asyncio
async def test_blocker2_remediation_genuinely_verified_registers_verified_version(
    sample_project: Project,
    db_session: AsyncSession,
):
    """Test that applying an approved proposal with passing tests registers a VERIFIED version."""
    exec_id = uuid.uuid4()
    failing_code = make_code_output(has_bug=True)

    wf = WorkflowExecution(
        workflow_execution_id=exec_id,
        project_id=sample_project.id,
        workflow_id="code-generation-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        step_count=1,
        completed_steps=1,
        failed_steps=0,
        skipped_steps=0,
        artifacts={
            "code-generation": failing_code.model_dump(mode="json"),
            "static_analysis": {
                "analysis_id": str(uuid.uuid4()),
                "project_id": str(sample_project.id),
                "status": "PASSED",
                "error_count": 0,
                "warning_count": 0,
                "security_issue_count": 0,
                "diagnostics": [],
                "summary": "Static analysis passed",
            },
            "sandbox_execution": {
                "execution_id": str(uuid.uuid4()),
                "project_id": str(sample_project.id),
                "execution_type": "TEST",
                "status": "FAILED",
                "exit_code": 1,
                "tests_passed": 0,
                "tests_failed": 1,
                "tests_total": 1,
                "stdout": "FAIL",
                "stderr": "AssertionError",
            },
        },
        errors=[],
    )
    db_session.add(wf)
    await db_session.flush()

    dev_service = DevelopmentVersionService(session=db_session)
    v1 = await dev_service.register_version_from_workflow(
        project_id=sample_project.id,
        workflow_execution_id=exec_id,
        artifact_key="code-generation",
        source_reason="INITIAL_GENERATION",
    )
    assert v1.status == DevelopmentVersionStatus.FAILED_VERIFICATION

    # Build FailureDiagnosis and RemediationProposal
    diagnosis_id = uuid.uuid4()
    diag = FailureDiagnosis(
        diagnosis_id=diagnosis_id,
        failure_type=FailureType.TEST_FAILURE,
        severity=DiagnosticSeverity.ERROR,
        title="Unit test failed",
        summary="Unit test failed due to AssertionError in test_example",
        root_cause="AssertionError in test_example asserting False instead of True",
        suggested_remediation="Change assertion to assert True in test_main.py",
        affected_files=["tests/test_main.py"],
    )

    proposal_id = uuid.uuid4()
    good_test_code = "def test_example():\n    assert True\n"
    patch_change = ProposedChange(
        file_path="tests/test_main.py",
        operation=ChangeOperation.MODIFY,
        original_region="def test_example():\n    assert False",
        proposed_region="def test_example():\n    assert True",
        reason="Fix assertion to pass",
    )

    proposal = RemediationProposal(
        proposal_id=proposal_id,
        diagnosis_id=str(diagnosis_id),
        project_id=sample_project.id,
        workflow_execution_id=exec_id,
        title="Fix failing assertion in test",
        summary="Replaces failing assert False with assert True.",
        rationale="Fix failing assertion",
        changes=[patch_change],
        affected_files=["tests/test_main.py"],
        unified_diff="--- a/tests/test_main.py\n+++ b/tests/test_main.py\n@@ -1,2 +1,2 @@\n def test_example():\n-    assert False\n+    assert True\n",
        expected_effect="Tests pass without AssertionError",
        verification_plan="Run pytest in sandbox",
        risk_level=RiskLevel.LOW,
        status=RemediationProposalStatus.APPROVED,
        parent_artifact_version=1,
    )

    # Mock Static Analysis passing
    mock_sa = MagicMock()
    mock_sa.analyze_artifact = AsyncMock(
        return_value=StaticAnalysisResult(
            analysis_id=uuid.uuid4(),
            project_id=sample_project.id,
            status=StaticAnalysisStatus.PASSED,
            error_count=0,
            warning_count=0,
            security_issue_count=0,
            diagnostics=[],
            summary="Static analysis passed",
        )
    )

    # Mock Sandbox Execution passing
    mock_sb = MagicMock()
    mock_sb.execute = AsyncMock(
        return_value=ExecutionResult(
            execution_id=uuid.uuid4(),
            project_id=sample_project.id,
            execution_type=ExecutionType.TEST,
            status=ExecutionStatus.PASSED,
            exit_code=0,
            tests_passed=1,
            tests_failed=0,
            tests_total=1,
            stdout="1 passed in 0.01s",
            stderr="",
        )
    )

    remediation_service = RemediationService(
        session=db_session,
        workflow_service=MagicMock(),
        executor=MagicMock(),
        context_engine=MagicMock(),
        static_analysis_service=mock_sa,
        sandbox_executor=mock_sb,
    )

    wf.artifacts["remediation_proposal"] = proposal.model_dump(mode="json")
    flag_modified(wf, "artifacts")
    await db_session.commit()

    applied_proposal, ver_result = await remediation_service.apply_proposal(
        project_id=sample_project.id,
        proposal_id=proposal_id,
    )

    assert applied_proposal.status == RemediationProposalStatus.VERIFIED
    assert ver_result.status == RemediationProposalStatus.VERIFIED
    assert ver_result.static_analysis_passed is True
    assert ver_result.sandbox_passed is True

    # 1. Verify that remediation creates a new DevelopmentVersion (v2)
    versions_resp = await dev_service.list_versions(sample_project.id)
    v2_dto = next((v for v in versions_resp.items if v.version_number == 2), None)
    assert v2_dto is not None
    assert v2_dto.version_number == 2
    assert v2_dto.parent_version_id == v1.id
    assert v2_dto.source_reason == "REMEDIATION_PATCH"

    # 2. Verify that the new version contains the correct verification snapshot
    assert v2_dto.verification_summary is not None
    assert v2_dto.verification_summary.is_verified is True

    # 3. Status becomes VERIFIED when verification genuinely passes
    assert v2_dto.status == DevelopmentVersionStatus.VERIFIED

    # 4. Verify deployment accepts genuinely VERIFIED version
    env_service = EnvironmentService(session=db_session)
    envs = await env_service.get_or_create_project_environments(sample_project.id)
    dev_env = next(e for e in envs if e.environment_type == EnvironmentType.DEVELOPMENT)

    record = await env_service.deploy_version(
        project_id=sample_project.id,
        env_id_or_type=dev_env.id,
        version_id=v2_dto.version_id,
        requested_by="lead_dev",
    )
    assert record.status == DeploymentStatus.SUCCEEDED
    assert dev_env.current_version_id == v2_dto.version_id


@pytest.mark.asyncio
async def test_blocker2_remediation_failing_verification_remains_failed_and_rejected_by_deployment(
    sample_project: Project,
    db_session: AsyncSession,
):
    """Test that applying a proposal with failing tests remains FAILED_VERIFICATION and is rejected by deployment."""
    exec_id = uuid.uuid4()
    failing_code = make_code_output(has_bug=True)

    wf = WorkflowExecution(
        workflow_execution_id=exec_id,
        project_id=sample_project.id,
        workflow_id="code-generation-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        step_count=1,
        completed_steps=1,
        failed_steps=0,
        skipped_steps=0,
        artifacts={
            "code-generation": failing_code.model_dump(mode="json"),
            "static_analysis": {
                "analysis_id": str(uuid.uuid4()),
                "project_id": str(sample_project.id),
                "status": "PASSED",
                "error_count": 0,
                "warning_count": 0,
                "security_issue_count": 0,
                "diagnostics": [],
                "summary": "Clean static analysis",
            },
            "sandbox_execution": {
                "execution_id": str(uuid.uuid4()),
                "project_id": str(sample_project.id),
                "execution_type": "TEST",
                "status": "FAILED",
                "exit_code": 1,
                "tests_passed": 0,
                "tests_failed": 1,
                "tests_total": 1,
                "stdout": "FAIL",
                "stderr": "AssertionError",
            },
        },
        errors=[],
    )
    db_session.add(wf)
    await db_session.flush()

    dev_service = DevelopmentVersionService(session=db_session)
    v1 = await dev_service.register_version_from_workflow(
        project_id=sample_project.id,
        workflow_execution_id=exec_id,
        artifact_key="code-generation",
        source_reason="INITIAL_GENERATION",
    )

    diagnosis_id = uuid.uuid4()
    diag = FailureDiagnosis(
        diagnosis_id=diagnosis_id,
        failure_type=FailureType.TEST_FAILURE,
        severity=DiagnosticSeverity.ERROR,
        title="Unit test failed",
        summary="Unit test failed due to AssertionError in test_example",
        root_cause="AssertionError in test_example asserting False instead of True",
        suggested_remediation="Change assertion to assert True in test_main.py",
        affected_files=["tests/test_main.py"],
    )

    proposal_id = uuid.uuid4()
    patch_change = ProposedChange(
        file_path="tests/test_main.py",
        operation=ChangeOperation.MODIFY,
        original_region="def test_example():\n    assert False",
        proposed_region="def test_example():\n    assert False # still broken",
        reason="Still failing assertion",
    )

    proposal = RemediationProposal(
        proposal_id=proposal_id,
        diagnosis_id=str(diagnosis_id),
        project_id=sample_project.id,
        workflow_execution_id=exec_id,
        title="Attempted fix that still fails",
        summary="Still broken test modification.",
        rationale="Fix failing assertion",
        changes=[patch_change],
        affected_files=["tests/test_main.py"],
        unified_diff="--- a/tests/test_main.py\n+++ b/tests/test_main.py\n@@ -1,2 +1,2 @@\n def test_example():\n-    assert False\n+    assert False # still broken\n",
        expected_effect="Tests might still fail",
        verification_plan="Run pytest in sandbox",
        risk_level=RiskLevel.LOW,
        status=RemediationProposalStatus.APPROVED,
        parent_artifact_version=1,
    )

    # Mock Static Analysis passing
    mock_sa = MagicMock()
    mock_sa.analyze_artifact = AsyncMock(
        return_value=StaticAnalysisResult(
            analysis_id=uuid.uuid4(),
            project_id=sample_project.id,
            status=StaticAnalysisStatus.PASSED,
            error_count=0,
            warning_count=0,
            security_issue_count=0,
            diagnostics=[],
            summary="Clean static analysis",
        )
    )

    # Mock Sandbox Execution FAILING
    mock_sb = MagicMock()
    mock_sb.execute = AsyncMock(
        return_value=ExecutionResult(
            execution_id=uuid.uuid4(),
            project_id=sample_project.id,
            execution_type=ExecutionType.TEST,
            status=ExecutionStatus.FAILED,
            exit_code=1,
            tests_passed=0,
            tests_failed=1,
            tests_total=1,
            stdout="FAIL",
            stderr="AssertionError: still broken",
        )
    )

    remediation_service = RemediationService(
        session=db_session,
        workflow_service=MagicMock(),
        executor=MagicMock(),
        context_engine=MagicMock(),
        static_analysis_service=mock_sa,
        sandbox_executor=mock_sb,
    )

    wf.artifacts["remediation_proposal"] = proposal.model_dump(mode="json")
    flag_modified(wf, "artifacts")
    await db_session.commit()

    applied_proposal, ver_result = await remediation_service.apply_proposal(
        project_id=sample_project.id,
        proposal_id=proposal_id,
    )

    assert applied_proposal.status == RemediationProposalStatus.VERIFICATION_FAILED
    assert ver_result.status == RemediationProposalStatus.VERIFICATION_FAILED
    assert ver_result.sandbox_passed is False

    # Check registered version
    versions_resp = await dev_service.list_versions(sample_project.id)
    v2_dto = next((v for v in versions_resp.items if v.version_number == 2), None)
    assert v2_dto is not None
    # 4. A failed verification remains FAILED_VERIFICATION
    assert v2_dto.status == DevelopmentVersionStatus.FAILED_VERIFICATION
    assert v2_dto.verification_summary.is_verified is False

    # 5. Deployment rejects FAILED_VERIFICATION version
    env_service = EnvironmentService(session=db_session)
    envs = await env_service.get_or_create_project_environments(sample_project.id)
    dev_env = next(e for e in envs if e.environment_type == EnvironmentType.DEVELOPMENT)

    with pytest.raises(ConflictError):
        await env_service.deploy_version(
            project_id=sample_project.id,
            env_id_or_type=dev_env.id,
            version_id=v2_dto.version_id,
            requested_by="lead_dev",
        )
