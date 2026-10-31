"""Unit tests for Code Studio File Operations, Validation, and Concurrency."""

import uuid
import pytest
from app.agents.code_generation.contracts import (
    CodeGenerationOutput,
    CodeGenerationPlan,
    FileType,
    GeneratedFile,
    PlannedFile,
)
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.development_version import DevelopmentVersion, DevelopmentVersionStatus
from app.models.project import Project, ProjectStatus
from app.models.user import User
from app.models.workflow_execution import WorkflowExecution, WorkflowExecutionStatus
from app.schemas.code_studio import SaveFileRequest
from app.services.development_version_service import (
    DevelopmentVersionService,
    FileValidator,
    build_file_tree,
    infer_file_language,
)


def _make_code_output(gen_files: list[GeneratedFile]) -> CodeGenerationOutput:
    """Helper to construct valid CodeGenerationOutput for unit tests."""
    planned = [
        PlannedFile(path=f.path, purpose=f"Test file {f.path}", file_type=FileType.SOURCE)
        for f in gen_files
    ]
    plan = CodeGenerationPlan(
        files=planned,
        rationale="Unit test generation plan rationale.",
    )
    return CodeGenerationOutput(
        plan=plan,
        generated_files=gen_files,
        total_files=len(gen_files),
        total_size_bytes=sum(f.size_bytes for f in gen_files),
        summary="Test generated files output summary.",
    )


def test_infer_file_language():
    """Verify correct language identification across polyglot project files."""
    assert infer_file_language("app/main.py") == "python"
    assert infer_file_language("src/App.tsx") == "typescript"
    assert infer_file_language("src/index.ts") == "typescript"
    assert infer_file_language("src/utils.js") == "javascript"
    assert infer_file_language("src/components/Card.jsx") == "javascript"
    assert infer_file_language("package.json") == "json"
    assert infer_file_language("index.html") == "html"
    assert infer_file_language("styles/app.css") == "css"
    assert infer_file_language("schema.sql") == "sql"
    assert infer_file_language("README.md") == "markdown"
    assert infer_file_language("Dockerfile") == "dockerfile"
    assert infer_file_language("notes.txt") == "plaintext"


def test_path_sanitization():
    """Verify strict path traversal and forbidden file rejection."""
    # Forbidden traversal
    assert DevelopmentVersionService.sanitize_file_path("../../etc/passwd") is None
    assert DevelopmentVersionService.sanitize_file_path("../secret.py") is None
    assert DevelopmentVersionService.sanitize_file_path("/root/file.py") is None
    assert DevelopmentVersionService.sanitize_file_path("C:/Windows/file.py") is None
    assert DevelopmentVersionService.sanitize_file_path("app/../../secret.py") is None
    assert DevelopmentVersionService.sanitize_file_path("app/\x00evil.py") is None
    assert DevelopmentVersionService.sanitize_file_path("") is None
    assert DevelopmentVersionService.sanitize_file_path("   ") is None

    # Forbidden extensions and secrets
    assert DevelopmentVersionService.sanitize_file_path(".git/config") is None
    assert DevelopmentVersionService.sanitize_file_path("node_modules/lib.js") is None
    assert DevelopmentVersionService.sanitize_file_path(".venv/bin/python") is None
    assert DevelopmentVersionService.sanitize_file_path("secret.key") is None
    assert DevelopmentVersionService.sanitize_file_path("cert.pem") is None
    assert DevelopmentVersionService.sanitize_file_path("id_rsa") is None
    assert DevelopmentVersionService.sanitize_file_path("secrets.json") is None

    # Valid relative paths
    assert DevelopmentVersionService.sanitize_file_path("app/main.py") == "app/main.py"
    assert DevelopmentVersionService.sanitize_file_path("src/components/Header.tsx") == "src/components/Header.tsx"
    assert DevelopmentVersionService.sanitize_file_path("README.md") == "README.md"


def test_file_validator_python_syntax():
    """Verify Python AST syntax validation."""
    valid_py = "def hello():\n    return 'world'\n"
    res_valid = FileValidator.validate("app/service.py", valid_py)
    assert res_valid.status == "PASSED"
    assert len(res_valid.errors) == 0

    invalid_py = "def broken(:\n    return 'fail'"
    res_invalid = FileValidator.validate("app/service.py", invalid_py)
    assert res_invalid.status == "FAILED"
    assert len(res_invalid.errors) > 0
    assert "SyntaxError" in res_invalid.errors[0]


def test_file_validator_json():
    """Verify JSON validation."""
    valid_json = '{"name": "test", "version": "1.0.0", "active": true}'
    res_valid = FileValidator.validate("package.json", valid_json)
    assert res_valid.status == "PASSED"

    invalid_json = '{"name": "broken", invalid_key: 123}'
    res_invalid = FileValidator.validate("package.json", invalid_json)
    assert res_invalid.status == "FAILED"
    assert len(res_invalid.errors) > 0


