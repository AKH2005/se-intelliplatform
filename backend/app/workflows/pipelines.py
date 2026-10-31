"""Predefined Workflow Pipeline Definitions and Explicit Artifact Routing Adapters."""

import logging
from typing import Any

from app.agents.explainability.contracts import ExplainabilityInput
from app.workflows.contracts import (
    WorkflowDefinition,
    WorkflowInput,
    WorkflowStep,
)

logger = logging.getLogger(__name__)

WORKFLOW_SOFTWARE_DESIGN_ID = "software-design-workflow"
WORKFLOW_PROJECT_ESTIMATION_ID = "project-estimation-workflow"
WORKFLOW_COMPREHENSIVE_AUDIT_ID = "comprehensive-audit-workflow"
WORKFLOW_CODE_GENERATION_ID = "code-generation-workflow"
WORKFLOW_BROWSER_JOURNEY_ID = "browser-journey-workflow"


# ==============================================================================
# 1. Pipeline Builders
# ==============================================================================

def build_software_design_workflow() -> WorkflowDefinition:
    """Build the Software Design Workflow definition.

    Sequence:
    1. requirement-analysis (MANDATORY)
    2. architecture-recommendation (OPTIONAL enrichment, depends on requirement-analysis)
    3. database-design (MANDATORY for success, depends on requirement-analysis and architecture-recommendation)
    """
    return WorkflowDefinition(
        workflow_id=WORKFLOW_SOFTWARE_DESIGN_ID,
        version="1.0.0",
        name="Software Design Workflow",
        description="Executes requirement analysis, architecture recommendation, and database design sequentially with typed artifact enrichment.",
        steps=[
            WorkflowStep(
                step_id="requirement-analysis",
                agent_id="requirement-analysis",
                required=True,
                depends_on=[],
                description="Analyze canonical requirements for ambiguities, conflicts, and gaps",
            ),
            WorkflowStep(
                step_id="architecture-recommendation",
                agent_id="architecture-recommendation",
                required=False,
                depends_on=["requirement-analysis"],
                description="Propose structural architecture styles, components, and trade-offs enriched by requirement analysis",
            ),
            WorkflowStep(
                step_id="database-design",
                agent_id="database-design",
                required=True,
                depends_on=["requirement-analysis", "architecture-recommendation"],
                description="Propose relational entities, relationships, indexes, and constraints enriched by architecture and requirement analysis",
            ),
        ],
    )


def build_code_generation_workflow() -> WorkflowDefinition:
    """Build the Code Generation Workflow definition.

    Sequence:
    1. requirement-analysis (MANDATORY)
    2. architecture-recommendation (MANDATORY, depends on requirement-analysis)
    3. database-design (MANDATORY, depends on requirement-analysis, architecture-recommendation)
    4. code-generation-planning (MANDATORY, depends on database-design)
    5. code-generation (MANDATORY, depends on code-generation-planning)
    """
    return WorkflowDefinition(
        workflow_id=WORKFLOW_CODE_GENERATION_ID,
        version="1.0.0",
        name="Code Generation Workflow",
        description="Executes requirement analysis, architecture recommendation, database design, scaffold planning, and verified code generation producing a deployable project scaffold artifact.",
        steps=[
            WorkflowStep(
                step_id="requirement-analysis",
                agent_id="requirement-analysis",
                required=True,
                depends_on=[],
                description="Analyze canonical requirements for ambiguities, conflicts, and gaps",
            ),
            WorkflowStep(
                step_id="architecture-recommendation",
                agent_id="architecture-recommendation",
                required=True,
                depends_on=["requirement-analysis"],
                description="Propose structural architecture styles, components, and trade-offs",
            ),
            WorkflowStep(
                step_id="database-design",
                agent_id="database-design",
                required=True,
                depends_on=["requirement-analysis", "architecture-recommendation"],
                description="Propose relational entities, relationships, indexes, and constraints",
            ),
            WorkflowStep(
                step_id="code-generation-planning",
                agent_id="code-generation-planning",
                required=True,
                depends_on=["requirement-analysis", "architecture-recommendation", "database-design"],
                description="Synthesize design outputs into a concrete file manifest and scaffold plan",
            ),
            WorkflowStep(
                step_id="code-generation",
                agent_id="code-generation",
                required=True,
                depends_on=["code-generation-planning"],
                description="Generate verified, syntactically valid source files strictly matching the planned manifest",
            ),
        ],
    )


