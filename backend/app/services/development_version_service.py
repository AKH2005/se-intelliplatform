"""Development Version Service for Phase 11H.

Orchestrates version lifecycle management, immutable version recording,
deterministic comparison, human-controlled activation, and non-destructive rollback.
"""

import difflib
import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.agents.code_generation.contracts import CodeGenerationOutput, GeneratedFile
from app.agents.failure_analysis.contracts import FailureDiagnosis
from app.agents.remediation.contracts import RemediationVerificationResult
from app.agents.test_generation.contracts import AITestExecutionResult, AITestSuite
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.development_version import (
    ChangeCategory,
    ChangeType,
    DevelopmentChange,
    DevelopmentVersion,
    DevelopmentVersionStatus,
)
from app.models.project import Project
from app.models.workflow_execution import WorkflowExecution
from app.sandbox.contracts import ExecutionResult
from app.sandbox.static_analysis.contracts import StaticAnalysisResult
from app.schemas.development_version import (
    DevelopmentChangeResponse,
    DevelopmentVersionListResponse,
    DevelopmentVersionResponse,
    StageVerificationResult,
    VerificationSnapshot,
    VerificationStatus,
    VersionComparisonResponse,
    VersionFileDiff,
    VersionFileSummary,
)
from app.schemas.browser_testing import BrowserTestRun
from app.services.verification_service import DevelopmentVerificationService

logger = logging.getLogger(__name__)