def test_file_validator_null_bytes():
    """Verify rejection of binary null bytes in source files."""
    binary_content = "def hello():\x00pass"
    res = FileValidator.validate("script.py", binary_content)
    assert res.status == "FAILED"


def test_build_file_tree_hierarchy():
    """Verify conversion of flat files map into a properly sorted nested tree."""
    files_dict = {
        "src/components/Button.tsx": {"path": "src/components/Button.tsx", "size_bytes": 120, "language": "typescript"},
        "src/components/Header.tsx": {"path": "src/components/Header.tsx", "size_bytes": 200, "language": "typescript"},
        "src/App.tsx": {"path": "src/App.tsx", "size_bytes": 350, "language": "typescript"},
        "README.md": {"path": "README.md", "size_bytes": 80, "language": "markdown"},
        "backend/main.py": {"path": "backend/main.py", "size_bytes": 500, "language": "python"},
    }

    tree = build_file_tree(files_dict)
    assert len(tree) == 3  # backend (dir), src (dir), README.md (file)

    names = [node.name for node in tree]
    # Directories sorted first alphabetically, files after
    assert names == ["backend", "src", "README.md"]

    # Check src directory
    src_node = next(n for n in tree if n.name == "src")
    assert src_node.type == "directory"
    assert len(src_node.children or []) == 2  # components (dir), App.tsx (file)

    comp_node = next(n for n in (src_node.children or []) if n.name == "components")
    assert comp_node.type == "directory"
    assert len(comp_node.children or []) == 2  # Button.tsx, Header.tsx


@pytest.mark.asyncio
async def test_get_file_tree_empty_project(db_session):
    """Empty project without versions returns empty tree with has_generated_code=False."""
    service = DevelopmentVersionService(db_session)
    proj = Project(name="Empty Project", slug="empty-proj", status=ProjectStatus.DRAFT)
    db_session.add(proj)
    await db_session.commit()

    resp = await service.get_file_tree(proj.id)
    assert resp.has_generated_code is False
    assert resp.total_files == 0
    assert resp.root_nodes == []
    assert resp.version_id is None


@pytest.mark.asyncio
async def test_get_file_tree_with_active_version(db_session):
    """Authorized project with generated files returns hierarchical tree with active version."""
    service = DevelopmentVersionService(db_session)
    proj = Project(name="Code Project", slug="code-proj", status=ProjectStatus.IN_PROGRESS)
    db_session.add(proj)
    await db_session.commit()

    # Seed workflow execution and version
    gen_files = [
        GeneratedFile(path="app/main.py", content="print('hello')", size_bytes=14, language="python"),
        GeneratedFile(path="README.md", content="# Project", size_bytes=9, language="markdown"),
    ]
    code_out = _make_code_output(gen_files)
    wf_id = uuid.uuid4()
    wf = WorkflowExecution(
        workflow_execution_id=wf_id,
        project_id=proj.id,
        workflow_id="code-generation",
        workflow_version="1.0.0",
        status=WorkflowExecutionStatus.COMPLETED,
        artifacts={"code-generation": code_out.model_dump(mode="json")},
    )
    db_session.add(wf)

    version_id = uuid.uuid4()
    version = DevelopmentVersion(
        id=version_id,
        project_id=proj.id,
        version_number=1,
        workflow_execution_id=wf_id,
        artifact_key="code-generation",
        status=DevelopmentVersionStatus.VERIFIED,
        content_hash="abc123hash",
        manifest_hash="def456hash",
        file_count=2,
        total_size_bytes=23,
        source_reason="INITIAL_GENERATION",
        created_by="system",
        files_manifest=[
            {"path": "app/main.py", "size_bytes": 14, "language": "python"},
            {"path": "README.md", "size_bytes": 9, "language": "markdown"},
        ],
    )
    db_session.add(version)
    proj.settings = {"active_version_id": str(version_id)}
    await db_session.commit()

    tree_resp = await service.get_file_tree(proj.id)
    assert tree_resp.has_generated_code is True
    assert tree_resp.version_id == version_id
    assert tree_resp.version_number == 1
    assert tree_resp.total_files == 2
    assert len(tree_resp.root_nodes) == 2


