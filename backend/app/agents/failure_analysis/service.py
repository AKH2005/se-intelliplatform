"""Service Orchestrating Failure Analysis, Artifact Resolution, and Provenance Persistence."""

import logging
import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.agents.execution import AgentExecutor
from app.agents.failure_analysis.agent import FailureAnalysisAgent
from app.agents.failure_analysis.contracts import (
    DiagnosticSeverity,
    FailureAnalysisInput,
    FailureConfidence,
    FailureDiagnosis,
    FailureSource,
    FailureType,
)
from app.core.exceptions import ValidationError
from app.models.workflow_execution import WorkflowExecution, WorkflowStatus
from app.services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)


class FailureAnalysisService:
    """Orchestrates Failure Analysis execution, authoritative artifact resolution, and persistence."""

    def __init__(
        self,
        session: AsyncSession,
        workflow_service: WorkflowService,
        executor: AgentExecutor,
    ) -> None:
        self.session = session
        self.workflow_service = workflow_service
        self.executor = executor
        self.agent = FailureAnalysisAgent()

    @staticmethod
    def should_trigger_analysis(
        execution_result: Any | None,
        static_analysis_result: Any | None,
        ai_test_execution_result: Any | None = None,
        browser_test_run: Any | None = None,
    ) -> tuple[bool, str]:
        """Deterministically determine if failure analysis should be triggered."""
        # 1. Check Browser Test Run (Phase 11J Stage 4)
        if browser_test_run is not None:
            status = getattr(browser_test_run, "status", None)
            tests_failed = getattr(browser_test_run, "tests_failed", 0)
            status_val = status.value if hasattr(status, "value") else str(status)

            if status_val in ("FAILED", "TIMEOUT", "STARTUP_FAILED", "BROWSER_ERROR", "RESOURCE_LIMIT", "VALIDATION_ERROR"):
                return True, f"Browser test execution status is '{status_val}'."
            if tests_failed > 0:
                return True, f"Browser test execution reported {tests_failed} failed test(s)."

        # 2. Check AI Test Execution Result (Phase 11F/11G)
        if ai_test_execution_result is not None:
            status = getattr(ai_test_execution_result, "status", None)
            exit_code = getattr(ai_test_execution_result, "exit_code", 0)
            tests_failed = getattr(ai_test_execution_result, "tests_failed", 0)
            status_val = status.value if hasattr(status, "value") else str(status)

            if status_val in ("FAILED", "TIMEOUT", "RESOURCE_LIMIT", "SANDBOX_ERROR", "VALIDATION_ERROR"):
                return True, f"AI test execution status is '{status_val}'."
            if exit_code is not None and exit_code != 0:
                return True, f"AI test execution exited with non-zero code {exit_code}."
            if tests_failed > 0:
                return True, f"AI test execution reported {tests_failed} failed test(s)."

        # 2. Check Sandbox Execution Result
        if execution_result is not None:
            status = getattr(execution_result, "status", None)
            exit_code = getattr(execution_result, "exit_code", 0)
            tests_failed = getattr(execution_result, "tests_failed", 0)
            status_val = status.value if hasattr(status, "value") else str(status)

            if status_val in ("FAILED", "TIMEOUT", "RESOURCE_LIMIT", "SANDBOX_ERROR", "VALIDATION_ERROR"):
                return True, f"Sandbox test execution status is '{status_val}'."
            if exit_code is not None and exit_code != 0:
                return True, f"Sandbox test execution exited with non-zero code {exit_code}."
            if tests_failed > 0:
                return True, f"Sandbox test execution reported {tests_failed} failed test(s)."

        # 3. Check Static Analysis Result
        if static_analysis_result is not None:
            status = getattr(static_analysis_result, "status", None)
            err_count = getattr(static_analysis_result, "error_count", 0)
            sec_count = getattr(static_analysis_result, "security_issue_count", 0)
            syn_count = getattr(static_analysis_result, "syntax_error_count", 0)
            status_val = status.value if hasattr(status, "value") else str(status)

            if status_val in ("VALIDATION_ERROR", "ANALYSIS_ERROR"):
                return True, f"Static analysis status is '{status_val}'."
            if err_count > 0 or sec_count > 0 or syn_count > 0:
                return True, f"Static analysis contains {err_count} error(s) and {sec_count} security issue(s)."

        return False, "All execution and static analysis checks passed with zero errors or failures."

    async def _resolve_workflow_execution(
        self,
        project_id: uuid.UUID,
        workflow_execution_id: uuid.UUID | None = None,
    ) -> WorkflowExecution:
        """Resolve authoritative WorkflowExecution record."""
        if workflow_execution_id is not None:
            exec_record = await self.workflow_service.get_workflow_execution(workflow_execution_id)
            if exec_record.project_id != project_id:
                raise ValidationError(
                    message=f"WorkflowExecution '{workflow_execution_id}' does not belong to project '{project_id}'."
                )
            return exec_record

        # Latest workflow execution with code-generation artifact
        stmt = (
            select(WorkflowExecution)
            .where(WorkflowExecution.project_id == project_id)
            .where(
                WorkflowExecution.status.in_(
                    [WorkflowStatus.COMPLETED, WorkflowStatus.PARTIAL_SUCCESS, WorkflowStatus.FAILED]
                )
            )
            .order_by(WorkflowExecution.started_at.desc())
        )
        result = await self.session.execute(stmt)
        executions = list(result.scalars().all())

        for ex in executions:
            if "code-generation" in ex.artifacts or "code_generation" in ex.artifacts:
                return ex

        raise ValidationError(
            message=f"No workflow execution with generated code artifacts found for project '{project_id}'."
        )

    async def analyze_failure(
        self,
        project_id: uuid.UUID,
        workflow_execution_id: uuid.UUID | None = None,
        force: bool = False,
        failure_source: FailureSource | None = None,
    ) -> FailureDiagnosis:
        """Execute failure analysis against verified workflow artifacts."""
        # 1. Verify project exists and generate canonical context
        project_context = await self.workflow_service.context_engine.generate_context(project_id)

        # 2. Resolve workflow execution
        target_exec = await self._resolve_workflow_execution(
            project_id=project_id,
            workflow_execution_id=workflow_execution_id,
        )

        artifacts = target_exec.artifacts or {}
        exec_res_dict = artifacts.get("sandbox_execution")
        static_res_dict = artifacts.get("static_analysis")
        code_out_dict = artifacts.get("code-generation") or artifacts.get("code_generation")
        req_out_dict = artifacts.get("requirement-analysis")
        arch_out_dict = artifacts.get("architecture-recommendation")
        db_out_dict = artifacts.get("database-design")
        ai_test_exec_dict = artifacts.get("ai_test_execution")
        ai_test_suite_dict = artifacts.get("ai_test_suite")

        # Convert dictionaries to typed contracts if necessary
        from app.sandbox.contracts import ExecutionResult
        from app.sandbox.static_analysis.contracts import StaticAnalysisResult
        from app.agents.code_generation.contracts import CodeGenerationOutput
        from app.agents.requirement_analysis.contracts import RequirementAnalysisOutput
        from app.agents.architecture_recommendation.contracts import ArchitectureRecommendationOutput
        from app.agents.database_design.contracts import DatabaseDesignOutput
        from app.agents.test_generation.contracts import AITestExecutionResult, AITestSuite

        exec_res = ExecutionResult.model_validate(exec_res_dict) if exec_res_dict else None
        static_res = StaticAnalysisResult.model_validate(static_res_dict) if static_res_dict else None
        code_out = CodeGenerationOutput.model_validate(code_out_dict) if code_out_dict else None
        req_out = RequirementAnalysisOutput.model_validate(req_out_dict) if req_out_dict else None
        arch_out = ArchitectureRecommendationOutput.model_validate(arch_out_dict) if arch_out_dict else None
        db_out = DatabaseDesignOutput.model_validate(db_out_dict) if db_out_dict else None
        ai_test_exec = AITestExecutionResult.model_validate(ai_test_exec_dict) if ai_test_exec_dict else None
        ai_test_suite = AITestSuite.model_validate(ai_test_suite_dict) if ai_test_suite_dict else None

        browser_run_dict = artifacts.get("browser_test_run") or artifacts.get("browser_validation")
        from app.schemas.browser_testing import BrowserTestRun
        browser_run = BrowserTestRun.model_validate(browser_run_dict) if browser_run_dict else None

        # 3. Deterministic Trigger Check
        should_run, reason = self.should_trigger_analysis(exec_res, static_res, ai_test_exec, browser_run)
        if not should_run and not force:
            logger.info(f"Skipping failure analysis for project '{project_id}': {reason}")
            # Return a clean / not-applicable diagnosis without calling LLM
            clean_diagnosis = FailureDiagnosis(
                failure_type=FailureType.UNKNOWN,
                failure_source=failure_source or FailureSource.SANDBOX,
                title="No Failure Detected",
                summary="Execution, static analysis, and browser validation passed with zero errors or failures. Diagnostic analysis was skipped.",
                root_cause="The generated project exhibits zero detected compilation, linting, security, browser, or test failures.",
                severity=DiagnosticSeverity.INFO,
                affected_files=[],
                evidence=[],
                claims=[],
                requirement_links=[],
                architecture_links=[],
                database_links=[],
                suggested_remediation="No remediation required; all verification criteria satisfied.",
                limitations=["No failing signals were present to diagnose."],
                confidence=FailureConfidence.HIGH,
                model_metadata={"trigger_status": "SKIPPED_CLEAN", "reason": reason},
            )
            # Store in artifacts
            artifacts_copy = dict(target_exec.artifacts or {})
            artifacts_copy["failure_analysis"] = clean_diagnosis.model_dump(mode="json")
            target_exec.artifacts = artifacts_copy
            flag_modified(target_exec, "artifacts")
            await self.session.commit()
            return clean_diagnosis

        # 4. Execute Failure Analysis via AgentExecutor
        agent_result = await self.executor.execute(
            agent=self.agent,
            context=project_context,
            session=self.session,
            context_snapshot_id=target_exec.context_snapshot_id,
            context_version=target_exec.context_version,
            workflow_execution_id=target_exec.workflow_execution_id,
            execution_result=exec_res,
            static_analysis_result=static_res,
            code_generation=code_out,
            requirement_analysis=req_out,
            architecture_recommendation=arch_out,
            database_design=db_out,
            ai_test_execution=ai_test_exec,
            ai_test_suite=ai_test_suite,
            browser_test_run=browser_run,
            failure_source=failure_source,
        )

        diagnosis = agent_result.output
        if not diagnosis:
            from app.core.exceptions import ValidationError
            errs = agent_result.validation_result.errors if agent_result.validation_result else ["Failure analysis agent produced no output"]
            raise ValidationError(f"Failure analysis validation failed: {errs}")
        diagnosis.diagnosis_id = agent_result.execution_id

        # 5. Persist Diagnosis into WorkflowExecution Artifacts
        artifacts_copy = dict(target_exec.artifacts or {})
        artifacts_copy["failure_analysis"] = diagnosis.model_dump(mode="json")
        if diagnosis.failure_source == FailureSource.AI_TEST:
            artifacts_copy["ai_test_failure_analysis"] = diagnosis.model_dump(mode="json")
        elif diagnosis.failure_source == FailureSource.BROWSER:
            artifacts_copy["browser_failure_analysis"] = diagnosis.model_dump(mode="json")
        target_exec.artifacts = artifacts_copy
        flag_modified(target_exec, "artifacts")
        await self.session.commit()

        return diagnosis