class DevelopmentVersionService:
    """Orchestrates development version creation, verification, activation, and rollback."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.verification_service = DevelopmentVerificationService()

    @staticmethod
    def compute_content_hash(files: list[GeneratedFile] | list[dict[str, Any]]) -> str:
        """Compute deterministic SHA-256 hash across sorted file contents."""
        hasher = hashlib.sha256()
        sorted_files = sorted(
            files,
            key=lambda f: f.path if hasattr(f, "path") else f.get("path", ""),
        )
        for f in sorted_files:
            p = f.path if hasattr(f, "path") else f.get("path", "")
            c = f.content if hasattr(f, "content") else f.get("content", "")
            hasher.update(p.encode("utf-8"))
            hasher.update(b"\0")
            hasher.update(c.encode("utf-8"))
            hasher.update(b"\0")
        return hasher.hexdigest()

    @staticmethod
    def compute_manifest_hash(files: list[GeneratedFile] | list[dict[str, Any]]) -> str:
        """Compute deterministic SHA-256 hash across sorted file paths."""
        sorted_paths = sorted(
            f.path if hasattr(f, "path") else f.get("path", "")
            for f in files
        )
        return hashlib.sha256("\n".join(sorted_paths).encode("utf-8")).hexdigest()

    async def _resolve_project(self, project_id: uuid.UUID) -> Project:
        """Fetch project or raise NotFoundError."""
        stmt = select(Project).where(Project.id == project_id)
        res = await self.session.execute(stmt)
        proj = res.scalar_one_or_none()
        if not proj:
            raise NotFoundError("Project", str(project_id))
        return proj

    async def register_version_from_workflow(
        self,
        project_id: uuid.UUID,
        workflow_execution_id: uuid.UUID,
        artifact_key: str = "code-generation",
        source_reason: str = "INITIAL_GENERATION",
        created_by: str = "system",
        parent_version_id: uuid.UUID | None = None,
        diagnosis_reference: str | None = None,
        remediation_reference: str | None = None,
        verification_snapshot: VerificationSnapshot | None = None,
    ) -> DevelopmentVersion:
        """Register a new immutable DevelopmentVersion from workflow execution artifacts."""
        project = await self._resolve_project(project_id)

        # 1. Fetch WorkflowExecution
        stmt_wf = select(WorkflowExecution).where(
            WorkflowExecution.workflow_execution_id == workflow_execution_id,
            WorkflowExecution.project_id == project_id,
        )
        wf_res = await self.session.execute(stmt_wf)
        wf = wf_res.scalar_one_or_none()
        if not wf:
            raise NotFoundError("WorkflowExecution", str(workflow_execution_id))

        artifacts = wf.artifacts or {}
        code_data = artifacts.get(artifact_key)
        if not code_data:
            # Fallback for key variances
            if artifact_key == "code-generation" and "code_generation" in artifacts:
                code_data = artifacts["code_generation"]
            elif artifact_key == "code_generation" and "code-generation" in artifacts:
                code_data = artifacts["code-generation"]

        if not code_data:
            raise ValidationError(
                f"Artifact '{artifact_key}' not found in WorkflowExecution '{workflow_execution_id}'."
            )

        code_artifact = CodeGenerationOutput.model_validate(code_data)

        # 2. Extract verification inputs from artifacts
        sa_data = artifacts.get("static_analysis")
        static_res = StaticAnalysisResult.model_validate(sa_data) if sa_data else None

        sb_data = artifacts.get("sandbox_execution") or artifacts.get("test_execution")
        sandbox_res = ExecutionResult.model_validate(sb_data) if sb_data else None

        ai_suite_data = artifacts.get("ai_test_suite")
        ai_suite = AITestSuite.model_validate(ai_suite_data) if ai_suite_data else None

        ai_exec_data = artifacts.get("ai_test_execution")
        ai_exec = AITestExecutionResult.model_validate(ai_exec_data) if ai_exec_data else None

        diag_data = artifacts.get("failure_analysis") or artifacts.get("ai_test_failure_analysis")
        failure_diag = FailureDiagnosis.model_validate(diag_data) if diag_data else None

        rem_ver_data = artifacts.get("remediation_verification")
        rem_ver = RemediationVerificationResult.model_validate(rem_ver_data) if rem_ver_data else None
        if rem_ver:
            if rem_ver.static_analysis_result:
                static_res = rem_ver.static_analysis_result
            if rem_ver.execution_result:
                sandbox_res = rem_ver.execution_result

        browser_run_data = artifacts.get("browser_test_run") or artifacts.get("browser_validation")
        browser_run = BrowserTestRun.model_validate(browser_run_data) if browser_run_data else None
        browser_required = bool(
            artifacts.get("browser_testing_required")
            or (artifacts.get("metadata") or {}).get("browser_testing_required")
            or browser_run is not None
        )

        # 3. Deterministic Verification Gate
        if verification_snapshot is None:
            verification_snapshot = self.verification_service.evaluate_verification(
                artifact=code_artifact,
                static_analysis=static_res,
                sandbox_execution=sandbox_res,
                ai_test_suite=ai_suite,
                ai_test_execution=ai_exec,
                failure_diagnosis=failure_diag,
                remediation_verification=rem_ver,
                browser_test_run=browser_run,
                browser_testing_required=browser_required,
            )

        initial_status = (
            DevelopmentVersionStatus.VERIFIED
            if verification_snapshot.is_verified
            else DevelopmentVersionStatus.FAILED_VERIFICATION
        )

        # 4. Monotonic Version Number Calculation
        stmt_max = select(DevelopmentVersion.version_number).where(
            DevelopmentVersion.project_id == project_id
        ).order_by(DevelopmentVersion.version_number.desc())
        max_res = await self.session.execute(stmt_max)
        latest_num = max_res.scalars().first() or 0
        new_version_num = latest_num + 1

        # 5. Extract requirement IDs and lightweight manifest
        req_ids = list(dict.fromkeys(
            r_id
            for f in code_artifact.generated_files
            for r_id in f.requirement_ids
        ))

        files_manifest = [
            VersionFileSummary(
                path=f.path,
                size_bytes=f.size_bytes,
                language=f.language,
                architecture_component=f.architecture_component,
                requirement_ids=f.requirement_ids,
            ).model_dump(mode="json")
            for f in code_artifact.generated_files
        ]

        content_hash = self.compute_content_hash(code_artifact.generated_files)
        manifest_hash = self.compute_manifest_hash(code_artifact.generated_files)

        # 6. Create DevelopmentVersion Record
        version_id = uuid.uuid4()
        dev_version = DevelopmentVersion(
            id=version_id,
            project_id=project_id,
            version_number=new_version_num,
            parent_version_id=parent_version_id,
            workflow_execution_id=workflow_execution_id,
            artifact_key=artifact_key,
            status=initial_status,
            content_hash=content_hash,
            manifest_hash=manifest_hash,
            file_count=code_artifact.total_files,
            total_size_bytes=code_artifact.total_size_bytes,
            source_reason=source_reason,
            created_by=created_by,
            requirement_ids=req_ids,
            files_manifest=files_manifest,
            verification_summary=verification_snapshot.model_dump(mode="json"),
            diagnosis_reference=diagnosis_reference,
            remediation_reference=remediation_reference,
            metadata_payload={
                "summary": code_artifact.summary,
                **({"runtime_manifest": artifacts.get("runtime_manifest")} if artifacts.get("runtime_manifest") else {}),
            },
        )
        self.session.add(dev_version)

        # 7. Record Code-Producing Change Audit
        is_remediation = source_reason == "REMEDIATION_PATCH"
        change_type = ChangeType.REMEDIATION_PATCH if is_remediation else ChangeType.INITIAL_CREATION
        change = DevelopmentChange(
            id=uuid.uuid4(),
            project_id=project_id,
            parent_version_id=parent_version_id,
            resulting_version_id=version_id,
            change_category=ChangeCategory.CODE_PRODUCING,
            change_type=change_type,
            reason=f"Synthesized version {new_version_num} via {source_reason}.",
            diagnosis_id=diagnosis_reference,
            remediation_proposal_id=remediation_reference,
            approved_by=created_by if is_remediation else None,
            approved_at=datetime.now(timezone.utc) if is_remediation else None,
            metadata_payload={"file_count": code_artifact.total_files, "status": initial_status.value},
        )
        self.session.add(change)

        # 8. Set initial active pointer if no active version exists
        proj_settings = dict(project.settings or {})
        if not proj_settings.get("active_version_id"):
            proj_settings["active_version_id"] = str(version_id)
            project.settings = proj_settings
            flag_modified(project, "settings")


        await self.session.commit()
        await self.session.refresh(dev_version)

        logger.info(
            f"Created DevelopmentVersion [v={new_version_num}, id={version_id}, "
            f"status={initial_status.value}] for project [{project_id}]."
        )
        return dev_version

    async def _bootstrap_versions_if_empty(self, project_id: uuid.UUID) -> None:
        """Auto-discover and register development versions from existing workflow executions if none exist."""
        stmt_check = select(DevelopmentVersion.id).where(DevelopmentVersion.project_id == project_id).limit(1)
        res_check = await self.session.execute(stmt_check)
        if res_check.scalar_one_or_none():
            return

        stmt_wf = (
            select(WorkflowExecution)
            .where(WorkflowExecution.project_id == project_id)
            .order_by(WorkflowExecution.started_at.asc())
        )
        wf_res = await self.session.execute(stmt_wf)
        wf_list = list(wf_res.scalars().all())

        for wf in wf_list:
            artifacts = wf.artifacts or {}
            if "code_generation_v1" in artifacts:
                try:
                    v1 = await self.register_version_from_workflow(
                        project_id=project_id,
                        workflow_execution_id=wf.workflow_execution_id,
                        artifact_key="code_generation_v1",
                        source_reason="INITIAL_GENERATION",
                    )
                    prop_data = artifacts.get("remediation_proposal", {})
                    diag_id = prop_data.get("diagnosis_id")
                    prop_id = prop_data.get("proposal_id")
                    key = "code-generation" if "code-generation" in artifacts else "code_generation"
                    await self.register_version_from_workflow(
                        project_id=project_id,
                        workflow_execution_id=wf.workflow_execution_id,
                        artifact_key=key,
                        source_reason="REMEDIATION_PATCH",
                        parent_version_id=v1.id,
                        diagnosis_reference=str(diag_id) if diag_id else None,
                        remediation_reference=str(prop_id) if prop_id else None,
                    )
                except Exception as e:
                    logger.warning(f"Failed to bootstrap remediated versions: {e}")
                break
            elif "code-generation" in artifacts or "code_generation" in artifacts:
                key = "code-generation" if "code-generation" in artifacts else "code_generation"
                try:
                    await self.register_version_from_workflow(
                        project_id=project_id,
                        workflow_execution_id=wf.workflow_execution_id,
                        artifact_key=key,
                        source_reason="INITIAL_GENERATION",
                    )
                except Exception as e:
                    logger.warning(f"Failed to bootstrap initial version: {e}")
                break

    async def list_versions(self, project_id: uuid.UUID) -> DevelopmentVersionListResponse:
        """List all versions for a project with active pointer marked."""
        project = await self._resolve_project(project_id)
        await self._bootstrap_versions_if_empty(project_id)

        active_id_str = (project.settings or {}).get("active_version_id")
        active_uuid = uuid.UUID(active_id_str) if active_id_str else None

        stmt = (
            select(DevelopmentVersion)
            .where(DevelopmentVersion.project_id == project_id)
            .order_by(DevelopmentVersion.version_number.asc())
        )
        res = await self.session.execute(stmt)
        versions = list(res.scalars().all())

        items = [
            self._map_version_response(v, active_version_id=active_uuid)
            for v in versions
        ]
        return DevelopmentVersionListResponse(
            items=items,
            total=len(items),
            active_version_id=active_uuid,
        )


    async def get_version(
        self,
        project_id: uuid.UUID,
        version_id: uuid.UUID,
    ) -> DevelopmentVersionResponse:
        """Get version detail by UUID validating project isolation."""
        project = await self._resolve_project(project_id)
        await self._bootstrap_versions_if_empty(project_id)
        active_id_str = (project.settings or {}).get("active_version_id")
        active_uuid = uuid.UUID(active_id_str) if active_id_str else None

        stmt = select(DevelopmentVersion).where(
            DevelopmentVersion.id == version_id,
            DevelopmentVersion.project_id == project_id,
        )
        res = await self.session.execute(stmt)
        version = res.scalar_one_or_none()
        if not version:
            raise NotFoundError("DevelopmentVersion", str(version_id))

        return self._map_version_response(version, active_version_id=active_uuid)

    async def resolve_runtime_manifest(
        self,
        project_id: uuid.UUID,
        version_id: uuid.UUID,
    ) -> Any | None:
        """Resolve authoritative ApplicationRuntimeManifest for a DevelopmentVersion."""
        from app.schemas.runtime import ApplicationRuntimeManifest

        stmt = select(DevelopmentVersion).where(
            DevelopmentVersion.id == version_id,
            DevelopmentVersion.project_id == project_id,
        )
        res = await self.session.execute(stmt)
        version = res.scalar_one_or_none()
        if not version:
            raise NotFoundError("DevelopmentVersion", str(version_id))

        raw_manifest = (version.metadata_payload or {}).get("runtime_manifest")
        if not raw_manifest and version.workflow_execution_id:
            stmt_wf = select(WorkflowExecution).where(
                WorkflowExecution.workflow_execution_id == version.workflow_execution_id,
                WorkflowExecution.project_id == project_id,
            )
            wf_res = await self.session.execute(stmt_wf)
            wf = wf_res.scalar_one_or_none()
            if wf and wf.artifacts:
                raw_manifest = wf.artifacts.get("runtime_manifest")

        if raw_manifest:
            try:
                return ApplicationRuntimeManifest.model_validate(raw_manifest)
            except Exception as e:
                raise ValidationError(f"Invalid runtime manifest for version '{version_id}': {e}")
        return None

    async def get_active_version(self, project_id: uuid.UUID) -> DevelopmentVersionResponse | None:
        """Get current project active version or None if not set."""
        project = await self._resolve_project(project_id)
        await self._bootstrap_versions_if_empty(project_id)
        active_id_str = (project.settings or {}).get("active_version_id")
        if not active_id_str:
            stmt_fallback = (
                select(DevelopmentVersion)
                .where(DevelopmentVersion.project_id == project_id)
                .order_by(DevelopmentVersion.version_number.desc())
                .limit(1)
            )
            res_fb = await self.session.execute(stmt_fallback)
            fallback_v = res_fb.scalar_one_or_none()
            if fallback_v:
                return self._map_version_response(fallback_v, active_version_id=fallback_v.id)
            return None

        try:
            active_uuid = uuid.UUID(active_id_str)
        except ValueError:
            active_uuid = None

        if active_uuid:
            stmt = select(DevelopmentVersion).where(
                DevelopmentVersion.id == active_uuid,
                DevelopmentVersion.project_id == project_id,
            )
            res = await self.session.execute(stmt)
            version = res.scalar_one_or_none()
            if version:
                return self._map_version_response(version, active_version_id=active_uuid)

        # Fallback to latest available version
        stmt_fallback = (
            select(DevelopmentVersion)
            .where(DevelopmentVersion.project_id == project_id)
            .order_by(DevelopmentVersion.version_number.desc())
            .limit(1)
        )
        res_fb = await self.session.execute(stmt_fallback)
        fallback_v = res_fb.scalar_one_or_none()
        if fallback_v:
            return self._map_version_response(fallback_v, active_version_id=fallback_v.id)
        return None



    async def activate_version(
        self,
        project_id: uuid.UUID,
        version_id: uuid.UUID,
        reason: str | None = None,
        activated_by: str = "user",
    ) -> DevelopmentVersionResponse:
        """Explicitly designate a verified software version as active.
        
        Requires VERIFIED status.
        Transitions previously active version to SUPERSEDED.
        """
        project = await self._resolve_project(project_id)
        stmt = select(DevelopmentVersion).where(
            DevelopmentVersion.id == version_id,
            DevelopmentVersion.project_id == project_id,
        )
        res = await self.session.execute(stmt)
        target_version = res.scalar_one_or_none()
        if not target_version:
            raise NotFoundError("DevelopmentVersion", str(version_id))

        if target_version.status not in (DevelopmentVersionStatus.VERIFIED, DevelopmentVersionStatus.SUPERSEDED):
            raise ConflictError(
                f"Only a VERIFIED version can be activated. Current status is '{target_version.status.value}'.",
                field="status",
                value=target_version.status.value,
            )

        proj_settings = dict(project.settings or {})
        prev_active_id_str = proj_settings.get("active_version_id")
        prev_active_id = uuid.UUID(prev_active_id_str) if prev_active_id_str else None

        if prev_active_id == version_id:
            # Idempotent re-activation
            return self._map_version_response(target_version, active_version_id=version_id)

        # Transition previous active version to SUPERSEDED
        if prev_active_id:
            stmt_prev = select(DevelopmentVersion).where(
                DevelopmentVersion.id == prev_active_id,
                DevelopmentVersion.project_id == project_id,
            )
            prev_res = await self.session.execute(stmt_prev)
            prev_ver = prev_res.scalar_one_or_none()
            if prev_ver:
                prev_ver.status = DevelopmentVersionStatus.SUPERSEDED

        # Update Project Active Pointer
        proj_settings["active_version_id"] = str(version_id)
        project.settings = proj_settings
        flag_modified(project, "settings")

        # Record Lifecycle Change Event
        change = DevelopmentChange(
            id=uuid.uuid4(),
            project_id=project_id,
            parent_version_id=prev_active_id,
            resulting_version_id=version_id,
            change_category=ChangeCategory.LIFECYCLE_EVENT,
            change_type=ChangeType.ACTIVATION,
            reason=reason or f"Explicit activation of version {target_version.version_number} by {activated_by}.",
            approved_by=activated_by,
            approved_at=datetime.now(timezone.utc),
            metadata_payload={"activated_version_number": target_version.version_number},
        )
        self.session.add(change)

        await self.session.commit()
        await self.session.refresh(target_version)

        logger.info(
            f"Activated DevelopmentVersion [v={target_version.version_number}, "
            f"id={version_id}] for project [{project_id}]."
        )
        return self._map_version_response(target_version, active_version_id=version_id)

    async def rollback_version(
        self,
        project_id: uuid.UUID,
        target_version_id: uuid.UUID,
        reason: str | None = None,
        rolled_back_by: str = "user",
    ) -> DevelopmentVersionResponse:
        """Non-destructively revert active pointer to a historical verified version."""
        project = await self._resolve_project(project_id)
        stmt = select(DevelopmentVersion).where(
            DevelopmentVersion.id == target_version_id,
            DevelopmentVersion.project_id == project_id,
        )
        res = await self.session.execute(stmt)
        target_ver = res.scalar_one_or_none()
        if not target_ver:
            raise NotFoundError("DevelopmentVersion", str(target_version_id))

        if target_ver.status not in (DevelopmentVersionStatus.VERIFIED, DevelopmentVersionStatus.SUPERSEDED):
            raise ConflictError(
                f"Cannot roll back to unverified version. Target version status is '{target_ver.status.value}'.",
                field="status",
                value=target_ver.status.value,
            )

        proj_settings = dict(project.settings or {})
        current_active_id_str = proj_settings.get("active_version_id")
        current_active_id = uuid.UUID(current_active_id_str) if current_active_id_str else None

        if current_active_id == target_version_id:
            # Idempotent rollback
            return self._map_version_response(target_ver, active_version_id=target_version_id)

        # Mark current active version as SUPERSEDED
        if current_active_id:
            stmt_curr = select(DevelopmentVersion).where(
                DevelopmentVersion.id == current_active_id,
                DevelopmentVersion.project_id == project_id,
            )
            curr_res = await self.session.execute(stmt_curr)
            curr_ver = curr_res.scalar_one_or_none()
            if curr_ver:
                curr_ver.status = DevelopmentVersionStatus.SUPERSEDED

        # Update Project Active Pointer
        proj_settings["active_version_id"] = str(target_version_id)
        project.settings = proj_settings
        flag_modified(project, "settings")

        # Record Lifecycle Change Event
        change = DevelopmentChange(
            id=uuid.uuid4(),
            project_id=project_id,
            parent_version_id=current_active_id,
            resulting_version_id=target_version_id,
            change_category=ChangeCategory.LIFECYCLE_EVENT,
            change_type=ChangeType.ROLLBACK,
            reason=reason or f"Non-destructive rollback to version {target_ver.version_number} by {rolled_back_by}.",
            approved_by=rolled_back_by,
            approved_at=datetime.now(timezone.utc),
            metadata_payload={
                "prior_active_id": str(current_active_id) if current_active_id else None,
                "reverted_to_version_number": target_ver.version_number,
            },
        )
        self.session.add(change)

        await self.session.commit()
        await self.session.refresh(target_ver)

        logger.info(
            f"Rolled back active pointer to DevelopmentVersion [v={target_ver.version_number}, "
            f"id={target_version_id}] for project [{project_id}]."
        )
        return self._map_version_response(target_ver, active_version_id=target_version_id)

    async def list_changes(
        self,
        project_id: uuid.UUID,
        version_id: uuid.UUID | None = None,
    ) -> list[DevelopmentChangeResponse]:
        """Retrieve chronological change log for project or specific version."""
        await self._resolve_project(project_id)
        stmt = select(DevelopmentChange).where(DevelopmentChange.project_id == project_id)
        if version_id:
            stmt = stmt.where(
                (DevelopmentChange.resulting_version_id == version_id)
                | (DevelopmentChange.parent_version_id == version_id)
            )
        stmt = stmt.order_by(DevelopmentChange.created_at.desc())
        res = await self.session.execute(stmt)
        changes = list(res.scalars().all())

        return [
            DevelopmentChangeResponse(
                change_id=c.id,
                project_id=c.project_id,
                parent_version_id=c.parent_version_id,
                resulting_version_id=c.resulting_version_id,
                change_category=c.change_category,
                change_type=c.change_type,
                reason=c.reason,
                diagnosis_id=c.diagnosis_id,
                remediation_proposal_id=c.remediation_proposal_id,
                approved_by=c.approved_by,
                approved_at=c.approved_at,
                created_at=c.created_at,
            )
            for c in changes
        ]

    async def _resolve_version_files_map(self, version: DevelopmentVersion) -> dict[str, str]:
        """Resolve full project files map {path: content} from underlying workflow execution."""
        manifest_files = {}
        for item in (version.files_manifest or []):
            if isinstance(item, dict) and "path" in item and "content" in item:
                manifest_files[item["path"]] = item["content"]
        if manifest_files:
            return manifest_files

        if not version.workflow_execution_id:
            return {}

        stmt = select(WorkflowExecution).where(
            WorkflowExecution.workflow_execution_id == version.workflow_execution_id
        )
        res = await self.session.execute(stmt)
        wf = res.scalar_one_or_none()
        if not wf or not wf.artifacts:
            return {}

        code_data = wf.artifacts.get(version.artifact_key)
        if not code_data:
            if version.artifact_key == "code-generation" and "code_generation" in wf.artifacts:
                code_data = wf.artifacts["code_generation"]
            elif version.artifact_key == "code_generation" and "code-generation" in wf.artifacts:
                code_data = wf.artifacts["code-generation"]

        if not code_data:
            return {}

        artifact = CodeGenerationOutput.model_validate(code_data)
        return {f.path: f.content for f in artifact.generated_files}

    async def get_version_file_content(
        self,
        project_id: uuid.UUID,
        version_id: uuid.UUID,
        file_path: str,
    ) -> str:
        """Fetch content of a single file in a version."""
        stmt = select(DevelopmentVersion).where(
            DevelopmentVersion.id == version_id,
            DevelopmentVersion.project_id == project_id,
        )
        res = await self.session.execute(stmt)
        version = res.scalar_one_or_none()
        if not version:
            raise NotFoundError("DevelopmentVersion", str(version_id))

        files_map = await self._resolve_version_files_map(version)
        clean_path = file_path.replace("\\", "/").strip()
        if clean_path not in files_map:
            raise NotFoundError("File", file_path)

        return files_map[clean_path]

    async def compare_versions(
        self,
        project_id: uuid.UUID,
        from_version_id: uuid.UUID,
        to_version_id: uuid.UUID,
    ) -> VersionComparisonResponse:
        """Deterministically compare two development versions using difflib."""
        await self._resolve_project(project_id)

        # 1. Fetch versions
        stmt_from = select(DevelopmentVersion).where(
            DevelopmentVersion.id == from_version_id,
            DevelopmentVersion.project_id == project_id,
        )
        res_from = await self.session.execute(stmt_from)
        ver_from = res_from.scalar_one_or_none()
        if not ver_from:
            raise NotFoundError("DevelopmentVersion", str(from_version_id))

        stmt_to = select(DevelopmentVersion).where(
            DevelopmentVersion.id == to_version_id,
            DevelopmentVersion.project_id == project_id,
        )
        res_to = await self.session.execute(stmt_to)
        ver_to = res_to.scalar_one_or_none()
        if not ver_to:
            raise NotFoundError("DevelopmentVersion", str(to_version_id))

        # 2. Resolve file maps
        from_files = await self._resolve_version_files_map(ver_from)
        to_files = await self._resolve_version_files_map(ver_to)

        from_paths = set(from_files.keys())
        to_paths = set(to_files.keys())

        added_paths = sorted(to_paths - from_paths)
        removed_paths = sorted(from_paths - to_paths)
        common_paths = sorted(from_paths & to_paths)

        files_added: list[VersionFileDiff] = []
        for p in added_paths:
            content = to_files[p]
            size = len(content.encode("utf-8"))
            files_added.append(
                VersionFileDiff(
                    path=p,
                    change_type="ADDED",
                    size_delta_bytes=size,
                    unified_diff=None,
                )
            )

        files_removed: list[VersionFileDiff] = []
        for p in removed_paths:
            content = from_files[p]
            size = len(content.encode("utf-8"))
            files_removed.append(
                VersionFileDiff(
                    path=p,
                    change_type="REMOVED",
                    size_delta_bytes=-size,
                    unified_diff=None,
                )
            )

        files_modified: list[VersionFileDiff] = []
        unchanged_count = 0

        for p in common_paths:
            content_from = from_files[p]
            content_to = to_files[p]
            if content_from == content_to:
                unchanged_count += 1
                continue

            size_from = len(content_from.encode("utf-8"))
            size_to = len(content_to.encode("utf-8"))
            delta = size_to - size_from

            diff_lines = list(
                difflib.unified_diff(
                    content_from.splitlines(keepends=True),
                    content_to.splitlines(keepends=True),
                    fromfile=f"a/{p}",
                    tofile=f"b/{p}",
                )
            )
            diff_text = "".join(diff_lines)

            files_modified.append(
                VersionFileDiff(
                    path=p,
                    change_type="MODIFIED",
                    size_delta_bytes=delta,
                    unified_diff=diff_text,
                )
            )

        # Requirement deltas
        from_reqs = set(ver_from.requirement_ids)
        to_reqs = set(ver_to.requirement_ids)
        reqs_added = sorted(to_reqs - from_reqs)
        reqs_removed = sorted(from_reqs - to_reqs)

        summary = (
            f"Compared v{ver_from.version_number} -> v{ver_to.version_number}: "
            f"{len(files_added)} added, {len(files_modified)} modified, "
            f"{len(files_removed)} removed, {unchanged_count} unchanged."
        )

        return VersionComparisonResponse(
            from_version_id=from_version_id,
            to_version_id=to_version_id,
            from_version_number=ver_from.version_number,
            to_version_number=ver_to.version_number,
            files_added=files_added,
            files_removed=files_removed,
            files_modified=files_modified,
            files_unchanged_count=unchanged_count,
            requirements_added=reqs_added,
            requirements_removed=reqs_removed,
            verification_change_summary=summary,
            diagnosis_reference=ver_to.diagnosis_reference,
            remediation_proposal_id=ver_to.remediation_reference,
        )

    async def reevaluate_verification(
        self,
        project_id: uuid.UUID,
        version_id: uuid.UUID,
    ) -> VerificationSnapshot:
        """Re-evaluate deterministic verification gate for an existing version.
        
        Does NOT modify code files or mutate historical artifact contents.
        """
        await self._resolve_project(project_id)
        stmt = select(DevelopmentVersion).where(
            DevelopmentVersion.id == version_id,
            DevelopmentVersion.project_id == project_id,
        )
        res = await self.session.execute(stmt)
        version = res.scalar_one_or_none()
        if not version:
            raise NotFoundError("DevelopmentVersion", str(version_id))

        if not version.workflow_execution_id:
            raise ValidationError("Version has no linked WorkflowExecution.")

        stmt_wf = select(WorkflowExecution).where(
            WorkflowExecution.workflow_execution_id == version.workflow_execution_id
        )
        wf_res = await self.session.execute(stmt_wf)
        wf = wf_res.scalar_one_or_none()
        if not wf:
            raise NotFoundError("WorkflowExecution", str(version.workflow_execution_id))

        artifacts = wf.artifacts or {}
        code_data = artifacts.get(version.artifact_key)
        code_artifact = CodeGenerationOutput.model_validate(code_data) if code_data else None

        sa_data = artifacts.get("static_analysis")
        static_res = StaticAnalysisResult.model_validate(sa_data) if sa_data else None

        sb_data = artifacts.get("sandbox_execution") or artifacts.get("test_execution")
        sandbox_res = ExecutionResult.model_validate(sb_data) if sb_data else None

        ai_suite_data = artifacts.get("ai_test_suite")
        ai_suite = AITestSuite.model_validate(ai_suite_data) if ai_suite_data else None

        ai_exec_data = artifacts.get("ai_test_execution")
        ai_exec = AITestExecutionResult.model_validate(ai_exec_data) if ai_exec_data else None

        diag_data = artifacts.get("failure_analysis") or artifacts.get("ai_test_failure_analysis")
        failure_diag = FailureDiagnosis.model_validate(diag_data) if diag_data else None

        rem_ver_data = artifacts.get("remediation_verification")
        rem_ver = RemediationVerificationResult.model_validate(rem_ver_data) if rem_ver_data else None
        if rem_ver:
            if rem_ver.static_analysis_result:
                static_res = rem_ver.static_analysis_result
            if rem_ver.execution_result:
                sandbox_res = rem_ver.execution_result

        browser_run_data = artifacts.get("browser_test_run") or artifacts.get("browser_validation")
        browser_run = BrowserTestRun.model_validate(browser_run_data) if browser_run_data else None
        browser_required = bool(
            artifacts.get("browser_testing_required")
            or (version.metadata_payload or {}).get("browser_testing_required")
            or browser_run is not None
        )

        snapshot = self.verification_service.evaluate_verification(
            artifact=code_artifact,
            static_analysis=static_res,
            sandbox_execution=sandbox_res,
            ai_test_suite=ai_suite,
            ai_test_execution=ai_exec,
            failure_diagnosis=failure_diag,
            remediation_verification=rem_ver,
            browser_test_run=browser_run,
            browser_testing_required=browser_required,
        )

        version.verification_summary = snapshot.model_dump(mode="json")
        if snapshot.is_verified and version.status == DevelopmentVersionStatus.FAILED_VERIFICATION:
            version.status = DevelopmentVersionStatus.VERIFIED
        elif not snapshot.is_verified and version.status == DevelopmentVersionStatus.VERIFIED:
            version.status = DevelopmentVersionStatus.FAILED_VERIFICATION

        flag_modified(version, "verification_summary")
        await self.session.commit()
        await self.session.refresh(version)

        logger.info(
            f"Re-evaluated verification for version [v={version.version_number}, "
            f"id={version_id}]: status={version.status.value}"
        )
        return snapshot

    def _map_version_response(
        self,
        version: DevelopmentVersion,
        active_version_id: uuid.UUID | None = None,
    ) -> DevelopmentVersionResponse:
        """Map ORM entity to response DTO."""
        is_active = (active_version_id is not None) and (version.id == active_version_id)
        ver_summary = (
            VerificationSnapshot.model_validate(version.verification_summary)
            if version.verification_summary
            else None
        )
        files = [
            VersionFileSummary.model_validate(f)
            for f in version.files_manifest
        ]
        return DevelopmentVersionResponse(
            version_id=version.id,
            project_id=version.project_id,
            version_number=version.version_number,
            parent_version_id=version.parent_version_id,
            workflow_execution_id=version.workflow_execution_id,
            artifact_key=version.artifact_key,
            status=version.status,
            is_active=is_active,
            content_hash=version.content_hash,
            manifest_hash=version.manifest_hash,
            file_count=version.file_count,
            total_size_bytes=version.total_size_bytes,
            source_reason=version.source_reason,
            created_by=version.created_by,
            requirement_ids=version.requirement_ids,
            files_manifest=files,
            verification_summary=ver_summary,
            diagnosis_reference=version.diagnosis_reference,
            remediation_reference=version.remediation_reference,
            created_at=version.created_at,
        )
