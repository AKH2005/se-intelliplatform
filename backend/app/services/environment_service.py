"""Authoritative Multi-Environment Development & Deployment Service for Phase 13.

Orchestrates:
- Project-scoped environment lifecycle (DEVELOPMENT, STAGING, PRODUCTION)
- Deterministic promotion policy and eligibility evaluation
- Deployment lifecycle management with target abstraction
- Non-destructive rollback per environment
- Authoritative append-only deployment audit trail
- Real-time telemetry emissions via Phase 12 ExecutionEventPublisher
"""

from datetime import datetime, timezone
import logging
from typing import Any
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.development_version import DevelopmentVersion, DevelopmentVersionStatus
from app.models.environment import (
    DeploymentOperation,
    DeploymentRecord,
    DeploymentStatus,
    Environment,
    EnvironmentStatus,
    EnvironmentType,
)
from app.models.project import Project
from app.schemas.environment import (
    DeploymentRecordResponse,
    EnvironmentResponse,
    PromotionEligibilityResponse,
)
from app.services.deployment_target import (
    AbstractDeploymentTarget,
    DeploymentExecutionResult,
    IsolatedRuntimeDeploymentAdapter,
)
from app.telemetry.contracts import EventSeverity, ExecutionEventType, ExecutionKind
from app.telemetry.publisher import ExecutionEventPublisher

logger = logging.getLogger(__name__)


