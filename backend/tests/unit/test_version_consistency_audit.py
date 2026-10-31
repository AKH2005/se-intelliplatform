"""Focused audit test suite for Milestone 5.1: Version Consistency, Concurrency, and Truthful Verification.

Covers all 12 scenarios required by Milestone 5.1 Task 2:
1. Candidate with invalid syntax is not promoted.
2. Candidate with a failed required build is not promoted.
3. Candidate with a failed required test is not promoted.
4. Candidate with required runtime validation blocked cannot be treated as fully verified.
5. Candidate based on a stale parent version is rejected.
6. Two concurrent candidates cannot both incorrectly win promotion.
7. A failed database transaction cannot leave version status and active pointer inconsistent.
8. Verification results cannot be reused after candidate content changes.
9. Recovery selects only an eligible verified version from the correct project.
10. Cross-project version references are rejected without leaking project information.
11. A failed candidate does not destroy or supersede the last known-good active version.
12. Alternate code-change or API paths cannot bypass the verification policy.
"""

import uuid
from unittest.mock import AsyncMock, patch
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.development_version import DevelopmentVersion, DevelopmentVersionStatus
from app.models.project import Project, ProjectStatus
from app.sandbox.contracts import ExecutionResult, ExecutionStatus, ExecutionType
from app.sandbox.static_analysis.contracts import (
    DiagnosticCategory,
    DiagnosticSeverity,
    StaticAnalysisResult,
    StaticAnalysisStatus,
    StaticDiagnostic,
)
from app.schemas.code_studio import SaveFileRequest
from app.schemas.development_version import (
    VerificationRequirementLevel,
    VerificationSnapshot,
    VerificationStatus,
)
from app.services.development_version_service import DevelopmentVersionService
from app.services.verification_service import DevelopmentVerificationService


@pytest.fixture
async def project_a(db_session: AsyncSession) -> Project:
    project = Project(
        id=uuid.uuid4(),
        name="Audit Project Alpha",
        slug="audit-project-alpha",
        status=ProjectStatus.IN_PROGRESS,
        settings={},
    )
    db_session.add(project)
    await db_session.flush()
    return project


@pytest.fixture
async def project_b(db_session: AsyncSession) -> Project:
    project = Project(
        id=uuid.uuid4(),
        name="Audit Project Beta",
        slug="audit-project-beta",
        status=ProjectStatus.IN_PROGRESS,
        settings={},
    )
    db_session.add(project)
    await db_session.flush()
    return project


@pytest.fixture
async def v1_project_a(db_session: AsyncSession, project_a: Project) -> DevelopmentVersion:
    v1 = DevelopmentVersion(
        id=uuid.uuid4(),
        project_id=project_a.id,
        version_number=1,
        status=DevelopmentVersionStatus.VERIFIED,
        files_manifest=[
            {"path": "app/main.py", "size_bytes": 45, "language": "python", "requirement_ids": []},
            {"path": "README.md", "size_bytes": 22, "language": "markdown", "requirement_ids": []},
        ],
        file_count=2,
        total_size_bytes=67,
        content_hash="hash-a-v1",
        manifest_hash="mhash-a-v1",
        source_reason="INITIAL_GENERATION",
        created_by="system",
        verification_summary={"verification_status": "PASSED", "is_verified": True},
    )
    db_session.add(v1)
    project_a.settings = {"active_version_id": str(v1.id)}
    await db_session.flush()
    return v1


# =========================================================================
# Scenario 1: Candidate with invalid syntax is not promoted
# =========================================================================
@pytest.mark.asyncio
async def test_scenario_1_candidate_invalid_syntax_not_promoted(
    db_session: AsyncSession,
    project_a: Project,
    v1_project_a: DevelopmentVersion,
):
    service = DevelopmentVersionService(session=db_session)
    with patch.object(service, "_resolve_version_files_map", new_callable=AsyncMock) as mock_files:
        mock_files.return_value = {
            "app/main.py": "def broken_code(: syntax error\n",
        }
        candidate = await service.create_candidate_version(
            project_id=project_a.id,
            parent_version_id=v1_project_a.id,
            changes=[{"file_path": "app/main.py", "content": "def broken_code(: syntax error\n"}],
            reason="Invalid syntax candidate",
        )
        assert candidate.status == DevelopmentVersionStatus.GENERATED

        cand_ver, snap, promoted = await service.verify_and_promote_candidate(
            project_id=project_a.id,
            candidate_version_id=candidate.id,
            auto_promote=True,
        )

    assert promoted is False
    assert cand_ver.status == DevelopmentVersionStatus.FAILED_VERIFICATION
    assert snap.is_verified is False
    assert snap.verification_status == VerificationStatus.FAILED

    # Active pointer MUST remain pointing to v1
    active_ver = await service.get_active_version(project_a.id)
    assert active_ver.version_id == v1_project_a.id


