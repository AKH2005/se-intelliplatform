"""Authoritative Pydantic Schemas for Bug / Defect Prediction Features.

Defines the frozen Phase 7C feature schema:
  - Predictors: 21 static-code metrics from JM1 dataset
  - Target: defects (binary classification, "true" vs "false")
  - Strictly excluded: defects (target leakage), synthetic/heuristic proxies
"""

import math
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, model_validator


class BugFeatureVector(BaseModel):
    """Validated 21-predictor feature vector for Bug Prediction inference.

    Shared across training, serialization, runtime feature extraction, and
    future BugPredictionAgent execution.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    # McCabe-style complexity metrics
    loc: float = Field(
        ...,
        ge=0.0,
        description="McCabe's line count of code",
    )
    v_g: float = Field(
        ...,
        alias="v(g)",
        ge=0.0,
        description="McCabe Cyclomatic Complexity",
    )
    ev_g: float = Field(
        ...,
        alias="ev(g)",
        ge=0.0,
        description="McCabe Essential Complexity",
    )
    iv_g: float = Field(
        ...,
        alias="iv(g)",
        ge=0.0,
        description="McCabe Design Complexity",
    )

    # Halstead-derived metrics
    n: float = Field(
        ...,
        ge=0.0,
        description="Halstead total operators + operands (N = N1 + N2)",
    )
    v: float = Field(
        ...,
        ge=0.0,
        description="Halstead Volume (V)",
    )
    l: float = Field(
        ...,
        ge=0.0,
        description="Halstead Program Length / Level (L)",
    )
    d: float = Field(
        ...,
        ge=0.0,
        description="Halstead Difficulty (D)",
    )
    i: float = Field(
        ...,
        ge=0.0,
        description="Halstead Intelligence (I)",
    )
    e: float = Field(
        ...,
        ge=0.0,
        description="Halstead Effort (E)",
    )
    b: float = Field(
        ...,
        ge=0.0,
        description="Halstead Delivered Bugs (B)",
    )
    t: float = Field(
        ...,
        ge=0.0,
        description="Halstead Time to Implement (T)",
    )

    # Line count metrics
    lOCode: float = Field(
        ...,
        alias="lOCode",
        ge=0.0,
        description="Halstead's count of lines of code",
    )
    lOComment: float = Field(
        ...,
        alias="lOComment",
        ge=0.0,
        description="Halstead's count of lines of comments",
    )
    lOBlank: float = Field(
        ...,
        alias="lOBlank",
        ge=0.0,
        description="Halstead's count of blank lines",
    )
    locCodeAndComment: float = Field(
        ...,
        alias="locCodeAndComment",
        ge=0.0,
        description="Count of lines containing both code and comments",
    )

    # Halstead raw operator/operand counts
    uniq_Op: float = Field(
        ...,
        alias="uniq_Op",
        ge=0.0,
        description="Unique operators (mu1 / eta1)",
    )
    uniq_Opnd: float = Field(
        ...,
        alias="uniq_Opnd",
        ge=0.0,
        description="Unique operands (mu2 / eta2)",
    )
    total_Op: float = Field(
        ...,
        alias="total_Op",
        ge=0.0,
        description="Total operators (N1)",
    )
    total_Opnd: float = Field(
        ...,
        alias="total_Opnd",
        ge=0.0,
        description="Total operands (N2)",
    )

    # Flow / branch metric
    branchCount: float = Field(
        ...,
        alias="branchCount",
        ge=0.0,
        description="Flow graph branch count",
    )

    @model_validator(mode="after")
    def validate_finite_values(self) -> "BugFeatureVector":
        """Verify that all metrics are finite floating-point numbers (no NaN, Inf)."""
        for field_name in self.model_fields_set:
            val = getattr(self, field_name)
            if isinstance(val, (int, float)):
                if math.isnan(val) or math.isinf(val):
                    raise ValueError(f"Feature '{field_name}' must be a finite number, got {val}.")
        return self

    def to_model_input_dict(self) -> dict[str, float]:
        """Convert feature vector to DataFrame row dictionary matching exact JM1 ARFF column names."""
        return {
            "loc": float(self.loc),
            "v(g)": float(self.v_g),
            "ev(g)": float(self.ev_g),
            "iv(g)": float(self.iv_g),
            "n": float(self.n),
            "v": float(self.v),
            "l": float(self.l),
            "d": float(self.d),
            "i": float(self.i),
            "e": float(self.e),
            "b": float(self.b),
            "t": float(self.t),
            "lOCode": float(self.lOCode),
            "lOComment": float(self.lOComment),
            "lOBlank": float(self.lOBlank),
            "locCodeAndComment": float(self.locCodeAndComment),
            "uniq_Op": float(self.uniq_Op),
            "uniq_Opnd": float(self.uniq_Opnd),
            "total_Op": float(self.total_Op),
            "total_Opnd": float(self.total_Opnd),
            "branchCount": float(self.branchCount),
        }


class BugFeatureSchema:
    """Authoritative metadata and constants for Bug Prediction feature contracts."""

    VERSION = "1.0.0"
    TARGET_COLUMN = "defects"
    POSITIVE_CLASS = "true"
    NEGATIVE_CLASS = "false"

    # Exactly 21 approved JM1 static-code metric predictors in original order
    APPROVED_FEATURES: list[str] = [
        "loc",
        "v(g)",
        "ev(g)",
        "iv(g)",
        "n",
        "v",
        "l",
        "d",
        "i",
        "e",
        "b",
        "t",
        "lOCode",
        "lOComment",
        "lOBlank",
        "locCodeAndComment",
        "uniq_Op",
        "uniq_Opnd",
        "total_Op",
        "total_Opnd",
        "branchCount",
    ]

    NUMERICAL_FEATURES: list[str] = APPROVED_FEATURES

    # Strictly excluded features to prevent data leakage
    EXCLUDED_LEAKAGE_FEATURES: list[str] = [
        "defects",  # Ground-truth defect target
    ]
