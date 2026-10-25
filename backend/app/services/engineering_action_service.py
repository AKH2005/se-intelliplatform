"""Engineering Action Service for Phase 11I Intelli Assistant.

Provides authoritative action dispatching, target authorization, anti-replay
confirmation token gating, and execution delegation to existing domain services.
Does NOT duplicate domain logic. Does NOT expose arbitrary shell/Docker execution.
"""

import copy
import hashlib
import json
import logging
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.assistant import (
    ActionConfirmationToken,
    AssistantActionAudit,
    AssistantMessage,
)
from app.models.development_version import DevelopmentVersion
from app.models.requirement import Requirement
from app.models.workflow_execution import WorkflowExecution, WorkflowStatus
from app.sandbox.contracts import ExecutionRequest, ExecutionType, ResourceLimits
from app.sandbox.static_analysis.contracts import StaticAnalysisRequest
from app.schemas.assistant import (
    ActionCategory,
    ActionConfirmationTokenPayload,
    ActionResult,
    ActionStatus,
)
from app.schemas.workflow import WorkflowExecuteRequest
from app.services.action_registry import (
    get_action_definition,
    is_confirmation_required,
    validate_action_parameters,
)
from app.services.context_engine import ProjectContextEngine
from app.services.development_version_service import DevelopmentVersionService
from app.services.requirement_service import RequirementService
from app.services.verification_service import DevelopmentVerificationService
from app.services.workflow_service import WorkflowService
from app.telemetry.contracts import EventSeverity, ExecutionEventType, ExecutionKind
from app.telemetry.publisher import ExecutionEventPublisher

logger = logging.getLogger(__name__)


