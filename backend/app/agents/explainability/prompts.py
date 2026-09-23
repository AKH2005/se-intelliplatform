"""Prompts for Explainability & Engineering Insights Agent."""

from typing import Any
from app.agents.explainability.contracts import ExplainabilityInput
from app.schemas.context import ProjectContextResponse

SYSTEM_PROMPT = """You are the Explainability & Engineering Insights Agent in SE IntelliPlatform.
Your role is to explain, contextualize, and synthesize already-generated, validated findings from software engineering agents into grounded, human-readable engineering insights.

CRITICAL OPERATIONAL & EPISTEMIC DIRECTIVES:
1. EXPLANATORY SYNTHESIZER ONLY: You do NOT predict, calculate, or recalculate ML model scores, risk bands, timeline durations, bug classifications, or test coverage. You explain what the existing upstream outputs mean.
2. STRICT TRACEABILITY (ZERO PHANTOM CITATIONS):
   - You may ONLY cite agent IDs that were explicitly provided in the input payload.
   - You may ONLY reference entity IDs (requirement UUIDs, finding IDs like CR-001, test case IDs like TC-001, component names, or model names) that actually exist in the supplied outputs.
   - Every insight must include at least one valid SourceReference.
3. GROUNDED CAUSALITY BOUNDARY:
   - Statistical ML models in this platform represent empirical associations within historical datasets; they do NOT establish definitive causality.
   - FORBIDDEN: Do NOT make ungrounded assertions such as "Feature X caused project delay" or "The team is incompetent" or "Code review proved a runtime crash".
   - APPROVED: Use objective, grounded language such as "The timeline model predicted...", "The code review identified a potential injection surface at...", "Based on active requirement REQ-01...".
4. PRESERVE REDACTIONS: If code review or upstream findings contain '***REDACTED_SECRET***', preserve this marker strictly. Never attempt to guess, reconstruct, or output raw credentials.
5. NO EXECUTION CLAIMS: Never claim that code was compiled, executed, or dynamically verified.
6. OUTPUT STRUCTURE: Return a valid structured JSON candidate with an executive summary and a list of EngineeringInsight objects matching the requested schema.
"""


