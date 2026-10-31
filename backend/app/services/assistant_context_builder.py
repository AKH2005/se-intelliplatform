"""Assistant Context Builder for Phase 11I Intelli Assistant.

Builds bounded canonical snapshots (target <= 2,000 tokens) summarizing
project metadata, active version, deterministic verification, recent failure diagnoses,
and remediation status. Never injects full repositories into LLM context.
"""

import json
import logging
import uuid
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.assistant import AssistantContext
from app.services.context_engine import ProjectContextEngine
from app.services.development_version_service import DevelopmentVersionService
from app.services.requirement_service import RequirementService

logger = logging.getLogger(__name__)


class AssistantContextBuilder:
    """Constructs bounded, token-efficient engineering context for conversational reasoning."""

    def __init__(
        self,
        session: AsyncSession,
        context_engine: ProjectContextEngine,
        version_service: DevelopmentVersionService,
        requirement_service: RequirementService,
        remediation_service: Any | None = None,
        browser_testing_service: Any | None = None,
    ) -> None:
        self.session = session
        self.context_engine = context_engine
        self.version_service = version_service
        self.requirement_service = requirement_service
        self.remediation_service = remediation_service
        self.browser_testing_service = browser_testing_service

    async def build_context(
        self,
        project_id: uuid.UUID,
        user_query: str | None = None,
        explicit_file_paths: list[str] | None = None,
        error_message: str | None = None,
        detected_intent: str | None = None,
        active_persona: str | None = None,
    ) -> AssistantContext:
        """Deterministically gather bounded context elements for the Assistant prompt."""
        # 1. Base project metadata
        project_ctx = await self.context_engine.generate_context(project_id)
        req_count = len(project_ctx.requirements) if project_ctx.requirements else 0

        # 2. Active software release version
        active_ver = await self.version_service.get_active_version(project_id)
        ver_id = getattr(active_ver, "version_id", getattr(active_ver, "id", None)) if active_ver else None
        ver_number = active_ver.version_number if active_ver else None
        ver_status = active_ver.status.value if active_ver else None
        ver_hash = active_ver.content_hash[:12] if active_ver and active_ver.content_hash else None

        verification_summary = None
        recent_change_summary = None
        if active_ver:
            raw_snap = getattr(active_ver, "verification_snapshot", None)
            raw_sum = getattr(active_ver, "verification_summary", None)
            target_val = raw_snap if raw_snap is not None else raw_sum
            if target_val is not None:
                if isinstance(target_val, str):
                    verification_summary = target_val
                elif hasattr(target_val, "summary") and isinstance(getattr(target_val, "summary"), str):
                    verification_summary = getattr(target_val, "summary")
                elif isinstance(target_val, dict):
                    verification_summary = str(target_val.get("summary") or json.dumps(target_val))
                else:
                    verification_summary = str(target_val)
            active_id = getattr(active_ver, "version_id", getattr(active_ver, "id", None))
            try:
                if active_id:
                    changes = await self.version_service.list_changes(project_id, active_id)
                    if changes:
                        latest = changes[:3]
                        recent_change_summary = "; ".join(
                            f"[{c.change_type.value}] {c.summary}" for c in latest
                        )
            except Exception as e:
                logger.debug(f"Could not load changes for version {active_id}: {e}")

        # 3. Recent failure diagnosis and remediation proposal status
        recent_failure_title = None
        recent_failure_severity = None
        active_remediation_proposal_id = None
        active_remediation_status = None

        if self.remediation_service:
            try:
                target_exec = await self.remediation_service._resolve_target_execution(project_id)
                artifacts = target_exec.artifacts or {}
                if "failure_analysis" in artifacts:
                    diag = artifacts["failure_analysis"]
                    recent_failure_title = diag.get("title")
                    recent_failure_severity = diag.get("severity")
                if "remediation_proposal" in artifacts:
                    prop = artifacts["remediation_proposal"]
                    active_remediation_proposal_id = prop.get("proposal_id")
                    active_remediation_status = prop.get("status")
            except Exception as e:
                logger.debug(f"Could not resolve workflow artifacts for project {project_id}: {e}")

        # 4. Latest Browser Test Status
        latest_browser_status = None
        latest_browser_summary = None
        if self.browser_testing_service:
            try:
                ver_target = getattr(active_ver, "version_id", getattr(active_ver, "id", None)) if active_ver else None
                run = await self.browser_testing_service.get_latest_browser_test_run(project_id, ver_target)
                if run:
                    latest_browser_status = run.status.value
                    latest_browser_summary = run.summary
            except Exception as e:
                logger.debug(f"Could not resolve browser testing run for project {project_id}: {e}")

        # 5. Live Telemetry Execution Status
        active_executions_summary = None
        try:
            from app.telemetry.bus import get_event_bus
            active_snaps = get_event_bus().list_active_executions(str(project_id))
            if active_snaps:
                running_snaps = [s for s in active_snaps if "RUNNING" in s.status]
                target_snaps = running_snaps if running_snaps else active_snaps[:3]
                summaries = []
                for s in target_snaps:
                    phase_str = f", phase='{s.current_phase}'" if s.current_phase else ""
                    dur_str = f", elapsed={s.duration_seconds}s" if s.duration_seconds is not None else ""
                    summaries.append(f"[{s.execution_kind.value}] status={s.status}{phase_str}{dur_str}")
                active_executions_summary = "; ".join(summaries)
        except Exception as e:
            logger.debug(f"Could not load live execution telemetry for project {project_id}: {e}")

        # 6. Multi-Environment Deployment Status (Phase 13)
        environments_summary = None
        try:
            from app.services.environment_service import EnvironmentService
            env_svc = EnvironmentService(self.session)
            envs = await env_svc.get_or_create_project_environments(project_id)
            if envs:
                env_parts = []
                for env in envs:
                    v_str = f"v{env.current_version.version_number}" if env.current_version else "no-version"
                    env_parts.append(f"{env.environment_type.value}: {v_str} ({env.status.value})")
                environments_summary = "; ".join(env_parts)
        except Exception as e:
            logger.debug(f"Could not load environment states for project {project_id}: {e}")

        # 7. Polyglot Code Intelligence Language Breakdown (Phase 14)
        polyglot_languages_summary = None
        try:
            if active_ver and active_ver.files_manifest:
                from collections import Counter
                from app.code_intelligence.detector import LanguageDetector
                lang_counts = Counter(
                    LanguageDetector.detect(
                        item.get("path") if isinstance(item, dict) else getattr(item, "path", "")
                    ).value
                    for item in active_ver.files_manifest
                )
                polyglot_languages_summary = ", ".join(f"{lang}: {cnt}" for lang, cnt in sorted(lang_counts.items()))
        except Exception as e:
            logger.debug(f"Could not load polyglot languages summary for project {project_id}: {e}")

        # 8. Project-Aware File & Source Retrieval (Phase 3A)
        files_manifest_summary: list[dict[str, Any]] = []
        retrieved_files: list[dict[str, Any]] = []
        missing_files_requested: list[str] = []
        manifest_map: dict[str, dict[str, Any]] = {}

        if active_ver and active_ver.files_manifest:
            for item in active_ver.files_manifest:
                p = item.get("path") if isinstance(item, dict) else getattr(item, "path", "")
                l = item.get("language") if isinstance(item, dict) else getattr(item, "language", "")
                s = item.get("size_bytes") if isinstance(item, dict) else getattr(item, "size_bytes", 0)
                if p:
                    entry = {"path": p, "language": l, "size_bytes": s}
                    files_manifest_summary.append(entry)
                    manifest_map[p.lower()] = {"original_path": p, "entry": entry}

        # Fallback: resolve from version ORM files map if files_manifest is empty
        if active_ver and not files_manifest_summary:
            try:
                from sqlalchemy import select
                from app.models.development_version import DevelopmentVersion
                from app.services.development_version_service import infer_file_language
                target_uuid = active_ver.version_id if hasattr(active_ver, "version_id") else active_ver.id
                stmt_v = select(DevelopmentVersion).where(
                    DevelopmentVersion.id == target_uuid,
                    DevelopmentVersion.project_id == project_id,
                )
                res_v = await self.session.execute(stmt_v)
                v_orm = res_v.scalar_one_or_none()
                if v_orm:
                    f_map = await self.version_service._resolve_version_files_map(v_orm)
                    for fp, fc in f_map.items():
                        flang = infer_file_language(fp)
                        fsize = len(fc.encode("utf-8"))
                        fentry = {"path": fp, "language": flang, "size_bytes": fsize}
                        files_manifest_summary.append(fentry)
                        manifest_map[fp.lower()] = {"original_path": fp, "entry": fentry}
            except Exception as e:
                logger.debug(f"Could not load fallback files manifest from ORM: {e}")

        # Identify files relevant to the user's inquiry
        candidate_paths: list[str] = []
        import re

        query_lower = (user_query or "").lower()

        # A. Explicit file paths
        if explicit_file_paths:
            for efp in explicit_file_paths:
                norm_efp = efp.strip().replace("\\", "/").lstrip("/").lower()
                if norm_efp in manifest_map:
                    candidate_paths.append(manifest_map[norm_efp]["original_path"])
                else:
                    missing_files_requested.append(efp)

        # B. User query file pattern mentions
        if user_query:
            tokens = re.findall(
                r"[\w./-]+\.(?:tsx|ts|jsx|js|py|json|html|css|md|txt|yml|yaml|toml)",
                user_query,
                re.IGNORECASE,
            )
            for token in tokens:
                clean_tok = token.strip().replace("\\", "/").lstrip("/").lower()
                if clean_tok in manifest_map:
                    candidate_paths.append(manifest_map[clean_tok]["original_path"])
                else:
                    base_matches = [
                        m["original_path"]
                        for k, m in manifest_map.items()
                        if k.endswith("/" + clean_tok) or k == clean_tok
                    ]
                    if base_matches:
                        candidate_paths.extend(base_matches)
                    else:
                        missing_files_requested.append(token)

            # Check if query mentions file stems or component names directly
            for k, m in manifest_map.items():
                stem = k.split("/")[-1].split(".")[0].lower()
                if len(stem) >= 3 and stem in query_lower:
                    candidate_paths.append(m["original_path"])

            # C. Keyword-based relevant anchors
            if any(k in query_lower for k in ["readme", "overview", "setup", "run", "how to"]):
                for k, m in manifest_map.items():
                    if k.endswith("readme.md"):
                        candidate_paths.append(m["original_path"])

            if any(k in query_lower for k in ["dependency", "dependencies", "package", "library", "libraries", "modules"]):
                for k, m in manifest_map.items():
                    if k.endswith("package.json") or k.endswith("requirements.txt"):
                        candidate_paths.append(m["original_path"])

            ui_keywords = [
                "frontend", "ui", "component", "react", "view", "page", "dashboard",
                "button", "card", "form", "input", "header", "footer", "navbar", "nav",
                "title", "theme", "color", "search", "filter", "modal", "dialog", "style",
                "css", "state", "tag", "badge", "table", "list", "item", "dark", "todo",
            ]
            if any(k in query_lower for k in ui_keywords):
                for k, m in manifest_map.items():
                    if any(k.endswith(f) for f in ["app.tsx", "app.jsx", "main.tsx", "main.jsx", "app.css"]):
                        candidate_paths.append(m["original_path"])
                    elif "/components/" in k or "/src/" in k:
                        candidate_paths.append(m["original_path"])

            if "html" in query_lower:
                for k, m in manifest_map.items():
                    if k.endswith("index.html"):
                        candidate_paths.append(m["original_path"])

            be_keywords = ["backend", "api", "route", "endpoints", "fastapi", "server", "crud", "query"]
            if any(k in query_lower for k in be_keywords):
                for k, m in manifest_map.items():
                    if any(k.endswith(f) for f in ["main.py", "api.py", "routes.py", "models.py"]):
                        candidate_paths.append(m["original_path"])

            if any(k in query_lower for k in ["database", "model", "schema", "store", "persistence"]):
                for k, m in manifest_map.items():
                    if any(k.endswith(f) for f in ["models.py", "persistence.py", "schema.sql"]):
                        candidate_paths.append(m["original_path"])

        # Default fallback anchor files if candidate paths empty and files exist
        if not candidate_paths and manifest_map:
            for k, m in manifest_map.items():
                if k.endswith("app.tsx") or k.endswith("main.py") or k.endswith("readme.md"):
                    candidate_paths.append(m["original_path"])
            if not candidate_paths:
                candidate_paths.extend([m["original_path"] for m in list(manifest_map.values())[:3]])

        # Deduplicate preserving order
        unique_paths: list[str] = []
        for p in candidate_paths:
            if p not in unique_paths:
                unique_paths.append(p)

        # Retrieve content with strict bounds: max 4 files, max 6 KB per file, max 16 KB total
        MAX_FILES = 4
        MAX_PER_FILE_BYTES = 6 * 1024
        MAX_TOTAL_BYTES = 16 * 1024
        total_retrieved = 0

        active_ver_id = getattr(active_ver, "id", getattr(active_ver, "version_id", None)) if active_ver else None
        if active_ver_id:
            for path in unique_paths[:MAX_FILES]:
                try:
                    file_res = await self.version_service.get_file_content_by_path(
                        project_id=project_id,
                        file_path=path,
                        version_id=active_ver_id,
                    )
                    content = file_res.content
                    encoded_len = len(content.encode("utf-8"))
                    if encoded_len > MAX_PER_FILE_BYTES:
                        content = content[:MAX_PER_FILE_BYTES] + "\n\n[... Truncated for context limits ...]"
                        encoded_len = len(content.encode("utf-8"))

                    if total_retrieved + encoded_len > MAX_TOTAL_BYTES:
                        break

                    retrieved_files.append({
                        "path": path,
                        "language": file_res.language,
                        "size_bytes": encoded_len,
                        "content": content,
                    })
                    total_retrieved += encoded_len
                except Exception as e:
                    logger.debug(f"Could not retrieve content for {path}: {e}")

        # Extract or format supplied error message
        supplied_error = error_message
        if not supplied_error and user_query:
            if any(err_sig in user_query for err_sig in ["Traceback (most recent call last):", "Error:", "TypeError:", "ValueError:", "SyntaxError:"]):
                supplied_error = user_query

        # Key requirements summary (bounded to 6)
        key_requirements = [
            {"id": str(r.id), "title": r.title, "description": r.description}
            for r in (project_ctx.requirements or [])[:6]
        ] if project_ctx.requirements else []

        # Tech stack metadata
        proj_settings = project_ctx.project.settings if isinstance(getattr(project_ctx.project, "settings", None), dict) else {}
        raw_tech_stack = proj_settings.get("technology_stack") if isinstance(proj_settings, dict) else None
        technology_stack = raw_tech_stack if isinstance(raw_tech_stack, dict) else None

        raw_desc = getattr(project_ctx.project, "description", None)
        project_description_str = raw_desc if isinstance(raw_desc, str) else None

        # 9. Live Preview Runtime Diagnostics
        preview_runtime_status = None
        preview_runtime_mode = None
        preview_runtime_port = None
        preview_active_project_id = None
        preview_diagnostics_summary = None
        try:
            from app.runtime.preview_runtime_manager import preview_runtime_manager
            ok, p_msg, p_data = await preview_runtime_manager.check_health()
            preview_runtime_status = "RUNNING" if ok else "UNAVAILABLE"
            if isinstance(p_data, dict):
                preview_runtime_mode = p_data.get("active_mode")
                preview_runtime_port = p_data.get("port", 8001)
                preview_active_project_id = p_data.get("active_project_id")
            else:
                preview_runtime_port = 8001

            project_match = (str(preview_active_project_id) == str(project_id)) if preview_active_project_id else False
            mode_desc = f"mode='{preview_runtime_mode}'" if preview_runtime_mode else ""
            match_desc = "active project matched" if project_match else f"serving project '{preview_active_project_id}'"
            preview_diagnostics_summary = (
                f"Preview runtime {preview_runtime_status} on port {preview_runtime_port}. "
                f"({mode_desc}; {match_desc})"
            )
        except Exception as e:
            logger.debug(f"Could not probe preview runtime diagnostics for project {project_id}: {e}")

        return AssistantContext(
            project_id=project_id,
            project_name=project_ctx.project.name,
            project_slug=project_ctx.project.slug,
            project_status=project_ctx.project.status,
            active_version_id=str(ver_id) if ver_id else None,
            active_version_number=ver_number,
            active_version_status=ver_status,
            active_version_hash=ver_hash,
            verification_summary=verification_summary,
            total_requirements_count=req_count,
            recent_failure_title=recent_failure_title,
            recent_failure_severity=recent_failure_severity,
            active_remediation_proposal_id=str(active_remediation_proposal_id) if active_remediation_proposal_id else None,
            active_remediation_status=active_remediation_status,
            recent_change_summary=recent_change_summary,
            latest_browser_status=latest_browser_status,
            latest_browser_summary=latest_browser_summary,
            active_executions_summary=active_executions_summary,
            environments_summary=environments_summary,
            polyglot_languages_summary=polyglot_languages_summary,
            project_description=project_description_str,
            technology_stack=technology_stack,
            key_requirements=key_requirements,
            files_manifest_summary=files_manifest_summary,
            retrieved_files=retrieved_files,
            missing_files_requested=missing_files_requested,
            supplied_error_text=supplied_error,
            detected_intent=detected_intent,
            active_persona=active_persona,
            preview_runtime_status=preview_runtime_status,
            preview_runtime_mode=preview_runtime_mode,
            preview_runtime_port=preview_runtime_port,
            preview_active_project_id=str(preview_active_project_id) if preview_active_project_id else None,
            preview_diagnostics_summary=preview_diagnostics_summary,
        )