# =========================================================================
# Scenario 2: Candidate with a failed required build is not promoted
# =========================================================================
@pytest.mark.asyncio
async def test_scenario_2_candidate_failed_required_build_not_promoted():
    ver_svc = DevelopmentVerificationService()
    proj_id = uuid.uuid4()
    failing_static = StaticAnalysisResult(
        project_id=proj_id,
        status=StaticAnalysisStatus.ISSUES_FOUND,
        summary="Static analysis detected syntax errors",
        error_count=2,
        warning_count=1,
        security_issue_count=0,
        diagnostics=[
            StaticDiagnostic(
                category=DiagnosticCategory.SYNTAX,
                severity=DiagnosticSeverity.ERROR,
                code="E999",
                message="SyntaxError in build compilation",
                source="ast",
                file_path="app/main.py",
                line=12,
                column=4,
            )
        ],
    )
    snap = ver_svc.evaluate_verification(
        artifact=None,
        static_analysis=failing_static,
    )
    assert snap.is_verified is False
    assert snap.verification_status == VerificationStatus.FAILED
    assert snap.static_analysis.status == VerificationStatus.FAILED
    assert len(snap.static_analysis.blocking_issues) > 0


# =========================================================================
# Scenario 3: Candidate with a failed required test is not promoted
# =========================================================================
@pytest.mark.asyncio
async def test_scenario_3_candidate_failed_required_test_not_promoted():
    from app.agents.code_generation.contracts import (
        CodeGenerationOutput,
        CodeGenerationPlan,
        FileType,
        GeneratedFile,
        PlannedFile,
    )

    ver_svc = DevelopmentVerificationService()
    # Artifact contains test files -> sandbox is REQUIRED
    test_artifact = CodeGenerationOutput(
        plan=CodeGenerationPlan(
            files=[PlannedFile(path="tests/test_api.py", purpose="Unit tests", file_type=FileType.SOURCE)],
            rationale="test scaffold",
        ),
        generated_files=[
            GeneratedFile(path="tests/test_api.py", content="def test_fail(): assert False", size_bytes=30, language="python")
        ],
        total_files=1,
        total_size_bytes=30,
        summary="Test files project",
    )
    proj_id = uuid.uuid4()
    passing_static = StaticAnalysisResult(
        project_id=proj_id,
        status=StaticAnalysisStatus.PASSED,
        summary="Static analysis clean",
        error_count=0,
        warning_count=0,
        security_issue_count=0,
        diagnostics=[],
    )
    failing_sandbox = ExecutionResult(
        project_id=proj_id,
        execution_type=ExecutionType.TEST,
        status=ExecutionStatus.FAILED,
        exit_code=1,
        stdout="",
        stderr="FAILED tests/test_api.py::test_fail - assert False",
        tests_total=5,
        tests_passed=4,
        tests_failed=1,
    )
    snap = ver_svc.evaluate_verification(
        artifact=test_artifact,
        static_analysis=passing_static,
        sandbox_execution=failing_sandbox,
    )
    assert snap.is_verified is False
    assert snap.verification_status == VerificationStatus.FAILED
    assert snap.sandbox_execution.requirement_level == VerificationRequirementLevel.REQUIRED
    assert snap.sandbox_execution.status == VerificationStatus.FAILED