class EnvironmentService:
    """Authoritative service managing environments, promotions, deployments, and rollbacks."""

    def __init__(
        self,
        session: AsyncSession,
        deployment_target: AbstractDeploymentTarget | None = None,
    ) -> None:
        self.session = session
        self.deployment_target = deployment_target or IsolatedRuntimeDeploymentAdapter()

    async def get_or_create_project_environments(self, project_id: uuid.UUID) -> list[Environment]:
        """Ensure standard DEVELOPMENT, STAGING, and PRODUCTION environments exist for project."""
        stmt = (
            select(Environment)
            .where(Environment.project_id == project_id)
            .order_by(Environment.created_at.asc())
        )
        result = await self.session.execute(stmt)
        existing = list(result.scalars().all())

        existing_types = {e.environment_type for e in existing}
        needed = [
            (EnvironmentType.DEVELOPMENT, "Development", False),
            (EnvironmentType.STAGING, "Staging", False),
            (EnvironmentType.PRODUCTION, "Production", True),
        ]

        created_any = False
        project = None

        for env_type, name, is_prod in needed:
            if env_type not in existing_types:
                if project is None:
                    p_stmt = select(Project).where(Project.id == project_id)
                    p_res = await self.session.execute(p_stmt)
                    project = p_res.scalar_one_or_none()
                    if not project:
                        raise NotFoundError(f"Project '{project_id}' not found.")

                active_v_id = None
                if env_type == EnvironmentType.DEVELOPMENT and project.settings:
                    raw_v_id = project.settings.get("active_version_id")
                    if raw_v_id:
                        try:
                            active_v_id = uuid.UUID(str(raw_v_id))
                        except Exception:
                            active_v_id = None

                env = Environment(
                    project_id=project_id,
                    environment_type=env_type,
                    name=name,
                    status=EnvironmentStatus.HEALTHY,
                    current_version_id=active_v_id,
                    is_production=is_prod,
                    configuration={
                        "auto_deploy": env_type == EnvironmentType.DEVELOPMENT,
                        "health_check_endpoint": "/health",
                    },
                )
                self.session.add(env)
                existing.append(env)
                created_any = True

        if created_any:
            await self.session.commit()
            for e in existing:
                await self.session.refresh(e)

        # Sort order: DEV -> STAGING -> PROD
        type_order = {
            EnvironmentType.DEVELOPMENT: 1,
            EnvironmentType.STAGING: 2,
            EnvironmentType.PRODUCTION: 3,
        }
        existing.sort(key=lambda x: type_order.get(x.environment_type, 99))
        return existing

    async def get_environment(
        self,
        project_id: uuid.UUID,
        env_id_or_type: str | uuid.UUID,
    ) -> Environment:
        """Retrieve an environment by UUID or EnvironmentType string."""
        await self.get_or_create_project_environments(project_id)

        if isinstance(env_id_or_type, EnvironmentType):
            stmt = select(Environment).where(
                Environment.project_id == project_id,
                Environment.environment_type == env_id_or_type,
            )
        elif isinstance(env_id_or_type, uuid.UUID):
            stmt = select(Environment).where(
                Environment.project_id == project_id,
                Environment.id == env_id_or_type,
            )
        else:
            clean_str = str(env_id_or_type).strip()
            env_type_match = None
            for et in EnvironmentType:
                if clean_str.upper() in (et.value, f"ENVIRONMENTTYPE.{et.value}"):
                    env_type_match = et
                    break

            if env_type_match:
                stmt = select(Environment).where(
                    Environment.project_id == project_id,
                    Environment.environment_type == env_type_match,
                )
            else:
                try:
                    env_uuid = uuid.UUID(clean_str)
                    stmt = select(Environment).where(
                        Environment.project_id == project_id,
                        Environment.id == env_uuid,
                    )
                except ValueError:
                    raise ValidationError(f"Invalid environment identifier '{env_id_or_type}'.")

        res = await self.session.execute(stmt)
        env = res.scalar_one_or_none()
        if not env:
            raise NotFoundError("Environment", env_id_or_type)
        return env

    async def list_deployments(
        self,
        project_id: uuid.UUID,
        environment_id: uuid.UUID | None = None,
        limit: int = 50,
    ) -> list[DeploymentRecord]:
        """Retrieve ordered append-only deployment history for a project or specific environment."""
        stmt = select(DeploymentRecord).where(DeploymentRecord.project_id == project_id)
        if environment_id:
            stmt = stmt.where(DeploymentRecord.environment_id == environment_id)
        stmt = stmt.order_by(DeploymentRecord.created_at.desc()).limit(limit)

        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_deployment(
        self,
        project_id: uuid.UUID,
        deployment_id: uuid.UUID,
    ) -> DeploymentRecord:
        """Retrieve single deployment record with project isolation."""
        stmt = select(DeploymentRecord).where(
            DeploymentRecord.id == deployment_id,
            DeploymentRecord.project_id == project_id,
        )
        res = await self.session.execute(stmt)
        record = res.scalar_one_or_none()
        if not record:
            raise NotFoundError("DeploymentRecord", deployment_id)
        return record

    async def check_promotion_eligibility(
        self,
        project_id: uuid.UUID,
        version_id: uuid.UUID,
        target_env_type: EnvironmentType | None = None,
        source_env_type: EnvironmentType | None = None,
        *,
        target_environment: EnvironmentType | None = None,
        source_environment: EnvironmentType | None = None,
    ) -> PromotionEligibilityResponse:
        """Deterministic policy evaluation for promoting a version to an environment."""
        resolved_target = target_env_type or target_environment
        resolved_source = source_env_type or source_environment
        if isinstance(resolved_target, str):
            resolved_target = EnvironmentType(resolved_target)
        if isinstance(resolved_source, str):
            resolved_source = EnvironmentType(resolved_source)
        if not resolved_target:
            raise ValidationError("Target environment must be specified.")

        # 1. Resolve candidate version
        v_stmt = select(DevelopmentVersion).where(
            DevelopmentVersion.id == version_id,
            DevelopmentVersion.project_id == project_id,
        )
        v_res = await self.session.execute(v_stmt)
        version = v_res.scalar_one_or_none()

        if not version:
            return PromotionEligibilityResponse(
                eligible=False,
                version_id=version_id,
                version_number=0,
                source_environment=resolved_source or EnvironmentType.DEVELOPMENT,
                target_environment=resolved_target,
                reasons=[f"Version '{version_id}' does not exist or does not belong to project '{project_id}'."],
                failed_checks=["version_exists"],
                requires_confirmation=True,
            )

        # 2. Determine default source environment if omitted
        if not resolved_source:
            if resolved_target == EnvironmentType.PRODUCTION:
                resolved_source = EnvironmentType.STAGING
            else:
                resolved_source = EnvironmentType.DEVELOPMENT

        # 3. Target environment must be STAGING or PRODUCTION
        if resolved_target == EnvironmentType.DEVELOPMENT:
            return PromotionEligibilityResponse(
                eligible=False,
                version_id=version_id,
                version_number=version.version_number,
                source_environment=resolved_source,
                target_environment=resolved_target,
                reasons=["Cannot promote to DEVELOPMENT; DEVELOPMENT is the source authoring environment."],
                failed_checks=["valid_promotion_target"],
                requires_confirmation=True,
            )

        # 3b. Progressive promotion path check: cannot promote DEV directly to PROD
        if resolved_source == EnvironmentType.DEVELOPMENT and resolved_target == EnvironmentType.PRODUCTION:
            return PromotionEligibilityResponse(
                eligible=False,
                version_id=version_id,
                version_number=version.version_number,
                source_environment=resolved_source,
                target_environment=resolved_target,
                reasons=["Direct promotion from DEVELOPMENT to PRODUCTION is disallowed. Candidate must be promoted to STAGING first."],
                failed_checks=["progressive_promotion_path"],
                requires_confirmation=True,
            )

        passed_checks: list[str] = [
            "Candidate version exists and belongs to project",
            "Target environment is valid promotion destination",
        ]
        failed_checks: list[str] = []
        warnings: list[str] = []
        reasons: list[str] = []

        # 4. Check target environment operational state
        target_env = await self.get_environment(project_id, resolved_target)
        if target_env.status == EnvironmentStatus.DEPLOYING:
            failed_checks.append("Target environment is ready")
            reasons.append(f"Target environment '{resolved_target.value}' is currently in DEPLOYING state.")
        else:
            passed_checks.append("Target environment is ready")

        # 5. Version verification status gate
        if version.status != DevelopmentVersionStatus.VERIFIED:
            failed_checks.append("Candidate version must be in VERIFIED status")
            reasons.append(f"Verification status is {version.status.value}. Candidate version must be in VERIFIED status.")
        else:
            passed_checks.append("Verification status is VERIFIED")

        # 6. Inspection of verification summary
        v_summary = version.verification_summary or {}
        stages = v_summary.get("stages", {})

        # Static analysis check
        static_st = stages.get("STATIC_ANALYSIS", {})
        if static_st.get("status") in ("PASSED", "SUCCESS"):
            passed_checks.append("static_analysis_passed")
        else:
            if "STATIC_ANALYSIS" in stages:
                failed_checks.append("static_analysis_passed")
                reasons.append("Static analysis stage did not pass.")
            else:
                warnings.append("Static analysis stage verification record not present.")

        # AI tests / unit tests check
        code_st = stages.get("AI_TESTS", {}) or stages.get("CODE_EXECUTION", {})
        if code_st.get("status") in ("PASSED", "SUCCESS"):
            passed_checks.append("tests_passed")
        else:
            if code_st:
                failed_checks.append("tests_passed")
                reasons.append("Automated test stage did not pass.")
            else:
                warnings.append("Automated test execution record not present.")

        # 7. Strict Staging prerequisite for Production promotion
        if resolved_target == EnvironmentType.PRODUCTION:
            staging_env = await self.get_environment(project_id, EnvironmentType.STAGING)
            is_active_in_staging = staging_env.current_version_id == version.id

            # Check if version has succeeded in staging deployment history
            hist_stmt = select(DeploymentRecord).where(
                DeploymentRecord.project_id == project_id,
                DeploymentRecord.environment_id == staging_env.id,
                DeploymentRecord.version_id == version.id,
                DeploymentRecord.status == DeploymentStatus.SUCCEEDED,
            )
            hist_res = await self.session.execute(hist_stmt)
            has_staging_history = hist_res.scalar_one_or_none() is not None

            if is_active_in_staging or has_staging_history:
                passed_checks.append("Version previously deployed to STAGING")
            else:
                failed_checks.append("Version has not been verified in STAGING")
                reasons.append(
                    f"Version v{version.version_number} has not been verified in the STAGING environment before promoting to PRODUCTION."
                )

            # Check browser test verification for web/runtime projects
            browser_st = stages.get("BROWSER_TESTS", {})
            if browser_st:
                if browser_st.get("status") in ("PASSED", "SUCCESS"):
                    passed_checks.append("browser_verification_passed")
                else:
                    failed_checks.append("browser_verification_passed")
                    reasons.append("Browser verification stage failed.")

        is_eligible = len(failed_checks) == 0
        if is_eligible:
            reasons.append(
                f"Version v{version.version_number} satisfies all promotion policy gates for {resolved_target.value}."
            )

        return PromotionEligibilityResponse(
            eligible=is_eligible,
            version_id=version.id,
            version_number=version.version_number,
            source_environment=resolved_source,
            target_environment=resolved_target,
            reasons=reasons,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warnings=warnings,
            requires_confirmation=True,
        )

    async def promote_version(
        self,
        project_id: uuid.UUID,
        version_id: uuid.UUID,
        target_env_type: EnvironmentType,
        source_env_type: EnvironmentType | None = None,
        requested_by: str = "user",
        notes: str | None = None,
    ) -> DeploymentRecord:
        """Promote a verified version from source environment to target environment."""
        eligibility = await self.check_promotion_eligibility(
            project_id=project_id,
            version_id=version_id,
            target_env_type=target_env_type,
            source_env_type=source_env_type,
        )

        if not eligibility.eligible:
            raise ConflictError(
                f"Version '{version_id}' is not eligible for promotion to {target_env_type.value}: "
                f"{'; '.join(eligibility.reasons)}"
            )

        source_env = await self.get_environment(project_id, eligibility.source_environment)
        target_env = await self.get_environment(project_id, target_env_type)

        v_stmt = select(DevelopmentVersion).where(DevelopmentVersion.id == version_id)
        v_res = await self.session.execute(v_stmt)
        version = v_res.scalar_one()

        deployment_id = uuid.uuid4()
        prev_v_id = target_env.current_version_id

        # Record requested deployment
        record = DeploymentRecord(
            id=deployment_id,
            project_id=project_id,
            environment_id=target_env.id,
            version_id=version.id,
            previous_version_id=prev_v_id,
            operation=DeploymentOperation.PROMOTION,
            source_environment_id=source_env.id,
            status=DeploymentStatus.REQUESTED,
            requested_by=requested_by,
            started_at=datetime.now(timezone.utc),
            verification_summary={
                "eligibility_reasons": eligibility.reasons,
                "passed_checks": eligibility.passed_checks,
                "warnings": eligibility.warnings,
            },
            metadata_payload={
                "notes": notes,
                "source_env_type": source_env.environment_type.value,
                "target_env_type": target_env.environment_type.value,
                "version_number": version.version_number,
                "content_hash": version.content_hash,
            },
        )
        self.session.add(record)
        target_env.status = EnvironmentStatus.DEPLOYING
        await self.session.commit()
        await self.session.refresh(record)

        # Emit PROMOTION_STARTED telemetry
        await ExecutionEventPublisher.emit(
            event_type=ExecutionEventType.PROMOTION_STARTED,
            project_id=project_id,
            execution_id=deployment_id,
            execution_kind=ExecutionKind.DEPLOYMENT,
            source="EnvironmentService.promote_version",
            status="STARTED",
            payload={
                "version_id": str(version.id),
                "version_number": version.version_number,
                "target_environment": target_env.environment_type.value,
                "source_environment": source_env.environment_type.value,
            },
        )

        # Execute deployment via target adapter
        val_ok, val_err = await self.deployment_target.validate_target(target_env, version)
        if not val_ok:
            record.status = DeploymentStatus.FAILED
            record.failure_reason = val_err
            record.completed_at = datetime.now(timezone.utc)
            target_env.status = EnvironmentStatus.DEGRADED
            # Note: target_env.current_version_id remains prev_v_id!
            await self.session.commit()

            await ExecutionEventPublisher.emit(
                event_type=ExecutionEventType.PROMOTION_FAILED,
                project_id=project_id,
                execution_id=deployment_id,
                execution_kind=ExecutionKind.DEPLOYMENT,
                source="EnvironmentService.promote_version",
                status="FAILED",
                payload={"error": val_err},
                severity=EventSeverity.ERROR,
            )
            raise ConflictError(f"Target validation failed: {val_err}")

        record.status = DeploymentStatus.DEPLOYING
        await self.session.commit()

        exec_res: DeploymentExecutionResult = await self.deployment_target.execute_deployment(
            environment=target_env,
            version=version,
            deployment_id=deployment_id,
        )

        if exec_res.success:
            record.status = DeploymentStatus.SUCCEEDED
            record.completed_at = datetime.now(timezone.utc)
            target_env.current_version_id = version.id
            target_env.status = EnvironmentStatus.HEALTHY
            target_env.last_deployed_at = datetime.now(timezone.utc)
            await self.session.commit()

            await ExecutionEventPublisher.emit(
                event_type=ExecutionEventType.PROMOTION_COMPLETED,
                project_id=project_id,
                execution_id=deployment_id,
                execution_kind=ExecutionKind.DEPLOYMENT,
                source="EnvironmentService.promote_version",
                status="COMPLETED",
                payload={
                    "version_id": str(version.id),
                    "version_number": version.version_number,
                    "target_environment": target_env.environment_type.value,
                },
            )
            return await self.get_deployment(project_id, deployment_id)
        else:
            record.status = DeploymentStatus.FAILED
            record.failure_reason = exec_res.error_message or "Execution failed."
            record.completed_at = datetime.now(timezone.utc)
            target_env.status = EnvironmentStatus.DEGRADED
            # Safe guarantee: target_env.current_version_id is NOT overwritten!
            await self.session.commit()

            await ExecutionEventPublisher.emit(
                event_type=ExecutionEventType.PROMOTION_FAILED,
                project_id=project_id,
                execution_id=deployment_id,
                execution_kind=ExecutionKind.DEPLOYMENT,
                source="EnvironmentService.promote_version",
                status="FAILED",
                payload={"error": record.failure_reason},
                severity=EventSeverity.ERROR,
            )
            raise RuntimeError(f"Promotion failed: {record.failure_reason}")

    async def deploy_version(
        self,
        project_id: uuid.UUID,
        env_id_or_type: str | uuid.UUID | None = None,
        version_id: uuid.UUID | None = None,
        requested_by: str = "user",
        notes: str | None = None,
        *,
        environment_id_or_type: str | uuid.UUID | None = None,
    ) -> DeploymentRecord:
        """Directly deploy a verified version to an environment."""
        resolved_env_id = env_id_or_type or environment_id_or_type
        if not resolved_env_id:
            raise ValidationError("Environment identifier must be provided.")
        if not version_id:
            raise ValidationError("Version UUID must be provided.")

        target_env = await self.get_environment(project_id, resolved_env_id)

        v_stmt = select(DevelopmentVersion).where(
            DevelopmentVersion.id == version_id,
            DevelopmentVersion.project_id == project_id,
        )
        v_res = await self.session.execute(v_stmt)
        version = v_res.scalar_one_or_none()
        if not version:
            raise NotFoundError("DevelopmentVersion", version_id)

        if version.status in (DevelopmentVersionStatus.REJECTED, DevelopmentVersionStatus.FAILED_VERIFICATION):
            raise ConflictError(f"Cannot deploy version with status '{version.status.value}'.")

        deployment_id = uuid.uuid4()
        prev_v_id = target_env.current_version_id

        record = DeploymentRecord(
            id=deployment_id,
            project_id=project_id,
            environment_id=target_env.id,
            version_id=version.id,
            previous_version_id=prev_v_id,
            operation=DeploymentOperation.DEPLOYMENT,
            status=DeploymentStatus.REQUESTED,
            requested_by=requested_by,
            started_at=datetime.now(timezone.utc),
            metadata_payload={
                "notes": notes,
                "environment_type": target_env.environment_type.value,
                "version_number": version.version_number,
            },
        )
        self.session.add(record)
        target_env.status = EnvironmentStatus.DEPLOYING
        await self.session.commit()
        await self.session.refresh(record)

        await ExecutionEventPublisher.emit(
            event_type=ExecutionEventType.DEPLOYMENT_STARTED,
            project_id=project_id,
            execution_id=deployment_id,
            execution_kind=ExecutionKind.DEPLOYMENT,
            source="EnvironmentService.deploy_version",
            status="STARTED",
            payload={
                "version_id": str(version.id),
                "version_number": version.version_number,
                "environment": target_env.environment_type.value,
            },
        )

        exec_res = await self.deployment_target.execute_deployment(target_env, version, deployment_id)

        if exec_res.success:
            record.status = DeploymentStatus.SUCCEEDED
            record.completed_at = datetime.now(timezone.utc)
            target_env.current_version_id = version.id
            target_env.status = EnvironmentStatus.HEALTHY
            target_env.last_deployed_at = datetime.now(timezone.utc)

            # Backward compatibility synchronization:
            if target_env.environment_type == EnvironmentType.DEVELOPMENT:
                p_stmt = select(Project).where(Project.id == project_id)
                p_res = await self.session.execute(p_stmt)
                proj = p_res.scalar_one_or_none()
                if proj:
                    if not proj.settings:
                        proj.settings = {}
                    proj.settings["active_version_id"] = str(version.id)
                    flag_modified(proj, "settings")

            await self.session.commit()

            await ExecutionEventPublisher.emit(
                event_type=ExecutionEventType.DEPLOYMENT_COMPLETED,
                project_id=project_id,
                execution_id=deployment_id,
                execution_kind=ExecutionKind.DEPLOYMENT,
                source="EnvironmentService.deploy_version",
                status="COMPLETED",
                payload={"environment": target_env.environment_type.value},
            )
            return await self.get_deployment(project_id, deployment_id)
        else:
            record.status = DeploymentStatus.FAILED
            record.failure_reason = exec_res.error_message or "Deployment failed."
            record.completed_at = datetime.now(timezone.utc)
            target_env.status = EnvironmentStatus.DEGRADED
            await self.session.commit()

            await ExecutionEventPublisher.emit(
                event_type=ExecutionEventType.DEPLOYMENT_FAILED,
                project_id=project_id,
                execution_id=deployment_id,
                execution_kind=ExecutionKind.DEPLOYMENT,
                source="EnvironmentService.deploy_version",
                status="FAILED",
                payload={"error": record.failure_reason},
                severity=EventSeverity.ERROR,
            )
            raise RuntimeError(f"Deployment failed: {record.failure_reason}")

    async def rollback_environment(
        self,
        project_id: uuid.UUID,
        env_id_or_type: str | uuid.UUID | None = None,
        target_version_id: uuid.UUID | None = None,
        requested_by: str = "user",
        reason: str = "Manual rollback",
        *,
        environment_id_or_type: str | uuid.UUID | None = None,
    ) -> DeploymentRecord:
        """Roll back an environment to an earlier verified version non-destructively."""
        resolved_env_id = env_id_or_type or environment_id_or_type
        if not resolved_env_id:
            raise ValidationError("Environment identifier must be provided.")
        if not target_version_id:
            raise ValidationError("Target version UUID must be provided.")

        target_env = await self.get_environment(project_id, resolved_env_id)

        v_stmt = select(DevelopmentVersion).where(
            DevelopmentVersion.id == target_version_id,
            DevelopmentVersion.project_id == project_id,
        )
        v_res = await self.session.execute(v_stmt)
        target_version = v_res.scalar_one_or_none()
        if not target_version:
            raise NotFoundError("DevelopmentVersion", target_version_id)

        if target_version.status == DevelopmentVersionStatus.REJECTED:
            raise ConflictError("Cannot roll back to a REJECTED version.")

        current_v_id = target_env.current_version_id
        if current_v_id == target_version.id:
            raise ConflictError(f"Environment is already running version v{target_version.version_number}.")

        deployment_id = uuid.uuid4()

        record = DeploymentRecord(
            id=deployment_id,
            project_id=project_id,
            environment_id=target_env.id,
            version_id=target_version.id,
            previous_version_id=current_v_id,
            operation=DeploymentOperation.ROLLBACK,
            status=DeploymentStatus.REQUESTED,
            requested_by=requested_by,
            started_at=datetime.now(timezone.utc),
            metadata_payload={
                "rollback_reason": reason,
                "environment_type": target_env.environment_type.value,
                "from_version_id": str(current_v_id) if current_v_id else None,
                "to_version_id": str(target_version.id),
                "to_version_number": target_version.version_number,
            },
        )
        self.session.add(record)
        target_env.status = EnvironmentStatus.DEPLOYING
        await self.session.commit()
        await self.session.refresh(record)

        await ExecutionEventPublisher.emit(
            event_type=ExecutionEventType.ROLLBACK_STARTED,
            project_id=project_id,
            execution_id=deployment_id,
            execution_kind=ExecutionKind.DEPLOYMENT,
            source="EnvironmentService.rollback_environment",
            status="STARTED",
            payload={
                "environment": target_env.environment_type.value,
                "to_version": target_version.version_number,
                "reason": reason,
            },
        )

        exec_res = await self.deployment_target.execute_deployment(target_env, target_version, deployment_id)

        if exec_res.success:
            record.status = DeploymentStatus.SUCCEEDED
            record.completed_at = datetime.now(timezone.utc)
            target_env.current_version_id = target_version.id
            target_env.status = EnvironmentStatus.HEALTHY
            target_env.last_deployed_at = datetime.now(timezone.utc)

            if target_env.environment_type == EnvironmentType.DEVELOPMENT:
                p_stmt = select(Project).where(Project.id == project_id)
                p_res = await self.session.execute(p_stmt)
                proj = p_res.scalar_one_or_none()
                if proj:
                    if not proj.settings:
                        proj.settings = {}
                    proj.settings["active_version_id"] = str(target_version.id)
                    flag_modified(proj, "settings")

            await self.session.commit()

            await ExecutionEventPublisher.emit(
                event_type=ExecutionEventType.ROLLBACK_COMPLETED,
                project_id=project_id,
                execution_id=deployment_id,
                execution_kind=ExecutionKind.DEPLOYMENT,
                source="EnvironmentService.rollback_environment",
                status="COMPLETED",
                payload={
                    "environment": target_env.environment_type.value,
                    "restored_version": target_version.version_number,
                },
            )
            return await self.get_deployment(project_id, deployment_id)
        else:
            record.status = DeploymentStatus.FAILED
            record.failure_reason = exec_res.error_message or "Rollback execution failed."
            record.completed_at = datetime.now(timezone.utc)
            target_env.status = EnvironmentStatus.DEGRADED
            await self.session.commit()

            await ExecutionEventPublisher.emit(
                event_type=ExecutionEventType.ROLLBACK_FAILED,
                project_id=project_id,
                execution_id=deployment_id,
                execution_kind=ExecutionKind.DEPLOYMENT,
                source="EnvironmentService.rollback_environment",
                status="FAILED",
                payload={"error": record.failure_reason},
                severity=EventSeverity.ERROR,
            )
            raise RuntimeError(f"Rollback failed: {record.failure_reason}")
