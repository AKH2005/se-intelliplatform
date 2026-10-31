"""Authoritative Action Registry for Phase 11I / 11J / 11K Intelli Assistant & Engineering Action Layer.

This module is the single authoritative source of truth for platform actions.
All counts, classifications, and parameter schemas derive strictly from ACTION_REGISTRY.
"""

from typing import Any
from pydantic import BaseModel

from app.core.exceptions import ValidationError
from app.schemas.assistant import (
    ActionCategory,
    ActionDefinition,
    ActivateVersionParams,
    AnalyzeCoverageGapsParams,
    AnalyzeFailureParams,
    AnalyzeRegressionImpactParams,
    ApplyCodeChangeParams,
    CheckPromotionEligibilityParams,
    CompareVersionsParams,
    CreateRemediationProposalParams,
    DeployToEnvironmentParams,
    EmptyParams,
    ExecuteRegressionParams,
    GenerateBrowserJourneysParams,
    GetBrowserTestResultsParams,
    GetCoverageReportParams,
    GetDeploymentHistoryParams,
    GetEnvironmentStatusParams,
    GetEnvironmentsParams,
    GetRemediationProposalParams,
    GetRequirementParams,
    GetTestInventoryParams,
    GetVersionFileContentParams,
    GetWorkflowHistoryParams,
    ListRequirementsParams,
    OptionalVersionTargetParams,
    PlanRegressionParams,
    PromoteVersionParams,
    ProposalTargetParams,
    RejectRemediationParams,
    RollbackEnvironmentParams,
    RollbackVersionParams,
    RunAITestsParams,
    RunBrowserTestsParams,
    RunWorkflowParams,
    VersionTargetParams,
)