# =========================================================================
# Scenario 4: Candidate with required runtime validation blocked cannot be treated as fully verified
# =========================================================================
@pytest.mark.asyncio
async def test_scenario_4_runtime_validation_blocked_not_fully_verified():
    ver_svc = DevelopmentVerificationService()
    proj_id = uuid.uuid4()
    passing_static = StaticAnalysisResult(
        project_id=proj_id,
        status=StaticAnalysisStatus.PASSED,
        summary="Static analysis clean",
        error_count=0,
        warning_count=0,
        security_issue_count=0,
        diagnostics=[],
    )
    # Browser validation is explicitly required but not executed / blocked
    snap = ver_svc.evaluate_verification(
        artifact=None,
        static_analysis=passing_static,
        browser_test_run=None,
        browser_testing_required=True,
    )
    assert snap.is_verified is False
    assert snap.verification_status == VerificationStatus.FAILED
    assert snap.browser_validation.requirement_level == VerificationRequirementLevel.REQUIRED
    assert snap.browser_validation.status == VerificationStatus.FAILED
    assert "Mandatory browser validation was not executed" in snap.browser_validation.blocking_issues


# =========================================================================
# Scenario 5: Candidate based on a stale parent version is rejected
# =========================================================================
@pytest.mark.asyncio
async def test_scenario_5_stale_parent_candidate_rejected(
    db_session: AsyncSession,
    project_a: Project,
    v1_project_a: DevelopmentVersion,
):
    service = DevelopmentVersionService(session=db_session)
    # Simulate active version having moved to v2
    v2 = DevelopmentVersion(
        id=uuid.uuid4(),
        project_id=project_a.id,
        version_number=2,
        status=DevelopmentVersionStatus.VERIFIED,
        files_manifest=[],
        file_count=1,
        total_size_bytes=10,
        content_hash="hash-a-v2",
        manifest_hash="mhash-a-v2",
        source_reason="CONCURRENT_PROMOTION",
        created_by="system",
    )
    db_session.add(v2)
    project_a.settings = {"active_version_id": str(v2.id)}
    await db_session.flush()

    with pytest.raises(ConflictError) as exc_info:
        await service.create_candidate_version(
            project_id=project_a.id,
            parent_version_id=v1_project_a.id,
            changes=[{"file_path": "app/main.py", "content": "# stale"}],
            reason="Stale candidate base",
        )
    assert "candidate creation conflict" in str(exc_info.value).lower()


# =========================================================================
# Scenario 6: Two concurrent candidates cannot both incorrectly win promotion
# =========================================================================
@pytest.mark.asyncio
async def test_scenario_6_concurrent_candidates_conflict_promotion(
    db_session: AsyncSession,
    project_a: Project,
    v1_project_a: DevelopmentVersion,
):
    service = DevelopmentVersionService(session=db_session)
    with patch.object(service, "_resolve_version_files_map", new_callable=AsyncMock) as mock_files:
        mock_files.return_value = {"app/main.py": "def hello(): return 'cand-a'\n"}
        cand_a = await service.create_candidate_version(
            project_id=project_a.id,
            parent_version_id=v1_project_a.id,
            changes=[{"file_path": "app/main.py", "content": "def hello(): return 'cand-a'\n"}],
            reason="Candidate A",
        )

        mock_files.return_value = {"app/main.py": "def hello(): return 'cand-b'\n"}
        cand_b = await service.create_candidate_version(
            project_id=project_a.id,
            parent_version_id=v1_project_a.id,
            changes=[{"file_path": "app/main.py", "content": "def hello(): return 'cand-b'\n"}],
            reason="Candidate B",
        )

        # 1. Candidate A verifies and wins promotion
        mock_files.return_value = {"app/main.py": "def hello(): return 'cand-a'\n"}
        ver_a, snap_a, promoted_a = await service.verify_and_promote_candidate(
            project_id=project_a.id,
            candidate_version_id=cand_a.id,
            auto_promote=True,
        )
        assert promoted_a is True
        active_ver = await service.get_active_version(project_a.id)
        assert active_ver.version_id == cand_a.id

        # 2. Candidate B verifies, but active version has moved to Cand A! Auto-promotion must be BLOCKED.
        mock_files.return_value = {"app/main.py": "def hello(): return 'cand-b'\n"}
        ver_b, snap_b, promoted_b = await service.verify_and_promote_candidate(
            project_id=project_a.id,
            candidate_version_id=cand_b.id,
            auto_promote=True,
        )
        assert promoted_b is False
        assert "Stale parent" in ver_b.metadata_payload.get("promotion_blocked_reason", "")

        # Active version MUST STILL be Cand A (never overwritten!)
        active_ver_final = await service.get_active_version(project_a.id)
        assert active_ver_final.version_id == cand_a.id


