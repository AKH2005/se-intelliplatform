"""Versioned Feature Contracts and Validation Schemas for Risk Prediction.

Defines the authoritative, shared feature contract between offline training,
serialized model pipelines, and online inference.
"""

import enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectSize(str, enum.Enum):
    """Categorization of project scope and magnitude."""
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"


class TeamExperienceLevel(str, enum.Enum):
    """Staffing and developer domain experience level."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class ComplexityLevel(str, enum.Enum):
    """Inherent architectural and domain complexity level."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class RequirementStability(str, enum.Enum):
    """Requirement volatility and scope churn assessment."""
    UNSTABLE = "Unstable"
    MODERATE = "Moderate"
    STABLE = "Stable"


class RiskFeatureVector(BaseModel):
    """Validated 5-predictor feature vector for Risk Prediction model inference.
    
    Shared identically across:
      - Training dataset feature selection
      - Saved scikit-learn preprocessing ColumnTransformer
      - Runtime feature extraction from ProjectContext
      - Future RiskPredictionAgent execution
    """

    model_config = ConfigDict(extra="forbid")

    project_size: ProjectSize = Field(
        ...,
        description="Explicit project size classification (Small, Medium, Large)",
    )
    team_experience_level: TeamExperienceLevel = Field(
        ...,
        description="Team experience level (Low, Medium, High)",
    )
    estimated_effort_hours: float = Field(
        ...,
        gt=0.0,
        description="Total estimated effort in engineering hours (must be strictly positive)",
    )
    complexity_level: ComplexityLevel = Field(
        ...,
        description="Project technical and domain complexity (Low, Medium, High)",
    )
    requirement_stability: RequirementStability = Field(
        ...,
        description="Requirement churn stability assessment (Unstable, Moderate, Stable)",
    )

    @field_validator("estimated_effort_hours")
    @classmethod
    def validate_effort_positive(cls, v: float) -> float:
        if v <= 0.0:
            raise ValueError("estimated_effort_hours must be strictly greater than 0.")
        return v

    def to_model_input_dict(self) -> dict[str, Any]:
        """Convert to dictionary matching dataset column naming convention."""
        return {
            "Project_Size": self.project_size.value,
            "Team_Experience_Level": self.team_experience_level.value,
            "Estimated_Effort_Hours": float(self.estimated_effort_hours),
            "Complexity_Level": self.complexity_level.value,
            "Requirement_Stability": self.requirement_stability.value,
        }


class ProjectMLSettings(BaseModel):
    """Runtime contract for project-level ML attributes stored in Project.settings.
    
    Enables supplying pre-project parameters via the existing JSONB settings field
    without requiring disruptive database schema migrations.
    """

    model_config = ConfigDict(extra="ignore")

    project_size: ProjectSize | None = Field(
        default=None,
        description="Project scale: Small, Medium, or Large",
    )
    team_experience_level: TeamExperienceLevel | None = Field(
        default=None,
        description="Team experience: Low, Medium, or High",
    )
    estimated_effort_hours: float | None = Field(
        default=None,
        gt=0.0,
        description="Estimated engineering effort hours (> 0)",
    )
    complexity_level: ComplexityLevel | None = Field(
        default=None,
        description="Complexity level: Low, Medium, or High",
    )
    requirement_stability: RequirementStability | None = Field(
        default=None,
        description="Requirement stability: Unstable, Moderate, or Stable",
    )


class RiskFeatureSchema:
    """Metadata describing the versioned feature contract."""

    VERSION: str = "1.0.0"
    TARGET_COLUMN: str = "Risk_Score"
    CATEGORICAL_FEATURES: list[str] = [
        "Project_Size",
        "Team_Experience_Level",
        "Complexity_Level",
        "Requirement_Stability",
    ]
    NUMERICAL_FEATURES: list[str] = [
        "Estimated_Effort_Hours",
    ]
    APPROVED_FEATURES: list[str] = [
        "Project_Size",
        "Team_Experience_Level",
        "Estimated_Effort_Hours",
        "Complexity_Level",
        "Requirement_Stability",
    ]
    EXCLUDED_LEAKAGE_FEATURES: list[str] = [
        "Project_ID",
        "Actual_Effort_Hours",
        "Budget_Deviation_Percentage",
        "Schedule_Deviation_Percentage",
        "Defects_Introduced",
        "ML_Feasibility_Score",
    ]
    ALLOWED_CATEGORIES: dict[str, list[str]] = {
        "Project_Size": [e.value for e in ProjectSize],
        "Team_Experience_Level": [e.value for e in TeamExperienceLevel],
        "Complexity_Level": [e.value for e in ComplexityLevel],
        "Requirement_Stability": [e.value for e in RequirementStability],
    }
