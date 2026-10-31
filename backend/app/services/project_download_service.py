"""Project Code Packaging and ZIP Archive Download Service.

Gathers generated and configured source files for an authorized project,
safely filters secrets and ephemeral build artifacts, prevents path traversal,
and packages an authoritative in-memory ZIP archive for download.
"""

import io
import logging
import os
import re
import uuid
import zipfile
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.code_generation.contracts import CodeGenerationOutput
from app.code_intelligence.detector import mask_credentials
from app.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.models.development_version import DevelopmentVersion
from app.models.project import Project
from app.models.user import User
from app.models.workflow_execution import WorkflowExecution
from app.services.development_version_service import DevelopmentVersionService

logger = logging.getLogger(__name__)

# Patterns and directories strictly excluded from downloaded source packages
EXCLUDED_PATTERNS = (
    ".git/",
    ".git",
    "node_modules/",
    "node_modules",
    ".venv/",
    "venv/",
    "env/",
    "__pycache__/",
    ".pytest_cache/",
    ".mypy_cache/",
    "dist/",
    "build/",
    ".next/",
    ".nuxt/",
)

EXCLUDED_EXTENSIONS = (
    ".pyc",
    ".pyo",
    ".pyd",
    ".key",
    ".pem",
    ".pfx",
    ".cert",
)

# Limits to prevent memory exhaustion
MAX_TOTAL_FILES = 1000
MAX_ARCHIVE_BYTES = 50 * 1024 * 1024  # 50 MB


class ProjectDownloadService:
    """Service to create safe, authenticated project ZIP downloads."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.version_service = DevelopmentVersionService(session)

    async def get_project_files(
        self,
        project_id: uuid.UUID,
        version_id: uuid.UUID | None = None,
    ) -> dict[str, str]:
        """Resolve authoritative files map for project, from active version or executions."""
        files_map: dict[str, str] = {}

        # 1. Try specified version
        target_version: DevelopmentVersion | None = None
        if version_id:
            stmt = select(DevelopmentVersion).where(
                DevelopmentVersion.id == version_id,
                DevelopmentVersion.project_id == project_id,
            )
            res = await self.session.execute(stmt)
            target_version = res.scalar_one_or_none()
        else:
            # 2. Try active development version
            active_resp = await self.version_service.get_active_version(project_id)
            if active_resp:
                stmt = select(DevelopmentVersion).where(
                    DevelopmentVersion.id == active_resp.version_id,
                    DevelopmentVersion.project_id == project_id,
                )
                res = await self.session.execute(stmt)
                target_version = res.scalar_one_or_none()

            # 3. Fallback to latest development version
            if not target_version:
                latest_stmt = (
                    select(DevelopmentVersion)
                    .where(DevelopmentVersion.project_id == project_id)
                    .order_by(DevelopmentVersion.version_number.desc())
                    .limit(1)
                )
                l_res = await self.session.execute(latest_stmt)
                target_version = l_res.scalar_one_or_none()

        if target_version:
            try:
                files_map = await self.version_service._resolve_version_files_map(target_version)
            except Exception as exc:
                logger.warning(f"Could not load version files for {target_version.id}: {exc}")

        # 4. If still empty, check WorkflowExecution artifacts across recent executions
        if not files_map:
            wf_stmt = (
                select(WorkflowExecution)
                .where(WorkflowExecution.project_id == project_id)
                .order_by(WorkflowExecution.started_at.desc())
            )
            wf_res = await self.session.execute(wf_stmt)
            for wf in wf_res.scalars().all():
                if wf and wf.artifacts:
                    for key in ("code-generation", "code_generation"):
                        if key in wf.artifacts:
                            try:
                                artifact = CodeGenerationOutput.model_validate(wf.artifacts[key])
                                files_map = {f.path: f.content for f in artifact.generated_files}
                                break
                            except Exception:
                                pass
                    if files_map:
                        break

        return files_map

    @classmethod
    def sanitize_path(cls, file_path: str) -> str | None:
        """Validate and normalize path, preventing directory traversal.
        
        Returns normalized path or None if path is unsafe.
        """
        clean = file_path.replace("\\", "/").strip()
        norm = os.path.normpath(clean).replace("\\", "/")

        # Forbid absolute paths, traversal prefix, drive letters
        if norm.startswith("/") or norm.startswith("..") or "/../" in norm or ":" in norm:
            logger.warning(f"Directory traversal attempt rejected: {file_path}")
            return None

        # Forbid excluded directories and patterns
        for exc in EXCLUDED_PATTERNS:
            if norm == exc.rstrip("/") or norm.startswith(exc) or f"/{exc}" in norm:
                return None

        # Forbid sensitive extensions
        _, ext = os.path.splitext(norm)
        if ext.lower() in EXCLUDED_EXTENSIONS:
            return None

        # Check for id_rsa or credential names
        base = os.path.basename(norm).lower()
        if base in ("id_rsa", "id_dsa", "id_ed25519", "credentials", "secrets.json"):
            return None

        return norm

    @classmethod
    def filter_and_sanitize_files(
        cls,
        files_map: dict[str, str],
        project: Project,
    ) -> dict[str, str]:
        """Apply security filters, mask passwords in .env, and ensure clean structure."""
        sanitized: dict[str, str] = {}
        env_content: str | None = None

        for raw_path, content in files_map.items():
            safe_path = cls.sanitize_path(raw_path)
            if not safe_path:
                continue

            # Special handling for .env: convert into safe .env.example
            base_name = os.path.basename(safe_path)
            if base_name in (".env", ".env.local", ".env.production", ".env.development"):
                env_content = content
                continue

            sanitized[safe_path] = content

        # Generate a safe .env.example with masked placeholders
        if env_content:
            masked_env_lines = []
            for line in env_content.splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, _ = line.split("=", 1)
                    k = k.strip()
                    masked_env_lines.append(f"{k}=your_{k.lower()}_here")
                else:
                    masked_env_lines.append(line)
            sanitized[".env.example"] = "\n".join(masked_env_lines) + "\n"

        # Ensure app package has an __init__.py if app/ directory contains python files
        has_app_py = any(p.startswith("app/") and p.endswith(".py") for p in sanitized.keys())
        if has_app_py and "app/__init__.py" not in sanitized:
            sanitized["app/__init__.py"] = '"""Application package initialization."""\n'

        # If project has no source files at all, generate an informative README
        if not sanitized:
            readme_text = f"""# {project.name}

