"""Unit tests for Milestone 6A: Verification Policy Finalization, Row-Level Concurrency Locking, and Safe Version Promotion.

Verifies:
1. Static-only local changes allow promotion with sandbox NOT_RUN (OPTIONAL).
2. Changes containing automated test files strictly require sandbox execution; when unavailable,
   sandbox status is truthfully recorded as BLOCKED, overall verification is BLOCKED,
   version status is FAILED_VERIFICATION, and promotion is refused across all entry points.
3. The last-known-good active version is preserved whenever verification fails or is blocked.
4. Row-level concurrency locking and stale candidate rebase guards prevent race conditions.
5. Direct version activation and rollback endpoints reject unverified versions with blocked tests.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.development_version import DevelopmentVersion, DevelopmentVersionStatus
from app.models.project import Project, ProjectStatus
from app.models.user import User
from app.models.workflow_execution import WorkflowExecution, WorkflowStatus
from app.schemas.code_studio import SaveFileRequest
from app.schemas.development_version import (
    VerificationRequirementLevel,
    VerificationSnapshot,
    VerificationStatus,
)
from app.services.development_version_service import DevelopmentVersionService
from app.services.engineering_action_service import EngineeringActionService
from app.services.verification_service import DevelopmentVerificationService


@pytest.fixture
async def sample_user(db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        email=f"tester-{uuid.uuid4().hex[:6]}@example.com",
        name=f"tester_{uuid.uuid4().hex[:6]}",
        hashed_password="hashed_pw_test",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def sample_project(db_session: AsyncSession) -> Project:
    project = Project(
        id=uuid.uuid4(),
        name="Milestone 6A Verification Project",
        slug=f"m6a-proj-{uuid.uuid4().hex[:6]}",
        status=ProjectStatus.IN_PROGRESS,
        settings={},
    )
    db_session.add(project)
    await db_session.flush()
    return project


@pytest.fixture
async def sample_v1_version(db_session: AsyncSession, sample_project: Project) -> DevelopmentVersion:
    v1 = DevelopmentVersion(
        id=uuid.uuid4(),
        project_id=sample_project.id,
        version_number=1,
        status=DevelopmentVersionStatus.VERIFIED,
        files_manifest=[
            {"path": "app/main.py", "size_bytes": 50, "language": "python", "requirement_ids": []},
            {"path": "README.md", "size_bytes": 30, "language": "markdown", "requirement_ids": []},
        ],
        file_count=2,
        total_size_bytes=80,
        content_hash="m6a-hash-v1",
        manifest_hash="m6a-mhash-v1",
        source_reason="INITIAL_GENERATION",
        created_by="system",
        verification_summary={"verification_status": "PASSED", "is_verified": True},
    )
    db_session.add(v1)

    # Designate v1 as initial active version
    sample_project.settings = {"active_version_id": str(v1.id)}
    await db_session.flush()
    return v1


# =========================================================================
# Task 1 & 2: Verification Policy Enforcement Across Entry Points
# =========================================================================

@pytest.mark.asyncio
async def test_candidate_promotion_static_only_allows_promotion(
    db_session: AsyncSession,
    sample_project: Project,
    sample_v1_version: DevelopmentVersion,
):
    """Static-only changes without test files allow promotion with sandbox NOT_RUN (OPTIONAL)."""
    service = DevelopmentVersionService(session=db_session)

    with patch.object(service, "_resolve_version_files_map", new_callable=AsyncMock) as mock_files:
        mock_files.return_value = {
            "app/main.py": "def main():\n    return 'static-v2'\n",
            "README.md": "# Title\nUpdated docs.\n",
        }

        changes = [
            {"file_path": "app/main.py", "content": "def main():\n    return 'static-v2'\n"},
        ]
        candidate = await service.create_candidate_version(
            project_id=sample_project.id,
            parent_version_id=sample_v1_version.id,
            changes=changes,
            reason="Static enhancement",
        )

        verified_cand, snapshot, promoted = await service.verify_and_promote_candidate(
            project_id=sample_project.id,
            candidate_version_id=candidate.id,
            auto_promote=True,
            promoted_by="lead-dev",
        )

    assert promoted is True
    assert verified_cand.status == DevelopmentVersionStatus.VERIFIED
    assert snapshot.is_verified is True
    assert snapshot.verification_status == VerificationStatus.PASSED
    assert snapshot.sandbox_execution.requirement_level == VerificationRequirementLevel.OPTIONAL
    assert snapshot.sandbox_execution.status == VerificationStatus.NOT_RUN

    # Active version advanced to candidate
    active = await service.get_active_version(sample_project.id)
    assert active.version_id == candidate.id
    assert active.version_number == 2


@pytest.mark.asyncio
async def test_candidate_promotion_with_tests_blocks_promotion_when_docker_unavailable(
    db_session: AsyncSession,
    sample_project: Project,
    sample_v1_version: DevelopmentVersion,
):
    """Changes containing automated test files require sandbox execution; blocks promotion if Docker is unavailable."""
    service = DevelopmentVersionService(session=db_session)

    with patch.object(service, "_resolve_version_files_map", new_callable=AsyncMock) as mock_files:
        mock_files.return_value = {
            "app/main.py": "def add(a, b):\n    return a + b\n",
            "tests/test_main.py": "def test_add():\n    assert add(1, 2) == 3\n",
        }

        changes = [
            {"file_path": "tests/test_main.py", "content": "def test_add():\n    assert add(1, 2) == 3\n"},
        ]
        candidate = await service.create_candidate_version(
            project_id=sample_project.id,
            parent_version_id=sample_v1_version.id,
            changes=changes,
            reason="Add unit tests",
        )

        verified_cand, snapshot, promoted = await service.verify_and_promote_candidate(
            project_id=sample_project.id,
            candidate_version_id=candidate.id,
            auto_promote=True,
            promoted_by="qa-engineer",
        )

    # Must NOT be promoted
    assert promoted is False
    assert verified_cand.status == DevelopmentVersionStatus.FAILED_VERIFICATION
    assert snapshot.is_verified is False
    assert snapshot.verification_status == VerificationStatus.BLOCKED
    assert snapshot.sandbox_execution.requirement_level == VerificationRequirementLevel.REQUIRED
    assert snapshot.sandbox_execution.status == VerificationStatus.BLOCKED
    assert len(snapshot.sandbox_execution.blocking_issues) > 0

    # Last-known-good active version (v1) MUST be preserved!
    active = await service.get_active_version(sample_project.id)
    assert active.version_id == sample_v1_version.id
    assert active.version_number == 1


@pytest.mark.asyncio
async def test_save_file_content_blocks_promotion_when_test_file_modified(
    db_session: AsyncSession,
    sample_project: Project,
    sample_v1_version: DevelopmentVersion,
):
    """Code Studio save_file_content blocks promotion when saving an automated test file."""
    service = DevelopmentVersionService(session=db_session)

    with patch.object(service, "_resolve_version_files_map", new_callable=AsyncMock) as mock_files:
        mock_files.return_value = {
            "app/main.py": "print('hello')",
            "tests/test_app.py": "def test_one(): pass",
        }

        req = SaveFileRequest(
            content="def test_one(): assert True\n",
            parent_version_id=sample_v1_version.id,
            reason="Update test assertion",
        )

        resp = await service.save_file_content(
            project_id=sample_project.id,
            file_path="tests/test_app.py",
            request=req,
            current_user=None,
        )

    assert resp.success is True
    assert "activation was blocked" in resp.message.lower()

    # Active version pointer MUST remain at v1
    active = await service.get_active_version(sample_project.id)
    assert active.version_id == sample_v1_version.id

    # The new version must exist in FAILED_VERIFICATION status
    saved_ver = await service.get_version(sample_project.id, resp.version_id)
    assert saved_ver.status == DevelopmentVersionStatus.FAILED_VERIFICATION


@pytest.mark.asyncio
async def test_save_file_content_promotes_static_change(
    db_session: AsyncSession,
    sample_project: Project,
    sample_v1_version: DevelopmentVersion,
):
    """Code Studio save_file_content successfully promotes static-only changes."""
    service = DevelopmentVersionService(session=db_session)

    with patch.object(service, "_resolve_version_files_map", new_callable=AsyncMock) as mock_files:
        mock_files.return_value = {
            "app/main.py": "def compute():\n    return 42\n",
            "README.md": "# Docs\n",
        }

        req = SaveFileRequest(
            content="def compute():\n    return 42\n",
            parent_version_id=sample_v1_version.id,
            reason="Add compute helper",
        )

        resp = await service.save_file_content(
            project_id=sample_project.id,
            file_path="app/main.py",
            request=req,
            current_user=None,
        )

    assert resp.success is True

    # Active version pointer advanced to v2
    active = await service.get_active_version(sample_project.id)
    assert active.version_id == resp.version_id
    assert active.version_number == 2
    assert active.status == DevelopmentVersionStatus.VERIFIED


@pytest.mark.asyncio
async def test_apply_code_change_blocks_activation_when_test_manifest_present(
    db_session: AsyncSession,
    sample_project: Project,
    sample_v1_version: DevelopmentVersion,
    sample_user: User,
):
    """EngineeringActionService APPLY_CODE_CHANGE refuses activation if project contains tests and Docker unavailable."""
    version_service = DevelopmentVersionService(session=db_session)
    action_service = EngineeringActionService(
        session=db_session,
        version_service=version_service,
        verification_service=DevelopmentVerificationService(),
        requirement_service=AsyncMock(),
        context_engine=AsyncMock(),
        workflow_service=AsyncMock(),
    )

    with patch.object(version_service, "_resolve_version_files_map", new_callable=AsyncMock) as mock_files:
        mock_files.return_value = {
            "app/main.py": "def run(): pass\n",
            "tests/test_run.py": "def test_run(): pass\n",
        }

        # Dispatch APPLY_CODE_CHANGE directly via internal dispatcher
        result, msg = await action_service._dispatch_action(
            project_id=sample_project.id,
            action_id="APPLY_CODE_CHANGE",
            parameters={
                "version_id": str(sample_v1_version.id),
                "changes": [
                    {"file_path": "tests/test_run.py", "content": "def test_run(): pass\n"},
                ],
                "reason": "Add integration test",
            },
            target_id=None,
            user_id=str(sample_user.id),
        )

    assert result["runtime_updated"] is False
    assert result["new_version"]["status"] == "FAILED_VERIFICATION"
    assert "blocked" in msg.lower()

    # Active version pointer preserved at v1
    active = await version_service.get_active_version(sample_project.id)
    assert active.version_id == sample_v1_version.id


@pytest.mark.asyncio
async def test_activate_version_rejects_version_with_unverified_tests(
    db_session: AsyncSession,
    sample_project: Project,
    sample_v1_version: DevelopmentVersion,
):
    """Direct activate_version call raises ConflictError if version has automated tests but unverified sandbox."""
    service = DevelopmentVersionService(session=db_session)

    # Create a version that has automated tests and BLOCKED sandbox execution
    unverified_ver = DevelopmentVersion(
        id=uuid.uuid4(),
        project_id=sample_project.id,
        version_number=2,
        parent_version_id=sample_v1_version.id,
        status=DevelopmentVersionStatus.FAILED_VERIFICATION,
        files_manifest=[
            {"path": "app/main.py", "size_bytes": 40, "language": "python", "requirement_ids": []},
            {"path": "tests/test_main.py", "size_bytes": 60, "language": "python", "requirement_ids": []},
        ],
        file_count=2,
        total_size_bytes=100,
        content_hash="hash-unver",
        manifest_hash="mhash-unver",
        source_reason="CANDIDATE_CREATION",
        created_by="tester",
        verification_summary={
            "verification_status": "BLOCKED",
            "is_verified": False,
            "sandbox_execution": {"status": "BLOCKED", "requirement_level": "REQUIRED"},
        },
    )
    db_session.add(unverified_ver)
    await db_session.flush()

    with pytest.raises(ConflictError) as exc_info:
        await service.activate_version(
            project_id=sample_project.id,
            version_id=unverified_ver.id,
            reason="Attempt direct bypass",
        )

    assert "only a verified version can be activated" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_rollback_version_rejects_unverified_version(
    db_session: AsyncSession,
    sample_project: Project,
    sample_v1_version: DevelopmentVersion,
):
    """Direct rollback_version call raises ConflictError if target version is unverified."""
    service = DevelopmentVersionService(session=db_session)

    unverified_ver = DevelopmentVersion(
        id=uuid.uuid4(),
        project_id=sample_project.id,
        version_number=2,
        parent_version_id=sample_v1_version.id,
        status=DevelopmentVersionStatus.FAILED_VERIFICATION,
        files_manifest=[{"path": "app/main.py", "size_bytes": 40, "language": "python", "requirement_ids": []}],
        file_count=1,
        total_size_bytes=40,
        content_hash="hash-bad",
        manifest_hash="mhash-bad",
        source_reason="MANUAL_EDIT",
        created_by="tester",
        verification_summary={"verification_status": "FAILED", "is_verified": False},
    )
    db_session.add(unverified_ver)
    await db_session.flush()

    with pytest.raises(ConflictError) as exc_info:
        await service.rollback_version(
            project_id=sample_project.id,
            target_version_id=unverified_ver.id,
            reason="Attempt rollback to broken version",
        )

    assert "cannot roll back to unverified version" in str(exc_info.value).lower()


# =========================================================================
# Task 3: Transaction and Concurrency Safety
# =========================================================================

@pytest.mark.asyncio
async def test_stale_candidate_parent_concurrency_conflict(
    db_session: AsyncSession,
    sample_project: Project,
    sample_v1_version: DevelopmentVersion,
):
    """Candidate creation is rejected with ConflictError when active version has moved past candidate parent."""
    service = DevelopmentVersionService(session=db_session)

    # Synthesize v2 and make it active
    v2 = DevelopmentVersion(
        id=uuid.uuid4(),
        project_id=sample_project.id,
        version_number=2,
        parent_version_id=sample_v1_version.id,
        status=DevelopmentVersionStatus.VERIFIED,
        files_manifest=[{"path": "app/main.py", "size_bytes": 40, "language": "python", "requirement_ids": []}],
        file_count=1,
        total_size_bytes=40,
        content_hash="hash-v2",
        manifest_hash="mhash-v2",
        source_reason="PROMOTION",
        created_by="system",
        verification_summary={"verification_status": "PASSED", "is_verified": True},
    )
    db_session.add(v2)
    sample_project.settings = {"active_version_id": str(v2.id)}
    await db_session.flush()

    # Attempt to create candidate based on stale parent (v1)
    with pytest.raises(ConflictError) as exc_info:
        await service.create_candidate_version(
            project_id=sample_project.id,
            parent_version_id=sample_v1_version.id,
            changes=[{"file_path": "app/main.py", "content": "stale change"}],
            reason="Branch from old version",
        )

    assert "candidate creation conflict" in str(exc_info.value).lower()
    assert "candidate proposal is stale" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_auto_promotion_aborts_if_active_version_advanced_during_verification(
    db_session: AsyncSession,
    sample_project: Project,
    sample_v1_version: DevelopmentVersion,
):
    """If another worker advanced active version while candidate was being verified, auto_promote aborts safely."""
    service = DevelopmentVersionService(session=db_session)

    with patch.object(service, "_resolve_version_files_map", new_callable=AsyncMock) as mock_files:
        mock_files.return_value = {"app/main.py": "def code(): return True\n"}

        # 1. Create candidate based on v1
        candidate = await service.create_candidate_version(
            project_id=sample_project.id,
            parent_version_id=sample_v1_version.id,
            changes=[{"file_path": "app/main.py", "content": "def code(): return True\n"}],
            reason="Concurrent race candidate",
        )

        # 2. Simulate concurrent worker advancing active version to v3
        v3 = DevelopmentVersion(
            id=uuid.uuid4(),
            project_id=sample_project.id,
            version_number=3,
            parent_version_id=sample_v1_version.id,
            status=DevelopmentVersionStatus.VERIFIED,
            files_manifest=[{"path": "app/main.py", "size_bytes": 50, "language": "python", "requirement_ids": []}],
            file_count=1,
            total_size_bytes=50,
            content_hash="hash-concurrent-v3",
            manifest_hash="mhash-concurrent-v3",
            source_reason="CONCURRENT_PROMOTION",
            created_by="other-worker",
            verification_summary={"verification_status": "PASSED", "is_verified": True},
        )
        db_session.add(v3)
        sample_project.settings = {"active_version_id": str(v3.id)}
        await db_session.flush()

        # 3. Candidate finishes verification and attempts auto_promote
        verified_cand, snapshot, promoted = await service.verify_and_promote_candidate(
            project_id=sample_project.id,
            candidate_version_id=candidate.id,
            auto_promote=True,
            promoted_by="candidate-worker",
        )

    # Candidate passed verification but auto_promote was aborted because active version moved!
    assert snapshot.is_verified is True
    assert promoted is False
    assert verified_cand.status == DevelopmentVersionStatus.VERIFIED
    assert "promotion_blocked_reason" in (verified_cand.metadata_payload or {})

    # Active pointer is STILL v3 (not overwritten by stale candidate)
    active = await service.get_active_version(sample_project.id)
    assert active.version_id == v3.id
    assert active.version_number == 3
