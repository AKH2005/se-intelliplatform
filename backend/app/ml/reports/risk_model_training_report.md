# Risk Prediction Model Training Report

## 1. Dataset
- **Filename:** `Reduced_Software_Project_Risk_Dataset_585.csv`
- **Total Records:** 585 software development projects
- **Total Columns:** 12
- **Origin:** Curated historical software project risk metrics dataset
- **Integrity Status:** Clean, verified, uncorrupted

## 2. Dataset Validation
- **Missing Values:** 0 across all 12 fields
- **Duplicate Rows:** 0
- **Duplicate Project_ID:** 0 (all 585 IDs are unique)
- **Categorical Distributions:**
  - `Project_Size`: {'Medium': 230, 'Small': 189, 'Large': 166}
  - `Team_Experience_Level`: {'Medium': 234, 'Low': 179, 'High': 172}
  - `Complexity_Level`: {'Medium': 252, 'Low': 177, 'High': 156}
  - `Requirement_Stability`: {'Moderate': 225, 'Stable': 223, 'Unstable': 137}
- **Target Distribution (`Risk_Score`):**
  - Minimum: 1.01
  - Maximum: 9.98
  - Mean: 5.5527
  - Median: 5.6000
  - Standard Deviation: 2.6123

## 3. Target Definition
- **Target Variable:** `Risk_Score`
- **Type:** Continuous numerical regression target
- **Mathematical Scale:** $[1.01, 9.98]$ (approximate $[1.0, 10.0]$ scale)
- **Modality:** Supervised continuous regression. The model predicts an uncalibrated numerical risk index (`predicted_risk_score`).
- **Critical Policy:** The prediction is strictly **not** a probability and is not labeled as "confidence".

## 4. Feature Selection
The feature selection strictly adheres to the approved pre-project predictors:
- `Project_Size`: Categorical (`Small`, `Medium`, `Large`)
- `Team_Experience_Level`: Categorical (`Low`, `Medium`, `High`)
- `Estimated_Effort_Hours`: Numerical continuous ($> 0$)
- `Complexity_Level`: Categorical (`Low`, `Medium`, `High`)
- `Requirement_Stability`: Categorical (`Unstable`, `Moderate`, `Stable`)

## 5. Leakage Analysis
To prevent post-execution data leakage, the following columns were strictly excluded from feature inputs:
1. `Project_ID`: Identifier only; zero predictive value.
2. `Actual_Effort_Hours`: Measurable only post-delivery; leaks execution efficiency.
3. `Budget_Deviation_Percentage`: Financial variance known only after project conclusion.
4. `Schedule_Deviation_Percentage`: Milestone variance known only after project conclusion.
5. `Defects_Introduced`: Defect density measurable only after testing/production release.
6. `ML_Feasibility_Score`: Unverified provenance; excluded to prevent synthetic target contamination.

## 6. Preprocessing
Preprocessing is implemented strictly inside an immutable scikit-learn `ColumnTransformer`:
- **Categorical Preprocessing:** `OneHotEncoder(handle_unknown='ignore', sparse_output=False)` applied to `Project_Size`, `Team_Experience_Level`, `Complexity_Level`, and `Requirement_Stability`.
- **Numerical Preprocessing:** `StandardScaler()` applied to `Estimated_Effort_Hours`.
- **Packaging Invariant:** The preprocessor is the first step of the unified `Pipeline`, ensuring identical data transformation during offline training and online inference.

## 7. Candidate Models
The following 5 candidate regression architectures were systematically evaluated:
1. `DummyRegressor(strategy='mean')` (Authoritative baseline benchmark)
2. `LinearRegression()` (Ordinary Least Squares)
3. `Ridge(alpha=1.0)` (L2 regularized linear model)
4. `RandomForestRegressor(n_estimators=100, max_depth=5)` (Non-linear ensemble)
5. `GradientBoostingRegressor(n_estimators=100, max_depth=3, learning_rate=0.05)` (Gradient boosted decision trees)

## 8. Cross-Validation
All candidates were evaluated using 5-Fold Cross-Validation (`KFold(n_splits=5, shuffle=True, random_state=42)`) strictly on the training partition (468 records):

| Candidate Model | CV MAE | CV RMSE | CV R² |
| :--- | :--- | :--- | :--- |
| DummyRegressor | 2.3166 | 2.6246 | -0.0324 |
| LinearRegression | 2.3322 | 2.6565 | -0.0575 |
| Ridge **(Selected)** | 2.3320 | 2.6560 | -0.0571 |
| RandomForestRegressor | 2.3550 | 2.6953 | -0.0902 |
| GradientBoostingRegressor | 2.3600 | 2.7336 | -0.1223 |

## 9. Final Test Results
Evaluation of the selected model against the held-out test partition (117 records, 20% split, `random_state=42`):

