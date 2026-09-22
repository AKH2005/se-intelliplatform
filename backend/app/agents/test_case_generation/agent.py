"""Test Case Generation Agent Implementation."""

import logging
from typing import Any
from pydantic import BaseModel

from app.agents.base import AbstractBaseAgent
from app.agents.contracts import (
    AgentMetadata,
    AgentType,
    ValidationResult,
)
from app.agents.providers.base import (
    AbstractLLMProvider,
    LLMMessage,
    LLMRequest,
)
from app.agents.test_case_generation.contracts import (
    DEFAULT_TEST_CASE_LIMITATIONS,
    TestCase,
    TestCaseCoverage,
    TestCaseGenerationCandidate,
    TestCaseGenerationOutput,
)
from app.agents.test_case_generation.prompts import (
    SYSTEM_PROMPT,
    build_test_case_prompt,
)
from app.agents.test_case_generation.validation import (
    get_active_requirement_ids,
    validate_test_case_generation_output,
)
from app.models.requirement import RequirementStatus
from app.schemas.context import ProjectContextResponse
from app.schemas.requirement import RequirementResponse

logger = logging.getLogger(__name__)


class TestCaseGenerationAgent(AbstractBaseAgent[TestCaseGenerationOutput]):
    """AI Agent responsible for generating structured test cases from canonical Project Context.

    Generates:
    - Functional, negative, edge-case, and validation test scenarios
    - Ordered, sequential step actions with expected observable behaviors
    - Explicit requirement traceability to active project requirements

    Guarantees:
    - Strictly read-only: Never mutates requirements or database state.
    - Deterministic coverage integrity: The LLM never calculates coverage metrics;
      these are strictly calculated by backend deterministic logic based on active requirements.
    - Single execution authority: Orchestrated exclusively through AgentExecutor.
    """

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id="test-case-generation",
            name="Test Case Generation Agent",
            description="Generates structured, traceable software test cases from canonical project requirements.",
            version="1.0.0",
            agent_type=AgentType.GENERATION,
        )

    @property
    def output_schema(self) -> type[TestCaseGenerationOutput]:
        return TestCaseGenerationOutput

    async def initialize(self) -> None:
        """Lifecycle Hook 1: Pre-execution initialization."""
        pass

    async def analyze(
        self,
        context: ProjectContextResponse,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Lifecycle Hook 2: Extract active requirements from canonical context.

        Filters out DEFERRED and REJECTED requirements.
        """
        active_requirements: list[RequirementResponse] = []
        for req in context.requirements:
            status_val = req.status.value if hasattr(req.status, "value") else str(req.status)
            if status_val not in (RequirementStatus.DEFERRED.value, RequirementStatus.REJECTED.value, "DEFERRED", "REJECTED"):
                active_requirements.append(req)

        return {
            "context": context,
            "active_requirements": active_requirements,
            "active_requirements_count": len(active_requirements),
            "project_name": context.project.name,
            "project_id": str(context.project.id),
        }

    async def generate(
        self,
        analysis_result: dict[str, Any],
        provider: AbstractLLMProvider,
        **kwargs: Any,
    ) -> TestCaseGenerationOutput:
        """Lifecycle Hook 3: Invoke LLM to generate candidate test cases,
        then authoritatively compute deterministic requirement coverage.
        """
        context: ProjectContextResponse = analysis_result["context"]
        active_requirements: list[RequirementResponse] = analysis_result.get("active_requirements", [])
        user_prompt = build_test_case_prompt(context, analysis_result)

        from app.core.config import settings

        model_name = kwargs.get("model", settings.LLM_MODEL)
        request = LLMRequest(
            messages=[
                LLMMessage(role="system", content=SYSTEM_PROMPT),
                LLMMessage(role="user", content=user_prompt),
            ],
            model=model_name,
            temperature=kwargs.get("temperature", 0.0),
        )

        # 1. Request structured candidate from provider
        candidate_or_output = await provider.generate_structured(
            request=request,
            response_model=TestCaseGenerationCandidate,
        )

        # 2. Extract candidate fields safely
        if isinstance(candidate_or_output, TestCaseGenerationOutput):
            candidate_summary = candidate_or_output.summary
            candidate_test_cases = candidate_or_output.test_cases
        elif isinstance(candidate_or_output, TestCaseGenerationCandidate):
            candidate_summary = candidate_or_output.summary
            candidate_test_cases = candidate_or_output.test_cases
        elif isinstance(candidate_or_output, dict):
            candidate_summary = candidate_or_output.get("summary", "Test case generation complete.")
            raw_cases = candidate_or_output.get("test_cases", [])
            candidate_test_cases = [
                tc if isinstance(tc, TestCase) else TestCase.model_validate(tc)
                for tc in raw_cases
            ]
        else:
            candidate_summary = "Test case generation complete."
            candidate_test_cases = []

        # 3. Deterministically compute Authoritative Requirement Coverage
        active_req_ids = get_active_requirement_ids(context)
        covered_req_ids: set[str] = set()

        for tc in candidate_test_cases:
            for req_id_str in tc.requirement_ids:
                req_clean = str(req_id_str).strip()
                if req_clean in active_req_ids:
                    covered_req_ids.add(req_clean)

        total_active = len(active_req_ids)
        requirements_with_tests = len(covered_req_ids)
        requirements_without_tests = total_active - requirements_with_tests
        coverage_percentage = (
            round((requirements_with_tests / total_active) * 100.0, 2)
            if total_active > 0
            else 0.0
        )
        uncovered_ids = sorted(list(active_req_ids - covered_req_ids))

        coverage = TestCaseCoverage(
            total_active_requirements=total_active,
            requirements_with_tests=requirements_with_tests,
            requirements_without_tests=requirements_without_tests,
            coverage_percentage=coverage_percentage,
            uncovered_requirement_ids=uncovered_ids,
        )

        # 4. Construct Final Authoritative Output
        final_output = TestCaseGenerationOutput(
            agent_id=self.metadata.agent_id,
            agent_version=self.metadata.version,
            summary=candidate_summary,
            test_cases=candidate_test_cases,
            total_test_cases=len(candidate_test_cases),
            coverage=coverage,
            limitations=list(DEFAULT_TEST_CASE_LIMITATIONS),
        )

        return final_output

    def validate_output(
        self,
        output: TestCaseGenerationOutput,
        context: ProjectContextResponse,
    ) -> ValidationResult:
        """Lifecycle Hook 4: Deterministic domain validation hook."""
        return validate_test_case_generation_output(output=output, context=context)
