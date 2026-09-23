"""AI Code Review Agent Implementation."""

import logging
from typing import Any
from pydantic import BaseModel

from app.agents.base import AbstractBaseAgent
from app.agents.code_review.analyzer import PythonASTAnalyzer, SecretScanner
from app.agents.code_review.contracts import (
    DEFAULT_CODE_REVIEW_LIMITATIONS,
    CodeFile,
    CodeReviewCandidate,
    CodeReviewFinding,
    CodeReviewInput,
    CodeReviewOutput,
    CodeReviewSummary,
    FindingCategory,
    FindingSeverity,
    FindingSource,
)
from app.agents.code_review.prompts import (
    SYSTEM_PROMPT,
    build_code_review_prompt,
)
from app.agents.code_review.validation import (
    validate_code_review_input,
    validate_code_review_output,
)
from app.agents.contracts import (
    AgentMetadata,
    AgentType,
    ValidationResult,
)
from app.agents.exceptions import AgentValidationError
from app.agents.providers.base import (
    AbstractLLMProvider,
    LLMMessage,
    LLMRequest,
)
from app.models.requirement import RequirementStatus
from app.schemas.context import ProjectContextResponse
from app.schemas.requirement import RequirementResponse

logger = logging.getLogger(__name__)


class CodeReviewAgent(AbstractBaseAgent[CodeReviewOutput]):
    """AI Agent responsible for deterministic static analysis and contextual code review.

    Combines:
    - Mandatory deterministic credential/secret scanning with pre-LLM redaction
    - Deterministic standard-library Python AST syntax and security rule checking
    - AI-powered semantic and architectural alignment review against active requirements
    - Unified structured output with clear provenance (STATIC_ANALYSIS, AI_REVIEW, HYBRID)

    Guarantees:
    - Never executes reviewed source code or dynamic suggestions.
    - Authoritative metric and line verification enforced strictly by backend.
    - Zero persistence of raw source code or detected credentials in audit logs.
    """

    def __init__(self) -> None:
        self._file_contents_map: dict[str, str] = {}

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id="code-review",
            name="AI Code Review Agent",
            description="Performs deterministic static AST analysis, credential scanning, and AI-powered contextual code review.",
            version="1.0.0",
            agent_type=AgentType.REVIEW,
        )

    @property
    def output_schema(self) -> type[CodeReviewOutput]:
        return CodeReviewOutput

    async def initialize(self) -> None:
        """Lifecycle Hook 1: Pre-execution initialization."""
        self._file_contents_map.clear()

    async def analyze(
        self,
        context: ProjectContextResponse,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Lifecycle Hook 2: Deterministic input validation, secret scanning, and AST analysis."""
        # 1. Extract and normalize code_input from kwargs
        raw_input = kwargs.get("code_input") or kwargs.get("input")
        if raw_input is None and "files" in kwargs:
            raw_input = {"files": kwargs["files"], "review_scope": kwargs.get("review_scope")}

        if raw_input is None:
            raise AgentValidationError(
                message="CodeReviewAgent requires 'code_input' containing source files to review.",
                validation_errors=["Missing required 'code_input' argument in agent execution."],
            )

        if isinstance(raw_input, CodeReviewInput):
            code_input = raw_input
        elif isinstance(raw_input, dict):
            try:
                code_input = CodeReviewInput.model_validate(raw_input)
            except Exception as exc:
                raise AgentValidationError(
                    message=f"Invalid CodeReviewInput schema: {exc}",
                    validation_errors=[str(exc)],
                ) from exc
        else:
            raise AgentValidationError(
                message=f"Unsupported code_input type '{type(raw_input).__name__}'. Expected CodeReviewInput or dict.",
                validation_errors=["Invalid input type."],
            )

        # 2. Strict Input Boundary Validation
        validate_code_review_input(code_input)

        # 3. Cache original file contents for deterministic validation hook
        self._file_contents_map = {f.file_path: f.content for f in code_input.files}

        # 4. Mandatory Secret Scanning & Pre-LLM Redaction
        static_findings: list[CodeReviewFinding] = []
        redacted_files: list[CodeFile] = []

        for original_file in code_input.files:
            redacted_content, secret_findings = SecretScanner.scan_and_redact(
                file_path=original_file.file_path,
                content=original_file.content,
            )
            static_findings.extend(secret_findings)

            # Redacted file object passed to prompts
            redacted_files.append(
                CodeFile(
                    file_path=original_file.file_path,
                    language=original_file.language,
                    content=redacted_content,
                    metadata=original_file.metadata,
                )
            )

        # 5. Deterministic Python AST Analysis
        for file in code_input.files:
            if file.language.strip().lower() in ("python", "py"):
                ast_findings = PythonASTAnalyzer.analyze(
                    file_path=file.file_path,
                    content=file.content,
                )
                static_findings.extend(ast_findings)

        # 6. Collate Active Requirements from Canonical Context
        active_requirements: list[RequirementResponse] = []
        for req in context.requirements:
            status_val = req.status.value if hasattr(req.status, "value") else str(req.status)
            if status_val not in (
                RequirementStatus.DEFERRED.value,
                RequirementStatus.REJECTED.value,
                "DEFERRED",
                "REJECTED",
            ):
                active_requirements.append(req)

        return {
            "context": context,
            "code_input": code_input,
            "redacted_files": redacted_files,
            "static_findings": static_findings,
            "active_requirements": active_requirements,
            "review_scope": code_input.review_scope,
            "file_contents_map": self._file_contents_map,
        }

    async def generate(
        self,
        analysis_result: dict[str, Any],
        provider: AbstractLLMProvider,
        **kwargs: Any,
    ) -> CodeReviewOutput:
        """Lifecycle Hook 3: Invoke LLM provider, merge findings, and compute authoritative metrics."""
        context: ProjectContextResponse = analysis_result["context"]
        redacted_files: list[CodeFile] = analysis_result["redacted_files"]
        static_findings: list[CodeReviewFinding] = analysis_result["static_findings"]
        active_requirements: list[RequirementResponse] = analysis_result.get("active_requirements", [])
        review_scope: str | None = analysis_result.get("review_scope")
        file_contents_map: dict[str, str] = analysis_result["file_contents_map"]

        user_prompt = build_code_review_prompt(
            context=context,
            files=redacted_files,
            static_findings=static_findings,
            active_requirements=active_requirements,
            review_scope=review_scope,
        )

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

        # 1. Request structured candidate from LLM provider
        candidate_or_output = await provider.generate_structured(
            request=request,
            response_model=CodeReviewCandidate,
        )

        # 2. Extract candidate fields safely
        if isinstance(candidate_or_output, CodeReviewOutput):
            candidate_summary = candidate_or_output.summary
            candidate_findings = candidate_or_output.findings
        elif isinstance(candidate_or_output, CodeReviewCandidate):
            candidate_summary = candidate_or_output.summary
            candidate_findings = candidate_or_output.findings
        elif isinstance(candidate_or_output, dict):
            candidate_summary = candidate_or_output.get("summary", "Code review completed.")
            raw_findings = candidate_or_output.get("findings", [])
            candidate_findings = [
                f if isinstance(f, CodeReviewFinding) else CodeReviewFinding.model_validate(f)
                for f in raw_findings
            ]
        else:
            candidate_summary = "Code review completed."
            candidate_findings = []

        # 3. Merge Static and AI Findings with Strict Line and Evidence Verification
        all_findings: list[CodeReviewFinding] = []
        seen_fingerprints: set[tuple[str, int, int, str]] = set()

        # Add all deterministic static findings first
        for sf in static_findings:
            fp = (
                sf.file_path,
                sf.line_start,
                sf.line_end,
                (sf.rule_id or sf.title).strip().lower(),
            )
            if fp not in seen_fingerprints:
                seen_fingerprints.add(fp)
                all_findings.append(sf)

        # Validate and merge AI findings
        for af in candidate_findings:
            # File authority: reject if file is not in input
            if af.file_path not in file_contents_map:
                logger.warning(f"Discarding AI finding for non-existent file: {af.file_path}")
                continue

            file_lines = file_contents_map[af.file_path].splitlines()
            total_lines = len(file_lines) if file_lines else 1

            # Line bounds: reject hallucinated line numbers
            if af.line_start < 1 or af.line_end < af.line_start or af.line_end > total_lines:
                logger.warning(
                    f"Discarding AI finding with invalid line bounds {af.line_start}-{af.line_end} "
                    f"for file {af.file_path} (total lines: {total_lines})"
                )
                continue

            # Evidence matching: verify evidence text appears in target lines
            target_slice = "\n".join(file_lines[af.line_start - 1 : af.line_end])
            normalized_slice = "".join(target_slice.split())
            normalized_evidence = "".join(af.evidence.split())

            if normalized_evidence and normalized_evidence not in normalized_slice:
                logger.warning(
                    f"Discarding AI finding with hallucinated evidence for {af.file_path}:{af.line_start}"
                )
                continue

            # Ensure provenance is marked as AI_REVIEW
            validated_ai_finding = af.model_copy(
                update={"source": FindingSource.AI_REVIEW}
            )

            # Check if this AI finding enriches an existing static finding at identical line
            matched_static = False
            for idx, existing in enumerate(all_findings):
                if (
                    existing.source == FindingSource.STATIC_ANALYSIS
                    and existing.file_path == validated_ai_finding.file_path
                    and existing.line_start == validated_ai_finding.line_start
                    and existing.line_end == validated_ai_finding.line_end
                ):
                    # Hybrid finding
                    all_findings[idx] = existing.model_copy(
                        update={
                            "source": FindingSource.HYBRID,
                            "recommendation": validated_ai_finding.recommendation or existing.recommendation,
                        }
                    )
                    matched_static = True
                    break

            if not matched_static:
                fp = (
                    validated_ai_finding.file_path,
                    validated_ai_finding.line_start,
                    validated_ai_finding.line_end,
                    validated_ai_finding.title.strip().lower(),
                )
                if fp not in seen_fingerprints:
                    seen_fingerprints.add(fp)
                    all_findings.append(validated_ai_finding)

        # 4. Normalize Finding IDs Sequentially (CR-001, CR-002, ...)
        finalized_findings: list[CodeReviewFinding] = []
        for idx, finding in enumerate(all_findings, start=1):
            normalized_finding = finding.model_copy(
                update={"finding_id": f"CR-{idx:03d}"}
            )
            finalized_findings.append(normalized_finding)

        # 5. Authoritatively Calculate Summary Metrics
        by_severity: dict[str, int] = {s.value: 0 for s in FindingSeverity}
        by_category: dict[str, int] = {c.value: 0 for c in FindingCategory}
        static_count = 0
        ai_count = 0

        for f in finalized_findings:
            by_severity[f.severity.value] = by_severity.get(f.severity.value, 0) + 1
            by_category[f.category.value] = by_category.get(f.category.value, 0) + 1
            if f.source == FindingSource.STATIC_ANALYSIS:
                static_count += 1
            elif f.source == FindingSource.AI_REVIEW:
                ai_count += 1

        summary_metrics = CodeReviewSummary(
            files_analyzed_count=len(redacted_files),
            total_findings=len(finalized_findings),
            findings_by_severity=by_severity,
            findings_by_category=by_category,
            static_findings_count=static_count,
            ai_findings_count=ai_count,
        )

        files_reviewed = [f.file_path for f in redacted_files]

        # 6. Construct Final Output Model
        return CodeReviewOutput(
            agent_id=self.metadata.agent_id,
            agent_version=self.metadata.version,
            summary=candidate_summary,
            files_reviewed=files_reviewed,
            findings=finalized_findings,
            metrics=summary_metrics,
            limitations=list(DEFAULT_CODE_REVIEW_LIMITATIONS),
        )

    def validate_output(
        self,
        output: CodeReviewOutput,
        context: ProjectContextResponse,
    ) -> ValidationResult:
        """Lifecycle Hook 4: Deterministic domain validation hook."""
        return validate_code_review_output(
            output=output,
            context=context,
            file_contents_map=self._file_contents_map,
        )
