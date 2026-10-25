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