def build_browser_journey_workflow() -> WorkflowDefinition:
    """Build the Browser Journey Generation Workflow definition.

    Sequence:
    1. browser-journey-generation (MANDATORY)
    """
    return WorkflowDefinition(
        workflow_id=WORKFLOW_BROWSER_JOURNEY_ID,
        version="1.0.0",
        name="Browser Journey Generation Workflow",
        description="Generates AI browser user journeys from bounded project requirements and routes for deterministic validation and Phase 11J browser execution.",
        steps=[
            WorkflowStep(
                step_id="browser-journey-generation",
                agent_id="browser-journey-generation",
                required=True,
                depends_on=[],
                description="Generate candidate browser user journeys from bounded project requirements and routes",
            ),
        ],
    )


def build_project_estimation_workflow() -> WorkflowDefinition:
    """Build the Project Estimation Workflow definition.

    Sequence:
    1. risk-prediction (INDEPENDENT ML)
    2. timeline-prediction (INDEPENDENT ML)
    3. bug-prediction (INDEPENDENT ML)

    All steps are independent supervised ML inference models.
    Sequential execution preserves provenance simplicity and deterministic testing.
    """
    return WorkflowDefinition(
        workflow_id=WORKFLOW_PROJECT_ESTIMATION_ID,
        version="1.0.0",
        name="Project Estimation Workflow",
        description="Runs supervised machine learning predictions for project risk, timeline duration, and defect susceptibility.",
        steps=[
            WorkflowStep(
                step_id="risk-prediction",
                agent_id="risk-prediction",
                required=False,
                depends_on=[],
                description="Predict project risk score and risk level using local Ridge regression pipeline",
            ),
            WorkflowStep(
                step_id="timeline-prediction",
                agent_id="timeline-prediction",
                required=False,
                depends_on=[],
                description="Predict project duration in elapsed months using local RandomForest pipeline",
            ),
            WorkflowStep(
                step_id="bug-prediction",
                agent_id="bug-prediction",
                required=False,
                depends_on=[],
                description="Predict module defect susceptibility using local Logistic Regression pipeline",
            ),
        ],
    )


