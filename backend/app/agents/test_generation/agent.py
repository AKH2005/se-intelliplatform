"""Test Generation Agent Implementation."""

import logging
from typing import Any
from app.agents.base import AbstractBaseAgent
from app.agents.contracts import AgentMetadata, AgentType, ValidationResult
from app.agents.providers.base import AbstractLLMProvider, LLMMessage, LLMRequest
from app.agents.test_generation.contracts import (
    AITestSuiteCandidate,
    TestCategory,
    TestGenerationInput,
)
from app.agents.test_generation.prompts import (
    SYSTEM_PROMPT,
    build_test_generation_prompt,
)
from app.agents.test_generation.validator import AITestValidator
from app.schemas.context import ProjectContextResponse

logger = logging.getLogger(__name__)


class TestGenerationAgent(AbstractBaseAgent[AITestSuiteCandidate]):
    """AI Agent responsible for generating bounded, structured pytest test suites for generated code.

    Guarantees:
    - Generates test specifications and test code ONLY.
    - Has ZERO execution authority: does not execute tests, invoke Docker, or write to host files.
    - Strictly bound to verified project files, known symbols, and active requirements.
    - Validates test code AST to reject dangerous builtins, network calls, and secrets.
    """

    __test__ = False

    def __init__(self) -> None:
        self._current_input: TestGenerationInput | None = None

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id="test-generation",
            name="AI Test Generation Agent",
            description="Generates structured, executable pytest test suites targeting verified generated software artifacts.",
            version="1.0.0",
            agent_type=AgentType.GENERATION,
        )

    @property
    def output_schema(self) -> type[AITestSuiteCandidate]:
        return AITestSuiteCandidate

    async def initialize(self) -> None:
        """Lifecycle Hook 1: Pre-execution initialization."""
        self._current_input = None

    async def analyze(
        self,
        context: ProjectContextResponse,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Lifecycle Hook 2: Prepare bounded input context and project source map."""
        raw_input = kwargs.get("test_input") or kwargs.get("input")

        if isinstance(raw_input, TestGenerationInput):
            test_input = raw_input
        else:
            code_out = kwargs.get("code_generation") or kwargs.get("code_output")
            if hasattr(code_out, "generated_files"):
                gen_files = code_out.generated_files
            elif isinstance(code_out, list):
                gen_files = code_out
            else:
                gen_files = []

            files_map = {f.path: f.content for f in gen_files if hasattr(f, "path") and hasattr(f, "content")}
            manifest = list(files_map.keys())

            req_ids: list[str] = []
            if context.requirements:
                for r in context.requirements:
                    req_ids.append(str(r.id))
                    if hasattr(r, "title") and r.title:
                        req_ids.append(r.title)

            arch_comps: list[str] = []
            arch_out = kwargs.get("architecture_recommendation")
            if arch_out and hasattr(arch_out, "components"):
                arch_comps = [c.name for c in arch_out.components if hasattr(c, "name")]

            db_entities: list[str] = []
            db_out = kwargs.get("database_design")
            if db_out and hasattr(db_out, "entities"):
                db_entities = [e.name for e in db_out.entities if hasattr(e, "name")]

            test_input = TestGenerationInput(
                project_id=context.project.id,
                workflow_execution_id=kwargs.get("workflow_execution_id"),
                manifest=manifest,
                files=files_map,
                available_requirement_ids=req_ids,
                available_architecture_components=arch_comps,
                available_database_entities=db_entities,
                static_analysis_result=kwargs.get("static_analysis_result"),
                failure_diagnosis=kwargs.get("failure_diagnosis") or kwargs.get("failure_analysis"),
                allowed_categories=kwargs.get("allowed_categories", list(TestCategory)),
            )

        self._current_input = test_input
        return {"test_input": test_input}

    async def generate(
        self,
        analysis_result: dict[str, Any],
        provider: AbstractLLMProvider,
        **kwargs: Any,
    ) -> AITestSuiteCandidate:
        """Lifecycle Hook 3: Invoke LLM provider with structured candidate output schema."""
        test_input: TestGenerationInput = analysis_result["test_input"]
        user_prompt = build_test_generation_prompt(test_input)

        request = LLMRequest(
            messages=[
                LLMMessage(role="system", content=SYSTEM_PROMPT),
                LLMMessage(role="user", content=user_prompt),
            ],
            model=provider.default_model,
            temperature=0.2,  # Controlled creativity for test scenarios while preserving deterministic syntax
            max_tokens=3000,
        )

        candidate = await provider.generate_structured(
            request=request,
            response_model=AITestSuiteCandidate,
        )
        return candidate

    def validate_output(
        self,
        output: AITestSuiteCandidate,
        context: Any = None,
        **kwargs: Any,
    ) -> ValidationResult:
        """Lifecycle Hook 4: Deterministic anti-hallucination and security validation."""
        if not self._current_input:
            return ValidationResult(is_valid=False, errors=["Missing active TestGenerationInput context."])

        return AITestValidator.validate(
            candidate=output,
            analysis_input=self._current_input,
        )