@pytest.mark.asyncio
async def test_get_file_content_and_missing(db_session):
    """Retrieving file content returns accurate metadata, while missing files raise NotFoundError."""
    service = DevelopmentVersionService(db_session)
    proj = Project(name="Fetch Project", slug="fetch-proj", status=ProjectStatus.IN_PROGRESS)
    db_session.add(proj)
    await db_session.commit()

    code_content = "def test():\n    return 42\n"
    gen_files = [GeneratedFile(path="app/test.py", content=code_content, size_bytes=len(code_content), language="python")]
    code_out = _make_code_output(gen_files)
    wf_id = uuid.uuid4()
    wf = WorkflowExecution(
        workflow_execution_id=wf_id,
        project_id=proj.id,
        workflow_id="code-generation",
        workflow_version="1.0.0",
        status=WorkflowExecutionStatus.COMPLETED,
        artifacts={"code-generation": code_out.model_dump(mode="json")},
    )
    db_session.add(wf)
    v_id = uuid.uuid4()
    ver = DevelopmentVersion(
        id=v_id,
        project_id=proj.id,
        version_number=1,
        workflow_execution_id=wf_id,
        artifact_key="code-generation",
        status=DevelopmentVersionStatus.VERIFIED,
        content_hash="h1",
        manifest_hash="m1",
        file_count=1,
        total_size_bytes=len(code_content),
        files_manifest=[{"path": "app/test.py", "size_bytes": len(code_content), "language": "python"}],
    )
    db_session.add(ver)
    proj.settings = {"active_version_id": str(v_id)}
    await db_session.commit()

    # Successful retrieval
    f_resp = await service.get_file_content_by_path(proj.id, "app/test.py")
    assert f_resp.path == "app/test.py"
    assert f_resp.content == code_content
    assert f_resp.language == "python"
    assert f_resp.version_number == 1

    # Missing file -> NotFoundError
    with pytest.raises(NotFoundError):
        await service.get_file_content_by_path(proj.id, "nonexistent.py")

    # Path traversal -> ValidationError
    with pytest.raises(ValidationError):
        await service.get_file_content_by_path(proj.id, "../etc/passwd")


@pytest.mark.asyncio
async def test_save_valid_file_creates_immutable_child_version(db_session):
    """Saving an edit creates child version v2, preserves other files, and updates active pointer."""
    service = DevelopmentVersionService(db_session)
    proj = Project(name="Save Project", slug="save-proj", status=ProjectStatus.IN_PROGRESS)
    db_session.add(proj)
    await db_session.commit()

    initial_main = "def original():\n    return 'v1'\n"
    initial_readme = "# Original README\nPreserved content.\n"
    gen_files = [
        GeneratedFile(path="app/main.py", content=initial_main, size_bytes=len(initial_main), language="python"),
        GeneratedFile(path="README.md", content=initial_readme, size_bytes=len(initial_readme), language="markdown"),
    ]
    code_out = _make_code_output(gen_files)
    wf_id = uuid.uuid4()
    wf = WorkflowExecution(
        workflow_execution_id=wf_id,
        project_id=proj.id,
        workflow_id="code-generation",
        workflow_version="1.0.0",
        status=WorkflowExecutionStatus.COMPLETED,
        artifacts={"code-generation": code_out.model_dump(mode="json")},
    )
    db_session.add(wf)
    v1_id = uuid.uuid4()
    v1 = DevelopmentVersion(
        id=v1_id,
        project_id=proj.id,
        version_number=1,
        workflow_execution_id=wf_id,
        artifact_key="code-generation",
        status=DevelopmentVersionStatus.VERIFIED,
        content_hash="content_v1",
        manifest_hash="manifest_v1",
        file_count=2,
        total_size_bytes=len(initial_main) + len(initial_readme),
        files_manifest=[
            {"path": "app/main.py", "size_bytes": len(initial_main), "language": "python"},
            {"path": "README.md", "size_bytes": len(initial_readme), "language": "markdown"},
        ],
    )
    db_session.add(v1)
    proj.settings = {"active_version_id": str(v1_id)}
    await db_session.commit()

    # Save edit to app/main.py
    updated_main = "def updated():\n    return 'v2 in Code Studio'\n"
    req = SaveFileRequest(
        content=updated_main,
        parent_version_id=v1_id,
        reason="Updated main logic in Code Studio",
    )

    save_resp = await service.save_file_content(proj.id, "app/main.py", req)
    assert save_resp.success is True
    assert save_resp.version_number == 2
    assert save_resp.parent_version_id == v1_id
    assert save_resp.path == "app/main.py"
    assert save_resp.validation.status == "PASSED"

    # Verify project active pointer advanced
    await db_session.refresh(proj)
    assert proj.settings.get("active_version_id") == str(save_resp.version_id)

    # Verify v1 is preserved with status SUPERSEDED
    await db_session.refresh(v1)
    assert v1.status == DevelopmentVersionStatus.SUPERSEDED

    # Verify unrelated file README.md is byte-for-byte preserved in v2
    readme_resp = await service.get_file_content_by_path(proj.id, "README.md")
    assert readme_resp.content == initial_readme

    # Verify updated main.py has new content
    main_resp = await service.get_file_content_by_path(proj.id, "app/main.py")
    assert main_resp.content == updated_main


