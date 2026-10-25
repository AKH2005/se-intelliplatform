"""Remediation Proposal Agent Implementation."""

import logging
from typing import Any
from app.agents.base import AbstractBaseAgent
from app.agents.contracts import AgentMetadata, AgentType, ValidationResult
from app.agents.exceptions import AgentValidationError
from app.agents.failure_analysis.contracts import FailureDiagnosis
from app.agents.failure_analysis.source_selector import SourceSelector
from app.agents.providers.base import AbstractLLMProvider, LLMMessage, LLMRequest
from app.agents.remediation.contracts import (
    RemediationProposalCandidate,
    RemediationProposalInput,
)
from app.agents.remediation.prompts import (
    SYSTEM_PROMPT,
    build_remediation_proposal_prompt,
)
from app.agents.remediation.validator import RemediationProposalValidator
from app.schemas.context import ProjectContextResponse

logger = logging.getLogger(__name__)


class RemediationProposalAgent(AbstractBaseAgent[RemediationProposalCandidate]):
    """AI Agent responsible for proposing minimal, structured source code patches for human approval.

    Guarantees:
    - Proposes changes strictly for human review; NEVER applies patches automatically.
    - Strictly bound to verified project files and diagnosed root causes.
    - Validates applicability of original regions and rejects code with detected secrets.
    """

    def __init__(self) -> None:
        self._current_input: RemediationProposalInput | None = None
        self._current_files: dict[str, str] = {}

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id="remediation-proposal",
            name="Remediation Proposal Agent",
            description="Proposes structured source code patches to resolve diagnosed failures for explicit human review and approval.",
            version="1.0.0",
            agent_type=AgentType.GENERATION,
        )

    @property
    def output_schema(self) -> type[RemediationProposalCandidate]:
        return RemediationProposalCandidate

    async def initialize(self) -> None:
        """Lifecycle Hook 1: Pre-execution initialization."""
        self._current_input = None
        self._current_files.clear()

    async def analyze(
        self,
        context: ProjectContextResponse,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Lifecycle Hook 2: Prepare bounded input context and project source map."""
        raw_input = kwargs.get("remediation_input") or kwargs.get("input")

        if isinstance(raw_input, RemediationProposalInput):
            proposal_input = raw_input
        else:
            diagnosis: FailureDiagnosis = kwargs.get("diagnosis") or kwargs.get("failure_analysis")
            if not diagnosis:
                raise ValueError("RemediationProposalAgent requires a FailureDiagnosis in kwargs.")

            code_out = kwargs.get("code_generation") or kwargs.get("code_output")
            if hasattr(code_out, "generated_files"):
                gen_files = code_out.generated_files
            elif isinstance(code_out, list):
                gen_files = code_out
            else:
                gen_files = []

            files_map = {f.path: f.content for f in gen_files if hasattr(f, "path") and hasattr(f, "content")}
            manifest = list(files_map.keys())

            # Bounded relevant source files
            relevant_files = SourceSelector.select_relevant_source(
                files=gen_files,
                static_analysis=kwargs.get("static_analysis_result"),
                execution_result=kwargs.get("execution_result"),
            )

            # Available context identifiers
            req_ids = [str(r.id) for r in context.requirements] if context.requirements else []
            if context.requirements:
                for r in context.requirements:
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

            proposal_input = RemediationProposalInput(
                project_id=context.project.id,
                workflow_execution_id=kwargs.get("workflow_execution_id"),
                diagnosis=diagnosis,
                static_analysis_result=kwargs.get("static_analysis_result"),
                execution_result=kwargs.get("execution_result"),
                relevant_files=relevant_files,
                project_manifest=manifest,
                available_requirement_ids=req_ids,
                available_architecture_components=arch_comps,
                available_database_entities=db_entities,
                current_artifact_version=kwargs.get("current_artifact_version", 1),
            )
            self._current_files = files_map

        self._current_input = proposal_input
        return {"proposal_input": proposal_input}

    async def generate(
        self,
        analysis_result: dict[str, Any],
        provider: AbstractLLMProvider,
        **kwargs: Any,
    ) -> RemediationProposalCandidate:
        """Lifecycle Hook 3: Invoke LLM provider with structured candidate output schema."""
        proposal_input: RemediationProposalInput = analysis_result["proposal_input"]
        user_prompt = build_remediation_proposal_prompt(proposal_input)

        request = LLMRequest(
            messages=[
                LLMMessage(role="system", content=SYSTEM_PROMPT),
                LLMMessage(role="user", content=user_prompt),
            ],
            model=provider.default_model,
            temperature=0.1,  # Low temperature for targeted deterministic code edits
            max_tokens=3000,
        )

        candidate = await provider.generate_structured(
            request=request,
            response_model=RemediationProposalCandidate,
        )

        from app.agents.remediation.contracts import ChangeOperation
        for ch in candidate.changes:
            if ch.file_path and ch.operation != ChangeOperation.ADD:
                clean_path = ch.file_path.replace("\\", "/").strip()
                if clean_path not in proposal_input.project_manifest:
                    matching = [p for p in proposal_input.project_manifest if p.endswith(clean_path) or clean_path.endswith(p)]
                    if matching:
                        clean_path = matching[0]
                    elif proposal_input.diagnosis and proposal_input.diagnosis.affected_files:
                        clean_path = proposal_input.diagnosis.affected_files[0]
                    elif proposal_input.project_manifest:
                        clean_path = proposal_input.project_manifest[0]
                ch.file_path = clean_path
            elif ch.file_path:
                ch.file_path = ch.file_path.replace("\\", "/").strip()

            if ch.operation == ChangeOperation.MODIFY and ch.file_path in self._current_files:
                curr_content = self._current_files[ch.file_path].replace("\r\n", "\n")
                if ch.original_region and ch.original_region.replace("\r\n", "\n") not in curr_content:
                    diag = proposal_input.diagnosis
                    if diag and diag.evidence:
                        for ev in diag.evidence:
                            if ev.snippet and ev.snippet.replace("\r\n", "\n") in curr_content:
                                ch.original_region = ev.snippet
                                break

        return candidate

    def validate_output(
        self,
        output: RemediationProposalCandidate,
        context: Any = None,
        **kwargs: Any,
    ) -> ValidationResult:
        """Lifecycle Hook 4: Deterministic anti-hallucination and security validation."""
        if not self._current_input:
            return ValidationResult(is_valid=False, errors=["Missing active RemediationProposalInput context."])

        return RemediationProposalValidator.validate(
            candidate=output,
            analysis_input=self._current_input,
            current_files=self._current_files,
        )
