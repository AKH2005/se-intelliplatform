# Bug / Defect Prediction Agent Architecture Specification

## 1. Purpose
The `BugPredictionAgent` is the third supervised Machine Learning agent in SE IntelliPlatform. It provides automated, empirical software module defect susceptibility classification based on verified historical static-code metrics from NASA flight software systems.

> **CRITICAL ARCHITECTURAL POLICY:**  
> The model is an empirical classification model trained on 8,912 deduplicated software modules from the NASA JM1 dataset. Its held-out test Recall is 0.4851, F1 is 0.4333, PR-AUC is 0.4254, and ROC-AUC is 0.6915. It must be treated as an advisory quality indicator, not a definitive guarantee that a module is defective or defect-free.

---

## 2. Inputs
The agent consumes the canonical `ProjectContextResponse` from the Phase 2 `ProjectContextEngine`:
- **Context Source:** `context.project.settings["ml_bug_inputs"]` (or top-level in settings).
- **Requirement:** All 21 static-code metric predictors must be explicitly provided and non-negative.
- **Zero Imputation Invariant:** If any predictor is missing, `BugFeatureUnavailableError` is raised immediately.
- **Leakage Invariant:** Target `defects` must NEVER enter the input vector or feature matrix.

---

## 3. Feature Extraction
Feature extraction is handled by `app.ml.features.bug_features.extract_bug_features()`:
- **McCabe Complexity**:
  - `loc`: Lines of code ($\ge 0.0$)
  - `v(g)`: Cyclomatic complexity ($\ge 0.0$)
  - `ev(g)`: Essential complexity ($\ge 0.0$)
  - `iv(g)`: Design complexity ($\ge 0.0$)
- **Halstead Metrics**:
  - `n`: Total operators and operands ($\ge 0.0$)
  - `v`: Program volume ($\ge 0.0$)
  - `l`: Program level / length ($\ge 0.0$)
  - `d`: Difficulty ($\ge 0.0$)
  - `i`: Intelligence content ($\ge 0.0$)
  - `e`: Effort ($\ge 0.0$)
  - `b`: Delivered bugs estimate ($\ge 0.0$)
  - `t`: Implementation time ($\ge 0.0$)
- **Line Counts**:
  - `lOCode`: Source lines of code ($\ge 0.0$)
  - `lOComment`: Lines of comments ($\ge 0.0$)
  - `lOBlank`: Blank lines ($\ge 0.0$)
  - `locCodeAndComment`: Lines containing both executable code and comments ($\ge 0.0$)
- **Raw Operator & Operand Counts**:
  - `uniq_Op`: Unique operators ($\eta_1 \ge 0.0$)
  - `uniq_Opnd`: Unique operands ($\eta_2 \ge 0.0$)
  - `total_Op`: Total operators ($N_1 \ge 0.0$)
  - `total_Opnd`: Total operands ($N_2 \ge 0.0$)
- **Branch Metric**:
  - `branchCount`: Number of branches in the module flowgraph ($\ge 0.0$)

Strictly excluded to prevent target leakage: `defects`.

---

## 4. Model
- **Algorithm:** Logistic Regression with balanced class weighting:
  `LogisticRegression(class_weight="balanced", max_iter=2000, random_state=42)`
- **Preprocessing:** `SimpleImputer(strategy="median")` + `StandardScaler()` inside a scikit-learn `Pipeline`.
- **Version:** `1.0.0`
- **Feature Schema Version:** `1.0.0`
- **Artifact:** `backend/app/ml/artifacts/bug_model_v1.joblib`
- **Integrity Validation:** Recalculates SHA-256 byte checksum (`563b2b0ffd522df7ff8f50b0a025a9e64a678fb917ac7bbddc2f15e2035e430e`) against authoritative metadata (`bug_model_v1_metadata.json`) prior to deserialization.

---

## 5. Prediction Flow
```text
                 ProjectContextResponse
                          │
                          ▼
                 Bug Feature Schema
                          │
                          ▼
                 Bug Feature Extractor
                          │
                          ▼
                  Bug Model Loader
                          │
                          ▼
              LogisticRegression Pipeline
                          │
                          ▼
               BugPredictionCandidate
                          │
                          ▼
             validate_bug_prediction_output
                          │
                          ▼
                 BugPredictionOutput
                          │
                          ▼
                     AgentResult
                          │
                          ▼
                 AgentExecutionAudit
```

---

## 6. Output Contract
- **Classification:** `prediction_label` $\in$ `{DEFECTIVE, NON_DEFECTIVE}`
- **Probability:** `predicted_probability` represents the classifier's raw positive-class probability estimate in $[0.0, 1.0]$. It is explicitly not labeled as confidence or certainty.
- **Target:** `defects`
- **Provenance:** Records `model_name`, `model_version`, `algorithm`, `training_dataset`, `feature_schema_version`, and `artifact_checksum`.
- **Features Used:** Human-readable summary of all 21 evaluated features.
- **Limitations:** Non-empty list documenting empirical model constraints.

---

## 7. Model Performance Baseline
Actual unvarnished metrics from the Phase 7C.0 training pipeline:

| Metric | 5-Fold Cross-Validation | Held-Out Test (20%) |
| :--- | :---: | :---: |
| Positive-Class Recall | 0.5072 | 0.4851 |
| Positive-Class F1 | 0.4407 | 0.4333 |
| PR-AUC | 0.4173 | 0.4254 |
| ROC-AUC | 0.6822 | 0.6915 |
| Positive-Class Precision | 0.3903 | 0.3916 |
| Accuracy *(supplementary)* | — | 0.7140 |

Held-Out Test Confusion Matrix:
- True Negatives (TN): 1,078
- False Positives (FP): 303
- False Negatives (FN): 207
- True Positives (TP): 195

---

## 8. Error Handling
- Missing features: `BugFeatureUnavailableError` (subclass of `AgentValidationError` and `ValueError`).
- Invalid feature values: Rejected via Pydantic model validation.
- Missing/Corrupted artifact: `BugModelUnavailableError` / `BugModelChecksumMismatchError`.
- Output validation errors: `validate_bug_prediction_output()` returns failing `ValidationResult`.

---

## 9. Invariants & Security
- **No LLM Usage:** Deterministic local ML execution only.
- **Read-Only:** Zero database mutation of projects, requirements, or settings.
- **No Public API:** Internal execution via `AgentExecutor`.
- **No Overstatement Language:** Prohibited words (`highly accurate`, `high confidence`, `guaranteed`, `zero defects`) are strictly rejected during validation.
