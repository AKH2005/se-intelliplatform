"""Unit tests for ML pipeline reproducibility and determinism."""

import pandas as pd
import pytest

from app.ml.inference.model_loader import get_risk_model_loader, predict_risk
from app.ml.schemas.risk_features import (
    ComplexityLevel,
    ProjectSize,
    RequirementStability,
    RiskFeatureVector,
    TeamExperienceLevel,
)


def test_inference_determinism():
    """Verify that identical inputs produce bitwise deterministic predictions."""
    vector = RiskFeatureVector(
        project_size=ProjectSize.LARGE,
        team_experience_level=TeamExperienceLevel.MEDIUM,
        estimated_effort_hours=1250.0,
        complexity_level=ComplexityLevel.HIGH,
        requirement_stability=RequirementStability.UNSTABLE,
    )

    pred1 = predict_risk(vector)
    pred2 = predict_risk(vector)
    assert pred1 == pred2


def test_pipeline_handles_all_category_permutations():
    """Verify the trained pipeline accepts all valid enum combinations without error."""
    loader = get_risk_model_loader()
    pipeline = loader.load_model()

    for size in ProjectSize:
        for team in TeamExperienceLevel:
            for comp in ComplexityLevel:
                for req in RequirementStability:
                    df = pd.DataFrame([{
                        "Project_Size": size.value,
                        "Team_Experience_Level": team.value,
                        "Estimated_Effort_Hours": 500.0,
                        "Complexity_Level": comp.value,
                        "Requirement_Stability": req.value,
                    }])
                    pred = float(pipeline.predict(df)[0])
                    assert isinstance(pred, float)
                    assert 1.0 <= pred <= 10.0
