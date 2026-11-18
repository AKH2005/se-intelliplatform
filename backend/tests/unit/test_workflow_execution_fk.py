"""Unit Tests for DevelopmentVersion and WorkflowExecution Foreign Key Integrity."""

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.workflow_execution import WorkflowExecution, WorkflowExecutionStatus
from app.models.development_version import DevelopmentVersion, DevelopmentVersionStatus, DevelopmentChange, ChangeCategory, ChangeType


@pytest.mark.asyncio
async def test_development_version_with_persisted_workflow_execution(session: AsyncSession):
    """Test that DevelopmentVersion persists successfully when referencing a flushed WorkflowExecution."""
    proj_id = uuid.uuid4()
    project = Project(id=proj_id, name="FK Test Project", slug=f"fk-test-{proj_id.hex[:8]}", description="Test Project")
    session.add(project)
    await session.commit()

    wf_id = uuid.uuid4()
    wf_exec = WorkflowExecution(
        id=uuid.uuid4(),
        workflow_execution_id=wf_id,
        project_id=proj_id,
        workflow_id="assistant-code-change",
        workflow_version="1.0.0",
        status=WorkflowExecutionStatus.COMPLETED,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        step_count=1,
        completed_steps=1,
        failed_steps=0,
        skipped_steps=0,
        artifacts={"code-generation": {}},
        errors=[],
        warnings=[],
        metadata_payload={"source": "test"},
    )
    session.add(wf_exec)
    await session.flush([wf_exec])

    ver_id = uuid.uuid4()
    version = DevelopmentVersion(
        id=ver_id,
        project_id=proj_id,
        version_number=1,
        workflow_execution_id=wf_id,
        artifact_key="code-generation",
        status=DevelopmentVersionStatus.VERIFIED,
        content_hash="hash-12345",
        manifest_hash="man-12345",
        file_count=2,
        total_size_bytes=200,
        source_reason="ASSISTANT_CODE_CHANGE",
        created_by="test-user",
        requirement_ids=[],
        files_manifest=[],
        verification_summary={"status": "PASSED"},
        metadata_payload={},
    )
    session.add(version)
    await session.commit()

    # Query back to verify relational integrity
    stmt = select(DevelopmentVersion).where(DevelopmentVersion.id == ver_id)
    res = await session.execute(stmt)
    persisted_ver = res.scalar_one_or_none()
    assert persisted_ver is not None
    assert persisted_ver.workflow_execution_id == wf_id


@pytest.mark.asyncio
async def test_development_version_with_nullable_workflow_execution(session: AsyncSession):
    """Test that DevelopmentVersion persists successfully with workflow_execution_id=None."""
    proj_id = uuid.uuid4()
    project = Project(id=proj_id, name="FK Null Test Project", slug=f"fk-null-{proj_id.hex[:8]}", description="Test Project")
    session.add(project)
    await session.commit()

    ver_id = uuid.uuid4()
    version = DevelopmentVersion(
        id=ver_id,
        project_id=proj_id,
        version_number=1,
        workflow_execution_id=None,
        artifact_key="code-generation",
        status=DevelopmentVersionStatus.VERIFIED,
        content_hash="hash-null-123",
        manifest_hash="man-null-123",
        file_count=1,
        total_size_bytes=100,
        source_reason="INITIAL_GENERATION",
        created_by="system",
        requirement_ids=[],
        files_manifest=[],
        verification_summary=None,
        metadata_payload={"bootstrap": True},
    )
    session.add(version)
    await session.commit()

    stmt = select(DevelopmentVersion).where(DevelopmentVersion.id == ver_id)
    res = await session.execute(stmt)
    persisted_ver = res.scalar_one_or_none()
    assert persisted_ver is not None
    assert persisted_ver.workflow_execution_id is None


@pytest.mark.asyncio
async def test_session_rollback_and_reuse_on_failure(session: AsyncSession):
    """Verify that a session rolled back after failure can cleanly continue with subsequent operations."""
    proj_id = uuid.uuid4()
    project = Project(id=proj_id, name="Rollback Test", slug=f"rb-test-{proj_id.hex[:8]}", description="Test")
    session.add(project)
    await session.commit()

    # Simulate an error by rolling back
    await session.rollback()

    # Verify session remains usable
    stmt = select(Project).where(Project.id == proj_id)
    res = await session.execute(stmt)
    p = res.scalar_one_or_none()
    assert p is not None
    assert p.name == "Rollback Test"