ACTION_REGISTRY: dict[str, ActionDefinition] = {
    # -------------------------------------------------------------------------
    # READ_ONLY (16 Actions) - Zero side-effects, fast querying
    # -------------------------------------------------------------------------
    "GET_PROJECT_CONTEXT": ActionDefinition(
        action_id="GET_PROJECT_CONTEXT",
        description="Retrieve canonical project context, metadata, and status overview.",
        category=ActionCategory.READ_ONLY,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["project"],
        parameter_schema=EmptyParams,
    ),
    "LIST_REQUIREMENTS": ActionDefinition(
        action_id="LIST_REQUIREMENTS",
        description="Retrieve all project requirements, optionally filtered by status.",
        category=ActionCategory.READ_ONLY,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["project"],
        parameter_schema=ListRequirementsParams,
    ),
    "GET_REQUIREMENT": ActionDefinition(
        action_id="GET_REQUIREMENT",
        description="Retrieve detailed specification and metadata for a single requirement by ID.",
        category=ActionCategory.READ_ONLY,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["requirement"],
        parameter_schema=GetRequirementParams,
    ),
    "LIST_WORKFLOWS": ActionDefinition(
        action_id="LIST_WORKFLOWS",
        description="List registered multi-agent workflow pipeline templates available in the platform.",
        category=ActionCategory.READ_ONLY,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["platform"],
        parameter_schema=EmptyParams,
    ),
    "GET_WORKFLOW_HISTORY": ActionDefinition(
        action_id="GET_WORKFLOW_HISTORY",
        description="Query past workflow executions, statuses, and runtime durations for the project.",
        category=ActionCategory.READ_ONLY,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["project"],
        parameter_schema=GetWorkflowHistoryParams,
    ),
    "LIST_VERSIONS": ActionDefinition(
        action_id="LIST_VERSIONS",
        description="List all immutable development versions with the current active release marked.",
        category=ActionCategory.READ_ONLY,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["project"],
        parameter_schema=EmptyParams,
    ),
    "GET_VERSION": ActionDefinition(
        action_id="GET_VERSION",
        description="Retrieve comprehensive metadata, hashes, and file manifest for a specific version.",
        category=ActionCategory.READ_ONLY,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["version"],
        parameter_schema=VersionTargetParams,
    ),
    "GET_ACTIVE_VERSION": ActionDefinition(
        action_id="GET_ACTIVE_VERSION",
        description="Retrieve the project's designated active software release.",
        category=ActionCategory.READ_ONLY,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["project"],
        parameter_schema=EmptyParams,
    ),
    "GET_VERSION_FILE_CONTENT": ActionDefinition(
        action_id="GET_VERSION_FILE_CONTENT",
        description="Retrieve source code for one manifest-verified file with strictly bounded size (<= 100 KB).",
        category=ActionCategory.READ_ONLY,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["version", "file"],
        parameter_schema=GetVersionFileContentParams,
    ),
    "COMPARE_VERSIONS": ActionDefinition(
        action_id="COMPARE_VERSIONS",
        description="Compute deterministic unified textual diffs and requirement deltas between two versions.",
        category=ActionCategory.READ_ONLY,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["version"],
        parameter_schema=CompareVersionsParams,
    ),
    "GET_VERSION_VERIFICATION": ActionDefinition(
        action_id="GET_VERSION_VERIFICATION",
        description="Retrieve granular multi-stage verification snapshot for a software version.",
        category=ActionCategory.READ_ONLY,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["version"],
        parameter_schema=VersionTargetParams,
    ),
    "GET_VERSION_CHANGES": ActionDefinition(
        action_id="GET_VERSION_CHANGES",
        description="Retrieve chronological audit log of changes relating to a software version.",
        category=ActionCategory.READ_ONLY,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["version"],
        parameter_schema=VersionTargetParams,
    ),
    "GET_REMEDIATION_PROPOSAL": ActionDefinition(
        action_id="GET_REMEDIATION_PROPOSAL",
        description="Retrieve active or historical remediation proposal with unified diff and rationale.",
        category=ActionCategory.READ_ONLY,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["proposal"],
        parameter_schema=GetRemediationProposalParams,
    ),
    "GET_BROWSER_TEST_RESULTS": ActionDefinition(
        action_id="GET_BROWSER_TEST_RESULTS",
        description="Retrieve latest or specific browser smoke test results and telemetry for an authorized version.",
        category=ActionCategory.READ_ONLY,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["version"],
        parameter_schema=GetBrowserTestResultsParams,
    ),
    "GET_TEST_INVENTORY": ActionDefinition(
        action_id="GET_TEST_INVENTORY",
        description="Retrieve authoritative Unified Test Inventory across all four testing tiers (UNIT, AI_TEST, BROWSER_SMOKE, BROWSER_JOURNEY).",
        category=ActionCategory.READ_ONLY,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["project", "version"],
        parameter_schema=GetTestInventoryParams,
    ),
    "GET_COVERAGE_REPORT": ActionDefinition(
        action_id="GET_COVERAGE_REPORT",
        description="Compute deterministic multi-tier requirement coverage across all four platform testing tiers.",
        category=ActionCategory.READ_ONLY,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["project", "version"],
        parameter_schema=GetCoverageReportParams,
    ),

    # -------------------------------------------------------------------------
    # ANALYSIS (5 Actions) - Assessment & diagnostic reasoning (no mutation)
    # -------------------------------------------------------------------------
    "RUN_STATIC_ANALYSIS": ActionDefinition(
        action_id="RUN_STATIC_ANALYSIS",
        description="Run deterministic Ruff linting and AST analysis on version source files.",
        category=ActionCategory.ANALYSIS,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["version"],
        parameter_schema=OptionalVersionTargetParams,
    ),
    "VERIFY_VERSION": ActionDefinition(
        action_id="VERIFY_VERSION",
        description="Recompute deterministic verification gate only. Strictly non-mutating (cannot create or activate versions).",
        category=ActionCategory.ANALYSIS,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["version"],
        parameter_schema=VersionTargetParams,
    ),
    "ANALYZE_FAILURE": ActionDefinition(
        action_id="ANALYZE_FAILURE",
        description="Analyze test or runtime failure evidence to produce structured diagnosis with root cause.",
        category=ActionCategory.ANALYSIS,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=True,
        supported_targets=["workflow_execution", "test_suite"],
        parameter_schema=AnalyzeFailureParams,
    ),
    "ANALYZE_COVERAGE_GAPS": ActionDefinition(
        action_id="ANALYZE_COVERAGE_GAPS",
        description="Identify active requirements lacking authoritative test coverage across any tier.",
        category=ActionCategory.ANALYSIS,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["project", "version"],
        parameter_schema=AnalyzeCoverageGapsParams,
    ),
    "ANALYZE_REGRESSION_IMPACT": ActionDefinition(
        action_id="ANALYZE_REGRESSION_IMPACT",
        description="Analyze static AST dependency impact of source code changes to identify affected tests and requirements.",
        category=ActionCategory.ANALYSIS,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["project", "version"],
        parameter_schema=AnalyzeRegressionImpactParams,
    ),

    # -------------------------------------------------------------------------
    # GENERATION (4 Actions) - Synthesis of uncommitted draft artifacts
    # -------------------------------------------------------------------------
    "GENERATE_AI_TESTS": ActionDefinition(
        action_id="GENERATE_AI_TESTS",
        description="Synthesize ephemeral AI test suite from requirements and codebase.",
        category=ActionCategory.GENERATION,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=True,
        supported_targets=["version"],
        parameter_schema=OptionalVersionTargetParams,
    ),
    "CREATE_REMEDIATION_PROPOSAL": ActionDefinition(
        action_id="CREATE_REMEDIATION_PROPOSAL",
        description="Synthesize code patch proposal from a failure diagnosis.",
        category=ActionCategory.GENERATION,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=True,
        supported_targets=["diagnosis"],
        parameter_schema=CreateRemediationProposalParams,
    ),
    "GENERATE_BROWSER_JOURNEYS": ActionDefinition(
        action_id="GENERATE_BROWSER_JOURNEYS",
        description="Synthesize, deterministically validate, adapt, and execute browser test journeys against the application.",
        category=ActionCategory.GENERATION,
        requires_confirmation=False,
        requires_execution=True,
        requires_llm=True,
        supported_targets=["version", "project"],
        parameter_schema=GenerateBrowserJourneysParams,
    ),
    "PLAN_REGRESSION": ActionDefinition(
        action_id="PLAN_REGRESSION",
        description="Generate a deterministic, validated selective regression plan mapped to changed components and requirements.",
        category=ActionCategory.GENERATION,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["project", "version"],
        parameter_schema=PlanRegressionParams,
    ),

    # -------------------------------------------------------------------------
    # EXECUTION (4 Actions) - Docker sandbox container executions
    # -------------------------------------------------------------------------
    "RUN_SANDBOX": ActionDefinition(
        action_id="RUN_SANDBOX",
        description="Execute unit test suite in isolated Docker container sandbox.",
        category=ActionCategory.EXECUTION,
        requires_confirmation=False,
        requires_execution=True,
        requires_llm=False,
        supported_targets=["version"],
        parameter_schema=OptionalVersionTargetParams,
    ),
    "RUN_AI_TESTS": ActionDefinition(
        action_id="RUN_AI_TESTS",
        description="Execute generated AI test suite in isolated Docker container sandbox.",
        category=ActionCategory.EXECUTION,
        requires_confirmation=False,
        requires_execution=True,
        requires_llm=False,
        supported_targets=["test_suite"],
        parameter_schema=RunAITestsParams,
    ),
    "RUN_BROWSER_TESTS": ActionDefinition(
        action_id="RUN_BROWSER_TESTS",
        description="Execute deterministic browser smoke tests against an isolated application container on Docker network.",
        category=ActionCategory.EXECUTION,
        requires_confirmation=False,
        requires_execution=True,
        requires_llm=False,
        supported_targets=["version"],
        parameter_schema=RunBrowserTestsParams,
    ),
    "EXECUTE_REGRESSION": ActionDefinition(
        action_id="EXECUTE_REGRESSION",
        description="Execute a validated selective regression test plan across unit, AI, and browser testing tiers.",
        category=ActionCategory.EXECUTION,
        requires_confirmation=False,
        requires_execution=True,
        requires_llm=False,
        supported_targets=["project", "version"],
        parameter_schema=ExecuteRegressionParams,
    ),


    # -------------------------------------------------------------------------
    # MUTATING (6 Actions) - Consequential state mutation (Requires confirmation)
    # -------------------------------------------------------------------------
    "APPROVE_REMEDIATION": ActionDefinition(
        action_id="APPROVE_REMEDIATION",
        description="Formally approve a remediation proposal for patch application.",
        category=ActionCategory.MUTATING,
        requires_confirmation=True,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["proposal"],
        parameter_schema=ProposalTargetParams,
    ),
    "REJECT_REMEDIATION": ActionDefinition(
        action_id="REJECT_REMEDIATION",
        description="Formally reject a remediation proposal with optional reason.",
        category=ActionCategory.MUTATING,
        requires_confirmation=True,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["proposal"],
        parameter_schema=RejectRemediationParams,
    ),
    "APPLY_REMEDIATION": ActionDefinition(
        action_id="APPLY_REMEDIATION",
        description="Apply approved patch, synthesize new immutable DevelopmentVersion, and verify in Docker.",
        category=ActionCategory.MUTATING,
        requires_confirmation=True,
        requires_execution=True,
        requires_llm=False,
        supported_targets=["proposal"],
        parameter_schema=ProposalTargetParams,
    ),
    "ACTIVATE_VERSION": ActionDefinition(
        action_id="ACTIVATE_VERSION",
        description="Update project active pointer to a verified version; supersede previously active version.",
        category=ActionCategory.MUTATING,
        requires_confirmation=True,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["version"],
        parameter_schema=ActivateVersionParams,
    ),
    "ROLLBACK_VERSION": ActionDefinition(
        action_id="ROLLBACK_VERSION",
        description="Revert project active pointer to an earlier verified version non-destructively.",
        category=ActionCategory.MUTATING,
        requires_confirmation=True,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["version"],
        parameter_schema=RollbackVersionParams,
    ),
    "RUN_WORKFLOW": ActionDefinition(
        action_id="RUN_WORKFLOW",
        description="Trigger multi-agent pipeline via WorkflowService -> WorkflowCoordinator.",
        category=ActionCategory.MUTATING,
        requires_confirmation=True,
        requires_execution=True,
        requires_llm=True,
        supported_targets=["workflow"],
        parameter_schema=RunWorkflowParams,
    ),
    "APPLY_CODE_CHANGE": ActionDefinition(
        action_id="APPLY_CODE_CHANGE",
        description="Apply a validated multi-file code change set, synthesize a new immutable DevelopmentVersion, and update active version pointer.",
        category=ActionCategory.MUTATING,
        requires_confirmation=True,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["version"],
        parameter_schema=ApplyCodeChangeParams,
    ),
    # -------------------------------------------------------------------------
    # Phase 13: Multi-Environment & Deployment Actions (7 Actions)
    # -------------------------------------------------------------------------
    "GET_ENVIRONMENTS": ActionDefinition(
        action_id="GET_ENVIRONMENTS",
        description="List all project deployment environments (DEVELOPMENT, STAGING, PRODUCTION) and active versions.",
        category=ActionCategory.READ_ONLY,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["project"],
        parameter_schema=GetEnvironmentsParams,
    ),
    "GET_ENVIRONMENT_STATUS": ActionDefinition(
        action_id="GET_ENVIRONMENT_STATUS",
        description="Retrieve detailed operational health, deployed version, and configuration for an environment.",
        category=ActionCategory.READ_ONLY,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["environment"],
        parameter_schema=GetEnvironmentStatusParams,
    ),
    "GET_DEPLOYMENT_HISTORY": ActionDefinition(
        action_id="GET_DEPLOYMENT_HISTORY",
        description="Retrieve append-only history of deployments and promotions for an environment.",
        category=ActionCategory.READ_ONLY,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["environment"],
        parameter_schema=GetDeploymentHistoryParams,
    ),
    "CHECK_PROMOTION_ELIGIBILITY": ActionDefinition(
        action_id="CHECK_PROMOTION_ELIGIBILITY",
        description="Deterministically evaluate promotion eligibility and verification gates for a version.",
        category=ActionCategory.READ_ONLY,
        requires_confirmation=False,
        requires_execution=False,
        requires_llm=False,
        supported_targets=["version", "environment"],
        parameter_schema=CheckPromotionEligibilityParams,
    ),
    "PROMOTE_VERSION": ActionDefinition(
        action_id="PROMOTE_VERSION",
        description="Promote a verified DevelopmentVersion to STAGING or PRODUCTION through deterministic verification gates.",
        category=ActionCategory.MUTATING,
        requires_confirmation=True,
        requires_execution=True,
        requires_llm=False,
        supported_targets=["version", "environment"],
        parameter_schema=PromoteVersionParams,
    ),
    "DEPLOY_TO_ENVIRONMENT": ActionDefinition(
        action_id="DEPLOY_TO_ENVIRONMENT",
        description="Deploy a verified DevelopmentVersion to a target environment.",
        category=ActionCategory.MUTATING,
        requires_confirmation=True,
        requires_execution=True,
        requires_llm=False,
        supported_targets=["version", "environment"],
        parameter_schema=DeployToEnvironmentParams,
    ),
    "ROLLBACK_ENVIRONMENT": ActionDefinition(
        action_id="ROLLBACK_ENVIRONMENT",
        description="Non-destructively revert an environment to an earlier verified version.",
        category=ActionCategory.MUTATING,
        requires_confirmation=True,
        requires_execution=True,
        requires_llm=False,
        supported_targets=["environment"],
        parameter_schema=RollbackEnvironmentParams,
    ),
}


