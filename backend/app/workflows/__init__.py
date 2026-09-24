"""Workflow Orchestration Package.

Provides deterministic multi-agent workflow coordination, strongly typed contracts,
and predefined software engineering intelligence pipelines.
"""

from app.workflows.contracts import (
    WorkflowDefinition,
    WorkflowInput,
    WorkflowResult,
    WorkflowStatus,
    WorkflowStep,
    WorkflowStepResult,
    WorkflowStepStatus,
)
from app.workflows.coordinator import WorkflowCoordinator
from app.workflows.pipelines import (
    WORKFLOW_COMPREHENSIVE_AUDIT_ID,
    WORKFLOW_PROJECT_ESTIMATION_ID,
    WORKFLOW_SOFTWARE_DESIGN_ID,
    build_comprehensive_audit_workflow,
    build_project_estimation_workflow,
    build_software_design_workflow,
    resolve_step_kwargs,
)

__all__ = [
    "WorkflowStatus",
    "WorkflowStepStatus",
    "WorkflowStep",
    "WorkflowDefinition",
    "WorkflowInput",
    "WorkflowStepResult",
    "WorkflowResult",
    "WorkflowCoordinator",
    "WORKFLOW_SOFTWARE_DESIGN_ID",
    "WORKFLOW_PROJECT_ESTIMATION_ID",
    "WORKFLOW_COMPREHENSIVE_AUDIT_ID",
    "build_software_design_workflow",
    "build_project_estimation_workflow",
    "build_comprehensive_audit_workflow",
    "resolve_step_kwargs",
]
