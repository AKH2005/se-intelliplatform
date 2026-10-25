"""Integration tests for Phase 11H Development Versions & Continuous Engineering Loop API."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.code_generation.contracts import (
    CodeGenerationOutput,
    CodeGenerationPlan,
    GeneratedFile,
    PlannedFile,
)
from app.models.development_version import (
    ChangeCategory,
    ChangeType,
    DevelopmentVersionStatus,
)
from app.models.project import Project, ProjectStatus
from app.models.workflow_execution import WorkflowExecution, WorkflowStatus
from app.sandbox.contracts import ExecutionResult, ExecutionStatus, ExecutionType
from app.sandbox.static_analysis.contracts import (
    DiagnosticCategory,
    DiagnosticSeverity,
    StaticAnalysisResult,
    StaticAnalysisStatus,
    StaticDiagnostic,
)
from app.schemas.development_version import (
    VerificationRequirementLevel,
    VerificationStatus,
)


def _build_sample_code_output(version_num: int = 1) -> CodeGenerationOutput:
    planned = [
        PlannedFile(path="app/main.py", purpose="App entry", file_type="SOURCE"),
        PlannedFile(path="tests/test_main.py", purpose="Unit tests", file_type="SOURCE"),
    ]
    gen_files = [
        GeneratedFile(
            path="app/main.py",
            content=f"def main(): return {version_num}\n",
            language="python",
            size_bytes=24,
            requirement_ids=["REQ-1"],
        ),
        GeneratedFile(
            path="tests/test_main.py",
            content=f"def test_main(): assert main() == {version_num}\n",
            language="python",
            size_bytes=38,
            requirement_ids=["REQ-1"],
        ),
    ]
    return CodeGenerationOutput(
        plan=CodeGenerationPlan(
            framework="fastapi",
            database="none",
            package_manager="pip",
            files=planned,
            rationale=f"Sample project design rationale v{version_num}",
        ),
        generated_files=gen_files,
        total_files=len(gen_files),
        total_size_bytes=sum(f.size_bytes for f in gen_files),
        summary=f"Sample code artifact v{version_num}",
    )


def _build_clean_static_analysis(project_id: uuid.UUID) -> StaticAnalysisResult:
    return StaticAnalysisResult(
        analysis_id=uuid.uuid4(),
        project_id=project_id,
        status=StaticAnalysisStatus.PASSED,
        duration_seconds=0.1,
        files_analyzed=2,
        files_skipped=0,
        error_count=0,
        warning_count=0,
        info_count=0,
        security_issue_count=0,
        syntax_error_count=0,
        lint_issue_count=0,
        diagnostics=[],
        summary="Static analysis passed cleanly",
    )


def _build_clean_sandbox_execution(project_id: uuid.UUID) -> ExecutionResult:
    return ExecutionResult(
        execution_id=uuid.uuid4(),
        project_id=project_id,
        execution_type=ExecutionType.TEST,
        status=ExecutionStatus.PASSED,
        exit_code=0,
        duration_seconds=0.3,
        stdout="1 passed in 0.05s",
        stderr="",
        tests_passed=1,
        tests_failed=0,
        tests_total=1,
    )


async def _seed_project_with_workflow(
    db_session: AsyncSession,
    version_num: int = 1,
    verified: bool = True,
) -> tuple[Project, WorkflowExecution]:
    project = Project(
        id=uuid.uuid4(),
        name=f"Dev Version Project {version_num}",
        slug=f"dev-version-project-{version_num}-{uuid.uuid4().hex[:6]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.commit()

    code_output = _build_sample_code_output(version_num=version_num)
    artifacts = {
        "code-generation": code_output.model_dump(mode="json"),
    }

    if verified:
        sa = _build_clean_static_analysis(project.id)
        sb = _build_clean_sandbox_execution(project.id)
        artifacts["static_analysis"] = sa.model_dump(mode="json")
        artifacts["sandbox_execution"] = sb.model_dump(mode="json")

    wf = WorkflowExecution(
        workflow_execution_id=uuid.uuid4(),
        project_id=project.id,
        workflow_id="code-generation-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        artifacts=artifacts,
    )
    db_session.add(wf)
    await db_session.commit()

    return project, wf


@pytest.mark.asyncio
async def test_list_versions_bootstraps_and_returns_versions(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """GET /projects/{project_id}/versions bootstraps version from existing workflow execution."""
    project, wf = await _seed_project_with_workflow(db_session, version_num=1, verified=True)

    resp = await client.get(f"/api/v1/projects/{project.id}/versions")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    v1 = data["items"][0]
    assert v1["version_number"] == 1
    assert v1["status"] in ("VERIFIED", "ACTIVE")
    assert v1["is_active"] is True
    assert v1["file_count"] == 2
    assert len(v1["files_manifest"]) == 2
    # Verify lightweight representation - content is not in manifest
    for file_summary in v1["files_manifest"]:
        assert "content" not in file_summary
        assert "path" in file_summary
        assert "size_bytes" in file_summary


@pytest.mark.asyncio
async def test_get_version_by_id(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """GET /projects/{project_id}/versions/{version_id} returns detailed metadata."""
    project, wf = await _seed_project_with_workflow(db_session, version_num=1, verified=True)

    # Trigger list to ensure bootstrapped
    list_resp = await client.get(f"/api/v1/projects/{project.id}/versions")
    v1_id = list_resp.json()["items"][0]["version_id"]

    resp = await client.get(f"/api/v1/projects/{project.id}/versions/{v1_id}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["version_id"] == v1_id
    assert data["project_id"] == str(project.id)
    assert data["version_number"] == 1
    assert data["workflow_execution_id"] == str(wf.workflow_execution_id)
    assert data["artifact_key"] == "code-generation"
    assert data["content_hash"] is not None
    assert len(data["content_hash"]) == 64
    assert data["manifest_hash"] is not None
    assert len(data["manifest_hash"]) == 64
    assert data["requirement_ids"] == ["REQ-1"]


@pytest.mark.asyncio
async def test_get_active_version(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """GET /projects/{project_id}/versions/active returns the project's active version."""
    project, wf = await _seed_project_with_workflow(db_session, version_num=1, verified=True)

    # Call active
    resp = await client.get(f"/api/v1/projects/{project.id}/versions/active")
    assert resp.status_code == 200
    data = resp.json()

    assert data is not None
    assert data["version_number"] == 1
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_version_file_content(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """GET /projects/{project_id}/versions/{version_id}/files/{path} returns raw source code."""
    project, wf = await _seed_project_with_workflow(db_session, version_num=1, verified=True)

    list_resp = await client.get(f"/api/v1/projects/{project.id}/versions")
    v1_id = list_resp.json()["items"][0]["version_id"]

    resp = await client.get(f"/api/v1/projects/{project.id}/versions/{v1_id}/files/app/main.py")
    assert resp.status_code == 200
    assert "def main(): return 1" in resp.text

    # Nonexistent file returns 404
    resp_404 = await client.get(f"/api/v1/projects/{project.id}/versions/{v1_id}/files/app/nonexistent.py")
    assert resp_404.status_code == 404


@pytest.mark.asyncio
async def test_version_verification_endpoints(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """GET and POST /projects/{project_id}/versions/{version_id}/verification."""
    project, wf = await _seed_project_with_workflow(db_session, version_num=1, verified=True)

    list_resp = await client.get(f"/api/v1/projects/{project.id}/versions")
    v1_id = list_resp.json()["items"][0]["version_id"]

    # GET verification snapshot
    resp = await client.get(f"/api/v1/projects/{project.id}/versions/{v1_id}/verification")
    assert resp.status_code == 200
    snap = resp.json()
    assert snap["is_verified"] is True
    assert snap["verification_status"] == "PASSED"
    assert snap["static_analysis"]["status"] == "PASSED"
    assert snap["sandbox_execution"]["status"] == "PASSED"

    # POST re-evaluate verify without modifying code version
    reval_resp = await client.post(f"/api/v1/projects/{project.id}/versions/{v1_id}/verify")
    assert reval_resp.status_code == 200
    reval_snap = reval_resp.json()
    assert reval_snap["is_verified"] is True
    assert reval_snap["verification_status"] == "PASSED"


@pytest.mark.asyncio
async def test_activation_and_rollback_lifecycle(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Test full version activation, rollback, and audit log tracking."""
    project, wf1 = await _seed_project_with_workflow(db_session, version_num=1, verified=True)

    # Create second workflow execution for version 2
    code_output_v2 = _build_sample_code_output(version_num=2)
    sa2 = _build_clean_static_analysis(project.id)
    sb2 = _build_clean_sandbox_execution(project.id)
    wf2 = WorkflowExecution(
        workflow_execution_id=uuid.uuid4(),
        project_id=project.id,
        workflow_id="code-generation-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        artifacts={
            "code-generation": code_output_v2.model_dump(mode="json"),
            "static_analysis": sa2.model_dump(mode="json"),
            "sandbox_execution": sb2.model_dump(mode="json"),
        },
    )
    db_session.add(wf2)
    await db_session.commit()

    # Register version 2 via service
    from app.services.development_version_service import DevelopmentVersionService
    from app.services.verification_service import DevelopmentVerificationService
    dev_service = DevelopmentVersionService(db_session)
    await dev_service.list_versions(project.id)  # bootstraps v1
    v2_record = await dev_service.register_version_from_workflow(
        project_id=project.id,
        workflow_execution_id=wf2.workflow_execution_id,
        artifact_key="code-generation",
        source_reason="NEW_FEATURE",
    )

    # 1. Activate v2
    act_resp = await client.post(
        f"/api/v1/projects/{project.id}/versions/{v2_record.id}/activate",
        json={"reason": "Activating release v2"},
    )
    assert act_resp.status_code == 200
    v2_act_data = act_resp.json()
    assert v2_act_data["is_active"] is True
    assert v2_act_data["version_number"] == 2

    # 2. Check active version endpoint confirms v2 is active
    active_resp = await client.get(f"/api/v1/projects/{project.id}/versions/active")
    assert active_resp.json()["version_number"] == 2

    # 3. Roll back to v1
    list_resp = await client.get(f"/api/v1/projects/{project.id}/versions")
    v1_id = [v["version_id"] for v in list_resp.json()["items"] if v["version_number"] == 1][0]

    rb_resp = await client.post(
        f"/api/v1/projects/{project.id}/versions/{v1_id}/rollback",
        json={"reason": "Reverting back to stable v1"},
    )
    assert rb_resp.status_code == 200
    rb_data = rb_resp.json()
    assert rb_data["is_active"] is True
    assert rb_data["version_number"] == 1

    # 4. Check active endpoint confirms v1 is restored as active
    active_after_rb = await client.get(f"/api/v1/projects/{project.id}/versions/active")
    assert active_after_rb.json()["version_number"] == 1

    # 5. Check change history records LIFECYCLE_EVENT
    changes_resp = await client.get(f"/api/v1/projects/{project.id}/versions/{v1_id}/changes")
    assert changes_resp.status_code == 200
    changes = changes_resp.json()
    assert len(changes) >= 1
    lifecycle_changes = [c for c in changes if c["change_category"] == "LIFECYCLE_EVENT"]
    assert len(lifecycle_changes) >= 1
    assert any(c["change_type"] in ("ACTIVATION", "ROLLBACK") for c in lifecycle_changes)


@pytest.mark.asyncio
async def test_compare_versions_endpoint(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """GET /projects/{project_id}/versions/compare produces deterministic unified diff."""
    project, wf1 = await _seed_project_with_workflow(db_session, version_num=1, verified=True)

    # Register v2 with an extra file and modified main.py
    code_output_v2 = _build_sample_code_output(version_num=2)
    # Add a new file to v2
    code_output_v2.generated_files.append(
        GeneratedFile(
            path="app/utils.py",
            content="def helper(): return 'v2'\n",
            language="python",
            size_bytes=28,
            requirement_ids=["REQ-2"],
        )
    )
    code_output_v2.total_files = len(code_output_v2.generated_files)

    wf2 = WorkflowExecution(
        workflow_execution_id=uuid.uuid4(),
        project_id=project.id,
        workflow_id="code-generation-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        artifacts={
            "code-generation": code_output_v2.model_dump(mode="json"),
            "static_analysis": _build_clean_static_analysis(project.id).model_dump(mode="json"),
            "sandbox_execution": _build_clean_sandbox_execution(project.id).model_dump(mode="json"),
        },
    )
    db_session.add(wf2)
    await db_session.commit()

    from app.services.development_version_service import DevelopmentVersionService
    from app.services.verification_service import DevelopmentVerificationService
    dev_service = DevelopmentVersionService(db_session)
    await dev_service.list_versions(project.id)
    v2_record = await dev_service.register_version_from_workflow(
        project_id=project.id,
        workflow_execution_id=wf2.workflow_execution_id,
        artifact_key="code-generation",
        source_reason="FEATURE_EXPANSION",
    )

    list_resp = await client.get(f"/api/v1/projects/{project.id}/versions")
    v1_id = [v["version_id"] for v in list_resp.json()["items"] if v["version_number"] == 1][0]

    compare_resp = await client.get(
        f"/api/v1/projects/{project.id}/versions/compare?from_version={v1_id}&to_version={v2_record.id}"
    )
    assert compare_resp.status_code == 200
    comp = compare_resp.json()

    assert comp["from_version_number"] == 1
    assert comp["to_version_number"] == 2
    assert len(comp["files_added"]) == 1
    assert comp["files_added"][0]["path"] == "app/utils.py"
    assert comp["files_added"][0]["change_type"] == "ADDED"

    assert len(comp["files_modified"]) >= 1
    modified_paths = [f["path"] for f in comp["files_modified"]]
    assert "app/main.py" in modified_paths
    main_diff = [f for f in comp["files_modified"] if f["path"] == "app/main.py"][0]
    assert "-def main(): return 1" in main_diff["unified_diff"]
    assert "+def main(): return 2" in main_diff["unified_diff"]

    assert comp["requirements_added"] == ["REQ-2"]


@pytest.mark.asyncio
async def test_project_isolation_security(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Accessing a version from a different project must return 404."""
    project1, _ = await _seed_project_with_workflow(db_session, version_num=1, verified=True)
    project2, _ = await _seed_project_with_workflow(db_session, version_num=2, verified=True)

    list1 = await client.get(f"/api/v1/projects/{project1.id}/versions")
    v1_id = list1.json()["items"][0]["version_id"]

    # Attempt to access project1's version under project2
    foreign_resp = await client.get(f"/api/v1/projects/{project2.id}/versions/{v1_id}")
    assert foreign_resp.status_code == 404

    # Attempt to activate project1's version under project2
    act_foreign = await client.post(f"/api/v1/projects/{project2.id}/versions/{v1_id}/activate")
    assert act_foreign.status_code == 404