{project.description or "Generated project source package from SE IntelliPlatform."}

## Overview
- **Project Slug:** `{project.slug}`
- **Project Status:** `{project.status.value}`
- **Created:** `{project.created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if project.created_at else 'N/A'}`

## Notice
This project archive currently contains only documentation because code generation has not been run yet.

To generate full multi-file executable source code:
1. Open the project in **SE IntelliPlatform**.
2. Navigate to the **Development Workspace**.
3. Run the **Code Generation Workflow** (or use IntelliAssist: `Run Code Generation`).
4. Re-download this source package to receive the complete project scaffold.
"""
            sanitized["README.md"] = readme_text

        return sanitized

    async def generate_project_zip(
        self,
        project_id: uuid.UUID,
        version_id: uuid.UUID | None = None,
        user: User | None = None,
    ) -> tuple[bytes, str]:
        """Generate a secure, filtered in-memory ZIP archive for an authorized project.
        
        Returns:
            tuple[bytes, str]: (archive_bytes, filename)
        """
        # 1. Authorize project access
        stmt = select(Project).where(Project.id == project_id)
        res = await self.session.execute(stmt)
        project = res.scalar_one_or_none()
        if not project:
            raise NotFoundError("Project", str(project_id))

        if project.owner_id is not None:
            if user is None:
                raise UnauthorizedError("Authentication required to download this project.")
            if project.owner_id != user.id:
                raise ForbiddenError("You do not have permission to download this project.")

        # 2. Retrieve project files
        files_map = await self.get_project_files(project_id, version_id)

        # 3. Sanitize paths and exclude secrets
        clean_files = self.filter_and_sanitize_files(files_map, project)

        if len(clean_files) > MAX_TOTAL_FILES:
            raise ValueError(f"Project contains {len(clean_files)} files, exceeding limit of {MAX_TOTAL_FILES}.")

        # 4. Synthesize ZIP archive in memory with POSIX permissions and directory entries
        zip_buffer = io.BytesIO()
        total_size = 0

        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            created_dirs: set[str] = set()
            for file_path, content in sorted(clean_files.items()):
                # Ensure parent directory entries exist in archive
                parts = file_path.split("/")
                if len(parts) > 1:
                    for i in range(1, len(parts)):
                        dir_path = "/".join(parts[:i]) + "/"
                        if dir_path not in created_dirs:
                            dir_info = zipfile.ZipInfo(filename=dir_path)
                            dir_info.create_system = 3  # UNIX
                            dir_info.external_attr = (0o755 << 16) | 0x10  # directory attribute
                            zf.writestr(dir_info, b"")
                            created_dirs.add(dir_path)

                encoded = content.encode("utf-8")
                total_size += len(encoded)
                if total_size > MAX_ARCHIVE_BYTES:
                    raise ValueError(f"Project uncompressed size exceeds limit of {MAX_ARCHIVE_BYTES // (1024 * 1024)}MB.")

                # Create zip entry with POSIX permission attributes
                info = zipfile.ZipInfo(filename=file_path)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3  # UNIX
                # Use standard 0o644 file permission
                info.external_attr = 0o644 << 16
                zf.writestr(info, encoded)

        zip_bytes = zip_buffer.getvalue()
        zip_filename = f"{project.slug or 'project'}.zip"

        logger.info(f"Generated ZIP archive '{zip_filename}' for project {project_id} ({len(clean_files)} files, {len(zip_bytes)} bytes).")
        return zip_bytes, zip_filename