@pytest.mark.asyncio
async def test_save_concurrency_conflict_detected(db_session):
    """Attempting to save using a stale parent_version_id raises ConflictError (409)."""
    service = DevelopmentVersionService(db_session)
    proj = Project(name="Conflict Project", slug="conflict-proj", status=ProjectStatus.IN_PROGRESS)
    db_session.add(proj)
    await db_session.commit()

    v1_id = uuid.uuid4()
    v1 = DevelopmentVersion(
        id=v1_id,
        project_id=proj.id,
        version_number=1,
        status=DevelopmentVersionStatus.SUPERSEDED,
        content_hash="h1",
        manifest_hash="m1",
        file_count=1,
        total_size_bytes=10,
        files_manifest=[{"path": "app.py", "size_bytes": 10}],
    )
    v2_id = uuid.uuid4()
    v2 = DevelopmentVersion(
        id=v2_id,
        project_id=proj.id,
        version_number=2,
        parent_version_id=v1_id,
        status=DevelopmentVersionStatus.VERIFIED,
        content_hash="h2",
        manifest_hash="m2",
        file_count=1,
        total_size_bytes=20,
        files_manifest=[{"path": "app.py", "size_bytes": 20}],
    )
    db_session.add_all([v1, v2])
    proj.settings = {"active_version_id": str(v2_id)}  # Active version is v2!
    await db_session.commit()

    # User tries to save against stale v1
    req = SaveFileRequest(
        content="print('stale edit')",
        parent_version_id=v1_id,
    )
    with pytest.raises(ConflictError) as exc_info:
        await service.save_file_content(proj.id, "app.py", req)
    assert "Version conflict" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_save_python_syntax_error_rejected_without_version_creation(db_session):
    """Syntax error in Python code is rejected with ValidationError; previous version remains active."""
    service = DevelopmentVersionService(db_session)
    proj = Project(name="Syntax Project", slug="syntax-proj", status=ProjectStatus.IN_PROGRESS)
    db_session.add(proj)
    await db_session.commit()

    code_content = "def valid():\n    pass\n"
    gen_files = [GeneratedFile(path="calc.py", content=code_content, size_bytes=len(code_content), language="python")]
    code_out = _make_code_output(gen_files)
    wf_id = uuid.uuid4()
    wf = WorkflowExecution(
        workflow_execution_id=wf_id,
        project_id=proj.id,
        workflow_id="code-generation",
        workflow_version="1.0.0",
        status=WorkflowExecutionStatus.COMPLETED,
        artifacts={"code-generation": code_out.model_dump(mode="json")},
    )
    db_session.add(wf)
    v1_id = uuid.uuid4()
    v1 = DevelopmentVersion(
        id=v1_id,
        project_id=proj.id,
        version_number=1,
        workflow_execution_id=wf_id,
        artifact_key="code-generation",
        status=DevelopmentVersionStatus.VERIFIED,
        content_hash="h_orig",
        manifest_hash="m_orig",
        file_count=1,
        total_size_bytes=len(code_content),
        files_manifest=[{"path": "calc.py", "size_bytes": len(code_content), "language": "python"}],
    )
    db_session.add(v1)
    proj.settings = {"active_version_id": str(v1_id)}
    await db_session.commit()

    # Broken Python syntax
    broken_code = "def syntax_error(:\n    return broken"
    req = SaveFileRequest(content=broken_code, parent_version_id=v1_id)

    with pytest.raises(ValidationError) as exc_info:
        await service.save_file_content(proj.id, "calc.py", req)
    assert "Validation failed" in str(exc_info.value.message)

    # Verify no new version created; active version remains v1
    await db_session.refresh(proj)
    assert proj.settings.get("active_version_id") == str(v1_id)
    await db_session.refresh(v1)
    assert v1.status == DevelopmentVersionStatus.VERIFIED


@pytest.mark.asyncio
async def test_save_ownership_authorization_enforced(db_session):
    """Unauthorized user attempting to save to another user's project is rejected with ForbiddenError."""
    service = DevelopmentVersionService(db_session)
    owner_id = uuid.uuid4()
    proj = Project(name="Private Project", slug="private-proj", owner_id=owner_id, status=ProjectStatus.IN_PROGRESS)
    db_session.add(proj)
    await db_session.commit()

    intruder = User(id=uuid.uuid4(), email="intruder@test.com", hashed_password="pw", is_active=True)

    req = SaveFileRequest(content="print('hacked')", parent_version_id=uuid.uuid4())
    with pytest.raises(ForbiddenError):
        await service.save_file_content(proj.id, "app.py", req, current_user=intruder)