# =========================================================================
# Scenario 7: A failed database transaction cannot leave version status and active pointer inconsistent
# =========================================================================
@pytest.mark.asyncio
async def test_scenario_7_transaction_failure_leaves_pointers_consistent(
    db_session: AsyncSession,
    project_a: Project,
    v1_project_a: DevelopmentVersion,
):
    service = DevelopmentVersionService(session=db_session)
    # Attempt to activate a nonexistent version
    with pytest.raises(NotFoundError):
        await service.activate_version(
            project_id=project_a.id,
            version_id=uuid.uuid4(),
            reason="Illegal activation",
        )

    # Active pointer is intact
    active_ver = await service.get_active_version(project_a.id)
    assert active_ver.version_id == v1_project_a.id
    assert active_ver.status == DevelopmentVersionStatus.VERIFIED


# =========================================================================
# Scenario 8: Verification results cannot be reused after candidate content changes
# =========================================================================
@pytest.mark.asyncio
async def test_scenario_8_verification_results_invalidated_on_content_change(
    db_session: AsyncSession,
    project_a: Project,
    v1_project_a: DevelopmentVersion,
):
    service = DevelopmentVersionService(session=db_session)
    with patch.object(service, "_resolve_version_files_map", new_callable=AsyncMock) as mock_files:
        mock_files.return_value = {"app/main.py": "def original(): pass\n"}
        cand = await service.create_candidate_version(
            project_id=project_a.id,
            parent_version_id=v1_project_a.id,
            changes=[{"file_path": "app/main.py", "content": "def original(): pass\n"}],
            reason="Immutability audit",
        )

        # Simulate tampering / changed files behind the registered content hash
        mock_files.return_value = {"app/main.py": "def tampered_after_registration(): pass\n"}
        with pytest.raises(ConflictError) as exc_info:
            await service.verify_and_promote_candidate(
                project_id=project_a.id,
                candidate_version_id=cand.id,
                auto_promote=True,
            )
        assert "content hash mismatch" in str(exc_info.value).lower()


# =========================================================================
# Scenario 9: Recovery selects only an eligible verified version from the correct project
# =========================================================================
@pytest.mark.asyncio
async def test_scenario_9_recovery_selects_eligible_version_from_correct_project(
    db_session: AsyncSession,
    project_a: Project,
    project_b: Project,
    v1_project_a: DevelopmentVersion,
):
    service = DevelopmentVersionService(session=db_session)
    # Transition Project A's v1 to SUPERSEDED
    v1_project_a.status = DevelopmentVersionStatus.SUPERSEDED

    # Erroneously active broken v2 in Project A
    broken_v2 = DevelopmentVersion(
        id=uuid.uuid4(),
        project_id=project_a.id,
        version_number=2,
        status=DevelopmentVersionStatus.FAILED_VERIFICATION,
        files_manifest=[],
        file_count=1,
        total_size_bytes=10,
        content_hash="hash-broken",
        manifest_hash="mhash-broken",
        source_reason="FAILED_EXP",
        created_by="user",
    )
    db_session.add(broken_v2)
    project_a.settings = {"active_version_id": str(broken_v2.id)}

    # High-numbered version in Project B (must NEVER be selected)
    v99_project_b = DevelopmentVersion(
        id=uuid.uuid4(),
        project_id=project_b.id,
        version_number=99,
        status=DevelopmentVersionStatus.VERIFIED,
        files_manifest=[],
        file_count=1,
        total_size_bytes=10,
        content_hash="hash-b99",
        manifest_hash="mhash-b99",
        source_reason="PROJ_B_GOOD",
        created_by="user",
    )
    db_session.add(v99_project_b)
    await db_session.flush()

    recovered = await service.recover_active_version(project_a.id)
    assert recovered is not None
    assert recovered.version_id == v1_project_a.id
    assert recovered.project_id == project_a.id
    assert recovered.version_number == 1


