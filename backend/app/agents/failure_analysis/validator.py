"""Deterministic Output Validation and Anti-Hallucination Guardrails for Failure Diagnosis."""

import logging
import re
from app.agents.contracts import ValidationResult
from app.agents.failure_analysis.contracts import FailureAnalysisInput, FailureDiagnosis

logger = logging.getLogger(__name__)


class FailureAnalysisValidator:
    """Validates FailureDiagnosis against authoritative ground truth and rejects hallucinations and code patches."""

    DIFF_MARKERS = [
        "diff --git",
        "--- a/",
        "+++ b/",
        "@@ -",
        "<<<<<<<",
        ">>>>>>>",
        "Index:",
        "====",
    ]

    REPLACEMENT_PATTERNS = [
        re.compile(r"(?i)\breplace\b.+?\bwith\b"),
        re.compile(r"(?i)\bsubstitute\b.+?\bwith\b"),
        re.compile(r"(?i)\bchange\s+['\"`].+?['\"`]\s+to\b"),
    ]

    INSERTION_PATTERNS = [
        re.compile(r"(?i)\b(?:add|insert)\s+(?:this|the|a)\s+line\b"),
        re.compile(r"(?i)\b(?:line\s+should\s+be\s+added|should\s+be\s+added|should\s+be\s+inserted)\b"),
        re.compile(r"(?i)\b(?:add|insert)\s+['\"`].+?['\"`]\s+(?:before|after)\b"),
    ]

    CODE_EXPRESSION_PATTERNS = [
        re.compile(r"```[\s\S]*?```"),  # Fenced code block
        re.compile(r"(?i)\b(?:def\s+\w+\s*\(|class\s+\w+\s*:|from\s+\w+\s+import\s+\w+)\b"),
        re.compile(r"\b[a-zA-Z_]\w*\s*=\s*(?:[a-zA-Z_]\w*\(|sum\(|['\"`\[\{0-9])"),
        re.compile(r"\breturn\s+(?:[a-zA-Z_]\w*\s*\(|sum\(|['\"`\[\{0-9]|total_sum\b)"),
    ]

    @classmethod
    def validate(
        cls,
        diagnosis: FailureDiagnosis,
        analysis_input: FailureAnalysisInput,
    ) -> ValidationResult:
        errors: list[str] = []

        valid_files = set(analysis_input.all_project_files)
        valid_diag_ids = set(analysis_input.available_diagnostic_ids)
        valid_req_ids = set(analysis_input.available_requirement_ids)
        valid_arch_components = set(analysis_input.available_architecture_components)
        valid_db_entities = set(analysis_input.available_database_entities)

        # Collect valid test IDs from analysis input
        valid_test_ids = set(analysis_input.available_test_ids)
        if analysis_input.ai_test_suite and hasattr(analysis_input.ai_test_suite, "tests"):
            for t in analysis_input.ai_test_suite.tests:
                valid_test_ids.add(t.test_id)
                valid_test_ids.add(t.name)
        if analysis_input.ai_test_execution_result:
            exec_id = getattr(analysis_input.ai_test_execution_result, "execution_id", None)
            if exec_id:
                valid_test_ids.add(str(exec_id))
            for tr in getattr(analysis_input.ai_test_execution_result, "test_results", []):
                valid_test_ids.add(tr.name)

        if analysis_input.browser_test_run:
            from app.agents.failure_analysis.sanitizer import normalize_browser_evidence
            norm_br = normalize_browser_evidence(analysis_input.browser_test_run)
            for bid in norm_br.get("available_browser_ids", []):
                valid_test_ids.add(bid)

        # 0. Validate Taxonomy
        from app.agents.failure_analysis.contracts import FailureType
        if diagnosis.failure_type not in FailureType:
            errors.append(
                f"Unsupported failure taxonomy '{diagnosis.failure_type}': Must be one of {[t.value for t in FailureType]}."
            )

        # 1. Validate Affected Files
        for fpath in diagnosis.affected_files:
            clean_path = fpath.replace("\\", "/").strip()
            if clean_path not in valid_files and not any(vf.endswith(clean_path) for vf in valid_files):
                errors.append(
                    f"Hallucinated affected file '{fpath}': File does not exist in generated project manifest."
                )

        # 2. Validate Evidence References
        allowed_exec_ids = {
            "sandbox_stdout",
            "sandbox_stderr",
            "exit_code",
            "execution",
            "sandbox_test",
            "ai_test_stdout",
            "ai_test_stderr",
            "ai_test_execution",
            "browser_run",
            "browser_stdout",
            "browser_stderr",
            "browser_validation",
        }
        if analysis_input.execution_result and hasattr(analysis_input.execution_result, "execution_id"):
            allowed_exec_ids.add(str(analysis_input.execution_result.execution_id))

        for ev in diagnosis.evidence:
            ev_id = ev.evidence_id.strip()
            is_valid_diag = ev_id in valid_diag_ids
            is_valid_test = ev_id in valid_test_ids
            is_valid_exec = (
                ev_id in allowed_exec_ids
                or ev_id.startswith("exec_")
                or ev_id.startswith("diag_")
                or ev_id.startswith("line_")
                or ev_id.startswith("failure_summary_")
            )
            clean_ev_path = ev_id.replace("\\", "/").strip()
            clean_file_path = ev.file_path.replace("\\", "/").strip() if ev.file_path else None
            is_valid_file = (
                clean_ev_path in valid_files
                or any(vf.endswith(clean_ev_path) for vf in valid_files)
                or (
                    (ev_id.startswith("source_") or ev_id.startswith("file_"))
                    and (
                        (clean_file_path and (clean_file_path in valid_files or any(vf.endswith(clean_file_path) for vf in valid_files)))
                        or any(vf.replace("/", "_").replace(".", "_") in ev_id for vf in valid_files)
                    )
                )
            )

            if not is_valid_diag and not is_valid_test and not is_valid_exec and not is_valid_file:
                errors.append(
                    f"Hallucinated evidence reference '{ev.evidence_id}': Evidence ID does not correspond to any supplied diagnostic, test case, execution output, or verified project file."
                )

            if ev.file_path:
                clean_path = ev.file_path.replace("\\", "/").strip()
                if clean_path not in valid_files and not any(vf.endswith(clean_path) for vf in valid_files):
                    errors.append(
                        f"Evidence reference '{ev.evidence_id}' cites non-existent file path '{ev.file_path}'."
                    )

        # 3. Validate Claims reference declared Evidence
        declared_ev_ids = {ev.evidence_id for ev in diagnosis.evidence}
        for idx, claim in enumerate(diagnosis.claims):
            for ref_id in claim.evidence_ids:
                clean_ref = ref_id.replace("\\", "/").strip()
                is_valid_claim_ref = (
                    ref_id in declared_ev_ids
                    or ref_id in valid_diag_ids
                    or ref_id in valid_test_ids
                    or ref_id in allowed_exec_ids
                    or clean_ref in valid_files
                    or any(vf.endswith(clean_ref) for vf in valid_files)
                    or ref_id.startswith("source_")
                    or ref_id.startswith("file_")
                )
                if not is_valid_claim_ref:
                    errors.append(
                        f"Claim #{idx + 1} ({claim.claim_type.value}) references undeclared evidence ID '{ref_id}'."
                    )

        # 4. Validate Requirement Links
        for req_id in diagnosis.requirement_links:
            clean_req = req_id.strip()
            if clean_req not in valid_req_ids:
                errors.append(
                    f"Hallucinated requirement link '{req_id}': Requirement ID does not exist in project context."
                )

        # 5. Validate Architecture Links
        for comp_name in diagnosis.architecture_links:
            clean_comp = comp_name.strip()
            if clean_comp not in valid_arch_components:
                errors.append(
                    f"Hallucinated architecture link '{comp_name}': Component does not exist in architecture context."
                )

        # 6. Validate Database Links
        for entity_name in diagnosis.database_links:
            clean_entity = entity_name.strip()
            if clean_entity not in valid_db_entities:
                errors.append(
                    f"Hallucinated database link '{entity_name}': Entity does not exist in database context."
                )

        # 7. Validate Suggested Remediation is strictly conceptual (No diffs, code snippets, or patch instructions)
        remediation_text = diagnosis.suggested_remediation

        # A. Diff and patch markers
        for marker in cls.DIFF_MARKERS:
            if marker in remediation_text:
                errors.append(
                    f"Forbidden code patch formatting detected in suggested_remediation ('{marker}'). "
                    "Remediation must be conceptual guidance only, not a code patch or diff."
                )

        # B. Source-code replacement instructions ("replace X with Y")
        for pat in cls.REPLACEMENT_PATTERNS:
            if pat.search(remediation_text):
                errors.append(
                    "Forbidden source replacement instruction detected in suggested_remediation ('replace ... with ...'). "
                    "Remediation must be conceptual guidance only, not a code replacement directive."
                )
                break

        # C. Line addition / insertion instructions ("add this line")
        for pat in cls.INSERTION_PATTERNS:
            if pat.search(remediation_text):
                errors.append(
                    "Forbidden line insertion instruction detected in suggested_remediation ('add this line'). "
                    "Remediation must be conceptual guidance, not line insertion directives."
                )
                break

        # D. Executable code snippets, expressions, or function body rewrites
        for pat in cls.CODE_EXPRESSION_PATTERNS:
            if pat.search(remediation_text):
                errors.append(
                    "Forbidden code snippet or statement expression detected in suggested_remediation. "
                    "Remediation must be high-level conceptual guidance, not concrete code expressions or rewrites."
                )
                break

        if errors:
            logger.warning(
                f"FailureDiagnosis validation failed with {len(errors)} error(s): {errors}"
            )
            return ValidationResult(is_valid=False, errors=errors)

        return ValidationResult(is_valid=True)
