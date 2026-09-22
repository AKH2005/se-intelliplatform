"""Data Contracts and Structured Output Models for Requirement Analysis Agent."""

import enum
import uuid
from pydantic import BaseModel, ConfigDict, Field

from app.models.requirement import RequirementPriority, RequirementType


class AnalysisSeverity(str, enum.Enum):
    """Severity classification for requirement issues and findings."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RequirementAmbiguity(BaseModel):
    """Finding representing an ambiguous, vague, or underspecified requirement."""

    requirement_id: uuid.UUID = Field(
        ...,
        description="UUID of the ambiguous requirement present in canonical context",
    )
    issue: str = Field(
        ...,
        min_length=3,
        description="Concise statement of ambiguity (e.g., 'Vague performance target')",
    )
    explanation: str = Field(
        ...,
        min_length=5,
        description="Detailed explanation of why the requirement lacks clarity or testability",
    )
    suggested_clarification: str = Field(
        ...,
        min_length=5,
        description="Specific question or phrasing to resolve the ambiguity",
    )
    severity: AnalysisSeverity = Field(
        default=AnalysisSeverity.MEDIUM,
        description="Impact of ambiguity on downstream design and testing",
    )


class RequirementConflict(BaseModel):
    """Finding representing a logical inconsistency or contradiction between two requirements."""

    requirement_id: uuid.UUID = Field(
        ...,
        description="UUID of the first conflicting requirement in canonical context",
    )
    related_requirement_id: uuid.UUID = Field(
        ...,
        description="UUID of the contradicting requirement in canonical context",
    )
    issue: str = Field(
        ...,
        min_length=3,
        description="Concise description of the contradictory constraints or behaviors",
    )
    explanation: str = Field(
        ...,
        min_length=5,
        description="Detailed rationale demonstrating how the two requirements conflict",
    )
    severity: AnalysisSeverity = Field(
        default=AnalysisSeverity.HIGH,
        description="Impact of the conflict on architectural feasibility",
    )


class MissingInformation(BaseModel):
    """Finding representing an architectural or functional gap not covered by current requirements."""

    area: str = Field(
        ...,
        min_length=2,
        description="Domain area with missing specification (e.g., 'Error Recovery', 'Authentication')",
    )
    description: str = Field(
        ...,
        min_length=5,
        description="Description of what engineering specification is absent",
    )
    reason: str = Field(
        ...,
        min_length=5,
        description="Why this information is essential before proceeding to architecture/implementation",
    )
    severity: AnalysisSeverity = Field(
        default=AnalysisSeverity.MEDIUM,
        description="Criticality of the missing specification",
    )


class RequirementRefinement(BaseModel):
    """Advisory recommendation suggesting improvements to an existing requirement.
    
    CRITICAL ARCHITECTURAL GUARANTEE:
    This is an advisory suggestion only. The agent NEVER mutates or updates requirements in the database.
    """

    requirement_id: uuid.UUID = Field(
        ...,
        description="UUID of the target requirement in canonical context",
    )
    suggestion: str = Field(
        ...,
        min_length=5,
        description="Recommended wording or structural enhancement",
    )
    reason: str = Field(
        ...,
        min_length=5,
        description="Justification for the suggested improvement",
    )
    suggested_type: RequirementType | None = Field(
        default=None,
        description="Optional recommendation to reclassify requirement type (Advisory only; never auto-mutated)",
    )
    suggested_priority: RequirementPriority | None = Field(
        default=None,
        description="Optional recommendation to reclassify requirement priority (Advisory only; never auto-mutated)",
    )


class ScopeClarification(BaseModel):
    """Clarification point identifying project scope boundaries or external integrations."""

    topic: str = Field(
        ...,
        min_length=2,
        description="Feature or operational topic requiring scope boundary confirmation",
    )
    question: str = Field(
        ...,
        min_length=5,
        description="Explicit question to be answered by the project stakeholder",
    )
    rationale: str = Field(
        ...,
        min_length=5,
        description="Why this boundary definition affects project planning or delivery",
    )


class RequirementAnalysisCandidate(BaseModel):
    """Candidate AI generation model containing solely LLM-derivable qualitative analysis.
    
    The LLM is strictly prohibited from authoritatively determining deterministic project metrics.
    Any deterministic metric keys (such as completeness_score) optionally supplied by an LLM
    are ignored in favor of backend Phase 2 canonical statistics.
    """

    model_config = ConfigDict(extra="ignore")

    summary: str = Field(
        ...,
        min_length=5,
        description="High-level engineering summary of the analyzed requirements",
    )
    ambiguities: list[RequirementAmbiguity] = Field(
        default_factory=list,
        description="List of detected ambiguous requirements",
    )
    conflicts: list[RequirementConflict] = Field(
        default_factory=list,
        description="List of detected conflicting requirement pairs",
    )
    missing_information: list[MissingInformation] = Field(
        default_factory=list,
        description="List of identified architectural or domain specification gaps",
    )
    refinements: list[RequirementRefinement] = Field(
        default_factory=list,
        description="Advisory improvement suggestions for specific requirements",
    )
    scope_clarifications: list[ScopeClarification] = Field(
        default_factory=list,
        description="Scope questions requiring stakeholder confirmation",
    )


class RequirementAnalysisOutput(BaseModel):
    """Authoritative structured output envelope for Requirement Analysis Agent.
    
    Combines verified AI qualitative findings with deterministically injected and validated
    Phase 2 context statistics.
    """

    summary: str = Field(
        ...,
        description="High-level engineering summary of the analyzed requirements",
    )
    ambiguities: list[RequirementAmbiguity] = Field(
        default_factory=list,
        description="List of detected ambiguous requirements",
    )
    conflicts: list[RequirementConflict] = Field(
        default_factory=list,
        description="List of detected conflicting requirement pairs",
    )
    missing_information: list[MissingInformation] = Field(
        default_factory=list,
        description="List of identified architectural or domain specification gaps",
    )
    refinements: list[RequirementRefinement] = Field(
        default_factory=list,
        description="Advisory improvement suggestions for specific requirements",
    )
    scope_clarifications: list[ScopeClarification] = Field(
        default_factory=list,
        description="Scope questions requiring stakeholder confirmation",
    )
    # Deterministic metrics authoritatively injected from Phase 2 canonical context
    completeness_score: float = Field(
        ...,
        description="Deterministic completion percentage derived strictly from Phase 2 RequirementStatistics.completion_percentage",
    )
    active_requirements_count: int = Field(
        ...,
        description="Count of active requirements derived strictly from Phase 2 RequirementStatistics.active_requirements",
    )
    total_requirements_count: int = Field(
        ...,
        description="Total requirements count derived strictly from Phase 2 RequirementStatistics.total_requirements",
    )
