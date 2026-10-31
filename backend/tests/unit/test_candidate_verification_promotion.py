"""Unit tests for Milestone 5 Candidate Version Verification, Deterministic Promotion, and Truthful Execution."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.exceptions import TransientProviderError
from app.agents.providers.groq import GroqProvider
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.development_version import DevelopmentVersion, DevelopmentVersionStatus
from app.models.project import Project, ProjectStatus
from app.schemas.development_version import VerificationSnapshot, VerificationStatus
from app.services.development_version_service import DevelopmentVersionService


@pytest.fixture
async def sample_project(db_session: AsyncSession) -> Project:
    project = Project(
        id=uuid.uuid4(),
        name="Candidate Verification Project",
        slug="candidate-ver-proj",
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
            {"path": "app/main.py", "size_bytes": 45, "language": "python", "requirement_ids": []},
            {"path": "README.md", "size_bytes": 22, "language": "markdown", "requirement_ids": []},
        ],
        file_count=2,
        total_size_bytes=67,
        content_hash="hash-v1",
        manifest_hash="mhash-v1",
        source_reason="INITIAL_GENERATION",
        created_by="system",
        verification_summary={"verification_status": "PASSED", "is_verified": True},
    )
    db_session.add(v1)

    # Set v1 as active
    sample_project.settings = {"active_version_id": str(v1.id)}
    await db_session.flush()
    return v1


@pytest.mark.asyncio
async def test_candidate_creation_in_generated_status(
    db_session: AsyncSession,
    sample_project: Project,
    sample_v1_version: DevelopmentVersion,
):
    """Verify that creating a candidate version sets status to GENERATED and does NOT promote yet."""
    service = DevelopmentVersionService(session=db_session)

    # Mock resolving parent files
    with patch.object(service, "_resolve_version_files_map", new_callable=AsyncMock) as mock_files:
        mock_files.return_value = {
            "app/main.py": "def hello():\n    return 'v1'\n",
            "README.md": "# Test Project\n",
        }

        changes = [
            {"file_path": "app/main.py", "content": "def hello():\n    return 'v2-candidate'\n"},
        ]
        candidate = await service.create_candidate_version(
            project_id=sample_project.id,
            parent_version_id=sample_v1_version.id,
            changes=changes,
            reason="Upgrade to v2 candidate",
            created_by="engineer-1",
        )

    assert candidate.version_number == 2
    assert candidate.status == DevelopmentVersionStatus.GENERATED
    assert candidate.parent_version_id == sample_v1_version.id
    assert candidate.metadata_payload.get("candidate_stage") == "PENDING_VERIFICATION"

    # Project active pointer MUST still point to v1
    active_ver = await service.get_active_version(sample_project.id)
    assert active_ver.version_id == sample_v1_version.id
    assert active_ver.version_number == 1


@pytest.mark.asyncio
async def test_candidate_verification_and_promotion_success(
    db_session: AsyncSession,
    sample_project: Project,
    sample_v1_version: DevelopmentVersion,
):
    """Verify that successful verification promotes the candidate to VERIFIED and marks it active."""
    service = DevelopmentVersionService(session=db_session)

    with patch.object(service, "_resolve_version_files_map", new_callable=AsyncMock) as mock_files:
        mock_files.return_value = {
            "app/main.py": "def hello():\n    return 'v2-verified'\n",
        }

        changes = [
            {"file_path": "app/main.py", "content": "def hello():\n    return 'v2-verified'\n"},
        ]
        candidate = await service.create_candidate_version(
            project_id=sample_project.id,
            parent_version_id=sample_v1_version.id,
            changes=changes,
            reason="Feature upgrade",
        )

        verified_cand, snapshot, promoted = await service.verify_and_promote_candidate(
            project_id=sample_project.id,
            candidate_version_id=candidate.id,
            auto_promote=True,
            promoted_by="qa-lead",
        )

    assert promoted is True
    assert verified_cand.status == DevelopmentVersionStatus.VERIFIED
    assert snapshot.is_verified is True
    assert snapshot.verification_status == VerificationStatus.PASSED

    # Verification summary must strictly conform to VerificationSnapshot schema
    loaded_snap = VerificationSnapshot.model_validate(verified_cand.verification_summary)
    assert loaded_snap.static_analysis.status == VerificationStatus.PASSED
    assert loaded_snap.sandbox_execution.status == VerificationStatus.NOT_RUN  # Truthful Docker skip

    # Project active pointer MUST now point to candidate v2
    active_ver = await service.get_active_version(sample_project.id)
    assert active_ver.version_id == candidate.id
    assert active_ver.version_number == 2

    # Prior version v1 MUST be SUPERSEDED
    await db_session.refresh(sample_v1_version)
    assert sample_v1_version.status == DevelopmentVersionStatus.SUPERSEDED


@pytest.mark.asyncio
async def test_candidate_verification_failure_preserves_last_known_good(
    db_session: AsyncSession,
    sample_project: Project,
    sample_v1_version: DevelopmentVersion,
):
    """Verify that candidate verification failure marks FAILED_VERIFICATION and preserves v1 as active."""
    service = DevelopmentVersionService(session=db_session)

    with patch.object(service, "_resolve_version_files_map", new_callable=AsyncMock) as mock_files:
        # Candidate has deliberate Python syntax error
        broken_files = {
            "app/main.py": "def broken_syntax(\n",
        }
        mock_files.return_value = broken_files

        changes = [
            {"file_path": "app/main.py", "content": "def broken_syntax(\n"},
        ]
        candidate = await service.create_candidate_version(
            project_id=sample_project.id,
            parent_version_id=sample_v1_version.id,
            changes=changes,
            reason="Deliberate broken update",
        )

        failed_cand, snapshot, promoted = await service.verify_and_promote_candidate(
            project_id=sample_project.id,
            candidate_version_id=candidate.id,
            auto_promote=True,
        )

    assert promoted is False
    assert failed_cand.status == DevelopmentVersionStatus.FAILED_VERIFICATION
    assert snapshot.is_verified is False
    assert snapshot.verification_status == VerificationStatus.FAILED
    assert len(snapshot.static_analysis.blocking_issues) > 0

    # Project active pointer MUST remain on v1 (last known-good!)
    active_ver = await service.get_active_version(sample_project.id)
    assert active_ver.version_id == sample_v1_version.id
    assert active_ver.version_number == 1

    # v1 MUST NOT be superseded
    await db_session.refresh(sample_v1_version)
    assert sample_v1_version.status == DevelopmentVersionStatus.VERIFIED


@pytest.mark.asyncio
async def test_stale_parent_candidate_conflict(
    db_session: AsyncSession,
    sample_project: Project,
    sample_v1_version: DevelopmentVersion,
):
    """Verify that creating a candidate against a superseded version raises ConflictError."""
    service = DevelopmentVersionService(session=db_session)

    # Simulate that another version v2 was already activated
    v2 = DevelopmentVersion(
        id=uuid.uuid4(),
        project_id=sample_project.id,
        version_number=2,
        status=DevelopmentVersionStatus.VERIFIED,
        files_manifest=[],
        file_count=1,
        total_size_bytes=10,
        content_hash="hash-v2",
        manifest_hash="mhash-v2",
        source_reason="CONCURRENT_UPDATE",
        created_by="system",
    )
    db_session.add(v2)
    sample_project.settings = {"active_version_id": str(v2.id)}
    await db_session.flush()

    with pytest.raises(ConflictError) as exc_info:
        await service.create_candidate_version(
            project_id=sample_project.id,
            parent_version_id=sample_v1_version.id,
            changes=[{"file_path": "app/main.py", "content": "# stale"}],
            reason="Stale candidate base",
        )

    assert "candidate creation conflict" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_recover_active_version_restores_last_known_good(
    db_session: AsyncSession,
    sample_project: Project,
    sample_v1_version: DevelopmentVersion,
):
    """Verify recover_active_version detects a broken active pointer and restores the last verified version."""
    service = DevelopmentVersionService(session=db_session)

    # Simulate an erroneously active failed version
    v_bad = DevelopmentVersion(
        id=uuid.uuid4(),
        project_id=sample_project.id,
        version_number=2,
        status=DevelopmentVersionStatus.FAILED_VERIFICATION,
        files_manifest=[],
        file_count=1,
        total_size_bytes=10,
        content_hash="hash-bad",
        manifest_hash="mhash-bad",
        source_reason="FAILED_EXPERIMENT",
        created_by="user",
    )
    db_session.add(v_bad)
    sample_project.settings = {"active_version_id": str(v_bad.id)}
    await db_session.flush()

    # Recover active version
    recovered = await service.recover_active_version(sample_project.id)

    assert recovered is not None
    assert recovered.version_id == sample_v1_version.id
    assert recovered.version_number == 1
    assert recovered.status == DevelopmentVersionStatus.VERIFIED


def test_groq_exception_retry_guidance_extraction():
    """Verify that GroqProvider._handle_groq_exception extracts retry guidance and tier limits."""
    provider = GroqProvider(api_key="gsk-mock-key-12345678901234567890")

    mock_rate_limit_exc = Exception("Rate limit reached. Please try again in 4.5s. Resource exhausted.")

    with pytest.raises(TransientProviderError) as exc_info:
        provider._handle_groq_exception(mock_rate_limit_exc)

    err = exc_info.value
    assert err.transient is True
    assert "retry guidance: please wait 4.5s" in str(err).lower()
    assert err.extra.get("retry_after") == 4.5
    assert err.extra.get("tier_boundary") == "8,000 TPM"
    assert "gsk-mock-key" not in str(err)  # Ensure no key leak


@pytest.mark.asyncio
async def test_runtime_status_truthful_execution_reporting():
    """Verify RuntimeStatusResponse truthfully models BLOCKED container execution."""
    from app.api.v1.endpoints.preview_runtime import RuntimeStatusResponse

    resp = RuntimeStatusResponse(
        status="RUNNING",
        port=8001,
        preview_url="http://127.0.0.1:8001/?project_id=123&app=taskflow",
        is_healthy=True,
        detail="Application running on port 8001.",
    )

    assert resp.execution_type == "domain_prototype"
    assert resp.container_status == "BLOCKED"
    assert "Docker is unavailable on this host" in (resp.container_detail or "")


@pytest.mark.asyncio
async def test_runtime_status_active_version_synchronization(
    db_session: AsyncSession,
    sample_project: Project,
    sample_v1_version: DevelopmentVersion,
):
    """Verify that _resolve_active_version_info correctly extracts version number and UUID."""
    from app.api.v1.endpoints.preview_runtime import _resolve_active_version_info

    ver_id, ver_num = await _resolve_active_version_info(sample_project, db_session)

    assert ver_id == str(sample_v1_version.id)
    assert ver_num == 1

