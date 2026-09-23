"""Contracts and Data Models for Explainability & Engineering Insights Agent."""

import enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.agents.architecture_recommendation.contracts import ArchitectureRecommendationOutput
from app.agents.bug_prediction.contracts import BugPredictionOutput
from app.agents.code_review.contracts import CodeReviewOutput
from app.agents.database_design.contracts import DatabaseDesignOutput
from app.agents.requirement_analysis.contracts import RequirementAnalysisOutput
from app.agents.risk_prediction.contracts import RiskPredictionOutput
from app.agents.test_case_generation.contracts import TestCaseGenerationOutput
from app.agents.timeline_prediction.contracts import TimelinePredictionOutput


class InsightCategory(str, enum.Enum):
    """Categorical classification of explainability and engineering insights."""

    REQUIREMENT = "REQUIREMENT"
    ARCHITECTURE = "ARCHITECTURE"
    DATABASE = "DATABASE"
    RISK = "RISK"
    TIMELINE = "TIMELINE"
    DEFECT = "DEFECT"
    TESTING = "TESTING"
    CODE_REVIEW = "CODE_REVIEW"
    CROSS_CUTTING = "CROSS_CUTTING"


class ClaimType(str, enum.Enum):
    """Epistemic classification of statements within an insight."""

    FACT = "FACT"
    INTERPRETATION = "INTERPRETATION"
    RECOMMENDATION = "RECOMMENDATION"
    LIMITATION = "LIMITATION"


class SourceReference(BaseModel):
    """Grounded reference identifying the upstream agent and entity for an insight claim."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Canonical ID of the upstream agent providing the fact or finding (e.g. 'risk-prediction')",
    )
    source_entity_id: str | None = Field(
        default=None,
        max_length=255,
        description="Identifier of the referenced entity (e.g. requirement UUID, finding ID 'CR-001', test case ID 'TC-001', model name)",
    )
    source_field: str | None = Field(
        default=None,
        max_length=100,
        description="Specific field referenced (e.g. 'predicted_risk_score', 'severity', 'evidence', 'ambiguities')",
    )
    claim_type: ClaimType = Field(
        ...,
        description="Epistemic status of the statement: FACT, INTERPRETATION, RECOMMENDATION, or LIMITATION",
    )


class EngineeringInsight(BaseModel):
    """Grounded, cross-domain engineering explanation and actionable insight."""

    model_config = ConfigDict(extra="forbid")

    insight_id: str = Field(
        ...,
        min_length=1,
        description="Authoritative sequential identifier (e.g. 'INSIGHT-001')",
    )
    category: InsightCategory = Field(
        ...,
        description="Domain categorization of the insight",
    )
    title: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Concise descriptive title of the insight",
    )
    summary: str = Field(
        ...,
        min_length=5,
        description="Brief summary of the engineering insight",
    )
    explanation: str = Field(
        ...,
        min_length=10,
        description="Detailed contextual narrative explaining the findings, trade-offs, or implications",
    )
    source_references: list[SourceReference] = Field(
        ...,
        min_length=1,
        description="Grounded upstream source references supporting this insight",
    )
    suggested_actions: list[str] = Field(
        default_factory=list,
        description="Non-destructive, actionable engineering next steps or mitigations",
    )


class ExplainabilitySummary(BaseModel):
    """Authoritative, backend-calculated summary statistics for explainability output."""

    model_config = ConfigDict(extra="forbid")

    analyzed_agents: list[str] = Field(
        ...,
        description="List of upstream agent IDs whose outputs were analyzed",
    )
    total_insights: int = Field(
        ...,
        ge=0,
        description="Total number of validated insights in the output",
    )
    insights_by_category: dict[str, int] = Field(
        default_factory=dict,
        description="Counts of insights grouped by InsightCategory",
    )
    claims_count_by_type: dict[str, int] = Field(
        default_factory=dict,
        description="Counts of source references grouped by ClaimType",
    )


class ExplainabilityCandidate(BaseModel):
    """Raw structured candidate proposed by the LLM before deterministic backend normalization."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(
        ...,
        description="Executive summary of the cross-agent analysis and insights",
    )
    insights: list[EngineeringInsight] = Field(
        default_factory=list,
        description="Proposed insights explaining the supplied upstream outputs",
    )


class ExplainabilityOutput(BaseModel):
    """Authoritative, validated structured result emitted by ExplainabilityAgent."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str = Field(
        default="explainability-insights",
        description="Executing agent identifier",
    )
    agent_version: str = Field(
        default="1.0.0",
        description="Agent implementation semantic version",
    )
    summary: str = Field(
        ...,
        description="Executive summary synthesizing the engineering findings and explanations",
    )
    insights: list[EngineeringInsight] = Field(
        ...,
        description="Validated collection of engineering insights with verified source traceability",
    )
    metrics: ExplainabilitySummary = Field(
        ...,
        description="Authoritative backend-calculated explainability summary metrics",
    )
    limitations: list[str] = Field(
        ...,
        description="Source-driven and platform limitations relevant to the explained outputs",
    )


class ExplainabilityInput(BaseModel):
    """Strongly typed input payload envelope for ExplainabilityAgent.

    Consumes validated outputs from any subset of existing platform agents.
    At least one upstream agent output must be provided.
    """

    model_config = ConfigDict(extra="forbid")

    target_scope: str | None = Field(
        default=None,
        max_length=500,
        description="Optional focus area or specific component scope to explain",
    )
    user_query: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional natural-language developer question (e.g. 'Why is risk level high?')",
    )

    requirement_analysis: RequirementAnalysisOutput | None = Field(
        default=None,
        description="Optional validated Phase 4 RequirementAnalysisOutput",
    )
    architecture_recommendation: ArchitectureRecommendationOutput | None = Field(
        default=None,
        description="Optional validated Phase 5 ArchitectureRecommendationOutput",
    )
    database_design: DatabaseDesignOutput | None = Field(
        default=None,
        description="Optional validated Phase 6 DatabaseDesignOutput",
    )
    risk_prediction: RiskPredictionOutput | None = Field(
        default=None,
        description="Optional validated Phase 7A RiskPredictionOutput",
    )
    timeline_prediction: TimelinePredictionOutput | None = Field(
        default=None,
        description="Optional validated Phase 7B TimelinePredictionOutput",
    )
    bug_prediction: BugPredictionOutput | None = Field(
        default=None,
        description="Optional validated Phase 7C BugPredictionOutput",
    )
    test_case_generation: TestCaseGenerationOutput | None = Field(
        default=None,
        description="Optional validated Phase 8.0 TestCaseGenerationOutput",
    )
    code_review: CodeReviewOutput | None = Field(
        default=None,
        description="Optional validated Phase 8.1 CodeReviewOutput",
    )

    @model_validator(mode="after")
    def validate_at_least_one_output(self) -> "ExplainabilityInput":
        """Deterministic invariant: At least one upstream agent output must be provided."""
        outputs = [
            self.requirement_analysis,
            self.architecture_recommendation,
            self.database_design,
            self.risk_prediction,
            self.timeline_prediction,
            self.bug_prediction,
            self.test_case_generation,
            self.code_review,
        ]
        if not any(out is not None for out in outputs):
            raise ValueError(
                "ExplainabilityInput must contain at least one upstream agent output to explain."
            )
        return self