class EngineeringActionService:
    """Authoritative execution boundary and confirmation gate for platform engineering actions."""

    def __init__(
        self,
        session: AsyncSession,
        version_service: DevelopmentVersionService,
        verification_service: DevelopmentVerificationService,
        requirement_service: RequirementService,
        context_engine: ProjectContextEngine,
        workflow_service: WorkflowService,
        remediation_service: Any | None = None,
        static_analysis_service: Any | None = None,
        ai_test_service: Any | None = None,
        failure_analysis_service: Any | None = None,
        sandbox_service: Any | None = None,
        browser_testing_service: Any | None = None,
        browser_journey_service: Any | None = None,
        inventory_service: Any | None = None,
        impact_service: Any | None = None,
        regression_planner: Any | None = None,
        regression_executor: Any | None = None,
        environment_service: Any | None = None,
    ) -> None:
        self.session = session
        self.version_service = version_service
        self.verification_service = verification_service
        self.requirement_service = requirement_service
        self.context_engine = context_engine
        self.workflow_service = workflow_service
        self.remediation_service = remediation_service
        self.static_analysis_service = static_analysis_service
        self.ai_test_service = ai_test_service
        self.failure_analysis_service = failure_analysis_service
        self.sandbox_service = sandbox_service
        self.browser_testing_service = browser_testing_service
        self.browser_journey_service = browser_journey_service
        self.inventory_service = inventory_service
        self.impact_service = impact_service
        self.regression_planner = regression_planner
        self.regression_executor = regression_executor
        self.environment_service = environment_service

    def _get_environment_service(self) -> Any:
        if self.environment_service:
            return self.environment_service
        from app.services.environment_service import EnvironmentService
        return EnvironmentService(self.session)

    def _get_inventory_service(self) -> Any:
        if self.inventory_service:
            return self.inventory_service
        from app.testing.inventory.service import UnifiedTestInventoryService
        return UnifiedTestInventoryService()

    def _get_impact_service(self) -> Any:
        if self.impact_service:
            return self.impact_service
        from app.testing.impact.service import ChangeImpactService
        return ChangeImpactService()

    def _get_regression_planner(self) -> Any:
        if self.regression_planner:
            return self.regression_planner
        from app.testing.regression.planner import SelectiveRegressionPlanner
        return SelectiveRegressionPlanner()

    async def _resolve_test_inputs(
        self,
        project_id: uuid.UUID,
        version_id: uuid.UUID | None = None,
        explicit_files_map: dict[str, str] | None = None,
    ) -> tuple[dict[str, str], Any, Any, Any, Any]:
        """Resolve files_map and auxiliary test suites for testing actions."""
        files_map: dict[str, str] = dict(explicit_files_map or {})
        ai_test_suite = None
        smoke_tests = None
        journey_suite = None
        resolved_version = None

        if version_id:
            resolved_version = await self.version_service.get_version(project_id, version_id)
        else:
            resolved_version = await self.version_service.get_active_version(project_id)

        if resolved_version:
            if not files_map:
                stmt_v = select(DevelopmentVersion).where(
                    DevelopmentVersion.id == resolved_version.version_id,
                    DevelopmentVersion.project_id == project_id,
                )
                v_res = await self.session.execute(stmt_v)
                v_entity = v_res.scalar_one_or_none()
                if v_entity:
                    files_map = await self.version_service._resolve_version_files_map(v_entity)

            if resolved_version.workflow_execution_id:
                stmt_wf = select(WorkflowExecution).where(
                    WorkflowExecution.workflow_execution_id == resolved_version.workflow_execution_id,
                    WorkflowExecution.project_id == project_id,
                )
                wf_res = await self.session.execute(stmt_wf)
                wf = wf_res.scalar_one_or_none()
                if wf and wf.artifacts:
                    if "ai_test_suite" in wf.artifacts:
                        from app.agents.test_generation.contracts import AITestSuite
                        try:
                            ai_test_suite = AITestSuite.model_validate(wf.artifacts["ai_test_suite"])
                        except Exception:
                            pass
                    if "browser_test_definitions" in wf.artifacts:
                        from app.browser.contracts import DeterministicBrowserTestDefinition
                        try:
                            smoke_tests = [
                                DeterministicBrowserTestDefinition.model_validate(item)
                                for item in wf.artifacts["browser_test_definitions"]
                            ]
                        except Exception:
                            pass
                    if "validated_journey_suite" in wf.artifacts:
                        from app.browser.journey.contracts import ValidatedBrowserJourneySuite
                        try:
                            journey_suite = ValidatedBrowserJourneySuite.model_validate(
                                wf.artifacts["validated_journey_suite"]
                            )
                        except Exception:
                            pass

        if journey_suite is None:
            stmt_j = (
                select(WorkflowExecution)
                .where(
                    WorkflowExecution.project_id == project_id,
                    WorkflowExecution.workflow_id == "browser-journey-workflow",
                    WorkflowExecution.status == WorkflowStatus.COMPLETED,
                )
                .order_by(WorkflowExecution.started_at.desc())
            )
            j_res = await self.session.execute(stmt_j)
            latest_j_wf = j_res.scalars().first()
            if latest_j_wf and latest_j_wf.artifacts and "validated_journey_suite" in latest_j_wf.artifacts:
                from app.browser.journey.contracts import ValidatedBrowserJourneySuite
                try:
                    journey_suite = ValidatedBrowserJourneySuite.model_validate(
                        latest_j_wf.artifacts["validated_journey_suite"]
                    )
                except Exception:
                    pass

        return files_map, ai_test_suite, smoke_tests, journey_suite, resolved_version

    @staticmethod
    def compute_parameters_hash(parameters: dict[str, Any]) -> str:
        """Compute deterministic SHA-256 hash of parameters."""
        canonical_str = json.dumps(parameters or {}, sort_keys=True, default=str)
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    async def _authorize_target(
        self,
        project_id: uuid.UUID,
        action_id: str,
        target_id: str | None,
        parameters: dict[str, Any],
    ) -> None:
        """Verify that any referenced entity belongs strictly to the project.
        
        Cross-project access raises NotFoundError (resulting in HTTP 404).
        """
        # 1. Version target
        ver_id_str = (
            parameters.get("version_id")
            or parameters.get("from_version_id")
            or parameters.get("target_version_id")
            or parameters.get("base_version_id")
        )
        if not ver_id_str and target_id and action_id in {
            "GET_VERSION", "GET_VERSION_FILE_CONTENT", "GET_VERSION_VERIFICATION",
            "GET_VERSION_CHANGES", "VERIFY_VERSION", "ACTIVATE_VERSION", "ROLLBACK_VERSION",
            "RUN_BROWSER_TESTS", "GET_BROWSER_TEST_RESULTS",
            "GET_TEST_INVENTORY", "GET_COVERAGE_REPORT", "ANALYZE_COVERAGE_GAPS",
            "ANALYZE_REGRESSION_IMPACT", "PLAN_REGRESSION", "EXECUTE_REGRESSION",
        }:
            ver_id_str = target_id

        if ver_id_str:
            try:
                ver_uuid = uuid.UUID(str(ver_id_str))
            except (ValueError, TypeError):
                raise ValidationError(f"Invalid UUID for version: {ver_id_str}")

            stmt = select(DevelopmentVersion.id).where(
                DevelopmentVersion.id == ver_uuid,
                DevelopmentVersion.project_id == project_id,
            )
            res = await self.session.execute(stmt)
            if not res.scalar_one_or_none():
                raise NotFoundError("DevelopmentVersion", str(ver_uuid))

        # Check secondary versions if present (to_version_id, base_version_id, target_version_id)
        for key in ("to_version_id", "base_version_id", "target_version_id"):
            val_str = parameters.get(key)
            if val_str:
                try:
                    sec_uuid = uuid.UUID(str(val_str))
                except (ValueError, TypeError):
                    raise ValidationError(f"Invalid UUID for version: {val_str}")
                stmt = select(DevelopmentVersion.id).where(
                    DevelopmentVersion.id == sec_uuid,
                    DevelopmentVersion.project_id == project_id,
                )
                res = await self.session.execute(stmt)
                if not res.scalar_one_or_none():
                    raise NotFoundError("DevelopmentVersion", str(sec_uuid))


        # 2. Requirement target
        req_id_str = parameters.get("requirement_id") or (target_id if action_id == "GET_REQUIREMENT" else None)
        if req_id_str:
            try:
                req_uuid = uuid.UUID(str(req_id_str))
                stmt = select(Requirement.id).where(
                    Requirement.id == req_uuid,
                    Requirement.project_id == project_id,
                )
                res = await self.session.execute(stmt)
                if not res.scalar_one_or_none():
                    raise NotFoundError("Requirement", str(req_id_str))
            except (ValueError, TypeError):
                # If requirement ID is a string slug/key rather than UUID
                stmt = select(Requirement.id).where(
                    Requirement.project_id == project_id,
                )
                res = await self.session.execute(stmt)
                if not res.scalars().first():
                    raise NotFoundError("Requirement", str(req_id_str))

        # 3. Remediation proposal target
        prop_id_str = parameters.get("proposal_id") or (target_id if action_id in {
            "GET_REMEDIATION_PROPOSAL", "APPROVE_REMEDIATION", "REJECT_REMEDIATION", "APPLY_REMEDIATION"
        } else None)
        if prop_id_str and self.remediation_service:
            try:
                prop_uuid = uuid.UUID(str(prop_id_str))
                await self.remediation_service.get_proposal(project_id, prop_uuid)
            except Exception as e:
                if isinstance(e, NotFoundError):
                    raise
                raise NotFoundError("RemediationProposal", str(prop_id_str))

        # 4. Workflow Execution target
        wf_exec_str = parameters.get("workflow_execution_id") or (target_id if action_id == "ANALYZE_FAILURE" else None)
        if wf_exec_str:
            try:
                wf_uuid = uuid.UUID(str(wf_exec_str))
                stmt = select(WorkflowExecution.workflow_execution_id).where(
                    WorkflowExecution.workflow_execution_id == wf_uuid,
                    WorkflowExecution.project_id == project_id,
                )
                res = await self.session.execute(stmt)
                if not res.scalar_one_or_none():
                    raise NotFoundError("WorkflowExecution", str(wf_uuid))
            except (ValueError, TypeError):
                raise ValidationError(f"Invalid UUID for workflow execution: {wf_exec_str}")

    async def execute_action(
        self,
        project_id: uuid.UUID,
        action_id: str,
        parameters: dict[str, Any] | None = None,
        target_id: str | None = None,
        user_id: str = "assistant_user",
        conversation_id: uuid.UUID | None = None,
        message_id: uuid.UUID | None = None,
        bypass_confirmation_gate: bool = False,
    ) -> ActionResult:
        """Validate, authorize, and dispatch an engineering action or issue confirmation token."""
        start_time = time.monotonic()
        normalized_action_id = action_id.strip().upper()
        definition = get_action_definition(normalized_action_id)

        clean_params = parameters.copy() if parameters else {}
        # Normalize target_id into parameters if expected
        if target_id and not any(k in clean_params for k in ("version_id", "proposal_id", "requirement_id", "workflow_execution_id", "suite_id")):
            if definition.supported_targets:
                primary_target = definition.supported_targets[0]
                if primary_target == "version":
                    clean_params["version_id"] = target_id
                elif primary_target == "proposal":
                    clean_params["proposal_id"] = target_id
                elif primary_target == "requirement":
                    clean_params["requirement_id"] = target_id

        # 1. Parameter Schema Validation
        try:
            validated_model = validate_action_parameters(normalized_action_id, clean_params)
            clean_params = validated_model.model_dump(mode="json")
        except Exception as e:
            return ActionResult(
                action_id=normalized_action_id,
                status=ActionStatus.INVALID_PARAMETERS,
                summary=f"Parameter validation failed for action '{normalized_action_id}'.",
                errors=[str(e)],
            )

        # 2. Target Authorization (Never trust LLM target_id)
        try:
            await self._authorize_target(project_id, normalized_action_id, target_id, clean_params)
        except NotFoundError:
            raise
        except Exception as e:
            return ActionResult(
                action_id=normalized_action_id,
                status=ActionStatus.UNAUTHORIZED_TARGET,
                summary=f"Target authorization failed: {e}",
                errors=[str(e)],
            )

        # 3. Confirmation Gate (MUTATING actions require explicit confirmation)
        if definition.requires_confirmation and not bypass_confirmation_gate:
            if not conversation_id:
                # Require or create conversation context for token binding
                raise ValidationError("A valid conversation_id is required to issue confirmation tokens.")

            params_hash = self.compute_parameters_hash(clean_params)
            token_str = secrets.token_urlsafe(32)
            token_id = uuid.uuid4()
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

            token_record = ActionConfirmationToken(
                token_id=token_id,
                token_hash=token_str,
                project_id=project_id,
                conversation_id=conversation_id,
                action_id=normalized_action_id,
                target_id=str(target_id) if target_id else None,
                parameters_hash=params_hash,
                parameters_payload=clean_params,
                issued_to_user_id=user_id,
                expires_at=expires_at,
                consumed_at=None,
            )
            self.session.add(token_record)

            # Record audit entry in PENDING_CONFIRMATION status
            audit = AssistantActionAudit(
                message_id=message_id,
                project_id=project_id,
                action_id=normalized_action_id,
                category=definition.category.value,
                parameters=clean_params,
                result_status=ActionStatus.PENDING_CONFIRMATION.value,
                confirmed_by=None,
                confirmed_at=None,
                execution_duration_ms=int((time.monotonic() - start_time) * 1000),
                metadata_payload={"token_id": str(token_id), "expires_at": expires_at.isoformat()},
            )
            self.session.add(audit)
            await self.session.commit()

            prompt_msg = (
                f"Action '{normalized_action_id}' requires explicit confirmation. "
                f"Description: {definition.description}"
            )
            return ActionResult(
                action_id=normalized_action_id,
                status=ActionStatus.PENDING_CONFIRMATION,
                summary=prompt_msg,
                requires_confirmation=True,
                confirmation_token=token_str,
                confirmation_prompt=prompt_msg,
                data={
                    "token_id": str(token_id),
                    "action_id": normalized_action_id,
                    "target_id": target_id,
                    "parameters": clean_params,
                    "expires_at": expires_at.isoformat(),
                },
                audit_reference=str(audit.id),
            )

        # 4. Dispatch to Domain Services
        action_execution_id = uuid.uuid4()
        await ExecutionEventPublisher.emit(
            event_type=ExecutionEventType.EXECUTION_STARTED,
            project_id=str(project_id),
            execution_id=str(action_execution_id),
            execution_kind=ExecutionKind.ASSISTANT_ACTION,
            source="EngineeringActionService",
            status="RUNNING",
            payload={
                "action_id": normalized_action_id,
                "category": definition.category.value,
                "target_id": str(target_id) if target_id else None,
                "phase": f"Executing action {normalized_action_id}",
            },
        )

        try:
            result_data, summary = await self._dispatch_action(
                project_id=project_id,
                action_id=normalized_action_id,
                parameters=clean_params,
                target_id=target_id,
                user_id=user_id,
            )
            duration_ms = int((time.monotonic() - start_time) * 1000)

            await ExecutionEventPublisher.emit(
                event_type=ExecutionEventType.EXECUTION_COMPLETED,
                project_id=str(project_id),
                execution_id=str(action_execution_id),
                execution_kind=ExecutionKind.ASSISTANT_ACTION,
                source="EngineeringActionService",
                status="SUCCESS",
                severity=EventSeverity.INFO,
                payload={
                    "action_id": normalized_action_id,
                    "duration_seconds": round(duration_ms / 1000.0, 3),
                    "summary": summary,
                    "phase": f"Action {normalized_action_id} completed",
                    "progress_pct": 100.0,
                },
            )

            # Record Audit
            audit = AssistantActionAudit(
                message_id=message_id,
                project_id=project_id,
                action_id=normalized_action_id,
                category=definition.category.value,
                parameters=clean_params,
                result_status=ActionStatus.SUCCESS.value,
                confirmed_by=user_id if definition.requires_confirmation else None,
                confirmed_at=datetime.now(timezone.utc) if definition.requires_confirmation else None,
                execution_duration_ms=duration_ms,
                metadata_payload={"summary": summary},
            )
            self.session.add(audit)
            await self.session.commit()

            return ActionResult(
                action_id=normalized_action_id,
                status=ActionStatus.SUCCESS,
                summary=summary,
                data=result_data,
                requires_confirmation=False,
                audit_reference=str(audit.id),
            )

        except Exception as e:
            logger.error(f"Action '{normalized_action_id}' execution failed: {e}", exc_info=True)
            duration_ms = int((time.monotonic() - start_time) * 1000)

            await ExecutionEventPublisher.emit(
                event_type=ExecutionEventType.EXECUTION_FAILED,
                project_id=str(project_id),
                execution_id=str(action_execution_id),
                execution_kind=ExecutionKind.ASSISTANT_ACTION,
                source="EngineeringActionService",
                status="FAILED",
                severity=EventSeverity.ERROR,
                payload={
                    "action_id": normalized_action_id,
                    "duration_seconds": round(duration_ms / 1000.0, 3),
                    "error": str(e),
                    "phase": f"Action {normalized_action_id} failed",
                },
            )

            audit = AssistantActionAudit(
                message_id=message_id,
                project_id=project_id,
                action_id=normalized_action_id,
                category=definition.category.value,
                parameters=clean_params,
                result_status=ActionStatus.FAILED.value,
                confirmed_by=user_id if definition.requires_confirmation else None,
                confirmed_at=datetime.now(timezone.utc) if definition.requires_confirmation else None,
                execution_duration_ms=duration_ms,
                metadata_payload={"error": str(e)},
            )
            self.session.add(audit)
            await self.session.commit()

            return ActionResult(
                action_id=normalized_action_id,
                status=ActionStatus.FAILED,
                summary=f"Action '{normalized_action_id}' failed: {e}",
                errors=[str(e)],
                audit_reference=str(audit.id),
            )

    async def confirm_action(
        self,
        project_id: uuid.UUID,
        confirmation_token: str,
        user_id: str = "assistant_user",
    ) -> ActionResult:
        """Validate single-use anti-replay token and execute confirmed mutating action."""
        stmt = select(ActionConfirmationToken).where(
            ActionConfirmationToken.token_hash == confirmation_token,
            ActionConfirmationToken.project_id == project_id,
        )
        res = await self.session.execute(stmt)
        token_record = res.scalar_one_or_none()

        if not token_record:
            raise NotFoundError("ActionConfirmationToken", "Invalid or unknown confirmation token for project.")

        # Anti-replay check
        if token_record.consumed_at is not None:
            raise ConflictError("Confirmation token has already been consumed (replay prevented).")

        # Expiry check
        now = datetime.now(timezone.utc)
        expires_at = token_record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
            raise ValidationError("Confirmation token has expired.")

        # Atomic single-use consumption
        token_record.consumed_at = now
        await self.session.commit()

        # Re-execute action with preserved bound parameters, bypassing confirmation gate
        return await self.execute_action(
            project_id=project_id,
            action_id=token_record.action_id,
            parameters=token_record.parameters_payload,
            target_id=token_record.target_id,
            user_id=user_id,
            conversation_id=token_record.conversation_id,
            bypass_confirmation_gate=True,
        )

    async def _dispatch_action(
        self,
        project_id: uuid.UUID,
        action_id: str,
        parameters: dict[str, Any],
        target_id: str | None,
        user_id: str,
    ) -> tuple[dict[str, Any], str]:
        """Internal dispatcher routing action strictly to existing domain service implementations."""
        # =====================================================================
        # READ_ONLY ACTIONS
        # =====================================================================
        if action_id == "GET_PROJECT_CONTEXT":
            ctx = await self.context_engine.generate_context(project_id)
            return {
                "project_id": str(ctx.project.id),
                "name": ctx.project.name,
                "description": ctx.project.description,
                "status": ctx.project.status,
                "requirements_count": len(ctx.requirements) if ctx.requirements else 0,
            }, f"Retrieved project context for '{ctx.project.name}'."

        if action_id == "LIST_REQUIREMENTS":
            status_filter = parameters.get("status_filter")
            reqs, total = await self.requirement_service.list_requirements(project_id)
            items = []
            for r in reqs:
                if status_filter and r.status.value != status_filter:
                    continue
                items.append({
                    "id": str(r.id),
                    "title": r.title,
                    "status": r.status.value,
                    "priority": r.priority.value,
                    "type": r.type.value,
                })
            return {"total": len(items), "requirements": items}, f"Found {len(items)} requirement(s)."

        if action_id == "GET_REQUIREMENT":
            req_id_str = parameters.get("requirement_id") or target_id
            req_uuid = uuid.UUID(str(req_id_str))
            req = await self.requirement_service.get_by_id(project_id, req_uuid)
            return {
                "id": str(req.id),
                "title": req.title,
                "description": req.description,
                "status": req.status.value,
                "priority": req.priority.value,
                "type": req.type.value,
            }, f"Requirement '{req.title}'."

        if action_id == "LIST_WORKFLOWS":
            wfs = self.workflow_service.list_workflows()
            items = [{"id": w.id, "name": w.name, "description": w.description} for w in wfs]
            return {"total": len(items), "workflows": items}, f"Found {len(items)} workflow definitions."

        if action_id == "GET_WORKFLOW_HISTORY":
            limit = parameters.get("limit", 10)
            execs, total = await self.workflow_service.list_project_workflow_history(project_id, limit=limit)
            items = [
                {
                    "workflow_execution_id": str(e.workflow_execution_id),
                    "workflow_id": e.workflow_id,
                    "status": e.status.value,
                    "started_at": e.started_at.isoformat() if e.started_at else None,
                    "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                }
                for e in execs
            ]
            return {"total": total, "executions": items}, f"Found {len(items)} workflow executions."

        if action_id == "LIST_VERSIONS":
            resp = await self.version_service.list_versions(project_id)
            return resp.model_dump(mode="json"), f"Found {resp.total} version(s)."

        if action_id == "GET_VERSION":
            ver_id_str = parameters.get("version_id") or target_id
            ver_uuid = uuid.UUID(str(ver_id_str))
            ver = await self.version_service.get_version(project_id, ver_uuid)
            return ver.model_dump(mode="json"), f"Retrieved version v{ver.version_number} ({ver.status.value})."

        if action_id == "GET_ACTIVE_VERSION":
            active_ver = await self.version_service.get_active_version(project_id)
            if not active_ver:
                return {"active_version": None}, "No active software version designated."
            return active_ver.model_dump(mode="json"), f"Active version is v{active_ver.version_number}."

        if action_id == "GET_VERSION_FILE_CONTENT":
            ver_id_str = parameters.get("version_id") or target_id
            ver_uuid = uuid.UUID(str(ver_id_str))
            file_path = parameters["file_path"]

            # Path safety checks
            clean_path = file_path.replace("\\", "/").strip().lstrip("/")
            if ".." in clean_path.split("/") or clean_path.startswith("/"):
                raise ValidationError("Path traversal is prohibited.")

            raw_content = await self.version_service.get_version_file_content(project_id, ver_uuid, clean_path)

            # Deterministic size bounding (<= 100 KB and <= 1,000 lines)
            max_bytes = 100 * 1024
            max_lines = 1000
            lines = raw_content.splitlines()
            total_lines = len(lines)
            truncated = False

            if len(lines) > max_lines:
                lines = lines[:max_lines]
                truncated = True
                bounded_content = "\n".join(lines) + f"\n... [Truncated: exceeded {max_lines} lines limit]"
            else:
                bounded_content = raw_content

            content_bytes = bounded_content.encode("utf-8")
            if len(content_bytes) > max_bytes:
                bounded_content = content_bytes[:max_bytes].decode("utf-8", errors="ignore") + f"\n... [Truncated: exceeded 100 KB limit]"
                truncated = True

            return {
                "file_path": clean_path,
                "version_id": str(ver_uuid),
                "content": bounded_content,
                "total_lines": total_lines,
                "truncated": truncated,
                "size_bytes": len(bounded_content.encode("utf-8")),
            }, f"File '{clean_path}' ({total_lines} lines, truncated={truncated})."

        if action_id == "COMPARE_VERSIONS":
            from_uuid = uuid.UUID(str(parameters["from_version_id"]))
            to_uuid = uuid.UUID(str(parameters["to_version_id"]))
            diff_resp = await self.version_service.compare_versions(project_id, from_uuid, to_uuid)
            return diff_resp.model_dump(mode="json"), f"Compared v{diff_resp.from_version_number} with v{diff_resp.to_version_number}."

        if action_id == "GET_VERSION_VERIFICATION":
            ver_id_str = parameters.get("version_id") or target_id
            ver_uuid = uuid.UUID(str(ver_id_str))
            ver = await self.version_service.get_version(project_id, ver_uuid)
            return ver.verification_snapshot.model_dump(mode="json"), f"Verification status: {ver.verification_snapshot.verification_status.value}."

        if action_id == "GET_VERSION_CHANGES":
            ver_id_str = parameters.get("version_id") or target_id
            ver_uuid = uuid.UUID(str(ver_id_str))
            changes = await self.version_service.list_changes(project_id, ver_uuid)
            items = [c.model_dump(mode="json") for c in changes]
            return {"total": len(items), "changes": items}, f"Found {len(items)} change event(s)."

        if action_id == "GET_REMEDIATION_PROPOSAL":
            if not self.remediation_service:
                raise ValidationError("RemediationService is not configured.")
            prop_id_str = parameters.get("proposal_id") or target_id
            if prop_id_str:
                prop_uuid = uuid.UUID(str(prop_id_str))
                prop = await self.remediation_service.get_proposal(project_id, prop_uuid)
            else:
                target_exec = await self.remediation_service._resolve_target_execution(project_id)
                artifacts = target_exec.artifacts or {}
                prop_data = artifacts.get("remediation_proposal")
                if not prop_data:
                    raise NotFoundError("RemediationProposal", "No remediation proposal found in current artifacts.")
                from app.agents.remediation.contracts import RemediationProposal
                prop = RemediationProposal.model_validate(prop_data)
            return prop.model_dump(mode="json"), f"Remediation Proposal {prop.proposal_id} ({prop.status.value})."

        if action_id == "GET_BROWSER_TEST_RESULTS":
            if not self.browser_testing_service:
                raise ValidationError("BrowserTestingService is not configured.")
            ver_id_str = parameters.get("version_id") or target_id
            ver_uuid = uuid.UUID(str(ver_id_str)) if ver_id_str else None
            run_id_str = parameters.get("run_id")
            if run_id_str:
                run = await self.browser_testing_service.get_browser_test_run(
                    project_id=project_id,
                    run_id=uuid.UUID(str(run_id_str)),
                )
            else:
                run = await self.browser_testing_service.get_latest_browser_test_run(
                    project_id=project_id,
                    version_id=ver_uuid,
                )
            if not run:
                raise NotFoundError("BrowserTestRun", f"No browser test run found for project {project_id}.")
            return run.model_dump(mode="json"), f"Browser Test Run: {run.status.value} ({run.tests_passed}/{run.tests_total} passed)."

        if action_id == "GET_TEST_INVENTORY":
            ver_id_str = parameters.get("version_id") or target_id
            ver_uuid = uuid.UUID(str(ver_id_str)) if ver_id_str else None
            strict = parameters.get("strict", True)
            files_map, ai_suite, smoke_tests, journey_suite, _ = await self._resolve_test_inputs(
                project_id=project_id, version_id=ver_uuid
            )
            inv_svc = self._get_inventory_service()
            inventory = inv_svc.build_inventory(
                project_id=project_id,
                files_map=files_map,
                ai_test_suite=ai_suite,
                smoke_tests=smoke_tests,
                journey_suite=journey_suite,
                strict=strict,
            )
            return inventory.model_dump(mode="json"), f"Test Inventory: {len(inventory.tests)} tests ({inventory.tier_counts})."

        if action_id == "GET_COVERAGE_REPORT":
            ver_id_str = parameters.get("version_id") or target_id
            ver_uuid = uuid.UUID(str(ver_id_str)) if ver_id_str else None
            files_map, ai_suite, smoke_tests, journey_suite, _ = await self._resolve_test_inputs(
                project_id=project_id, version_id=ver_uuid
            )
            inv_svc = self._get_inventory_service()
            inventory = inv_svc.build_inventory(
                project_id=project_id,
                files_map=files_map,
                ai_test_suite=ai_suite,
                smoke_tests=smoke_tests,
                journey_suite=journey_suite,
                strict=False,
            )
            from app.testing.coverage.engine import UnifiedCoverageEngine
            reqs, _ = await self.requirement_service.list_requirements(project_id=project_id, limit=1000)
            report = UnifiedCoverageEngine.compute_coverage(
                active_requirements=reqs,
                inventory=inventory,
                project_id=project_id,
            )
            return report.model_dump(mode="json"), f"Coverage Report: {report.combined_coverage_percentage:.1f}% ({report.combined_covered_count}/{report.total_active_requirements} covered)."

        # =====================================================================
        # ANALYSIS ACTIONS
        # =====================================================================
        if action_id == "RUN_STATIC_ANALYSIS":
            if not self.static_analysis_service:
                raise ValidationError("StaticAnalysisService is not configured.")
            ver_id_str = parameters.get("version_id") or target_id
            wf_uuid = None
            if ver_id_str:
                ver = await self.version_service.get_version(project_id, uuid.UUID(str(ver_id_str)))
                wf_uuid = ver.workflow_execution_id

            req = StaticAnalysisRequest(project_id=project_id, workflow_execution_id=wf_uuid)
            res = await self.static_analysis_service.analyze(req)
            return res.model_dump(mode="json"), f"Static Analysis: {res.status.value} ({res.error_count} error(s), {res.warning_count} warning(s))."

        if action_id == "VERIFY_VERSION":
            # STRICT INVARIANT: Non-mutating! Recomputes verification gate only.
            ver_id_str = parameters.get("version_id") or target_id
            ver_uuid = uuid.UUID(str(ver_id_str))
            snapshot = await self.version_service.reevaluate_verification(project_id, ver_uuid)
            return snapshot.model_dump(mode="json"), f"Version verification re-evaluated: {snapshot.verification_status.value} (is_verified={snapshot.is_verified})."

        if action_id == "ANALYZE_FAILURE":
            if not self.failure_analysis_service:
                raise ValidationError("FailureAnalysisService is not configured.")
            wf_id_str = parameters.get("workflow_execution_id") or target_id
            wf_uuid = uuid.UUID(str(wf_id_str)) if wf_id_str else None
            diagnosis = await self.failure_analysis_service.analyze_failure(
                project_id=project_id,
                workflow_execution_id=wf_uuid,
                force=True,
            )
            return diagnosis.model_dump(mode="json"), f"Failure Diagnosis: '{diagnosis.title}' ({diagnosis.severity.value})."

        if action_id == "ANALYZE_COVERAGE_GAPS":
            ver_id_str = parameters.get("version_id") or target_id
            ver_uuid = uuid.UUID(str(ver_id_str)) if ver_id_str else None
            files_map, ai_suite, smoke_tests, journey_suite, _ = await self._resolve_test_inputs(
                project_id=project_id, version_id=ver_uuid
            )
            inv_svc = self._get_inventory_service()
            inventory = inv_svc.build_inventory(
                project_id=project_id,
                files_map=files_map,
                ai_test_suite=ai_suite,
                smoke_tests=smoke_tests,
                journey_suite=journey_suite,
                strict=False,
            )
            from app.testing.coverage.engine import UnifiedCoverageEngine
            reqs, _ = await self.requirement_service.list_requirements(project_id=project_id, limit=1000)
            report = UnifiedCoverageEngine.compute_coverage(
                active_requirements=reqs,
                inventory=inventory,
                project_id=project_id,
            )
            gaps = [
                {
                    "requirement_id": rid,
                    "covering_tiers": [t.value if hasattr(t, "value") else str(t) for t in report.requirement_traceability[rid].covering_tiers] if rid in report.requirement_traceability else [],
                }
                for rid in report.combined_uncovered_requirement_ids
            ]
            return {
                "project_id": report.project_id,
                "total_active_requirements": report.total_active_requirements,
                "uncovered_count": report.combined_uncovered_count,
                "uncovered_requirement_ids": report.combined_uncovered_requirement_ids,
                "gaps": gaps,
                "calculated_at": report.calculated_at.isoformat(),
            }, f"Coverage Gaps: {report.combined_uncovered_count} uncovered requirement(s)."

        if action_id == "ANALYZE_REGRESSION_IMPACT":
            base_str = parameters.get("base_version_id")
            target_str = parameters.get("target_version_id") or parameters.get("version_id") or target_id
            base_uuid = uuid.UUID(str(base_str)) if base_str else None
            target_uuid = uuid.UUID(str(target_str)) if target_str else None
            changed_files = parameters.get("changed_files")

            if not changed_files and base_uuid and target_uuid:
                comparison = await self.version_service.compare_versions(
                    project_id=project_id, from_version_id=base_uuid, to_version_id=target_uuid
                )
                changed_files = [f.file_path for f in comparison.file_diffs]

            files_map, ai_suite, smoke_tests, journey_suite, _ = await self._resolve_test_inputs(
                project_id=project_id, version_id=target_uuid
            )
            if not changed_files:
                changed_files = list(files_map.keys())

            inv_svc = self._get_inventory_service()
            inventory = inv_svc.build_inventory(
                project_id=project_id,
                files_map=files_map,
                ai_test_suite=ai_suite,
                smoke_tests=smoke_tests,
                journey_suite=journey_suite,
                strict=False,
            )
            reqs, _ = await self.requirement_service.list_requirements(project_id=project_id, limit=1000)
            active_ids = [str(r.id) for r in reqs if not getattr(r, "is_archived", False)]

            impact_svc = self._get_impact_service()
            report = impact_svc.analyze_change_impact(
                project_id=project_id,
                changed_files=changed_files,
                files_map=files_map,
                inventory=inventory,
                active_requirement_ids=active_ids,
            )
            return report.model_dump(mode="json"), f"Change Impact: {len(report.all_affected_files)} affected files, {len(report.affected_tests)} affected tests."

        # =====================================================================
        # GENERATION ACTIONS
        # =====================================================================
        if action_id == "GENERATE_AI_TESTS":
            if not self.ai_test_service:
                raise ValidationError("AITestService is not configured.")
            ver_id_str = parameters.get("version_id") or target_id
            wf_uuid = None
            if ver_id_str:
                ver = await self.version_service.get_version(project_id, uuid.UUID(str(ver_id_str)))
                wf_uuid = ver.workflow_execution_id
            suite = await self.ai_test_service.generate_tests(project_id=project_id, workflow_execution_id=wf_uuid)
            return suite.model_dump(mode="json"), f"Generated AI Test Suite {suite.suite_id} ({suite.test_count} tests)."

        if action_id == "CREATE_REMEDIATION_PROPOSAL":
            if not self.remediation_service:
                raise ValidationError("RemediationService is not configured.")
            wf_id_str = parameters.get("workflow_execution_id")
            wf_uuid = uuid.UUID(str(wf_id_str)) if wf_id_str else None
            prop = await self.remediation_service.create_proposal(project_id=project_id, workflow_execution_id=wf_uuid)
            return prop.model_dump(mode="json"), f"Created Remediation Proposal {prop.proposal_id} ({prop.status.value})."

        if action_id == "GENERATE_BROWSER_JOURNEYS":
            if not self.browser_journey_service:
                from app.services.browser_journey_service import BrowserJourneyService
                self.browser_journey_service = BrowserJourneyService(
                    session=self.session,
                    context_engine=self.context_engine,
                    version_service=self.version_service,
                    browser_testing_service=self.browser_testing_service,
                    workflow_service=self.workflow_service,
                )
            ver_id_str = parameters.get("version_id") or target_id
            ver_uuid = uuid.UUID(str(ver_id_str)) if ver_id_str else None
            exec_tests = parameters.get("execute_browser_tests", True)
            max_j = parameters.get("max_journeys", 10)

            res = await self.browser_journey_service.generate_and_execute_journeys(
                project_id=project_id,
                version_id=ver_uuid,
                execute_browser_tests=exec_tests,
                max_journeys=max_j,
            )

            from app.schemas.browser_journeys import BrowserJourneyWorkflowResponse
            response_dto = BrowserJourneyWorkflowResponse.from_result(res)

            summary = (
                f"Browser Journey Workflow {res.status.value}: "
                f"{response_dto.journey_count} journey(s) generated, "
                f"validation {'passed' if response_dto.validation_passed else 'failed'}"
            )
            if response_dto.browser_tests_executed:
                summary += f", browser tests {'passed' if response_dto.browser_tests_passed else 'failed'}."
            else:
                summary += "."

            return response_dto.model_dump(mode="json"), summary

        if action_id == "PLAN_REGRESSION":
            base_str = parameters.get("base_version_id")
            target_str = parameters.get("target_version_id") or parameters.get("version_id") or target_id
            base_uuid = uuid.UUID(str(base_str)) if base_str else None
            target_uuid = uuid.UUID(str(target_str)) if target_str else None
            changed_files = parameters.get("changed_files")
            mode_str = parameters.get("mode", "SELECTIVE")
            auto_broaden = parameters.get("auto_broaden", False)

            if not changed_files and base_uuid and target_uuid:
                comparison = await self.version_service.compare_versions(
                    project_id=project_id, from_version_id=base_uuid, to_version_id=target_uuid
                )
                changed_files = [f.file_path for f in comparison.file_diffs]

            files_map, ai_suite, smoke_tests, journey_suite, _ = await self._resolve_test_inputs(
                project_id=project_id, version_id=target_uuid
            )
            if not changed_files:
                changed_files = list(files_map.keys())

            inv_svc = self._get_inventory_service()
            inventory = inv_svc.build_inventory(
                project_id=project_id,
                files_map=files_map,
                ai_test_suite=ai_suite,
                smoke_tests=smoke_tests,
                journey_suite=journey_suite,
                strict=False,
            )
            reqs, _ = await self.requirement_service.list_requirements(project_id=project_id, limit=1000)
            active_ids = [str(r.id) for r in reqs if not getattr(r, "is_archived", False)]

            impact_svc = self._get_impact_service()
            impact_report = impact_svc.analyze_change_impact(
                project_id=project_id,
                changed_files=changed_files,
                files_map=files_map,
                inventory=inventory,
                active_requirement_ids=active_ids,
            )
            from app.testing.coverage.engine import UnifiedCoverageEngine
            coverage_report = UnifiedCoverageEngine.compute_coverage(
                active_requirements=reqs,
                inventory=inventory,
                project_id=project_id,
            )
            from app.testing.regression.contracts import RegressionPlanMode
            plan_mode = RegressionPlanMode(mode_str) if mode_str in [m.value for m in RegressionPlanMode] else RegressionPlanMode.SELECTIVE

            planner = self._get_regression_planner()
            plan = planner.plan_regression(
                project_id=project_id,
                inventory=inventory,
                impact_report=impact_report,
                coverage_report=coverage_report,
                mode=plan_mode,
                auto_broaden=auto_broaden,
                base_version_id=str(base_uuid) if base_uuid else None,
                target_version_id=str(target_uuid) if target_uuid else None,
            )
            return plan.model_dump(mode="json"), f"Regression Plan ({plan.mode.value}): {len(plan.selected_test_ids)} test(s) selected across {len(plan.selected_tests_by_tier)} tiers."

        # =====================================================================
        # EXECUTION ACTIONS
        # =====================================================================
        if action_id == "RUN_SANDBOX":
            if not self.sandbox_service:
                raise ValidationError("SandboxService is not configured.")
            ver_id_str = parameters.get("version_id") or target_id
            wf_uuid = None
            if ver_id_str:
                ver = await self.version_service.get_version(project_id, uuid.UUID(str(ver_id_str)))
                wf_uuid = ver.workflow_execution_id
            req = ExecutionRequest(
                project_id=project_id,
                workflow_execution_id=wf_uuid,
                execution_type=ExecutionType.TEST,
                limits=ResourceLimits(timeout_seconds=30),
            )
            res = await self.sandbox_service.execute(req)
            return res.model_dump(mode="json"), f"Sandbox execution: {res.status.value} (exit code: {res.exit_code})."

        if action_id == "RUN_AI_TESTS":
            if not self.ai_test_service:
                raise ValidationError("AITestService is not configured.")
            suite_id_str = parameters.get("suite_id") or target_id
            if not suite_id_str:
                raise ValidationError("suite_id is required to execute AI tests.")
            suite_uuid = uuid.UUID(str(suite_id_str))
            res = await self.ai_test_service.execute_tests(project_id=project_id, suite_id=suite_uuid)
            return res.model_dump(mode="json"), f"AI tests executed: {res.status.value} ({res.tests_passed}/{res.tests_total} passed)."

        if action_id == "RUN_BROWSER_TESTS":
            if not self.browser_testing_service:
                raise ValidationError("BrowserTestingService is not configured.")
            ver_id_str = parameters.get("version_id") or target_id
            ver_uuid = None
            if ver_id_str:
                ver_uuid = uuid.UUID(str(ver_id_str))
            else:
                active_ver = await self.version_service.get_active_version(project_id)
                if active_ver:
                    ver_uuid = active_ver.id
            run = await self.browser_testing_service.execute_browser_tests(
                project_id=project_id,
                version_id=ver_uuid,
            )
            return run.model_dump(mode="json"), f"Browser test execution {run.status.value}: {run.summary}"

        if action_id == "EXECUTE_REGRESSION":
            if not self.regression_executor:
                raise ValidationError("RegressionExecutionService is not configured.")
            base_str = parameters.get("base_version_id")
            target_str = parameters.get("target_version_id") or parameters.get("version_id") or target_id
            base_uuid = uuid.UUID(str(base_str)) if base_str else None
            target_uuid = uuid.UUID(str(target_str)) if target_str else None
            changed_files = parameters.get("changed_files")
            mode_str = parameters.get("mode", "SELECTIVE")
            auto_broaden = parameters.get("auto_broaden", False)
            skip_browser = parameters.get("skip_browser_tests", False)
            browser_base_url = parameters.get("browser_base_url")
            timeout_s = parameters.get("execution_timeout_seconds", 300)

            if not changed_files and base_uuid and target_uuid:
                comparison = await self.version_service.compare_versions(
                    project_id=project_id, from_version_id=base_uuid, to_version_id=target_uuid
                )
                changed_files = [f.file_path for f in comparison.file_diffs]

            files_map, ai_suite, smoke_tests, journey_suite, resolved_version = await self._resolve_test_inputs(
                project_id=project_id, version_id=target_uuid
            )
            if not changed_files:
                changed_files = list(files_map.keys())

            inv_svc = self._get_inventory_service()
            inventory = inv_svc.build_inventory(
                project_id=project_id,
                files_map=files_map,
                ai_test_suite=ai_suite,
                smoke_tests=smoke_tests,
                journey_suite=journey_suite,
                strict=False,
            )
            reqs, _ = await self.requirement_service.list_requirements(project_id=project_id, limit=1000)
            active_ids = [str(r.id) for r in reqs if not getattr(r, "is_archived", False)]

            impact_svc = self._get_impact_service()
            impact_report = impact_svc.analyze_change_impact(
                project_id=project_id,
                changed_files=changed_files,
                files_map=files_map,
                inventory=inventory,
                active_requirement_ids=active_ids,
            )
            from app.testing.coverage.engine import UnifiedCoverageEngine
            coverage_report = UnifiedCoverageEngine.compute_coverage(
                active_requirements=reqs,
                inventory=inventory,
                project_id=project_id,
            )
            from app.testing.regression.contracts import RegressionPlanMode
            plan_mode = RegressionPlanMode(mode_str) if mode_str in [m.value for m in RegressionPlanMode] else RegressionPlanMode.SELECTIVE

            planner = self._get_regression_planner()
            plan = planner.plan_regression(
                project_id=project_id,
                inventory=inventory,
                impact_report=impact_report,
                coverage_report=coverage_report,
                mode=plan_mode,
                auto_broaden=auto_broaden,
                base_version_id=str(base_uuid) if base_uuid else None,
                target_version_id=str(target_uuid) if target_uuid else None,
            )
            from app.testing.regression.validator import RegressionPlanValidator
            RegressionPlanValidator().validate(plan, inventory)

            manifest = None
            if resolved_version:
                raw_manifest = getattr(resolved_version, "runtime_manifest", None)
                if raw_manifest:
                    from app.schemas.runtime import ApplicationRuntimeManifest
                    try:
                        manifest = ApplicationRuntimeManifest.model_validate(raw_manifest)
                    except Exception as e:
                        raise ValidationError(f"Invalid runtime manifest for version '{resolved_version.version_id}': {e}")
                else:
                    manifest = await self.version_service.resolve_runtime_manifest(project_id, resolved_version.version_id)

            result = await self.regression_executor.execute_plan(
                project_id=project_id,
                plan=plan,
                inventory=inventory,
                files_map=files_map,
                application_manifest=manifest,
                skip_browser_tests=skip_browser,
                browser_base_url=browser_base_url,
                execution_timeout_seconds=timeout_s,
            )
            return result.model_dump(mode="json"), f"Regression Execution {result.status.value}: {result.passed_tests}/{result.total_tests} tests passed."


        # =====================================================================
        # MUTATING ACTIONS (Guarded by confirmation token in execute_action)
        # =====================================================================
        if action_id == "APPROVE_REMEDIATION":
            if not self.remediation_service:
                raise ValidationError("RemediationService is not configured.")
            prop_id_str = parameters.get("proposal_id") or target_id
            prop_uuid = uuid.UUID(str(prop_id_str))
            prop = await self.remediation_service.approve_proposal(project_id, prop_uuid)
            return prop.model_dump(mode="json"), f"Approved remediation proposal {prop.proposal_id}."

        if action_id == "REJECT_REMEDIATION":
            if not self.remediation_service:
                raise ValidationError("RemediationService is not configured.")
            prop_id_str = parameters.get("proposal_id") or target_id
            prop_uuid = uuid.UUID(str(prop_id_str))
            reason = parameters.get("reason")
            prop = await self.remediation_service.reject_proposal(project_id, prop_uuid, reason=reason)
            return prop.model_dump(mode="json"), f"Rejected remediation proposal {prop.proposal_id}."

        if action_id == "APPLY_REMEDIATION":
            if not self.remediation_service:
                raise ValidationError("RemediationService is not configured.")
            prop_id_str = parameters.get("proposal_id") or target_id
            prop_uuid = uuid.UUID(str(prop_id_str))

            # Idempotency check: if proposal already applied, return current state
            existing_prop = await self.remediation_service.get_proposal(project_id, prop_uuid)
            from app.agents.remediation.contracts import RemediationProposalStatus
            if existing_prop.status == RemediationProposalStatus.APPLIED:
                active_ver = await self.version_service.get_active_version(project_id)
                return {
                    "proposal": existing_prop.model_dump(mode="json"),
                    "active_version": active_ver.model_dump(mode="json") if active_ver else None,
                    "idempotent": True,
                }, f"Remediation proposal {prop_uuid} was already applied."

            prop, verif = await self.remediation_service.apply_proposal(project_id, prop_uuid)
            # Register newly created remediation artifact as a new DevelopmentVersion
            target_exec = await self.remediation_service._resolve_target_execution(project_id, prop.workflow_execution_id)
            new_version = await self.version_service.register_version_from_workflow(
                project_id=project_id,
                execution=target_exec,
                is_remediation=True,
            )
            return {
                "proposal": prop.model_dump(mode="json"),
                "verification": verif.model_dump(mode="json"),
                "new_version": new_version.model_dump(mode="json"),
            }, f"Remediation applied. New version v{new_version.version_number} synthesized and verified."

        if action_id == "ACTIVATE_VERSION":
            ver_id_str = parameters.get("version_id") or target_id
            ver_uuid = uuid.UUID(str(ver_id_str))

            # Idempotency check: if already active version, return without duplicate transition
            current_active = await self.version_service.get_active_version(project_id)
            cand_id = getattr(current_active, "id", None)
            if not isinstance(cand_id, (uuid.UUID, str)):
                cand_id = getattr(current_active, "version_id", None)
            if isinstance(cand_id, str):
                try:
                    cand_id = uuid.UUID(cand_id)
                except ValueError:
                    cand_id = None

            if current_active and cand_id == ver_uuid:
                dump_data = current_active.model_dump(mode="json") if hasattr(current_active, "model_dump") else {}
                return dump_data, f"Version v{getattr(current_active, 'version_number', '')} is already active."

            reason = parameters.get("reason") or "Activated via Intelli Assistant"
            res = await self.version_service.activate_version(
                project_id=project_id,
                version_id=ver_uuid,
                reason=reason,
                activated_by=user_id,
            )
            return res.model_dump(mode="json"), f"Activated version v{res.version_number}."

        if action_id == "ROLLBACK_VERSION":
            target_id_str = parameters.get("target_version_id") or target_id
            target_uuid = uuid.UUID(str(target_id_str))

            # Idempotency check: if already targeting the requested version, return current state
            current_active = await self.version_service.get_active_version(project_id)
            cand_id = getattr(current_active, "id", None)
            if not isinstance(cand_id, (uuid.UUID, str)):
                cand_id = getattr(current_active, "version_id", None)
            if isinstance(cand_id, str):
                try:
                    cand_id = uuid.UUID(cand_id)
                except ValueError:
                    cand_id = None

            if current_active and cand_id == target_uuid:
                dump_data = current_active.model_dump(mode="json") if hasattr(current_active, "model_dump") else {}
                return dump_data, f"Version v{getattr(current_active, 'version_number', '')} is already active."

            reason = parameters.get("reason") or "Rollback via Intelli Assistant"
            res = await self.version_service.rollback_version(
                project_id=project_id,
                target_version_id=target_uuid,
                reason=reason,
                rolled_back_by=user_id,
            )
            return res.model_dump(mode="json"), f"Rolled back active version to v{res.version_number}."

        if action_id == "RUN_WORKFLOW":
            workflow_id = parameters["workflow_id"]
            workflow_input = parameters.get("workflow_input", {})
            req = WorkflowExecuteRequest(
                project_id=project_id,
                options=workflow_input,
            )
            res = await self.workflow_service.execute_workflow(workflow_id, req)
            return res.model_dump(mode="json"), f"Workflow '{workflow_id}' executed with status '{res.status.value}'."

        # =====================================================================
        # Phase 13 Multi-Environment Actions
        # =====================================================================
        if action_id == "GET_ENVIRONMENTS":
            env_svc = self._get_environment_service()
            envs = await env_svc.get_or_create_project_environments(project_id)
            return {
                "environments": [
                    {
                        "id": str(e.id),
                        "environment_type": e.environment_type.value,
                        "name": e.name,
                        "status": e.status.value,
                        "current_version_id": str(e.current_version_id) if e.current_version_id else None,
                        "current_version_number": e.current_version.version_number if e.current_version else None,
                        "is_production": e.is_production,
                        "last_deployed_at": e.last_deployed_at.isoformat() if e.last_deployed_at else None,
                    }
                    for e in envs
                ]
            }, f"Retrieved {len(envs)} environments for project."

        if action_id == "GET_ENVIRONMENT_STATUS":
            env_type_str = parameters.get("environment_type") or target_id
            env_svc = self._get_environment_service()
            e = await env_svc.get_environment(project_id, env_type_str)
            v_num = e.current_version.version_number if e.current_version else None
            return {
                "id": str(e.id),
                "environment_type": e.environment_type.value,
                "name": e.name,
                "status": e.status.value,
                "current_version_id": str(e.current_version_id) if e.current_version_id else None,
                "current_version_number": v_num,
                "is_production": e.is_production,
                "configuration": e.configuration or {},
                "last_deployed_at": e.last_deployed_at.isoformat() if e.last_deployed_at else None,
            }, f"Environment {e.environment_type.value} is {e.status.value} (running v{v_num if v_num is not None else 'None'})."

        if action_id == "GET_DEPLOYMENT_HISTORY":
            env_type_str = parameters.get("environment_type")
            limit = int(parameters.get("limit", 10))
            env_svc = self._get_environment_service()
            env_id = None
            if env_type_str:
                env_obj = await env_svc.get_environment(project_id, env_type_str)
                env_id = env_obj.id
            records = await env_svc.list_deployments(project_id, environment_id=env_id, limit=limit)
            return {
                "deployments": [
                    {
                        "id": str(r.id),
                        "environment_id": str(r.environment_id),
                        "version_id": str(r.version_id),
                        "version_number": r.version.version_number if r.version else None,
                        "operation": r.operation.value,
                        "status": r.status.value,
                        "requested_by": r.requested_by,
                        "started_at": r.started_at.isoformat(),
                        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                        "failure_reason": r.failure_reason,
                    }
                    for r in records
                ]
            }, f"Retrieved {len(records)} deployment records."

        if action_id == "CHECK_PROMOTION_ELIGIBILITY":
            ver_uuid = uuid.UUID(str(parameters["version_id"]))
            from app.models.environment import EnvironmentType
            target_env = EnvironmentType(str(parameters["target_environment"]).upper())
            source_env = EnvironmentType(str(parameters["source_environment"]).upper()) if parameters.get("source_environment") else None
            env_svc = self._get_environment_service()
            eligibility = await env_svc.check_promotion_eligibility(
                project_id=project_id,
                version_id=ver_uuid,
                target_env_type=target_env,
                source_env_type=source_env,
            )
            verdict_str = "ELIGIBLE" if eligibility.eligible else "INELIGIBLE"
            return eligibility.model_dump(mode="json"), f"Promotion eligibility for {target_env.value}: {verdict_str}."

        if action_id == "PROMOTE_VERSION":
            ver_uuid = uuid.UUID(str(parameters["version_id"]))
            from app.models.environment import EnvironmentType
            target_env = EnvironmentType(str(parameters["target_environment"]).upper())
            source_env = EnvironmentType(str(parameters["source_environment"]).upper()) if parameters.get("source_environment") else None
            notes = parameters.get("notes")
            env_svc = self._get_environment_service()
            rec = await env_svc.promote_version(
                project_id=project_id,
                version_id=ver_uuid,
                target_env_type=target_env,
                source_env_type=source_env,
                requested_by=user_id,
                notes=notes,
            )
            v_num = rec.version.version_number if rec.version else None
            return {
                "deployment_id": str(rec.id),
                "operation": rec.operation.value,
                "status": rec.status.value,
                "target_environment": target_env.value,
                "version_number": v_num,
            }, f"Successfully promoted version v{v_num} to {target_env.value}."

        if action_id == "DEPLOY_TO_ENVIRONMENT":
            env_target = parameters.get("environment_type") or target_id
            ver_uuid = uuid.UUID(str(parameters["version_id"]))
            notes = parameters.get("notes")
            env_svc = self._get_environment_service()
            rec = await env_svc.deploy_version(
                project_id=project_id,
                environment_id_or_type=env_target,
                version_id=ver_uuid,
                requested_by=user_id,
                notes=notes,
            )
            return {
                "deployment_id": str(rec.id),
                "status": rec.status.value,
                "environment": str(env_target),
            }, f"Successfully deployed version to {env_target}."

        if action_id == "ROLLBACK_ENVIRONMENT":
            env_target = parameters.get("environment_type") or target_id
            target_uuid = uuid.UUID(str(parameters["target_version_id"]))
            reason = parameters.get("reason") or "Rollback via Intelli Assistant"
            env_svc = self._get_environment_service()
            rec = await env_svc.rollback_environment(
                project_id=project_id,
                environment_id_or_type=env_target,
                target_version_id=target_uuid,
                requested_by=user_id,
                reason=reason,
            )
            v_num = rec.version.version_number if rec.version else None
            return {
                "deployment_id": str(rec.id),
                "operation": "ROLLBACK",
                "status": rec.status.value,
                "environment": str(env_target),
                "restored_version": v_num,
            }, f"Successfully rolled back {env_target} to version v{v_num}."

        raise ValidationError(f"Unhandled action dispatch for '{action_id}'.")
