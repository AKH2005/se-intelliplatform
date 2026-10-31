"""Unit tests for ProjectDownloadService security and ZIP packaging."""

import io
import zipfile
import pytest
from app.models.project import Project, ProjectStatus
from app.services.project_download_service import ProjectDownloadService


def test_sanitize_path_traversal_protection():
    """Verify directory traversal patterns are safely blocked."""
    assert ProjectDownloadService.sanitize_path("../../etc/passwd") is None
    assert ProjectDownloadService.sanitize_path("../secret.py") is None
    assert ProjectDownloadService.sanitize_path("/root/secret.txt") is None
    assert ProjectDownloadService.sanitize_path("C:/Windows/System32/cmd.exe") is None
    assert ProjectDownloadService.sanitize_path("src/../../evil.py") is None

    # Valid relative paths must pass
    assert ProjectDownloadService.sanitize_path("src/main.py") == "src/main.py"
    assert ProjectDownloadService.sanitize_path("frontend/src/App.tsx") == "frontend/src/App.tsx"
    assert ProjectDownloadService.sanitize_path("package.json") == "package.json"


def test_sanitize_path_excludes_ephemeral_and_sensitive_files():
    """Verify secrets, git history, node_modules, and virtualenvs are excluded."""
    assert ProjectDownloadService.sanitize_path(".git/config") is None
    assert ProjectDownloadService.sanitize_path(".git/HEAD") is None
    assert ProjectDownloadService.sanitize_path("node_modules/react/index.js") is None
    assert ProjectDownloadService.sanitize_path(".venv/bin/python") is None
    assert ProjectDownloadService.sanitize_path("venv/lib/site-packages/pkg.py") is None
    assert ProjectDownloadService.sanitize_path("src/__pycache__/utils.cpython-312.pyc") is None
    assert ProjectDownloadService.sanitize_path(".pytest_cache/v/cache/lastfailed") is None
    assert ProjectDownloadService.sanitize_path("dist/assets/index.js") is None
    assert ProjectDownloadService.sanitize_path(".next/server/pages.js") is None
    assert ProjectDownloadService.sanitize_path("private.key") is None
    assert ProjectDownloadService.sanitize_path("ssl/certificate.pem") is None
    assert ProjectDownloadService.sanitize_path("keys/id_rsa") is None


def test_filter_and_sanitize_files_with_env_masking():
    """Verify real .env is converted to safe .env.example with placeholders."""
    raw_files = {
        "src/app.py": "print('hello world')",
        "package.json": '{"name": "test-project"}',
        ".env": "DATABASE_URL=postgres://root:SuperSecret999@localhost:5432/db\nAPI_KEY=sk_live_123456789\nDEBUG=True\n",
        "node_modules/fake.js": "console.log('should be excluded')",
        "__pycache__/app.pyc": "binary",
    }
    project = Project(
        name="Security Test Project",
        slug="security-test-project",
        status=ProjectStatus.IN_PROGRESS,
    )

    clean_files = ProjectDownloadService.filter_and_sanitize_files(raw_files, project)

    # .env must be absent
    assert ".env" not in clean_files
    # node_modules and pycache must be absent
    assert "node_modules/fake.js" not in clean_files
    assert "__pycache__/app.pyc" not in clean_files

    # .env.example must be generated with placeholders
    assert ".env.example" in clean_files
    example_content = clean_files[".env.example"]
    assert "SuperSecret999" not in example_content
    assert "sk_live_123456789" not in example_content
    assert "DATABASE_URL=your_database_url_here" in example_content
    assert "API_KEY=your_api_key_here" in example_content


def test_filter_and_sanitize_empty_project_generates_readme():
    """Verify empty projects receive an authoritative README.md rather than failing."""
    project = Project(
        name="Empty Project",
        slug="empty-project",
        description="A project waiting for code generation.",
        status=ProjectStatus.DRAFT,
    )

    clean_files = ProjectDownloadService.filter_and_sanitize_files({}, project)

    assert "README.md" in clean_files
    readme = clean_files["README.md"]
    assert "# Empty Project" in readme
    assert "empty-project" in readme
    assert "DRAFT" in readme
    assert "Code Generation Workflow" in readme


def test_filter_and_sanitize_files_ensures_app_init_py():
    """Verify app/__init__.py is added when app/ directory contains Python source files."""
    raw_files = {
        "app/main.py": "from fastapi import FastAPI\napp = FastAPI()\n",
        "app/config.py": "class Settings: pass\n",
        "requirements.txt": "fastapi>=0.110.0\n",
    }
    project = Project(
        name="Init Package App",
        slug="init-package-app",
        status=ProjectStatus.IN_PROGRESS,
    )

    clean_files = ProjectDownloadService.filter_and_sanitize_files(raw_files, project)

    assert "app/__init__.py" in clean_files
    assert "app/main.py" in clean_files
    assert "app/config.py" in clean_files


