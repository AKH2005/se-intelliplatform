"""AI Test Generation & Ephemeral Sandbox Execution Service."""

import copy
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.agents.code_generation.contracts import (
    CodeGenerationOutput,
    GeneratedFile,
)
from app.agents.execution import AgentExecutor
from app.agents.failure_analysis.contracts import FailureDiagnosis
from app.agents.test_generation.agent import TestGenerationAgent
from app.agents.test_generation.contracts import (
    AITestCaseResult,
    AITestExecutionRequest,
    AITestExecutionResult,
    AITestSuite,
    AITestSuiteCandidate,
    TestCategory,
    TestGenerationInput,
)
from app.agents.test_generation.validator import AITestValidator
from app.core.exceptions import NotFoundError, ValidationError
from app.models.workflow_execution import WorkflowExecution
from app.sandbox.contracts import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    ExecutionType,
    ResourceLimits,
)
from app.sandbox.docker_executor import DockerSandboxExecutor
from app.sandbox.static_analysis.contracts import StaticAnalysisResult
from app.services.context_engine import ProjectContextEngine
from app.services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)


class AITestService:
    """Orchestrates AI test generation, deterministic validation, and ephemeral sandbox execution."""

    def __init__(
        self,
        session: AsyncSession,
        workflow_service: WorkflowService,
        executor: AgentExecutor,
        context_engine: ProjectContextEngine,
        sandbox_executor: DockerSandboxExecutor | None = None,
    ) -> None:
        self.session = session
        self.workflow_service = workflow_service
        self.executor = executor
        self.context_engine = context_engine
        self.agent = TestGenerationAgent()
        self.sandbox_executor = sandbox_executor or DockerSandboxExecutor()

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
        candidates = res.scalars().all()
        if not candidates:
            raise NotFoundError("WorkflowExecution", str(project_id))
        for c in candidates:
            if c.artifacts and ("code_generation" in c.artifacts or "code-generation" in c.artifacts):
                return c
        return candidates[0]

    async def generate_tests(
        self,
        project_id: uuid.UUID,
        workflow_execution_id: uuid.UUID | None = None,
        allowed_categories: list[TestCategory] | None = None,
    ) -> AITestSuite:
        """Generate, validate, and compile an AI test suite for a verified code generation artifact.

        The original code artifact remains unchanged. The suite is stored in execution artifacts.
        """
        target_exec = await self._resolve_target_execution(project_id, workflow_execution_id)
        artifacts = target_exec.artifacts or {}

        # 1. Authoritative Code Generation Artifact
        code_data = artifacts.get("code_generation") or artifacts.get("code-generation")
        if not code_data:
            raise ValidationError(
                "No code generation artifact found. Please complete code generation before generating tests."
            )
        code_output = CodeGenerationOutput.model_validate(code_data)
        files_map = {f.path: f.content for f in code_output.generated_files}
        manifest = list(files_map.keys())

        # 2. Build Project Context
        project_context = await self.context_engine.generate_context(project_id)

        # 3. Upstream Context Identifiers
        req_ids: list[str] = []
        if project_context.requirements:
            for r in project_context.requirements:
                req_ids.append(str(r.id))
                if hasattr(r, "title") and r.title:
                    req_ids.append(r.title)

        arch_comps: list[str] = []
        arch_data = artifacts.get("architecture_recommendation") or artifacts.get("architecture-recommendation")
        if arch_data and isinstance(arch_data, dict):
            for c in arch_data.get("components", []):
                if isinstance(c, dict) and "name" in c:
                    arch_comps.append(c["name"])

        db_entities: list[str] = []
        db_data = artifacts.get("database_design") or artifacts.get("database-design")
        if db_data and isinstance(db_data, dict):
            for e in db_data.get("entities", []):
                if isinstance(e, dict) and "name" in e:
                    db_entities.append(e["name"])

        # Static Analysis Context
        static_analysis = None
        sa_data = artifacts.get("static_analysis") or artifacts.get("static-analysis")
        if sa_data:
            try:
                static_analysis = StaticAnalysisResult.model_validate(sa_data)
            except Exception:
                pass

        # Failure Diagnosis Context
        failure_diagnosis = None
        fa_data = artifacts.get("failure_analysis") or artifacts.get("failure-analysis")
        if fa_data:
            try:
                failure_diagnosis = FailureDiagnosis.model_validate(fa_data)
            except Exception:
                pass

        test_input = TestGenerationInput(
            project_id=project_id,
            workflow_execution_id=target_exec.workflow_execution_id,
            manifest=manifest,
            files=files_map,
            available_requirement_ids=req_ids,
            available_architecture_components=arch_comps,
            available_database_entities=db_entities,
            static_analysis_result=static_analysis,
            failure_diagnosis=failure_diagnosis,
            allowed_categories=allowed_categories or list(TestCategory),
        )

        # 4. Authoritative Agent Execution
        result = await self.executor.execute(
            self.agent,
            project_context,
            session=self.session,
            test_input=test_input,
        )

        if result.status != "COMPLETED" or not result.output:
            err_msg = result.error.message if result.error else "Unknown test generation failure"
            raise ValidationError(f"Test generation validation failed: {err_msg}")

        # 5. Compile Candidate into Authoritative AITestSuite
        candidate: AITestSuiteCandidate = result.output
        suite = AITestValidator.compile_candidate_to_suite(
            candidate=candidate,
            analysis_input=test_input,
            raw_metadata=result.metadata,
        )

        # 6. Persist to WorkflowExecution artifacts
        suite_dict = suite.model_dump(mode="json")
        artifacts_copy = dict(artifacts)
        artifacts_copy["ai_test_suite"] = suite_dict
        suite_history = list(artifacts_copy.get("ai_test_suites", []))
        suite_history.append(suite_dict)
        artifacts_copy["ai_test_suites"] = suite_history

        target_exec.artifacts = artifacts_copy
        flag_modified(target_exec, "artifacts")
        await self.session.commit()
        await self.session.refresh(target_exec)

        logger.info(
            f"Successfully generated AI test suite [{suite.suite_id}] with {suite.test_count} tests "
            f"for project [{project_id}]"
        )
        return suite

    async def get_test_suite(
        self,
        project_id: uuid.UUID,
        suite_id: uuid.UUID,
        workflow_execution_id: uuid.UUID | None = None,
    ) -> AITestSuite:
        """Retrieve a specific AI test suite by ID."""
        target_exec = await self._resolve_target_execution(project_id, workflow_execution_id)
        artifacts = target_exec.artifacts or {}

        latest_suite = artifacts.get("ai_test_suite")
        if latest_suite and str(latest_suite.get("suite_id")) == str(suite_id):
            return AITestSuite.model_validate(latest_suite)

        for s in artifacts.get("ai_test_suites", []):
            if str(s.get("suite_id")) == str(suite_id):
                return AITestSuite.model_validate(s)

        raise NotFoundError("AITestSuite", str(suite_id))

    async def get_latest_test_suite(
        self,
        project_id: uuid.UUID,
        workflow_execution_id: uuid.UUID | None = None,
    ) -> AITestSuite | None:
        """Retrieve the latest generated AI test suite for this project."""
        target_exec = await self._resolve_target_execution(project_id, workflow_execution_id)
        artifacts = target_exec.artifacts or {}
        latest = artifacts.get("ai_test_suite")
        if not latest:
            return None
        return AITestSuite.model_validate(latest)

    async def execute_tests(
        self,
        project_id: uuid.UUID,
        suite_id: uuid.UUID,
        timeout_seconds: int = 30,
        workflow_execution_id: uuid.UUID | None = None,
    ) -> AITestExecutionResult:
        """Execute a validated AI test suite in an isolated ephemeral sandbox workspace.

        Security & Architectural Guarantees:
        1. Materializes an ephemeral in-memory CodeGenerationOutput combining original files + test files.
        2. The original project artifact is NEVER mutated.
        3. Tests execute ONLY inside the hardened Docker sandbox with network disabled, non-root, read-only rootfs.
        4. Does NOT trigger autonomous repair loops if tests fail.
        """
        suite = await self.get_test_suite(project_id, suite_id, workflow_execution_id)
        target_exec = await self._resolve_target_execution(project_id, workflow_execution_id)
        artifacts = target_exec.artifacts or {}

        code_data = artifacts.get("code_generation") or artifacts.get("code-generation")
        if not code_data:
            raise ValidationError("Original code generation artifact missing from workflow execution.")
        original_output = CodeGenerationOutput.model_validate(code_data)

        # 1. Assemble Ephemeral Artifact in Memory
        combined_files: list[GeneratedFile] = list(original_output.generated_files)
        for t_path, t_content in suite.test_files.items():
            content_bytes = t_content.encode("utf-8")
            combined_files.append(
                GeneratedFile(
                    path=t_path,
                    content=t_content,
                    language="python",
                    size_bytes=len(content_bytes),
                    architecture_component="testing",
                    requirement_ids=[],
                )
            )

        ephemeral_output = CodeGenerationOutput(
            plan=original_output.plan,
            generated_files=combined_files,
            total_files=len(combined_files),
            total_size_bytes=sum(f.size_bytes for f in combined_files),
            summary=f"Ephemeral testing artifact for suite {suite.suite_id}",
        )

        # 2. Build Sandbox Execution Request targeting the generated test file
        primary_test_target = list(suite.test_files.keys())[0] if suite.test_files else "tests/"
        req = ExecutionRequest(
            project_id=project_id,
            workflow_execution_id=target_exec.workflow_execution_id,
            execution_type=ExecutionType.TEST,
            test_target=primary_test_target,
            limits=ResourceLimits(timeout_seconds=min(max(5, timeout_seconds), 60)),
        )

        # 3. Execute in Hardened Docker Sandbox
        sandbox_res: ExecutionResult = await self.sandbox_executor.execute(req, ephemeral_output)

        # 4. Parse Individual Test Results and Diagnostic Summaries from Pytest Output
        individual_results, failure_summaries = self._parse_detailed_test_results(
            sandbox_res.stdout,
            sandbox_res.stderr,
            suite.tests,
        )

        execution_result = AITestExecutionResult(
            execution_id=sandbox_res.execution_id,
            suite_id=suite.suite_id,
            project_id=project_id,
            workflow_execution_id=target_exec.workflow_execution_id,
            status=sandbox_res.status,
            exit_code=sandbox_res.exit_code,
            duration_seconds=sandbox_res.duration_seconds,
            tests_total=sandbox_res.tests_total,
            tests_passed=sandbox_res.tests_passed,
            tests_failed=sandbox_res.tests_failed,
            tests_skipped=max(0, sandbox_res.tests_total - sandbox_res.tests_passed - sandbox_res.tests_failed),
            stdout=sandbox_res.stdout,
            stderr=sandbox_res.stderr,
            failure_summaries=failure_summaries,
            test_results=individual_results,
            executed_at=datetime.now(timezone.utc),
            metadata=sandbox_res.metadata,
        )

        # 5. Persist Execution Result without mutating original code artifact
        artifacts_copy = dict(artifacts)
        artifacts_copy["ai_test_execution"] = execution_result.model_dump(mode="json")
        target_exec.artifacts = artifacts_copy
        flag_modified(target_exec, "artifacts")
        await self.session.commit()
        await self.session.refresh(target_exec)

        logger.info(
            f"AI Test Suite [{suite.suite_id}] execution completed with status [{execution_result.status.value}] "
            f"({execution_result.tests_passed}/{execution_result.tests_total} passed)"
        )
        return execution_result

    def _parse_detailed_test_results(
        self,
        stdout: str,
        stderr: str,
        tests: list[Any],
    ) -> tuple[list[AITestCaseResult], list[str]]:
        """Parse test names and pass/fail statuses from pytest output."""
        individual_results: list[AITestCaseResult] = []
        failure_summaries: list[str] = []

        # Pytest verbose line regex: e.g. tests/test_ai_generated.py::test_name PASSED [ 50%]
        line_pattern = re.compile(r"::(test_[a-zA-Z0-9_]+)\s+(PASSED|FAILED|ERROR|SKIPPED)")

        parsed_names: dict[str, str] = {}
        for line in stdout.splitlines():
            m = line_pattern.search(line)
            if m:
                test_name = m.group(1)
                test_status = m.group(2)
                parsed_names[test_name] = test_status

        # Map to known tests in suite
        for t in tests:
            status = parsed_names.get(t.name, "PASSED" if "1 passed" in stdout and len(tests) == 1 else "UNKNOWN")
            individual_results.append(
                AITestCaseResult(
                    name=t.name,
                    status=status,
                    duration_seconds=0.0,
                    message=None,
                )
            )

        # Extract failure sections from pytest stdout
        in_failure_section = False
        current_failure_lines: list[str] = []

        for line in stdout.splitlines():
            if "=== FAILURES ===" in line or "=== ERRORS ===" in line:
                in_failure_section = True
                continue
            if in_failure_section and line.startswith("==="):
                in_failure_section = False
                if current_failure_lines:
                    failure_summaries.append("\n".join(current_failure_lines[:10]))
                    current_failure_lines = []
                continue
            if in_failure_section:
                current_failure_lines.append(line)

        if current_failure_lines:
            failure_summaries.append("\n".join(current_failure_lines[:10]))

        return individual_results, failure_summaries
