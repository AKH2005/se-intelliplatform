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

    async def build_context(self, project_id: uuid.UUID) -> AssistantContext:
        """Deterministically gather bounded context elements for the Assistant prompt."""
        # 1. Base project metadata
        project_ctx = await self.context_engine.generate_context(project_id)
        req_count = len(project_ctx.requirements) if project_ctx.requirements else 0

        # 2. Active software release version
        active_ver = await self.version_service.get_active_version(project_id)
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

        return AssistantContext(
            project_id=project_id,
            project_name=project_ctx.project.name,
            project_slug=project_ctx.project.slug,
            project_status=project_ctx.project.status,
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
        )
