"""Abstract Sandbox Executor Interface."""

from abc import ABC, abstractmethod

from app.agents.code_generation.contracts import CodeGenerationOutput
from app.sandbox.contracts import ExecutionRequest, ExecutionResult


class AbstractSandboxExecutor(ABC):
    """Abstract base class separating WHAT to execute from HOW isolation is provided."""

    @abstractmethod
    async def is_available(self) -> bool:
        """Deterministically detect if the underlying execution runtime is ready."""
        pass

    @abstractmethod
    async def execute(
        self,
        request: ExecutionRequest,
        code_output: CodeGenerationOutput,
    ) -> ExecutionResult:
        """Execute validation or tests against the provided generated code within isolation.

        Guarantees:
        - Must never execute code in the host FastAPI process.
        - Must return structured ExecutionResult.
        """
        pass