def build_comprehensive_audit_workflow() -> WorkflowDefinition:
    """Build the Comprehensive Audit Workflow definition.

    Sequence:
    1. requirement-analysis (MANDATORY)
    2. architecture-recommendation (OPTIONAL)
    3. database-design (OPTIONAL)
    4. risk-prediction (OPTIONAL)
    5. timeline-prediction (OPTIONAL)
    6. bug-prediction (OPTIONAL)
    7. test-case-generation (OPTIONAL)
    8. code-review (OPTIONAL, skipped if CodeReviewInput absent)
    9. explainability-insights (OPTIONAL terminal synthesis, consumes successful upstream outputs)
    """
    return WorkflowDefinition(
        workflow_id=WORKFLOW_COMPREHENSIVE_AUDIT_ID,
        version="1.0.0",
        name="Comprehensive Audit Workflow",
        description="Executes all platform intelligence agents across requirements, design, ML estimates, test cases, and code review, concluding with grounded explainability insights.",
        steps=[
            WorkflowStep(
                step_id="requirement-analysis",
                agent_id="requirement-analysis",
                required=True,
                depends_on=[],
                description="Analyze canonical requirements",
            ),
            WorkflowStep(
                step_id="architecture-recommendation",
                agent_id="architecture-recommendation",
                required=False,
                depends_on=["requirement-analysis"],
                description="Recommend software architecture based on context and requirements",
            ),
            WorkflowStep(
                step_id="database-design",
                agent_id="database-design",
                required=False,
                depends_on=["requirement-analysis", "architecture-recommendation"],
                description="Propose database schema design",
            ),
            WorkflowStep(
                step_id="risk-prediction",
                agent_id="risk-prediction",
                required=False,
                depends_on=[],
                description="Predict continuous project risk",
            ),
            WorkflowStep(
                step_id="timeline-prediction",
                agent_id="timeline-prediction",
                required=False,
                depends_on=[],
                description="Predict project delivery timeline",
            ),
            WorkflowStep(
                step_id="bug-prediction",
                agent_id="bug-prediction",
                required=False,
                depends_on=[],
                description="Predict defect susceptibility",
            ),
            WorkflowStep(
                step_id="test-case-generation",
                agent_id="test-case-generation",
                required=False,
                depends_on=[],
                description="Generate structured test scenarios from active requirements",
            ),
            WorkflowStep(
                step_id="code-review",
                agent_id="code-review",
                required=False,
                depends_on=[],
                description="Perform static AST analysis, credential scanning, and AI review on supplied source files",
            ),
            WorkflowStep(
                step_id="explainability-insights",
                agent_id="explainability-insights",
                required=False,
                depends_on=[],
                description="Synthesize grounded explanations and cross-domain insights from successful upstream outputs",
            ),
        ],
    )


# ==============================================================================
# 2. Explicit Artifact Routing Adapters
# ==============================================================================

