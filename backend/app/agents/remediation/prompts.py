"""Prompt templates and builder for Remediation Proposal Agent."""

import json
from app.agents.remediation.contracts import RemediationProposalInput

SYSTEM_PROMPT = """You are the Senior Software Remediation Proposal Engine for SE IntelliPlatform.
Your role is to propose a minimal, high-quality, structured patch that directly resolves an evidence-grounded failure diagnosis.

CRITICAL INVARIANTS & SAFETY RULES:
1. PROPOSE ONLY FOR HUMAN REVIEW:
   - You are proposing a patch for MANDATORY HUMAN REVIEW and EXPLICIT APPROVAL.
   - You do NOT apply patches. You do NOT execute code. You do NOT assume approval.
   - Do NOT claim tests have passed or that a fix has already been applied.

2. MINIMAL TARGETED CHANGES:
   - Propose modifications ONLY to files directly implicated by the failure diagnosis and evidence.
   - Keep changes minimal, surgically addressing the root cause while preserving all existing unrelated code and architectural styles.
   - Do NOT rewrite entire files when a small targeted function edit suffices.

3. PRECISE REPLACEMENT REGIONS:
   - For 'MODIFY' operations: 'original_region' MUST EXACTLY MATCH a contiguous substring in the target file.
   - 'proposed_region' must contain the corrected code that replaces 'original_region'.
   - For 'ADD' operations: 'original_region' is null, 'proposed_region' is the full file content.
   - For 'DELETE' operations: 'original_region' is the full file content, 'proposed_region' is empty string.

4. ANTI-HALLUCINATION CONSTRAINTS:
   - You may ONLY modify files listed under 'AVAILABLE PROJECT FILES'.
   - Do NOT invent files, directories, or package installations.
   - Do NOT invent requirement IDs, architecture components, or database entities. Cite ONLY those listed under 'VALID CONTEXT IDENTIFIERS'.
   - Never insert credentials, fake keys, or secret tokens.

5. TAXONOMY:
   - 'risk_level' must be one of: LOW, MEDIUM, HIGH.
   - 'operation' must be one of: MODIFY, ADD, DELETE.

You must respond with valid JSON adhering strictly to the RemediationProposalCandidate schema."""


def build_remediation_proposal_prompt(analysis_input: RemediationProposalInput) -> str:
    """Construct bounded, authoritative prompt for proposing a code remediation."""
    sections: list[str] = []

    sections.append("# FAILURE DIAGNOSIS & REMEDIATION CONTEXT")
    sections.append(f"Target Project ID: {analysis_input.project_id}")
    if analysis_input.workflow_execution_id:
        sections.append(f"Workflow Execution ID: {analysis_input.workflow_execution_id}")

    # 1. Authoritative Failure Diagnosis
    diag = analysis_input.diagnosis
    sections.append("\n## 1. AUTHORITATIVE FAILURE DIAGNOSIS")
    sections.append(f"- Diagnosis ID: {diag.diagnosis_id}")
    sections.append(f"- Failure Type: {diag.failure_type.value}")
    sections.append(f"- Severity: {diag.severity.value}")
    sections.append(f"- Confidence: {diag.confidence.value}")
    sections.append(f"- Headline: {diag.title}")
    sections.append(f"- Summary: {diag.summary}")
    sections.append(f"- Root Cause: {diag.root_cause}")
    sections.append(f"- Suggested Conceptual Remediation: {diag.suggested_remediation}")
    if diag.affected_files:
        sections.append(f"- Implicated Files: {', '.join(diag.affected_files)}")

    # 2. Diagnostic Evidence
    sections.append("\n## 2. DETERMINISTIC EVIDENCE & FINDINGS")
    if diag.evidence:
        for ev in diag.evidence:
            loc = f" at {ev.file_path}:{ev.line}" if ev.file_path else ""
            sections.append(f"- [Evidence ID: {ev.evidence_id}] [{ev.source}] {ev.code or ''}{loc}: {ev.description or ev.snippet or ''}")

    # 3. Relevant Source Code
    sections.append("\n## 3. RELEVANT PROJECT SOURCE CODE")
    if analysis_input.relevant_files:
        for rf in analysis_input.relevant_files:
            sections.append(f"\nFILE: {rf.path} (Selection Reason: {rf.selection_reason})")
            sections.append(f"```python\n{rf.content}\n```")
    else:
        sections.append("No source files provided.")

    # 4. Context Boundaries
    sections.append("\n## 4. VALID CONTEXT IDENTIFIERS")
    sections.append(f"- Available Project Files: {json.dumps(analysis_input.project_manifest)}")
    sections.append(f"- Available Requirement IDs: {json.dumps(analysis_input.available_requirement_ids)}")
    sections.append(f"- Available Architecture Components: {json.dumps(analysis_input.available_architecture_components)}")
    sections.append(f"- Available Database Entities: {json.dumps(analysis_input.available_database_entities)}")

    sections.append(
        "\nINSTRUCTIONS:\n"
        "Carefully analyze the root cause and relevant source code. Formulate a structured patch proposal "
        "that resolves the defect with minimal modification. For each change, specify file_path, operation (MODIFY/ADD/DELETE), "
        "exact original_region to replace, and proposed_region. Return strictly JSON matching RemediationProposalCandidate."
    )

    return "\n".join(sections)
