"""Deterministic Mock Sandbox Executor for Offline Testing."""

import uuid
from typing import Any

from app.agents.code_generation.contracts import CodeGenerationOutput
from app.sandbox.base import AbstractSandboxExecutor
from app.sandbox.contracts import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    ExecutionType,
)
from app.sandbox.validation import validate_artifact_for_execution


class MockSandboxExecutor(AbstractSandboxExecutor):
    """Offline deterministic sandbox executor for automated tests."""

    def __init__(
        self,
        default_status: ExecutionStatus = ExecutionStatus.PASSED,
        is_available_flag: bool = True,
        mock_stdout: str = "1 passed in 0.05s",
        mock_stderr: str = "",
        mock_tests_passed: int = 1,
        mock_tests_failed: int = 0,
        mock_exit_code: int = 0,
    ) -> None:
        self.default_status = default_status
        self.is_available_flag = is_available_flag
        self.mock_stdout = mock_stdout
        self.mock_stderr = mock_stderr
        self.mock_tests_passed = mock_tests_passed
        self.mock_tests_failed = mock_tests_failed
        self.mock_exit_code = mock_exit_code
        self.last_request: ExecutionRequest | None = None
        self.last_code_output: CodeGenerationOutput | None = None

    async def is_available(self) -> bool:
        return self.is_available_flag

    async def execute(
        self,
        request: ExecutionRequest,
        code_output: CodeGenerationOutput,
    ) -> ExecutionResult:
        self.last_request = request
        self.last_code_output = code_output

        # 1. Deterministic validation check
        validation_errors = validate_artifact_for_execution(
            code_output,
            test_target=request.test_target,
        )
        if validation_errors:
            return ExecutionResult(
                execution_id=uuid.uuid4(),
                project_id=request.project_id,
                workflow_execution_id=request.workflow_execution_id,
                execution_type=request.execution_type,
                status=ExecutionStatus.VALIDATION_ERROR,
                exit_code=None,
                duration_seconds=0.01,
                stdout="",
                stderr="",
                is_truncated=False,
                tests_passed=0,
                tests_failed=0,
                tests_total=0,
                validation_errors=validation_errors,
                metadata={"mock": True},
            )

        if not self.is_available_flag:
            return ExecutionResult(
                execution_id=uuid.uuid4(),
                project_id=request.project_id,
                workflow_execution_id=request.workflow_execution_id,
                execution_type=request.execution_type,
                status=ExecutionStatus.SANDBOX_UNAVAILABLE,
                exit_code=None,
                duration_seconds=0.01,
                stdout="",
                stderr="Mock sandbox runtime is marked unavailable.",
                is_truncated=False,
                tests_passed=0,
                tests_failed=0,
                tests_total=0,
                validation_errors=[],
                metadata={"mock": True},
            )

        if request.execution_type == ExecutionType.STATIC_VALIDATE:
            return ExecutionResult(
                execution_id=uuid.uuid4(),
                project_id=request.project_id,
                workflow_execution_id=request.workflow_execution_id,
                execution_type=request.execution_type,
                status=ExecutionStatus.PASSED,
                exit_code=0,
                duration_seconds=0.02,
                stdout="Static analysis and AST verification passed.",
                stderr="",
                is_truncated=False,
                tests_passed=1,
                tests_failed=0,
                tests_total=1,
                validation_errors=[],
                metadata={"mock": True},
            )

        if request.execution_type == ExecutionType.LINT:
            lint_stdout = self.mock_stdout if self.mock_stdout.startswith("[") else "[]"
            return ExecutionResult(
                execution_id=uuid.uuid4(),
                project_id=request.project_id,
                workflow_execution_id=request.workflow_execution_id,
                execution_type=request.execution_type,
                status=self.default_status if self.default_status in (ExecutionStatus.TIMEOUT, ExecutionStatus.RESOURCE_LIMIT, ExecutionStatus.SANDBOX_ERROR) else ExecutionStatus.PASSED,
                exit_code=self.mock_exit_code,
                duration_seconds=0.05,
                stdout=lint_stdout,
                stderr=self.mock_stderr,
                is_truncated=False,
                tests_passed=0,
                tests_failed=0,
                tests_total=0,
                validation_errors=[],
                metadata={"mock": True},
            )

        # Handle programmed statuses
        if self.default_status == ExecutionStatus.TIMEOUT:
            return ExecutionResult(
                execution_id=uuid.uuid4(),
                project_id=request.project_id,
                workflow_execution_id=request.workflow_execution_id,
                execution_type=request.execution_type,
                status=ExecutionStatus.TIMEOUT,
                exit_code=-1,
                duration_seconds=float(request.limits.timeout_seconds),
                stdout="",
                stderr="Mock timeout reached.",
                is_truncated=False,
                tests_passed=0,
                tests_failed=0,
                tests_total=0,
                validation_errors=[],
                metadata={"mock": True},
            )

        if self.default_status == ExecutionStatus.RESOURCE_LIMIT:
            return ExecutionResult(
                execution_id=uuid.uuid4(),
                project_id=request.project_id,
                workflow_execution_id=request.workflow_execution_id,
                execution_type=request.execution_type,
                status=ExecutionStatus.RESOURCE_LIMIT,
                exit_code=137,
                duration_seconds=0.5,
                stdout="",
                stderr="Mock memory limit exceeded.",
                is_truncated=False,
                tests_passed=0,
                tests_failed=0,
                tests_total=0,
                validation_errors=[],
                metadata={"mock": True},
            )

        return ExecutionResult(
            execution_id=uuid.uuid4(),
            project_id=request.project_id,
            workflow_execution_id=request.workflow_execution_id,
            execution_type=request.execution_type,
            status=self.default_status,
            exit_code=self.mock_exit_code,
            duration_seconds=0.1,
            stdout=self.mock_stdout,
            stderr=self.mock_stderr,
            is_truncated=False,
            tests_passed=self.mock_tests_passed,
            tests_failed=self.mock_tests_failed,
            tests_total=self.mock_tests_passed + self.mock_tests_failed,
            validation_errors=[],
            metadata={"mock": True},
        )