def resolve_step_kwargs(
    workflow_id: str,
    step: WorkflowStep,
    artifacts: dict[str, Any],
    workflow_input: WorkflowInput,
) -> tuple[dict[str, Any], str | None]:
    """Deterministically resolve keyword arguments for an agent step based on available artifacts.

    Returns:
        tuple[dict[str, Any], str | None]:
            - Dict of kwargs to pass to AgentExecutor.execute()
            - Optional skip_reason string if step preconditions are not satisfied (e.g. missing input payload)
    """
    step_id = step.step_id
    agent_id = step.agent_id

    # 1. Architecture Recommendation routing: inject requirement_analysis output if available
    if agent_id == "architecture-recommendation":
        req_out = artifacts.get("requirement-analysis")
        return {"requirement_analysis": req_out}, None

    # 2. Database Design routing: inject requirement_analysis and architecture_recommendation outputs if available
    if agent_id == "database-design":
        req_out = artifacts.get("requirement-analysis")
        arch_out = artifacts.get("architecture-recommendation")
        return {
            "requirement_analysis": req_out,
            "architecture_recommendation": arch_out,
        }, None

    # 3. Code Review routing: requires external CodeReviewInput payload
    if agent_id == "code-review":
        if workflow_input.code_review_input is None:
            return {}, "CodeReviewInput was not provided in workflow input."
        return {"code_input": workflow_input.code_review_input}, None

    # 4. Explainability Insights routing: requires at least one successful upstream agent output
    if agent_id == "explainability-insights":
        req_out = artifacts.get("requirement-analysis")
        arch_out = artifacts.get("architecture-recommendation")
        db_out = artifacts.get("database-design")
        risk_out = artifacts.get("risk-prediction")
        timeline_out = artifacts.get("timeline-prediction")
        bug_out = artifacts.get("bug-prediction")
        test_out = artifacts.get("test-case-generation")
        cr_out = artifacts.get("code-review")

        candidate_outputs = [
            req_out,
            arch_out,
            db_out,
            risk_out,
            timeline_out,
            bug_out,
            test_out,
            cr_out,
        ]

        if not any(out is not None for out in candidate_outputs):
            return {}, "No upstream agent outputs available for explainability synthesis."

        try:
            explainability_input = ExplainabilityInput(
                target_scope=workflow_input.explainability_target_scope,
                user_query=workflow_input.explainability_user_query,
                requirement_analysis=req_out,
                architecture_recommendation=arch_out,
                database_design=db_out,
                risk_prediction=risk_out,
                timeline_prediction=timeline_out,
                bug_prediction=bug_out,
                test_case_generation=test_out,
                code_review=cr_out,
            )
            return {"explainability_input": explainability_input}, None
        except Exception as exc:
            return {}, f"Failed to construct ExplainabilityInput: {exc}"

    # 5. Code Generation Planning routing: inject upstream design artifacts
    if agent_id == "code-generation-planning":
        req_out = artifacts.get("requirement-analysis")
        arch_out = artifacts.get("architecture-recommendation")
        db_out = artifacts.get("database-design")
        return {
            "requirement_analysis": req_out,
            "architecture_recommendation": arch_out,
            "database_design": db_out,
        }, None

    # 6. Code Generation routing: inject plan from code-generation-planning and upstream design artifacts
    if agent_id == "code-generation":
        plan = artifacts.get("code-generation-planning")
        if plan is None:
            return {}, "CodeGenerationPlan was not produced by upstream planning step."
        req_out = artifacts.get("requirement-analysis")
        arch_out = artifacts.get("architecture-recommendation")
        db_out = artifacts.get("database-design")
        return {
            "plan": plan,
            "requirement_analysis": req_out,
            "architecture_recommendation": arch_out,
            "database_design": db_out,
        }, None

    # 7. Failure Analysis routing: inject execution, static analysis, and design artifacts
    if agent_id == "failure-analysis":
        exec_res = artifacts.get("sandbox_execution")
        static_res = artifacts.get("static_analysis")
        code_out = artifacts.get("code-generation") or artifacts.get("code_generation")
        req_out = artifacts.get("requirement-analysis")
        arch_out = artifacts.get("architecture-recommendation")
        db_out = artifacts.get("database-design")

        # Determine if failure analysis is needed
        needs_analysis = False
        if exec_res is not None:
            status = getattr(exec_res, "status", None)
            exit_code = getattr(exec_res, "exit_code", 0)
            tests_failed = getattr(exec_res, "tests_failed", 0)
            status_val = status.value if hasattr(status, "value") else str(status)
            if status_val != "PASSED" or exit_code != 0 or tests_failed > 0:
                needs_analysis = True

        if static_res is not None:
            err_count = getattr(static_res, "error_count", 0)
            status = getattr(static_res, "status", None)
            status_val = status.value if hasattr(status, "value") else str(status)
            if err_count > 0 or status_val in ("VALIDATION_ERROR", "ANALYSIS_ERROR"):
                needs_analysis = True

        if not needs_analysis:
            return {}, "No execution or static analysis failure detected. Failure analysis skipped."

        return {
            "execution_result": exec_res,
            "static_analysis_result": static_res,
            "code_generation": code_out,
            "requirement_analysis": req_out,
            "architecture_recommendation": arch_out,
            "database_design": db_out,
        }, None

    # 8. Remediation Proposal routing: requires failure diagnosis and code generation artifact
    if agent_id == "remediation-proposal":
        diag = artifacts.get("failure_analysis")
        if diag is None:
            return {}, "No failure diagnosis found. Remediation proposal skipped."
        code_out = artifacts.get("code-generation") or artifacts.get("code_generation")
        if code_out is None:
            return {}, "No generated code artifact found to remediate."
        return {
            "diagnosis": diag,
            "code_generation": code_out,
            "static_analysis_result": artifacts.get("static_analysis"),
            "execution_result": artifacts.get("sandbox_execution"),
            "architecture_recommendation": artifacts.get("architecture-recommendation"),
            "database_design": artifacts.get("database-design"),
        }, None

    # 9. Browser Journey Generation routing
    if agent_id == "browser-journey-generation":
        bj_input = getattr(workflow_input, "browser_journey_input", None)
        if bj_input is not None:
            return {"browser_journey_input": bj_input}, None
        return {}, None

    # Default: independent agents consume canonical ProjectContextResponse (no additional kwargs)
    return {}, None
