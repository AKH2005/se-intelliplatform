"""Unit tests for Bug / Defect Prediction pipeline reproducibility and deterministic behavior."""

import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import StratifiedKFold, train_test_split

from app.ml.inference.bug_model_loader import get_bug_model_loader
from app.ml.schemas.bug_features import BugFeatureSchema, BugFeatureVector
from app.ml.training.train_bug_model import (
    deduplicate_dataset,
    find_dataset_path,
    load_dataset,
)


@pytest.fixture(scope="module")
def processed_jm1_data() -> tuple[pd.DataFrame, pd.Series]:
    """Load, deduplicate, and partition JM1 data."""
    df = load_dataset(find_dataset_path())
    df_dedup, _ = deduplicate_dataset(df)
    X = df_dedup[BugFeatureSchema.APPROVED_FEATURES].copy()
    y = (df_dedup[BugFeatureSchema.TARGET_COLUMN] == "true").astype(int)
    return X, y


def test_deterministic_train_test_split(processed_jm1_data: tuple[pd.DataFrame, pd.Series]):
    """Verify that train_test_split produces identical row partitions with random_state=42."""
    X, y = processed_jm1_data

    X_tr1, X_te1, y_tr1, y_te1 = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    X_tr2, X_te2, y_tr2, y_te2 = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    assert X_tr1.index.equals(X_tr2.index)
    assert X_te1.index.equals(X_te2.index)
    assert y_tr1.equals(y_tr2)
    assert y_te1.equals(y_te2)


def test_deterministic_cv_folds(processed_jm1_data: tuple[pd.DataFrame, pd.Series]):
    """Verify that StratifiedKFold produces identical splits with random_state=42."""
    X, y = processed_jm1_data
    cv1 = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv2 = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    splits1 = list(cv1.split(X, y))
    splits2 = list(cv2.split(X, y))

    for (tr1, te1), (tr2, te2) in zip(splits1, splits2):
        assert np.array_equal(tr1, tr2)
        assert np.array_equal(te1, te2)


def test_deterministic_inference_predictions():
    """Verify that repeated inferences on identical feature vectors produce identical results."""
    loader = get_bug_model_loader()
    loader.reset_cache()

    vec = BugFeatureVector(
        loc=50.0,
        v_g=8.0,
        ev_g=4.0,
        iv_g=5.0,
        n=150.0,
        v=800.0,
        l=0.04,
        d=25.0,
        i=32.0,
        e=20000.0,
        b=0.27,
        t=1111.0,
        lOCode=40.0,
        lOComment=5.0,
        lOBlank=5.0,
        locCodeAndComment=2.0,
        uniq_Op=20.0,
        uniq_Opnd=30.0,
        total_Op=90.0,
        total_Opnd=60.0,
        branchCount=15.0,
    )

    pred1 = loader.predict(vec)
    pred2 = loader.predict(vec)
    prob1 = loader.predict_proba(vec)
    prob2 = loader.predict_proba(vec)

    assert pred1 == pred2
    assert prob1 == prob2


def test_select_best_model_hierarchy():
    """Verify select_best_model enforces the frozen hierarchy:
    Recall -> F1 -> PR-AUC -> Simplicity
    """
    from app.ml.training.train_bug_model import select_best_model

    simplicity_order = ["LogisticRegression", "RandomForestClassifier", "DummyClassifier"]

    # 1. Higher recall wins
    cand1 = {
        "LogisticRegression": {"cv_recall": 0.50, "cv_f1": 0.40, "cv_pr_auc": 0.30},
        "RandomForestClassifier": {"cv_recall": 0.60, "cv_f1": 0.30, "cv_pr_auc": 0.20},
    }
    best, _ = select_best_model(cand1, simplicity_order)
    assert best == "RandomForestClassifier"

    # 2. Tied recall -> higher F1 wins
    cand2 = {
        "LogisticRegression": {"cv_recall": 0.50, "cv_f1": 0.45, "cv_pr_auc": 0.30},
        "RandomForestClassifier": {"cv_recall": 0.50, "cv_f1": 0.40, "cv_pr_auc": 0.35},
    }
    best, _ = select_best_model(cand2, simplicity_order)
    assert best == "LogisticRegression"

    # 3. Tied recall and F1 -> higher PR-AUC wins
    cand3 = {
        "LogisticRegression": {"cv_recall": 0.50, "cv_f1": 0.45, "cv_pr_auc": 0.30},
        "RandomForestClassifier": {"cv_recall": 0.50, "cv_f1": 0.45, "cv_pr_auc": 0.35},
    }
    best, _ = select_best_model(cand3, simplicity_order)
    assert best == "RandomForestClassifier"

    # 4. Completely tied -> simplicity order wins
    cand4 = {
        "RandomForestClassifier": {"cv_recall": 0.50, "cv_f1": 0.45, "cv_pr_auc": 0.35},
        "LogisticRegression": {"cv_recall": 0.50, "cv_f1": 0.45, "cv_pr_auc": 0.35},
    }
    best, _ = select_best_model(cand4, simplicity_order)
    assert best == "LogisticRegression"
