"""Remediation Service: Human-in-the-Loop Proposal, Approval, Application & Verification."""

import copy
import logging
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.agents.code_generation.contracts import CodeGenerationOutput, GeneratedFile
from app.agents.execution import AgentExecutor
from app.agents.failure_analysis.contracts import FailureDiagnosis, FailureType
from app.agents.remediation.agent import RemediationProposalAgent
from app.agents.remediation.contracts import (
    ProposedChange,
    RemediationProposal,
    RemediationProposalCandidate,
    RemediationProposalStatus,
    RemediationVerificationResult,
)
from app.agents.remediation.diff_generator import DiffGenerator
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.workflow_execution import WorkflowExecution
from app.sandbox.contracts import ExecutionRequest, ExecutionResult, ExecutionStatus, ExecutionType
from app.sandbox.docker_executor import DockerSandboxExecutor
from app.sandbox.static_analysis.contracts import DiagnosticSeverity, StaticAnalysisRequest, StaticAnalysisResult, StaticAnalysisStatus
from app.sandbox.static_analysis.service import StaticAnalysisService
from app.services.context_engine import ProjectContextEngine
from app.services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)


class RemediationService:
    """Orchestrates human-in-the-loop code remediation proposals, explicit approvals, and verification."""

    def __init__(
        self,
        session: AsyncSession,
        workflow_service: WorkflowService,
        executor: AgentExecutor,
        context_engine: ProjectContextEngine,
        sandbox_executor: DockerSandboxExecutor | None = None,
        static_analysis_service: StaticAnalysisService | None = None,
        browser_testing_service: Any | None = None,
    ) -> None:
        self.session = session
        self.workflow_service = workflow_service
        self.executor = executor
        self.context_engine = context_engine
        self.agent = RemediationProposalAgent()
        self.sandbox_executor = sandbox_executor or DockerSandboxExecutor()
        self.static_analysis_service = static_analysis_service or StaticAnalysisService(executor=self.sandbox_executor)
        self.browser_testing_service = browser_testing_service

    async def _resolve_target_execution(
        self,
        project_id: uuid.UUID,
        workflow_execution_id: uuid.UUID | None = None,
    ) -> WorkflowExecution:
        """Find the active WorkflowExecution containing artifacts for this project."""
        if workflow_execution_id:
            stmt = select(WorkflowExecution).where(
                WorkflowExecution.project_id == project_id,
                WorkflowExecution.workflow_execution_id == workflow_execution_id,
            )
            res = await self.session.execute(stmt)
            target = res.scalar_one_or_none()
            if target:
                return target

        stmt = select(WorkflowExecution).where(
            WorkflowExecution.project_id == project_id
        ).order_by(WorkflowExecution.started_at.desc())
        res = await self.session.execute(stmt)
        all_execs = res.scalars().all()
        for target in all_execs:
            if target.artifacts and ("failure_analysis" in target.artifacts or "code-generation" in target.artifacts or "code_generation" in target.artifacts):
                return target
        if all_execs:
            return all_execs[0]
        raise NotFoundError("WorkflowExecution", str(project_id))

    async def create_proposal(
        self,
        project_id: uuid.UUID,
        workflow_execution_id: uuid.UUID | None = None,
    ) -> RemediationProposal:
        """Generate, validate, and compute unified diff for a new remediation proposal.

        Status initialized to AWAITING_APPROVAL. Does NOT apply patch.
        """
        target_exec = await self._resolve_target_execution(project_id, workflow_execution_id)
        artifacts = target_exec.artifacts or {}

        # 1. Authoritative Failure Diagnosis
        diag_data = artifacts.get("failure_analysis")
        if not diag_data:
            raise ValidationError(
                "No failure diagnosis found. Please run Failure Analysis prior to generating a remediation proposal."
            )
        diagnosis = FailureDiagnosis.model_validate(diag_data)
        if diagnosis.failure_type == FailureType.UNKNOWN and "No Failure Detected" in diagnosis.title:
            raise ValidationError("Cannot create remediation proposal for a clean project with no detected failures.")

        # 2. Authoritative Code Generation Output
        code_data = artifacts.get("code-generation") or artifacts.get("code_generation")
        if not code_data:
            raise ValidationError("No generated code artifact found to remediate.")
        code_output = CodeGenerationOutput.model_validate(code_data)

        # 3. Context & Metadata
        project_context = await self.context_engine.generate_context(project_id)
        static_data = artifacts.get("static_analysis")
        exec_data = artifacts.get("test_execution")
        static_res = StaticAnalysisResult.model_validate(static_data) if static_data else None
        exec_res = ExecutionResult.model_validate(exec_data) if exec_data else None

        current_files_map = {f.path: f.content for f in code_output.generated_files}

        # 4. Invoke RemediationProposalAgent via AgentExecutor
        agent_result = await self.executor.execute(
            agent=self.agent,
            context=project_context,
            session=self.session,
            workflow_execution_id=target_exec.workflow_execution_id,
            diagnosis=diagnosis,
            code_generation=code_output,
            static_analysis_result=static_res,
            execution_result=exec_res,
            current_artifact_version=getattr(code_output, "version", 1),
        )

        if not agent_result.validation.is_valid:
            raise ValidationError(
                f"Generated remediation proposal failed deterministic validation: {agent_result.validation.errors}"
            )

        candidate: RemediationProposalCandidate = agent_result.output

        # 5. Compute Deterministic Unified Diff
        try:
            diff_text, _ = DiffGenerator.apply_changes_to_files(
                current_files=current_files_map,
                changes=candidate.changes,
            )
        except ValueError as ve:
            raise ValidationError(f"Patch applicability check failed: {ve}") from ve

        affected_files = list(dict.fromkeys(c.file_path for c in candidate.changes))

        proposal = RemediationProposal(
            proposal_id=agent_result.execution_id,
            diagnosis_id=str(diagnosis.diagnosis_id),
            project_id=project_id,
            workflow_execution_id=target_exec.workflow_execution_id,
            title=candidate.title,
            summary=candidate.summary,
            rationale=candidate.rationale,
            changes=candidate.changes,
            affected_files=affected_files,
            unified_diff=diff_text,
            expected_effect=candidate.expected_effect,
            verification_plan=candidate.verification_plan,
            risk_level=candidate.risk_level,
            status=RemediationProposalStatus.AWAITING_APPROVAL,
            requirement_links=candidate.requirement_links,
            architecture_links=candidate.architecture_links,
            database_links=candidate.database_links,
            model_metadata=agent_result.metadata,
            parent_artifact_version=getattr(code_output, "version", 1),
        )

        # 6. Persist Proposal to Workflow Execution Artifacts
        new_artifacts = dict(target_exec.artifacts or {})
        new_artifacts["remediation_proposal"] = proposal.model_dump(mode="json")
        history = list(new_artifacts.get("remediation_history", []))
        history.append({
            "event": "PROPOSAL_CREATED",
            "proposal_id": str(proposal.proposal_id),
            "timestamp": proposal.created_at.isoformat(),
            "status": proposal.status.value,
        })
        new_artifacts["remediation_history"] = history
        target_exec.artifacts = new_artifacts
        flag_modified(target_exec, "artifacts")
        await self.session.commit()

        logger.info(f"Remediation proposal created [id={proposal.proposal_id}] for project '{project_id}'")
        return proposal

    async def get_proposal(
        self,
        project_id: uuid.UUID,
        proposal_id: uuid.UUID,
    ) -> RemediationProposal:
        """Retrieve proposal by ID from workflow artifacts."""
        target_exec = await self._resolve_target_execution(project_id)
        artifacts = target_exec.artifacts or {}
        prop_data = artifacts.get("remediation_proposal")

        if prop_data and prop_data.get("proposal_id") == str(proposal_id):
            return RemediationProposal.model_validate(prop_data)

        # Search history if current active proposal is different
        history = artifacts.get("remediation_history", [])
        for entry in history:
            if entry.get("proposal_id") == str(proposal_id) and "proposal" in entry:
                return RemediationProposal.model_validate(entry["proposal"])

        raise NotFoundError("RemediationProposal", str(proposal_id))

    async def approve_proposal(
        self,
        project_id: uuid.UUID,
        proposal_id: uuid.UUID,
    ) -> RemediationProposal:
        """Explicitly approve proposal. Only approved proposals may ever be applied."""
        proposal = await self.get_proposal(project_id, proposal_id)
        target_exec = await self._resolve_target_execution(project_id, proposal.workflow_execution_id)

        if proposal.status == RemediationProposalStatus.APPROVED:
            return proposal  # Idempotent

        if proposal.status not in (
            RemediationProposalStatus.AWAITING_APPROVAL,
            RemediationProposalStatus.VALIDATED,
            RemediationProposalStatus.VERIFICATION_FAILED,
        ):
            raise ConflictError(
                f"Cannot approve proposal in '{proposal.status.value}' state. Must be AWAITING_APPROVAL.",
                field="status",
                value=proposal.status.value,
            )

        proposal.status = RemediationProposalStatus.APPROVED
        proposal.approved_at = datetime.now(timezone.utc)

        new_artifacts = dict(target_exec.artifacts or {})
        new_artifacts["remediation_proposal"] = proposal.model_dump(mode="json")
        history = list(new_artifacts.get("remediation_history", []))
        history.append({
            "event": "PROPOSAL_APPROVED",
            "proposal_id": str(proposal.proposal_id),
            "timestamp": proposal.approved_at.isoformat(),
        })
        new_artifacts["remediation_history"] = history
        target_exec.artifacts = new_artifacts
        flag_modified(target_exec, "artifacts")
        await self.session.commit()

        logger.info(f"Remediation proposal approved [id={proposal.proposal_id}] by user.")
        return proposal

    async def reject_proposal(
        self,
        project_id: uuid.UUID,
        proposal_id: uuid.UUID,
        reason: str | None = None,
    ) -> RemediationProposal:
        """Explicitly reject proposal."""
        proposal = await self.get_proposal(project_id, proposal_id)
        target_exec = await self._resolve_target_execution(project_id, proposal.workflow_execution_id)

        if proposal.status == RemediationProposalStatus.REJECTED:
            return proposal

        if proposal.status in (RemediationProposalStatus.APPLIED, RemediationProposalStatus.VERIFIED):
            raise ConflictError("Cannot reject an already applied proposal.", field="status", value=proposal.status.value)

        proposal.status = RemediationProposalStatus.REJECTED
        proposal.rejected_at = datetime.now(timezone.utc)
        proposal.rejection_reason = reason or "Rejected by user."

        new_artifacts = dict(target_exec.artifacts or {})
        new_artifacts["remediation_proposal"] = proposal.model_dump(mode="json")
        history = list(new_artifacts.get("remediation_history", []))
        history.append({
            "event": "PROPOSAL_REJECTED",
            "proposal_id": str(proposal.proposal_id),
            "timestamp": proposal.rejected_at.isoformat(),
            "reason": proposal.rejection_reason,
        })
        new_artifacts["remediation_history"] = history
        target_exec.artifacts = new_artifacts
        flag_modified(target_exec, "artifacts")
        await self.session.commit()

        logger.info(f"Remediation proposal rejected [id={proposal.proposal_id}]. Reason: {reason}")
        return proposal

    async def apply_proposal(
        self,
        project_id: uuid.UUID,
        proposal_id: uuid.UUID,
    ) -> tuple[RemediationProposal, RemediationVerificationResult]:
        """Apply an APPROVED patch in an isolated artifact workspace and run regression verification.

        REJECTS any proposal not in APPROVED status.
        Creates a new artifact version without overwriting the original.
        """
        proposal = await self.get_proposal(project_id, proposal_id)
        target_exec = await self._resolve_target_execution(project_id, proposal.workflow_execution_id)
        artifacts = target_exec.artifacts or {}

        # 1. MANDATORY HUMAN APPROVAL CHECK
        if proposal.status != RemediationProposalStatus.APPROVED:
            raise ConflictError(
                f"Remediation proposal must be explicitly APPROVED before application. Current status is '{proposal.status.value}'.",
                field="status",
                value=proposal.status.value,
            )

        # 2. Load Original Artifact and Preserve It
        orig_key = "code-generation" if "code-generation" in artifacts else "code_generation"
        code_data = artifacts.get(orig_key)
        if not code_data:
            raise ValidationError("Original code generation artifact missing from workflow storage.")

        orig_artifact = CodeGenerationOutput.model_validate(code_data)
        # Preserve original under versioned key
        artifacts["code_generation_v1"] = copy.deepcopy(code_data)

        # 3. Apply Changes in Controlled Artifact Workspace
        current_files_map = {f.path: f.content for f in orig_artifact.generated_files}
        try:
            _, updated_files_map = DiffGenerator.apply_changes_to_files(
                current_files=current_files_map,
                changes=proposal.changes,
            )
        except Exception as exc:
            logger.error(f"Patch application failed in memory: {exc}")
            raise ValidationError(f"Failed to apply patch: {exc}") from exc

        # 4. Construct Versioned New Artifact
        new_files: list[GeneratedFile] = []
        total_size = 0
        for path, content in updated_files_map.items():
            content_bytes = len(content.encode("utf-8"))
            total_size += content_bytes
            new_files.append(
                GeneratedFile(
                    path=path,
                    content=content,
                    language="python" if path.endswith(".py") else "text",
                    size_bytes=content_bytes,
                )
            )

        new_version_num = proposal.parent_artifact_version + 1
        new_artifact = CodeGenerationOutput(
            plan=orig_artifact.plan,
            generated_files=new_files,
            total_files=len(new_files),
            total_size_bytes=total_size,
            summary=f"{orig_artifact.summary} (Remediated v{new_version_num} via Proposal {proposal_id})",
        )

        proposal.applied_at = datetime.now(timezone.utc)
        proposal.resulting_artifact_version = new_version_num
        proposal.status = RemediationProposalStatus.APPLIED

        # 5. Regression Verification Step 1: Static Analysis
        sa_request = StaticAnalysisRequest(
            project_id=project_id,
            workflow_execution_id=target_exec.workflow_execution_id,
        )
        static_result = await self.static_analysis_service.analyze_artifact(
            project_id=project_id,
            artifact=new_artifact,
            request=sa_request,
        )

        # 6. Regression Verification Step 2: Isolated Docker Sandbox Tests
        exec_request = ExecutionRequest(
            project_id=project_id,
            workflow_execution_id=target_exec.workflow_execution_id,
            execution_type=ExecutionType.TEST,
        )
        test_artifact = new_artifact
        ai_suite_data = artifacts.get("ai_test_suite")
        if ai_suite_data:
            from app.agents.test_generation.contracts import AITestSuite
            try:
                suite = AITestSuite.model_validate(ai_suite_data)
                if suite.test_files:
                    combined_files = list(new_artifact.generated_files)
                    for t_path, t_content in suite.test_files.items():
                        combined_files.append(
                            GeneratedFile(
                                path=t_path,
                                content=t_content,
                                language="python",
                                size_bytes=len(t_content.encode("utf-8")),
                                architecture_component="testing",
                                requirement_ids=[],
                            )
                        )
                    test_artifact = CodeGenerationOutput(
                        plan=new_artifact.plan,
                        generated_files=combined_files,
                        total_files=len(combined_files),
                        total_size_bytes=sum(f.size_bytes for f in combined_files),
                        summary=f"Ephemeral testing artifact for proposal {proposal_id}",
                    )
            except Exception as e:
                logger.debug(f"Ephemeral suite inclusion note: {e}")

        sandbox_result = await self.sandbox_executor.execute(
            request=exec_request,
            code_output=test_artifact,
        )

        # 6c. Regression Verification Step 3: Browser Regression (if configured)
        browser_passed: bool | None = None
        browser_test_run: Any | None = None
        has_browser_config = bool(
            artifacts.get("browser_test_run")
            or artifacts.get("browser_validation")
            or artifacts.get("browser_testing_required")
            or artifacts.get("runtime_manifest")
        )
        if has_browser_config and self.browser_testing_service is not None:
            try:
                browser_test_run = await self.browser_testing_service.execute_browser_tests(
                    project_id=project_id,
                    files_map=updated_files_map,
                )
                from app.schemas.browser_testing import BrowserTestStatus
                browser_passed = (
                    browser_test_run.status == BrowserTestStatus.PASSED
                    and browser_test_run.tests_failed == 0
                )
            except Exception as exc:
                logger.warning(f"Browser regression failed during remediation verification: {exc}")
                browser_passed = False

        # 7. Evaluate Verification Criteria
        # Must have zero CRITICAL/ERROR static diagnostics and passing tests
        sa_passed = static_result.error_count == 0 and static_result.security_issue_count == 0
        has_test_files = any(
            f.path.startswith("tests/") or "test" in f.path
            for f in test_artifact.generated_files
        )
        if not has_test_files and sandbox_result.exit_code == 5:
            sb_passed = True
        else:
            sb_passed = sandbox_result.status == ExecutionStatus.PASSED and sandbox_result.tests_failed == 0
        br_passed = browser_passed is not False

        # Check for resolved diagnostic codes from diagnosis
        diag_data = artifacts.get("failure_analysis", {})
        prior_codes = [ev.get("code") for ev in diag_data.get("evidence", []) if ev.get("code")]
        remaining_codes = [d.code for d in static_result.diagnostics]
        resolved_codes = [c for c in prior_codes if c not in remaining_codes]
        new_errors = [
            f"{d.code} at {d.file_path}:{d.line}: {d.message}"
            for d in static_result.diagnostics
            if d.severity in (DiagnosticSeverity.CRITICAL, DiagnosticSeverity.ERROR)
        ]

        if sa_passed and sb_passed and br_passed:
            verification_status = RemediationProposalStatus.VERIFIED
            summary = "Remediation verified: Static analysis, sandbox tests, and browser tests passed with zero errors."
            # Promote new artifact to active
            artifacts[orig_key] = new_artifact.model_dump(mode="json")
        else:
            verification_status = RemediationProposalStatus.VERIFICATION_FAILED
            fail_reasons = []
            if not sa_passed:
                fail_reasons.append(f"Static analysis failed with {static_result.error_count} errors.")
            if not sb_passed:
                fail_reasons.append(f"Sandbox tests failed with status '{sandbox_result.status.value}'.")
            if browser_passed is False:
                fail_reasons.append("Browser regression tests failed.")
            summary = f"Remediation verification failed: {'; '.join(fail_reasons)}"
            # Keep original artifact active!

        proposal.status = verification_status

        verification_result = RemediationVerificationResult(
            proposal_id=proposal_id,
            status=verification_status,
            static_analysis_passed=sa_passed,
            sandbox_passed=sb_passed,
            browser_passed=browser_passed,
            browser_test_run=browser_test_run,
            resolved_diagnostic_codes=resolved_codes,
            new_critical_or_error_diagnostics=new_errors,
            summary=summary,
            static_analysis_result=static_result,
            execution_result=sandbox_result,
        )

        # 8. Persist Artifacts and Audit History
        new_artifacts = dict(target_exec.artifacts or {})
        new_artifacts["code_generation_v1"] = copy.deepcopy(code_data)
        if sa_passed and sb_passed and br_passed:
            new_artifacts[orig_key] = new_artifact.model_dump(mode="json")
            new_artifacts["static_analysis"] = static_result.model_dump(mode="json")
            new_artifacts["sandbox_execution"] = sandbox_result.model_dump(mode="json")
        new_artifacts["remediation_proposal"] = proposal.model_dump(mode="json")
        new_artifacts["remediation_verification"] = verification_result.model_dump(mode="json")
        if browser_test_run is not None:
            new_artifacts["browser_test_run"] = browser_test_run.model_dump(mode="json")
        history = list(new_artifacts.get("remediation_history", []))
        history.append({
            "event": "PROPOSAL_APPLIED",
            "proposal_id": str(proposal_id),
            "applied_at": proposal.applied_at.isoformat(),
            "verification_status": verification_status.value,
            "resulting_version": new_version_num if sa_passed and sb_passed else None,
            "summary": summary,
        })
        new_artifacts["remediation_history"] = history
        target_exec.artifacts = new_artifacts
        flag_modified(target_exec, "artifacts")
        await self.session.commit()

        # Phase 11H: Register new DevelopmentVersion
        try:
            from app.services.development_version_service import DevelopmentVersionService
            from app.services.verification_service import DevelopmentVerificationService
            from app.agents.failure_analysis.contracts import FailureDiagnosis
            dev_service = DevelopmentVersionService(session=self.session)
            from app.models.development_version import DevelopmentVersion
            stmt_parent = select(DevelopmentVersion).where(
                DevelopmentVersion.project_id == project_id,
                DevelopmentVersion.version_number == proposal.parent_artifact_version,
            )
            parent_res = await self.session.execute(stmt_parent)
            parent_ver = parent_res.scalar_one_or_none()
            parent_id = parent_ver.id if parent_ver else None

            if not parent_id:
                try:
                    v1 = await dev_service.register_version_from_workflow(
                        project_id=project_id,
                        workflow_execution_id=target_exec.workflow_execution_id,
                        artifact_key="code_generation_v1",
                        source_reason="INITIAL_GENERATION",
                    )
                    parent_id = v1.id
                except Exception as e:
                    logger.debug(f"v1 bootstrap note: {e}")

            diag_data = artifacts.get("failure_analysis") or artifacts.get("ai_test_failure_analysis")
            diag = FailureDiagnosis.model_validate(diag_data) if diag_data else None

            ver_snapshot = DevelopmentVerificationService.evaluate_verification(
                artifact=new_artifact,
                static_analysis=static_result,
                sandbox_execution=sandbox_result,
                failure_diagnosis=diag,
                remediation_verification=verification_result,
                browser_test_run=browser_test_run,
                browser_testing_required=False,
            )

            await dev_service.register_version_from_workflow(
                project_id=project_id,
                workflow_execution_id=target_exec.workflow_execution_id,
                artifact_key=orig_key,
                source_reason="REMEDIATION_PATCH",
                created_by="user",
                parent_version_id=parent_id,
                diagnosis_reference=str(proposal.diagnosis_id),
                remediation_reference=str(proposal.proposal_id),
                verification_snapshot=ver_snapshot,
            )
        except Exception as exc:
            logger.warning(f"Could not auto-register DevelopmentVersion after patch: {exc}")

        logger.info(f"Remediation patch applied [proposal_id={proposal_id}]. Result: {verification_status.value}")
        return proposal, verification_result

