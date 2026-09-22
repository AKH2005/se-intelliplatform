"""Unit tests for Timeline Prediction pipeline reproducibility and determinism."""

import pandas as pd
import pytest

from app.ml.inference.timeline_model_loader import get_timeline_model_loader, predict_duration
from app.ml.schemas.timeline_features import ResourceLevel, TimelineFeatureVector


def test_timeline_inference_determinism():
    """Verify that identical inputs produce bitwise deterministic duration predictions."""
    vector = TimelineFeatureVector(
        afp=500.0,
        input_count=60.0,
        output_count=40.0,
        enquiry_count=30.0,
        file_count=20.0,
        interface_count=10.0,
        resource_level=ResourceLevel.LEVEL_2,
    )

    pred1 = predict_duration(vector)
    pred2 = predict_duration(vector)
    assert pred1 == pred2


def test_timeline_pipeline_handles_all_resource_levels():
    """Verify the trained pipeline accepts all valid Resource levels without error."""
    loader = get_timeline_model_loader()
    pipeline = loader.load_model()

    for level in ResourceLevel:
        df = pd.DataFrame([{
            "AFP": 400.0,
            "Input": 30.0,
            "Output": 20.0,
            "Enquiry": 15.0,
            "File": 10.0,
            "Interface": 5.0,
            "Resource": level.value,
        }])
        pred = float(pipeline.predict(df)[0])
        assert isinstance(pred, float)
        assert pred > 0.0
