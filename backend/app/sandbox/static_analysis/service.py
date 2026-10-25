"""Deterministic Static Analysis Service orchestrating AST, Dependency, Discovery, and Ruff."""

import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.code_generation.contracts import CodeGenerationOutput
from app.agents.contracts import AgentExecutionStatus
from app.core.exceptions import ValidationError
from app.models.agent_audit import AgentExecutionAudit
from app.models.workflow_execution import WorkflowExecution, WorkflowStatus
from app.sandbox.base import AbstractSandboxExecutor
from app.sandbox.static_analysis.ast_analyzer import ASTAnalyzer, ParsedModuleData
from app.sandbox.static_analysis.contracts import (
    DiagnosticCategory,
    DiagnosticSeverity,
    StaticAnalysisRequest,
    StaticAnalysisResult,
    StaticAnalysisStatus,
    StaticDiagnostic,
)
from app.sandbox.static_analysis.dependency_analyzer import DependencyAnalyzer
from app.sandbox.static_analysis.ruff_analyzer import RuffAnalyzer
from app.sandbox.static_analysis.test_discovery import TestDiscovery
from app.sandbox.validation import validate_artifact_for_execution
from app.services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)


class StaticAnalysisService:
    """Orchestrates deterministic static analysis across security, AST, dependencies, and Ruff."""

    def __init__(
        self,
        session: AsyncSession | None = None,
        workflow_service: WorkflowService | None = None,
        executor: AbstractSandboxExecutor | None = None,
    ) -> None:
        self.session = session
        self.workflow_service = workflow_service
        self.executor = executor
        self.ast_analyzer = ASTAnalyzer()
        self.dependency_analyzer = DependencyAnalyzer()
        self.test_discovery = TestDiscovery()
        self.ruff_analyzer = RuffAnalyzer(executor=executor) if executor is not None else None

    async def _resolve_code_artifact(
        self,
        project_id: uuid.UUID,
        workflow_execution_id: uuid.UUID | None = None,
    ) -> tuple[CodeGenerationOutput, WorkflowExecution | None]:
        """Resolve authoritative CodeGenerationOutput from persisted workflow executions."""
        if workflow_execution_id is not None:
            exec_record = await self.workflow_service.get_workflow_execution(workflow_execution_id)
            if exec_record.project_id != project_id:
                raise ValidationError(
                    message=f"WorkflowExecution '{workflow_execution_id}' does not belong to project '{project_id}'."
                )

            artifact_dict = exec_record.artifacts.get("code-generation") or exec_record.artifacts.get("code_generation")
            if not artifact_dict:
                raise ValidationError(
                    message=f"WorkflowExecution '{workflow_execution_id}' does not contain a 'code-generation' artifact."
                )

            try:
                code_output = CodeGenerationOutput.model_validate(artifact_dict)
            except Exception as exc:
                raise ValidationError(
                    message=f"Artifact in WorkflowExecution '{workflow_execution_id}' is not a valid CodeGenerationOutput: {exc}"
                )

            return code_output, exec_record

        # Latest completed execution with code-generation artifact
        stmt = (
            select(WorkflowExecution)
            .where(WorkflowExecution.project_id == project_id)
            .where(
                WorkflowExecution.status.in_(
                    [WorkflowStatus.COMPLETED, WorkflowStatus.PARTIAL_SUCCESS]
                )
            )
            .order_by(WorkflowExecution.started_at.desc())
        )
        result = await self.session.execute(stmt)
        executions = list(result.scalars().all())

        for ex in executions:
            artifact_dict = ex.artifacts.get("code-generation") or ex.artifacts.get("code_generation")
            if artifact_dict:
                try:
                    code_output = CodeGenerationOutput.model_validate(artifact_dict)
                    return code_output, ex
                except Exception:
                    continue

        raise ValidationError(
            message=f"No completed workflow execution with a valid code-generation artifact found for project '{project_id}'."
        )

    def _deduplicate_diagnostics(self, diagnostics: list[StaticDiagnostic]) -> list[StaticDiagnostic]:
        """Deduplicate findings sharing category, code, file, line, and column."""
        unique_list: list[StaticDiagnostic] = []
        seen: set[tuple[str, str, str | None, int | None, int | None]] = set()

        for d in diagnostics:
            key = (d.category.value, d.code, d.file_path, d.line, d.column)
            if key not in seen:
                seen.add(key)
                unique_list.append(d)

        return unique_list

    async def analyze(self, request: StaticAnalysisRequest) -> StaticAnalysisResult:
        """Execute deterministic multi-stage static analysis on generated project artifact."""
        if self.session is None or self.workflow_service is None:
            raise RuntimeError("Database session and workflow service are required to resolve artifacts.")

        # 1. Verify project exists
        await self.workflow_service.context_engine._get_project(request.project_id)

        # 2. Resolve code artifact
        code_output, target_exec = await self._resolve_code_artifact(
            project_id=request.project_id,
            workflow_execution_id=request.workflow_execution_id,
        )

        return await self.analyze_artifact(
            project_id=request.project_id,
            artifact=code_output,
            request=request,
            target_exec=target_exec,
        )

    async def analyze_artifact(
        self,
        project_id: uuid.UUID,
        artifact: CodeGenerationOutput,
        request: StaticAnalysisRequest,
        target_exec: WorkflowExecution | None = None,
    ) -> StaticAnalysisResult:
        """Execute deterministic pipeline on an in-memory CodeGenerationOutput artifact."""
        start_time = time.monotonic()
        analysis_id = uuid.uuid4()
        code_output = artifact

        all_paths = [f.path for f in code_output.generated_files]
        diagnostics: list[StaticDiagnostic] = []

        # 3. Stage 1: Security & Path Validation (Phase 11A/11B re-used)
        pre_val_errors = validate_artifact_for_execution(code_output)
        fatal_security = False

        for err in pre_val_errors:
            err_lower = err.lower()
            if "secret" in err_lower:
                fatal_security = True
                diagnostics.append(
                    StaticDiagnostic(
                        category=DiagnosticCategory.SECURITY,
                        severity=DiagnosticSeverity.CRITICAL,
                        code="SEC_KEY_DETECTED",
                        message=err,
                        source="secret_scanner",
                    )
                )
            elif "path safety" in err_lower or "traversal" in err_lower:
                fatal_security = True
                diagnostics.append(
                    StaticDiagnostic(
                        category=DiagnosticCategory.SECURITY,
                        severity=DiagnosticSeverity.CRITICAL,
                        code="PATH_TRAVERSAL",
                        message=err,
                        source="path_validator",
                    )
                )
            elif "forbidden dynamic" in err_lower:
                fatal_security = True
                diagnostics.append(
                    StaticDiagnostic(
                        category=DiagnosticCategory.SECURITY,
                        severity=DiagnosticSeverity.CRITICAL,
                        code="FORBIDDEN_CALL",
                        message=err,
                        source="security_validator",
                    )
                )
            else:
                diagnostics.append(
                    StaticDiagnostic(
                        category=DiagnosticCategory.STRUCTURE,
                        severity=DiagnosticSeverity.ERROR,
                        code="VALIDATION_FAILED",
                        message=err,
                        source="artifact_validator",
                    )
                )

        # If fatal security or structural violations occurred, do NOT proceed into tooling
        if fatal_security:
            duration = round(time.monotonic() - start_time, 4)
            return self._build_result(
                analysis_id=analysis_id,
                project_id=request.project_id,
                workflow_execution_id=target_exec.workflow_execution_id if target_exec else request.workflow_execution_id,
                status=StaticAnalysisStatus.VALIDATION_ERROR,
                duration_seconds=duration,
                diagnostics=diagnostics,
                files_analyzed=0,
                files_skipped=len(all_paths),
                test_file_count=0,
                summary="Static analysis halted: Fatal security or path traversal violations detected.",
            )

        # 4. Stage 2: AST Analysis (Single-pass parse)
        parsed_modules: list[ParsedModuleData] = []
        requirements_content: str | None = None
        has_syntax_errors = False

        for f in code_output.generated_files:
            if f.path == "requirements.txt" or f.path.endswith("/requirements.txt"):
                requirements_content = f.content

            if f.path.endswith(".py"):
                mod_data, ast_diags = self.ast_analyzer.analyze_file(f.path, f.content)
                parsed_modules.append(mod_data)
                diagnostics.extend(ast_diags)
                if any(d.category == DiagnosticCategory.SYNTAX for d in ast_diags):
                    has_syntax_errors = True

        # 5. Stage 3: Import & Dependency Analysis
        dep_diags = self.dependency_analyzer.analyze(
            modules=parsed_modules,
            all_file_paths=all_paths,
            requirements_content=requirements_content,
        )
        diagnostics.extend(dep_diags)

        # 6. Stage 4: Test Discovery
        test_files, _total_tests, test_diags = self.test_discovery.discover(parsed_modules)
        diagnostics.extend(test_diags)

        # 7. Stage 5: Ruff Linting via Sandbox (Skip if fatal syntax errors to avoid redundant crashes)
        if not has_syntax_errors:
            from app.sandbox.contracts import ExecutionRequest
            ruff_req = ExecutionRequest(
                project_id=request.project_id,
                workflow_execution_id=target_exec.workflow_execution_id if target_exec else request.workflow_execution_id,
            )
            ruff_diags = await self.ruff_analyzer.analyze(ruff_req, code_output)
            diagnostics.extend(ruff_diags)

        # 8. Deduplicate and Aggregate
        unique_diags = self._deduplicate_diagnostics(diagnostics)
        duration = round(time.monotonic() - start_time, 4)

        # Determine terminal status
        error_count = sum(1 for d in unique_diags if d.severity in (DiagnosticSeverity.ERROR, DiagnosticSeverity.CRITICAL))
        warning_count = sum(1 for d in unique_diags if d.severity == DiagnosticSeverity.WARNING)

        if any(d.severity == DiagnosticSeverity.CRITICAL for d in unique_diags):
            status = StaticAnalysisStatus.VALIDATION_ERROR
        elif has_syntax_errors:
            status = StaticAnalysisStatus.VALIDATION_ERROR
        elif error_count > 0 or warning_count > 0:
            status = StaticAnalysisStatus.ISSUES_FOUND
        else:
            status = StaticAnalysisStatus.PASSED

        summary = (
            f"Static analysis {status.value}: {error_count} error(s), "
            f"{warning_count} warning(s) across {len(all_paths)} file(s)."
        )

        result = self._build_result(
            analysis_id=analysis_id,
            project_id=request.project_id,
            workflow_execution_id=target_exec.workflow_execution_id if target_exec else request.workflow_execution_id,
            status=status,
            duration_seconds=duration,
            diagnostics=unique_diags,
            files_analyzed=len(all_paths),
            files_skipped=0,
            test_file_count=len(test_files),
            summary=summary,
        )

        # 9. Audit Persistence
        await self._persist_audit(result=result, target_exec=target_exec)

        return result

    def _build_result(
        self,
        analysis_id: uuid.UUID,
        project_id: uuid.UUID,
        workflow_execution_id: uuid.UUID | None,
        status: StaticAnalysisStatus,
        duration_seconds: float,
        diagnostics: list[StaticDiagnostic],
        files_analyzed: int,
        files_skipped: int,
        test_file_count: int,
        summary: str,
    ) -> StaticAnalysisResult:
        """Construct the strongly typed StaticAnalysisResult."""
        error_count = sum(1 for d in diagnostics if d.severity in (DiagnosticSeverity.ERROR, DiagnosticSeverity.CRITICAL))
        warning_count = sum(1 for d in diagnostics if d.severity == DiagnosticSeverity.WARNING)
        info_count = sum(1 for d in diagnostics if d.severity == DiagnosticSeverity.INFO)

        security_count = sum(1 for d in diagnostics if d.category == DiagnosticCategory.SECURITY)
        syntax_count = sum(1 for d in diagnostics if d.category == DiagnosticCategory.SYNTAX)
        lint_count = sum(1 for d in diagnostics if d.category == DiagnosticCategory.LINT)

        return StaticAnalysisResult(
            analysis_id=analysis_id,
            project_id=project_id,
            workflow_execution_id=workflow_execution_id,
            status=status,
            duration_seconds=duration_seconds,
            diagnostics=diagnostics,
            files_analyzed=files_analyzed,
            files_skipped=files_skipped,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            security_issue_count=security_count,
            syntax_error_count=syntax_count,
            lint_issue_count=lint_count,
            test_file_count=test_file_count,
            summary=summary,
            metadata={"analyzer_version": "1.0.0", "ruff_version": "0.8.4"},
        )

    async def _persist_audit(
        self,
        result: StaticAnalysisResult,
        target_exec: WorkflowExecution | None,
    ) -> None:
        """Persist execution audit and update workflow execution artifacts."""
        if self.session is None:
            return

        completed_at = datetime.now(timezone.utc)
        started_at = completed_at - timedelta(seconds=max(result.duration_seconds, 0.001))

        audit_status = (
            AgentExecutionStatus.COMPLETED
            if result.status == StaticAnalysisStatus.PASSED
            else AgentExecutionStatus.FAILED
        )

        audit_record = AgentExecutionAudit(
            execution_id=result.analysis_id,
            project_id=result.project_id,
            agent_id="static-analysis-runner",
            agent_version="1.0.0",
            status=audit_status,
            context_snapshot_id=target_exec.context_snapshot_id if target_exec else None,
            context_version=target_exec.context_version if target_exec else None,
            started_at=started_at,
            completed_at=completed_at,
            output_summary=result.summary,
            error_code=None if result.status == StaticAnalysisStatus.PASSED else result.status.value,
            error_message=result.summary if result.status != StaticAnalysisStatus.PASSED else None,
            metadata_payload=result.model_dump(mode="json"),
        )
        self.session.add(audit_record)

        if target_exec:
            current_artifacts = dict(target_exec.artifacts)
            current_artifacts["static_analysis"] = result.model_dump(mode="json")
            target_exec.artifacts = current_artifacts

        await self.session.commit()