def test_zip_archive_structure_and_integrity():
    """Verify generated ZIP archive unpacks with correct filenames and contents."""
    raw_files = {
        "src/main.py": "def main():\n    print('Hello IntelliPlatform!')\n",
        "README.md": "# My Demo App\n",
        "config.json": '{"mode": "production"}',
    }
    project = Project(
        name="Demo App",
        slug="demo-app",
        status=ProjectStatus.IN_PROGRESS,
    )

    clean_files = ProjectDownloadService.filter_and_sanitize_files(raw_files, project)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p, c in clean_files.items():
            zf.writestr(p, c.encode("utf-8"))

    zip_bytes = zip_buffer.getvalue()

    # Read back and verify ZIP integrity
    read_buf = io.BytesIO(zip_bytes)
    with zipfile.ZipFile(read_buf, mode="r") as zf:
        namelist = zf.namelist()
        assert "src/main.py" in namelist
        assert "README.md" in namelist
        assert "config.json" in namelist
        assert zf.read("src/main.py").decode("utf-8") == raw_files["src/main.py"]


@pytest.mark.asyncio
async def test_generate_project_zip_parent_directories_and_posix_permissions(db_session):
    """Verify generate_project_zip produces explicit directory entries and UNIX attributes."""
    import uuid
    from app.models.workflow_execution import WorkflowExecution, WorkflowStatus
    from app.agents.code_generation.contracts import (
        CodeGenerationOutput,
        CodeGenerationPlan,
        GeneratedFile,
        PlannedFile,
        FileType,
    )

    project = Project(
        id=uuid.uuid4(),
        name="Structured Zip App",
        slug="structured-zip-app",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)

    # Add workflow execution with nested app/ structure
    code_output = CodeGenerationOutput(
        plan=CodeGenerationPlan(
            files=[
                PlannedFile(path="app/main.py", purpose="FastAPI application entrypoint", file_type=FileType.SOURCE),
                PlannedFile(path="requirements.txt", purpose="Project dependencies specification", file_type=FileType.DEPENDENCY),
            ],
            rationale="Test project scaffold plan",
        ),
        generated_files=[
            GeneratedFile(path="app/main.py", content="print('hello')", size_bytes=14),
            GeneratedFile(path="requirements.txt", content="fastapi>=0.110.0\n", size_bytes=16),
        ],
        total_files=2,
        total_size_bytes=30,
        summary="Generated scaffold",
    )
    wf = WorkflowExecution(
        workflow_execution_id=uuid.uuid4(),
        project_id=project.id,
        workflow_id="code-generation-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        artifacts={"code-generation": code_output.model_dump(mode="json")},
    )
    db_session.add(wf)
    await db_session.commit()

    service = ProjectDownloadService(db_session)
    zip_bytes, zip_filename = await service.generate_project_zip(project.id)

    assert zip_filename == "structured-zip-app.zip"
    assert len(zip_bytes) > 0

    read_buf = io.BytesIO(zip_bytes)
    with zipfile.ZipFile(read_buf, "r") as zf:
        infolist = zf.infolist()
        namelist = [info.filename for info in infolist]

        # Directory entry for 'app/' must exist
        assert "app/" in namelist
        app_dir_info = next(i for i in infolist if i.filename == "app/")
        assert app_dir_info.create_system == 3  # UNIX
        # Directory bit must be set (0x10)
        assert (app_dir_info.external_attr & (0x10 << 16)) or (app_dir_info.external_attr & 0x10)

        # File entry permissions must be UNIX (create_system=3)
        main_info = next(i for i in infolist if i.filename == "app/main.py")
        assert main_info.create_system == 3
        # Mode 0o644 in high 16 bits
        assert (main_info.external_attr >> 16) & 0o777 == 0o644

        # Auto-added package init must be present
        assert "app/__init__.py" in namelist


@pytest.mark.asyncio
async def test_get_project_files_scans_across_multiple_workflow_executions(db_session):
    """Verify get_project_files finds code artifact even if later non-code executions occurred."""
    import uuid
    from datetime import datetime, timezone, timedelta
    from app.models.workflow_execution import WorkflowExecution, WorkflowStatus
    from app.agents.code_generation.contracts import (
        CodeGenerationOutput,
        CodeGenerationPlan,
        GeneratedFile,
        PlannedFile,
        FileType,
    )

    project = Project(
        id=uuid.uuid4(),
        name="Multi Run App",
        slug="multi-run-app",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)

    # 1. Earlier execution that produced code
    earlier_code = CodeGenerationOutput(
        plan=CodeGenerationPlan(
            files=[PlannedFile(path="app/main.py", purpose="Application entrypoint", file_type=FileType.SOURCE)],
            rationale="Earlier plan",
        ),
        generated_files=[
            GeneratedFile(path="app/main.py", content="# App code from v1", size_bytes=17),
        ],
        total_files=1,
        total_size_bytes=17,
        summary="Scaffold v1",
    )
    wf_code = WorkflowExecution(
        workflow_execution_id=uuid.uuid4(),
        project_id=project.id,
        workflow_id="code-generation-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        started_at=datetime.now(timezone.utc) - timedelta(minutes=10),
        artifacts={"code-generation": earlier_code.model_dump(mode="json")},
    )
    db_session.add(wf_code)

    # 2. Later execution that did NOT produce code (e.g. estimation workflow)
    wf_est = WorkflowExecution(
        workflow_execution_id=uuid.uuid4(),
        project_id=project.id,
        workflow_id="project-estimation-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        started_at=datetime.now(timezone.utc),
        artifacts={"risk-prediction": {"risk_score": 0.2}},
    )
    db_session.add(wf_est)
    await db_session.commit()

    service = ProjectDownloadService(db_session)
    files_map = await service.get_project_files(project.id)

    assert "app/main.py" in files_map
    assert files_map["app/main.py"] == "# App code from v1"