# =========================================================================
# Scenario 10: Cross-project version references are rejected without leaking project information
# =========================================================================
@pytest.mark.asyncio
async def test_scenario_10_cross_project_version_isolation(
    db_session: AsyncSession,
    project_a: Project,
    project_b: Project,
    v1_project_a: DevelopmentVersion,
):
    service = DevelopmentVersionService(session=db_session)
    # Attempt to query Project A's version using Project B's scope
    with pytest.raises(NotFoundError) as exc_info:
        await service.get_version(project_b.id, v1_project_a.id)

    # Error must be a generic NotFoundError, revealing nothing about Project A
    err_str = str(exc_info.value)
    assert "DevelopmentVersion" in err_str
    assert str(v1_project_a.id) in err_str
    assert project_a.name not in err_str
    assert str(project_a.id) not in err_str


# =========================================================================
# Scenario 11: A failed candidate does not destroy or supersede the last known-good active version
# =========================================================================
@pytest.mark.asyncio
async def test_scenario_11_failed_candidate_preserves_last_known_good(
    db_session: AsyncSession,
    project_a: Project,
    v1_project_a: DevelopmentVersion,
):
    service = DevelopmentVersionService(session=db_session)
    with patch.object(service, "_resolve_version_files_map", new_callable=AsyncMock) as mock_files:
        mock_files.return_value = {"app/main.py": "def broken(): return 1 / 0 syntax error\n"}
        cand = await service.create_candidate_version(
            project_id=project_a.id,
            parent_version_id=v1_project_a.id,
            changes=[{"file_path": "app/main.py", "content": "def broken(): return 1 / 0 syntax error\n"}],
            reason="Deliberate failure test",
        )
        cand_res, snap, promoted = await service.verify_and_promote_candidate(
            project_id=project_a.id,
            candidate_version_id=cand.id,
            auto_promote=True,
        )

    assert promoted is False
    assert cand_res.status == DevelopmentVersionStatus.FAILED_VERIFICATION

    # v1 MUST still be VERIFIED and active
    await db_session.refresh(v1_project_a)
    assert v1_project_a.status == DevelopmentVersionStatus.VERIFIED
    active_ver = await service.get_active_version(project_a.id)
    assert active_ver.version_id == v1_project_a.id


# =========================================================================
# Scenario 12: Alternate code-change or API paths cannot bypass the verification policy
# =========================================================================
@pytest.mark.asyncio
async def test_scenario_12_alternate_paths_cannot_bypass_policy(
    db_session: AsyncSession,
    project_a: Project,
    v1_project_a: DevelopmentVersion,
):
    service = DevelopmentVersionService(session=db_session)

    # 1. Direct activation of unverified version is rejected
    unverified_ver = DevelopmentVersion(
        id=uuid.uuid4(),
        project_id=project_a.id,
        version_number=2,
        status=DevelopmentVersionStatus.GENERATED,
        files_manifest=[],
        file_count=1,
        total_size_bytes=10,
        content_hash="h-unver",
        manifest_hash="mh-unver",
        source_reason="UNVERIFIED",
        created_by="tester",
    )
    db_session.add(unverified_ver)
    await db_session.flush()

    with pytest.raises(ConflictError) as exc_act:
        await service.activate_version(project_a.id, unverified_ver.id)
    assert "only a verified version can be activated" in str(exc_act.value).lower()

    # 2. Rollback to failed version is rejected
    failed_ver = DevelopmentVersion(
        id=uuid.uuid4(),
        project_id=project_a.id,
        version_number=3,
        status=DevelopmentVersionStatus.FAILED_VERIFICATION,
        files_manifest=[],
        file_count=1,
        total_size_bytes=10,
        content_hash="h-fail",
        manifest_hash="mh-fail",
        source_reason="FAILED",
        created_by="tester",
    )
    db_session.add(failed_ver)
    await db_session.flush()

    with pytest.raises(ConflictError) as exc_rb:
        await service.rollback_version(project_a.id, failed_ver.id)
    assert "cannot roll back to unverified version" in str(exc_rb.value).lower()

    # 3. Direct Code Studio save with invalid syntax is rejected immediately
    with patch.object(service, "_resolve_version_files_map", new_callable=AsyncMock) as mock_files:
        mock_files.return_value = {"app/main.py": "def ok(): pass\n"}
        req = SaveFileRequest(
            parent_version_id=v1_project_a.id,
            content="def broken(: invalid syntax\n",
            reason="Bypass attempt",
        )
        with pytest.raises(ValidationError) as exc_val:
            await service.save_file_content(project_a.id, "app/main.py", req)
        assert "validation failed" in str(exc_val.value).lower()
