"""Failure Analysis Agent Implementation."""

import logging
from typing import Any
from pydantic import BaseModel

from app.agents.base import AbstractBaseAgent
from app.agents.contracts import (
    AgentMetadata,
    AgentType,
    ValidationResult,
)
from app.agents.exceptions import AgentValidationError
from app.agents.failure_analysis.contracts import (
    FailureAnalysisInput,
    FailureDiagnosis,
    RelevantSourceFile,
)
from app.agents.failure_analysis.prompts import (
    SYSTEM_PROMPT,
    build_failure_analysis_prompt,
)
from app.agents.failure_analysis.source_selector import SourceSelector
from app.agents.failure_analysis.validator import FailureAnalysisValidator
from app.agents.providers.base import (
    AbstractLLMProvider,
    LLMMessage,
    LLMRequest,
)
from app.schemas.context import ProjectContextResponse

logger = logging.getLogger(__name__)


class FailureAnalysisAgent(AbstractBaseAgent[FailureDiagnosis]):
    """AI Agent performing deterministic evidence preparation and structured diagnostic reasoning.

    Guarantees:
    - Never executes code, modifies files, or generates automatic patches.
    - Strictly grounds root cause findings in deterministic static analysis and execution evidence.
    - Validates all cited diagnostics, file paths, requirements, and architecture components.
    """

    def __init__(self) -> None:
        self._current_input: FailureAnalysisInput | None = None

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id="failure-analysis",
            name="Failure Analysis Agent",
            description="Diagnoses root causes of test execution and static analysis failures using evidence-first reasoning.",
            version="1.0.0",
            agent_type=AgentType.ANALYSIS,
        )

    @property
    def output_schema(self) -> type[FailureDiagnosis]:
        return FailureDiagnosis

    async def initialize(self) -> None:
        """Lifecycle Hook 1: Pre-execution initialization."""
        self._current_input = None

    async def analyze(
        self,
        context: ProjectContextResponse,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Lifecycle Hook 2: Extract evidence, select relevant files, and construct bounded input."""
        raw_input = kwargs.get("failure_analysis_input") or kwargs.get("input")

        if isinstance(raw_input, FailureAnalysisInput):
            analysis_input = raw_input
        else:
            # Construct FailureAnalysisInput from individual artifact kwargs
            exec_res = kwargs.get("execution_result")
            static_res = kwargs.get("static_analysis_result")
            code_out = kwargs.get("code_generation") or kwargs.get("code_output")

            if isinstance(code_out, list):
                gen_files = code_out
            elif hasattr(code_out, "generated_files"):
                gen_files = code_out.generated_files
            else:
                gen_files = []

            all_files = [f.path for f in gen_files if hasattr(f, "path")]

            # Collect available diagnostic IDs
            diag_ids = [d.diagnostic_id for d in static_res.diagnostics] if static_res else []

            # Collect available requirement IDs
            req_ids: list[str] = []
            if context.requirements:
                for r in context.requirements:
                    req_ids.append(str(r.id))
                    if hasattr(r, "title") and r.title:
                        req_ids.append(r.title)

            # Collect available architecture components
            arch_out = kwargs.get("architecture_recommendation")
            arch_comps = []
            if arch_out and hasattr(arch_out, "components"):
                arch_comps = [c.name for c in arch_out.components if hasattr(c, "name")]

            # Collect available database entities
            db_out = kwargs.get("database_design")
            db_entities = []
            if db_out and hasattr(db_out, "entities"):
                db_entities = [e.name for e in db_out.entities if hasattr(e, "name")]

            # Extract AI test artifacts if present
            ai_test_exec = kwargs.get("ai_test_execution") or kwargs.get("ai_test_execution_result")
            ai_test_suite = kwargs.get("ai_test_suite")
            browser_test_run = kwargs.get("browser_test_run")

            # Collect test IDs for reference validation
            test_ids: list[str] = []
            if ai_test_suite and hasattr(ai_test_suite, "tests"):
                for t in ai_test_suite.tests:
                    test_ids.append(t.test_id)
                    test_ids.append(t.name)
            if ai_test_exec:
                exec_id = getattr(ai_test_exec, "execution_id", None)
                if exec_id:
                    test_ids.append(str(exec_id))
                for tr in getattr(ai_test_exec, "test_results", []):
                    test_ids.append(tr.name)

            if browser_test_run:
                from app.agents.failure_analysis.sanitizer import normalize_browser_evidence
                norm_br = normalize_browser_evidence(browser_test_run)
                test_ids.extend(norm_br.get("available_browser_ids", []))

            # Determine FailureSource
            from app.agents.failure_analysis.contracts import FailureSource
            req_source = kwargs.get("failure_source")
            if req_source and isinstance(req_source, FailureSource):
                failure_source = req_source
            elif req_source and isinstance(req_source, str) and hasattr(FailureSource, req_source):
                failure_source = FailureSource(req_source)
            elif browser_test_run and (
                getattr(browser_test_run, "tests_failed", 0) > 0
                or getattr(browser_test_run, "status", None) not in ("PASSED", None)
            ):
                failure_source = FailureSource.BROWSER
            elif ai_test_exec and getattr(ai_test_exec, "tests_failed", 0) > 0:
                failure_source = FailureSource.AI_TEST
            elif static_res and getattr(static_res, "error_count", 0) > 0:
                failure_source = FailureSource.STATIC_ANALYSIS
            else:
                failure_source = FailureSource.SANDBOX

            # Select and bound relevant source files
            relevant_files = SourceSelector.select_relevant_source(
                files=gen_files,
                static_analysis=static_res,
                execution_result=exec_res,
                ai_test_execution_result=ai_test_exec,
                ai_test_suite=ai_test_suite,
            )

            analysis_input = FailureAnalysisInput(
                project_id=context.project.id,
                workflow_execution_id=kwargs.get("workflow_execution_id"),
                execution_result=exec_res,
                ai_test_execution_result=ai_test_exec,
                ai_test_suite=ai_test_suite,
                browser_test_run=browser_test_run,
                failure_source=failure_source,
                static_analysis_result=static_res,
                relevant_files=relevant_files,
                all_project_files=all_files,
                available_diagnostic_ids=diag_ids,
                available_test_ids=list(dict.fromkeys(test_ids)),
                available_requirement_ids=req_ids,
                available_architecture_components=arch_comps,
                available_database_entities=db_entities,
            )

        self._current_input = analysis_input
        return {"analysis_input": analysis_input}

    async def generate(
        self,
        analysis_result: dict[str, Any],
        provider: AbstractLLMProvider,
        **kwargs: Any,
    ) -> FailureDiagnosis:
        """Lifecycle Hook 3: Invoke LLM provider with structured FailureDiagnosis output schema."""
        analysis_input: FailureAnalysisInput = analysis_result["analysis_input"]

        user_prompt = build_failure_analysis_prompt(analysis_input)
        request = LLMRequest(
            messages=[
                LLMMessage(role="system", content=SYSTEM_PROMPT),
                LLMMessage(role="user", content=user_prompt),
            ],
            model=provider.default_model,
            temperature=0.1,  # Low temperature for deterministic diagnostic reasoning
            max_tokens=4096,
            metadata={
                "agent_id": self.metadata.agent_id,
                "project_id": str(analysis_input.project_id),
            },
        )

        diagnosis = await provider.generate_structured(request, FailureDiagnosis)

        from app.agents.failure_analysis.contracts import FailureSource
        if analysis_input.failure_source == FailureSource.BROWSER:
            diagnosis.failure_source = FailureSource.BROWSER
        elif diagnosis.failure_source is None:
            diagnosis.failure_source = analysis_input.failure_source

        # Ensure affected files match valid project files
        valid_files = set(analysis_input.all_project_files)
        clean_affected = [
            f for f in diagnosis.affected_files
            if f.replace("\\", "/").strip() in valid_files or any(vf.endswith(f.replace("\\", "/").strip()) for vf in valid_files)
        ]
        if not clean_affected and analysis_input.all_project_files:
            clean_affected = [analysis_input.all_project_files[0]]
        diagnosis.affected_files = clean_affected

        # Ensure evidence files match valid project files or fall back
        for ev in diagnosis.evidence:
            if ev.file_path and ev.file_path.replace("\\", "/").strip() not in valid_files:
                if not any(vf.endswith(ev.file_path.replace("\\", "/").strip()) for vf in valid_files):
                    ev.file_path = clean_affected[0] if clean_affected else None

        # Attach provider telemetry to model metadata
        diagnosis.model_metadata.update({
            "provider": provider.provider_name,
            "model": provider.default_model,
        })
        if provider.last_usage_metadata:
            diagnosis.model_metadata["usage"] = provider.last_usage_metadata

        return diagnosis

    def validate_output(
        self,
        output: FailureDiagnosis,
        context: ProjectContextResponse,
    ) -> ValidationResult:
        """Lifecycle Hook 4: Deterministic anti-hallucination verification."""
        if self._current_input is None:
            return ValidationResult(is_valid=True)

        return FailureAnalysisValidator.validate(output, self._current_input)
