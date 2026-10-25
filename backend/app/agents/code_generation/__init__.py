"""Code Generation Architecture and Scaffolding Module."""

from app.agents.code_generation.contracts import (
    CodeGenerationCandidate,
    CodeGenerationOutput,
    CodeGenerationPlan,
    CodeGenerationPlanCandidate,
    FileType,
    GeneratedFile,
    PlannedFile,
)
from app.agents.code_generation.generation_agent import CodeGenerationAgent
from app.agents.code_generation.planning_agent import CodeGenerationPlanningAgent
from app.agents.code_generation.validation import (
    validate_code_generation_output,
    validate_code_generation_plan,
    validate_path_safety,
)

__all__ = [
    "CodeGenerationAgent",
    "CodeGenerationCandidate",
    "CodeGenerationOutput",
    "CodeGenerationPlan",
    "CodeGenerationPlanCandidate",
    "CodeGenerationPlanningAgent",
    "FileType",
    "GeneratedFile",
    "PlannedFile",
    "validate_code_generation_output",
    "validate_code_generation_plan",
    "validate_path_safety",
]