def get_action_definition(action_id: str) -> ActionDefinition:
    """Retrieve action metadata or raise ValidationError if action is unregistered."""
    normalized_id = action_id.strip().upper()
    if normalized_id not in ACTION_REGISTRY:
        raise ValidationError(f"Unknown or unregistered action_id: '{action_id}'. Must be one of the registered actions.")
    return ACTION_REGISTRY[normalized_id]


def list_action_definitions() -> list[ActionDefinition]:
    """Return all registered action definitions."""
    return list(ACTION_REGISTRY.values())


def get_actions_by_category(category: ActionCategory) -> list[ActionDefinition]:
    """Filter registered actions by operational category."""
    return [a for a in ACTION_REGISTRY.values() if a.category == category]


def is_confirmation_required(action_id: str) -> bool:
    """Return True if the action is categorized as MUTATING requiring human confirmation."""
    action = get_action_definition(action_id)
    return action.requires_confirmation


def validate_action_parameters(action_id: str, parameters: dict[str, Any]) -> BaseModel:
    """Validate parameters against the action's authoritative Pydantic schema."""
    action = get_action_definition(action_id)
    try:
        return action.parameter_schema.model_validate(parameters or {})
    except Exception as e:
        raise ValidationError(f"Invalid parameters for action '{action_id}': {e}")