def build_explainability_prompt(
    context: ProjectContextResponse,
    input_data: ExplainabilityInput,
    source_index: dict[str, Any],
) -> str:
    """Format contextual prompt for explainability candidate generation."""
    prompt_lines: list[str] = []

    prompt_lines.append("# EXPLAINABILITY & ENGINEERING INSIGHTS INVOCATION")
    prompt_lines.append(f"Project: {context.project.name} (ID: {context.project.id})")
    if context.project.description:
        prompt_lines.append(f"Description: {context.project.description}")

    if input_data.target_scope:
        prompt_lines.append(f"Target Scope Focus: {input_data.target_scope}")
    if input_data.user_query:
        prompt_lines.append(f"Developer Query / Question: {input_data.user_query}")
    prompt_lines.append("")

    prompt_lines.append("## SUPPLIED UPSTREAM AGENT OUTPUTS")

    # 1. Requirement Analysis
    if input_data.requirement_analysis is not None:
        ra = input_data.requirement_analysis
        prompt_lines.append("### Upstream Output: requirement-analysis")
        prompt_lines.append(f"- Summary: {ra.summary}")
        prompt_lines.append(
            f"- Metrics: Active Requirements = {ra.active_requirements_count}, "
            f"Completeness Score = {ra.completeness_score:.1f}%"
        )
        if ra.ambiguities:
            prompt_lines.append(f"- Ambiguities ({len(ra.ambiguities)}):")
            for amb in ra.ambiguities:
                prompt_lines.append(f"  * Req [{amb.requirement_id}]: {amb.issue} (Severity: {amb.severity.value}) - {amb.explanation}")
        if ra.conflicts:
            prompt_lines.append(f"- Conflicts ({len(ra.conflicts)}):")
            for conf in ra.conflicts:
                prompt_lines.append(f"  * Req [{conf.requirement_id}] vs [{conf.related_requirement_id}]: {conf.issue}")
        if ra.missing_information:
            prompt_lines.append(f"- Missing Information ({len(ra.missing_information)}):")
            for gap in ra.missing_information:
                prompt_lines.append(f"  * Area [{gap.area}]: {gap.description}")
        prompt_lines.append("")

    # 2. Architecture Recommendation
    if input_data.architecture_recommendation is not None:
        arch = input_data.architecture_recommendation
        prompt_lines.append("### Upstream Output: architecture-recommendation")
        prompt_lines.append(f"- Summary: {arch.summary}")
        if arch.architecture_styles:
            styles_str = ", ".join(f"{s.style.value} ({s.rationale})" for s in arch.architecture_styles)
            prompt_lines.append(f"- Recommended Styles: {styles_str}")
        if arch.components:
            comp_str = ", ".join(f"{c.name} ({c.responsibility})" for c in arch.components)
            prompt_lines.append(f"- Components: {comp_str}")
        if arch.trade_offs:
            prompt_lines.append(f"- Trade-Off Analyses ({len(arch.trade_offs)}):")
            for t in arch.trade_offs:
                prompt_lines.append(f"  * Decision: {t.decision_area} -> Recommended: {t.recommended_option}")
        prompt_lines.append("")

    # 3. Database Design
    if input_data.database_design is not None:
        db = input_data.database_design
        prompt_lines.append("### Upstream Output: database-design")
        prompt_lines.append(f"- Summary: {db.summary}")
        prompt_lines.append(f"- Paradigm: {db.database_paradigm.value}")
        if db.entities:
            ent_str = ", ".join(e.name for e in db.entities)
            prompt_lines.append(f"- Entities: {ent_str}")
        prompt_lines.append("")

    # 4. Risk Prediction
    if input_data.risk_prediction is not None:
        rp = input_data.risk_prediction
        prompt_lines.append("### Upstream Output: risk-prediction")
        prompt_lines.append(f"- Summary: {rp.summary}")
        prompt_lines.append(f"- Predicted Risk Score: {rp.predicted_risk_score:.2f} (Scale: 1.0 - 10.0)")
        prompt_lines.append(f"- Risk Level Band: {rp.risk_level.value}")
        prompt_lines.append(f"- Input Features: {rp.feature_summary}")
        prompt_lines.append(f"- Model: {rp.model_provenance.model_name} (Algorithm: {rp.model_provenance.algorithm})")
        prompt_lines.append("")

    # 5. Timeline Prediction
    if input_data.timeline_prediction is not None:
        tp = input_data.timeline_prediction
        prompt_lines.append("### Upstream Output: timeline-prediction")
        prompt_lines.append(f"- Summary: {tp.summary}")
        prompt_lines.append(f"- Predicted Duration: {tp.predicted_duration_months:.1f} {tp.target_unit}")
        prompt_lines.append(f"- Input Function Points: {tp.feature_summary}")
        prompt_lines.append(f"- Model: {tp.model_provenance.model_name} (Algorithm: {tp.model_provenance.algorithm})")
        prompt_lines.append("")

    # 6. Bug Prediction
    if input_data.bug_prediction is not None:
        bp = input_data.bug_prediction
        prompt_lines.append("### Upstream Output: bug-prediction")
        prompt_lines.append(f"- Summary: {bp.summary}")
        prompt_lines.append(f"- Defect Classification Label: {bp.prediction_label.value}")
        prompt_lines.append(f"- Predicted Probability: {bp.predicted_probability:.4f}")
        prompt_lines.append(f"- Static Complexity Features: {bp.feature_summary}")
        prompt_lines.append(f"- Model: {bp.model_provenance.model_name} (Algorithm: {bp.model_provenance.algorithm})")
        prompt_lines.append("")

    # 7. Test Case Generation
    if input_data.test_case_generation is not None:
        tc = input_data.test_case_generation
        prompt_lines.append("### Upstream Output: test-case-generation")
        prompt_lines.append(f"- Summary: {tc.summary}")
        prompt_lines.append(f"- Total Test Cases: {tc.total_test_cases}")
        prompt_lines.append(f"- Requirement Coverage: {tc.coverage.coverage_percentage:.1f}%")
        if tc.test_cases:
            tc_summary = ", ".join(f"[{c.test_case_id}: {c.title}]" for c in tc.test_cases[:5])
            prompt_lines.append(f"- Sample Test Cases: {tc_summary}")
        prompt_lines.append("")

    # 8. Code Review
    if input_data.code_review is not None:
        cr = input_data.code_review
        prompt_lines.append("### Upstream Output: code-review")
        prompt_lines.append(f"- Summary: {cr.summary}")
        prompt_lines.append(
            f"- Metrics: Files = {cr.metrics.files_analyzed_count}, "
            f"Total Findings = {cr.metrics.total_findings} (Static: {cr.metrics.static_findings_count}, AI: {cr.metrics.ai_findings_count})"
        )
        if cr.findings:
            prompt_lines.append(f"- Findings ({len(cr.findings)}):")
            for f in cr.findings:
                prompt_lines.append(
                    f"  * [{f.finding_id}] {f.file_path}:{f.line_start}-{f.line_end} | "
                    f"Severity: {f.severity.value} | Category: {f.category.value} | Rule: {f.rule_id or 'AI'} | "
                    f"Title: {f.title}"
                )
                prompt_lines.append(f"    Evidence: {f.evidence}")
                prompt_lines.append(f"    Recommendation: {f.recommendation}")
        prompt_lines.append("")

    prompt_lines.append("## INSTRUCTIONS FOR INSIGHT SYNTHESIS")
    prompt_lines.append(
        "Generate a structured ExplainabilityCandidate containing an executive summary and a collection of EngineeringInsight objects. "
        "Each insight must contain:\n"
        "- category: One of InsightCategory\n"
        "- title: Concise title\n"
        "- summary: Executive summary of insight\n"
        "- explanation: In-depth narrative explaining what the finding implies, how it relates to engineering practices or requirements\n"
        "- source_references: At least one SourceReference linking to the exact agent_id and entity ID (CR-001, TC-001, req UUID, model name)\n"
        "- suggested_actions: Actionable, advisory engineering next steps\n"
        "Ground all claims strictly in the provided data."
    )

    return "\n".join(prompt_lines)
