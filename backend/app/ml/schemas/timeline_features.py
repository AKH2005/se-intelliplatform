"""Authoritative Pydantic Schemas for Timeline (Duration) Prediction Features.

Defines the frozen Phase 7B feature schema:
  - Predictors: AFP, Input, Output, Enquiry, File, Interface, Resource
  - Target: Duration (months, continuous regression)
  - Strictly excluded: ID, Changed, Deleted, PDR_AFP, PDR_UFP, NPDR_AFP, NPDU_UFP,
                       Dev.Type, N_effort, Effort, Added (leakage/post-delivery/constant)
"""

import enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ResourceLevel(int, enum.Enum):
    """Categorical resource level in China dataset (1, 2, 3, 4).
    
    Represents organization/team staffing and resource tier assigned to the project.
    """
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4


class TimelineFeatureVector(BaseModel):
    """Validated 7-predictor feature vector for Timeline Prediction inference.
    
    Shared across training, serialization, runtime feature extraction, and
    future TimelinePredictionAgent execution.
    """

    model_config = ConfigDict(extra="forbid")

    afp: float = Field(
        ...,
        gt=0.0,
        description="Adjusted Function Points (AFP) representing total functional size",
    )
    input_count: float = Field(
        ...,
        ge=0.0,
        description="Number of external input transactions (Input)",
    )
    output_count: float = Field(
        ...,
        ge=0.0,
        description="Number of external output transactions (Output)",
    )
    enquiry_count: float = Field(
        ...,
        ge=0.0,
        description="Number of external inquiry transactions (Enquiry)",
    )
    file_count: float = Field(
        ...,
        ge=0.0,
        description="Number of internal logical files (File)",
    )
    interface_count: float = Field(
        ...,
        ge=0.0,
        description="Number of external interface files (Interface)",
    )
    resource_level: ResourceLevel = Field(
        ...,
        description="Resource allocation tier (1, 2, 3, or 4)",
    )

    @field_validator("afp")
    @classmethod
    def validate_afp_positive(cls, v: float) -> float:
        if v <= 0.0:
            raise ValueError("AFP must be strictly greater than 0.")
        return float(v)

    def to_model_input_dict(self) -> dict[str, Any]:
        """Convert feature vector to DataFrame row dictionary matching training column names."""
        return {
            "AFP": float(self.afp),
            "Input": float(self.input_count),
            "Output": float(self.output_count),
            "Enquiry": float(self.enquiry_count),
            "File": float(self.file_count),
            "Interface": float(self.interface_count),
            "Resource": int(self.resource_level.value),
        }


class TimelineFeatureSchema:
    """Authoritative metadata and constants for Timeline Prediction feature contracts."""

    VERSION = "1.0.0"
    TARGET_COLUMN = "Duration"
    TARGET_UNIT = "months"

    # Exactly 7 approved planning-stage features
    APPROVED_FEATURES = [
        "AFP",
        "Input",
        "Output",
        "Enquiry",
        "File",
        "Interface",
        "Resource",
    ]

    NUMERICAL_FEATURES = [
        "AFP",
        "Input",
        "Output",
        "Enquiry",
        "File",
        "Interface",
    ]

    CATEGORICAL_FEATURES = [
        "Resource",
    ]

    ALLOWED_RESOURCE_LEVELS = [1, 2, 3, 4]

    # Strictly excluded features to prevent data leakage and non-predictive noise
    EXCLUDED_LEAKAGE_FEATURES = [
        "ID",             # Non-predictive unique project identifier
        "Changed",        # Post-planning change activity metric
        "Deleted",        # Post-planning deletion activity metric
        "PDR_AFP",        # Productivity delivery rate (outcome derivative)
        "PDR_UFP",        # Productivity delivery rate (outcome derivative)
        "NPDR_AFP",       # Normalized productivity delivery rate
        "NPDU_UFP",       # Normalized productivity delivery rate
        "Dev.Type",       # Constant across all records (0.0), non-predictive
        "N_effort",       # Post-execution normalized effort outcome
        "Effort",         # Post-execution total effort outcome
        "Added",          # Excluded conservatively in v1 (uncertain planning-stage availability)
    ]