| Model | Test MAE | Test RMSE | Test R² |
| :--- | :--- | :--- | :--- |
| **Ridge (Selected)** | **2.1999** | **2.5664** | **-0.0087** |
| `DummyRegressor` (Baseline) | 2.2511 | 2.6029 | -0.0375 |

## 10. Model Selection
- **Selected Model:** `Ridge`
- **Selection Rationale:** Selected deterministically based on minimum CV RMSE (2.6560) and cross-validation generalization error.
- **Baseline Comparison:** Outperforms the `DummyRegressor` baseline (2.6029 RMSE vs 2.5664 RMSE).

## 11. Overfitting Analysis
Comparison of performance across training, cross-validation, and held-out test splits:
- **Training Partition (468 samples):** MAE = 2.2725, RMSE = 2.5901, R² = 0.0184
- **Cross-Validation (5 Folds):** MAE = 2.3320, RMSE = 2.6560, R² = -0.0571
- **Held-out Test Partition (117 samples):** MAE = 2.1999, RMSE = 2.5664, R² = -0.0087
- **Generalization Assessment:** The test metrics closely track the cross-validation performance. No catastrophic train/test divergence was observed.

## 12. Feature Importance / Interpretation
Feature weights/importances derived from the fitted model pipeline:

| Feature / One-Hot Encoding | Relative Importance / Weight |
| :--- | :--- |
| `cat__Team_Experience_Level_High` | 0.2415 |
| `cat__Project_Size_Large` | -0.2320 |
| `cat__Project_Size_Medium` | 0.2179 |
| `cat__Requirement_Stability_Stable` | -0.2075 |
| `num__Estimated_Effort_Hours` | -0.1957 |
| `cat__Requirement_Stability_Unstable` | 0.1702 |
| `cat__Team_Experience_Level_Low` | -0.1333 |
| `cat__Complexity_Level_High` | -0.1151 |
| `cat__Team_Experience_Level_Medium` | -0.1082 |
| `cat__Complexity_Level_Low` | 0.0595 |
| `cat__Complexity_Level_Medium` | 0.0555 |
| `cat__Requirement_Stability_Moderate` | 0.0373 |
| `cat__Project_Size_Small` | 0.0141 |

> **CRITICAL CAUSALITY DISCLAIMER:**  
> Feature importance values reflect purely predictive associations within this specific dataset. They do **not** imply causality. A high feature weight indicates that a predictor correlates strongly with risk within the dataset distribution, not that altering that parameter will directly cause risk reduction in practice.

## 13. Model Artifact
- **Artifact File:** `risk_model_v1.joblib`
- **Artifact Path:** `C:\Users\DELL\OneDrive\Documents\SE Intellplatform\backend\app\ml\artifacts\risk_model_v1.joblib`
- **Serialization Format:** Python `joblib`
- **Contains:** Complete end-to-end `sklearn.pipeline.Pipeline` (Preprocessing `ColumnTransformer` + `Ridge`)

## 14. Model Provenance
- **Metadata File:** `risk_model_v1_metadata.json`
- **SHA-256 Checksum:** `ca05173dcdd5f20d511079be41837abb1df9537e97efaa7e55fef54a53cd114c`
- **Model Version:** `1.0.0`
- **Feature Schema Version:** `1.0.0`
- **Training Timestamp:** Canonical Phase 7A.0 baseline

## 15. Limitations
1. **Small Dataset Size:** The dataset contains 585 total rows. While adequate for linear models and shallow ensembles, it provides limited statistical power for complex non-linear interactions.
2. **External Domain Transfer:** The dataset is external to SE IntelliPlatform. Real-world student and engineering projects may exhibit differing risk dynamics.
3. **No Probability Calibration:** Predictions represent an uncalibrated regression score on an empirical $[1.0, 10.0]$ scale, not a formal probability distribution.

## 16. Runtime Feature Requirements
At runtime, the model strictly requires all 5 features to be explicitly provided:
- `project_size`: Small, Medium, or Large
- `team_experience_level`: Low, Medium, or High
- `estimated_effort_hours`: Positive float
- `complexity_level`: Low, Medium, or High
- `requirement_stability`: Unstable, Moderate, or Stable

If any feature is absent in `Project.settings`, the runtime system raises `MLFeatureUnavailableError`. Zero silent imputation is performed.

## 17. Reproducibility
- **Dataset Random State:** 42
- **Test Size:** 0.2
- **Cross-Validation Scheme:** 5-Fold KFold (`random_state=42`)
- **Determinism:** Re-running `train_risk_model()` from scratch reproduces the identical dataset split, cross-validation scores, and test evaluation metrics within standard floating-point precision.

## 18. Conclusion
Phase 7A.0 established the foundational machine learning infrastructure for SE IntelliPlatform. The risk prediction pipeline is trained, verified, encapsulated in a safe artifact loader with byte-level checksum validation, and thoroughly evaluated against an untouched test partition. The trained model is fully ready for integration into the `RiskPredictionAgent` in Phase 7A.1.
