# Timeline (Duration) Prediction Model Training Report

## 1. Dataset
- **Dataset Name:** China Software Project Estimation Dataset
- **Total Records:** 499 software development projects
- **Total Original Attributes:** 19
- **Origin:** Empirical software metrics repository (PROMISE / ISBSG derived)
- **Integrity Status:** Clean, verified, uncorrupted

## 2. Dataset Validation
- **Missing Values:** 0 across all 19 fields
- **Duplicate Rows:** 0
- **Duplicate Project IDs (`ID`):** 0 (all 499 project IDs are unique)
- **Categorical Distribution (`Resource`):**
  - Resource Level 1: 346 projects
  - Resource Level 2: 108 projects
  - Resource Level 4: 31 projects
  - Resource Level 3: 14 projects
- **Target Distribution (`Duration` in months):**
  - Minimum: 1.00 months
  - Maximum: 84.00 months
  - Mean: 8.7192 months
  - Median: 7.0000 months
  - 25th Percentile: 4.0000 months
  - 75th Percentile: 11.0000 months
  - Standard Deviation: 7.3471 months

## 3. Target Definition
- **Target Variable:** `Duration`
- **Unit of Measure:** Months
- **Type:** Continuous numerical regression target
- **Mathematical Scale:** $[1.0, 84.0]$ months
- **Modality:** Supervised continuous regression. The model predicts project elapsed duration in months.
- **Critical Policy:** Strictly NOT converted to classification, risk bands, probabilities, or arbitrary duration categories.

## 4. Feature Definitions
The feature selection strictly adheres to the 7 approved planning-stage predictors:
- `AFP`: Adjusted Function Points (total functional size, continuous numerical)
- `Input`: Number of external input transactions (continuous numerical)
- `Output`: Number of external output transactions (continuous numerical)
- `Enquiry`: Number of external inquiry transactions (continuous numerical)
- `File`: Number of internal logical files (continuous numerical)
- `Interface`: Number of external interface files (continuous numerical)
- `Resource`: Resource allocation tier (categorical levels: 1, 2, 3, 4)

## 5. Leakage Analysis
To prevent post-execution data leakage and artificial score inflation, 11 variables were strictly excluded:
1. `ID`: Non-predictive identifier.
2. `Changed`: Post-planning requirement change activity; leaks lifecycle volatility.
3. `Deleted`: Post-planning requirement deletion activity; leaks lifecycle scope adjustments.
4. `PDR_AFP`: Productivity delivery rate; calculated directly from effort and functional size.
5. `PDR_UFP`: Productivity delivery rate on unadjusted functional size.
6. `NPDR_AFP`: Normalized productivity delivery rate.
7. `NPDU_UFP`: Normalized productivity delivery rate.
8. `Dev.Type`: Constant across all records (0.0), provides zero discriminative variance.
9. `N_effort`: Normalized effort outcome; known only post-delivery.
10. `Effort`: Total engineering effort hours; primary project delivery outcome.
11. `Added`: Excluded conservatively in v1 methodology due to uncertain planning-stage availability.

## 6. Excluded Features
| Variable | Role in Dataset | Exclusion Rationale |
| :--- | :--- | :--- |
| `ID` | Identifier | Non-predictive sequence ID |
| `Changed` | Change metric | Post-baseline development volatility |
| `Deleted` | Change metric | Post-baseline scope contraction |
| `PDR_AFP` | Ratio | Productivity metric derived from outcome |
| `PDR_UFP` | Ratio | Productivity metric derived from outcome |
| `NPDR_AFP` | Ratio | Normalized productivity metric |
| `NPDU_UFP` | Ratio | Normalized productivity metric |
| `Dev.Type` | Constant | Zero variance across all 499 rows |
| `N_effort` | Outcome | Post-delivery engineering effort |
| `Effort` | Outcome | Post-delivery total effort |
| `Added` | Change metric | Conservative v1 exclusion |

## 7. Preprocessing
Preprocessing is implemented strictly inside an immutable scikit-learn `ColumnTransformer`:
- **Numerical Preprocessing:** `StandardScaler()` applied to `AFP`, `Input`, `Output`, `Enquiry`, `File`, and `Interface`.
- **Categorical Preprocessing:** `OneHotEncoder(handle_unknown='ignore', sparse_output=False)` applied to `Resource`.
- **Packaging Invariant:** The preprocessor and regressor are coupled into a unified `Pipeline`, guaranteeing identical transformation offline and online.

## 8. Train/Test Methodology
- **Partitioning:** 80% training partition (399 projects) / 20% held-out test partition (100 projects).
- **Random Seed:** `42`.
- **Integrity:** The 20% test partition was completely untouched during model selection and candidate evaluation.

## 9. Cross-Validation Methodology
- **Scheme:** 5-Fold Cross-Validation (`KFold(n_splits=5, shuffle=True, random_state=42)`).
- **Scope:** Evaluated strictly on the 399 training records.
- **Leakage Prevention:** Preprocessor fits independently within each training fold.

## 10. Candidate Models
Five candidate regression architectures were systematically trained and compared:
1. `DummyRegressor(strategy='mean')` (Authoritative baseline benchmark)
2. `LinearRegression()` (Ordinary Least Squares)
3. `Ridge(alpha=1.0)` (L2 regularized linear regression)
4. `RandomForestRegressor(n_estimators=100, max_depth=5)` (Non-linear decision tree ensemble)
5. `GradientBoostingRegressor(n_estimators=100, max_depth=3, learning_rate=0.05)` (Gradient boosted trees)

## 11. Cross-Validation Results
| Candidate Model | CV MAE (months) | CV RMSE (months) | CV R² |
| :--- | :--- | :--- | :--- |
| DummyRegressor | 4.7330 | 6.6406 | -0.0348 |
| LinearRegression | 4.2133 | 6.1862 | 0.0958 |
| Ridge | 4.2090 | 6.1725 | 0.1006 |
| RandomForestRegressor **(Selected)** | 4.2031 | 5.9602 | 0.1685 |
| GradientBoostingRegressor | 4.2104 | 6.0640 | 0.1387 |

## 12. Held-Out Test Results
Evaluation against the untouched held-out test partition (100 records):

| Model | Test MAE (months) | Test RMSE (months) | Test R² |
| :--- | :--- | :--- | :--- |
| **RandomForestRegressor (Selected)** | **4.5926** | **8.4414** | **0.2362** |
| `DummyRegressor` (Baseline) | 4.9353 | 9.6607 | -0.0004 |

## 13. Model Selection
- **Selected Architecture:** `RandomForestRegressor`
- **Selection Rationale:** `RandomForestRegressor` achieved the lowest 5-fold CV RMSE (5.9602 months) and the highest cross-validation coefficient of determination (R² = 0.1685).
- **Held-out Confirmation:** On the untouched test set, `RandomForestRegressor` improved test RMSE from 9.6607 to 8.4414 and test MAE from 4.9353 to 4.5926 (Test R² = 0.2362).

## 14. Baseline Comparison
- **Dummy Baseline MAE:** 4.9353 months
- **Selected Model MAE:** 4.5926 months
- **Absolute Error Improvement:** 0.3428 months reduction in average prediction error.
- **Variance Explained:** The model explains 23.6% of timeline variance on the held-out test partition.

## 15. Limitations
1. **Dataset Scope:** 499 historical software engineering projects from the China metrics repository.
2. **Domain Transfer:** Historical organizational patterns may differ from modern student or microservice architectures.
3. **Empirical Correlation vs Causality:** Predictions reflect empirical correlations between functional sizing and duration; they do NOT imply direct causal control.
4. **Residual Variance:** A substantial portion of timeline variance is governed by organizational, process, and human factors not captured in function point metrics.
5. **Not a Schedule Guarantee:** The output represents an uncalibrated regression point estimate in months, not a contractually binding project management deadline.

## 16. Reproducibility
- **Dataset Random State:** 42
- **Test Size:** 0.2
- **Cross-Validation:** 5-Fold KFold (shuffle=True, random_state=42)
- **Deterministic Execution:** Re-running the pipeline generates identical data splits, cross-validation metrics, and test scores within standard floating-point precision.

## 17. Artifact Provenance
- **Model Artifact Path:** `C:\Users\DELL\OneDrive\Documents\SE Intellplatform\backend\app\ml\artifacts\timeline_model_v1.joblib`
- **Metadata JSON Path:** `C:\Users\DELL\OneDrive\Documents\SE Intellplatform\backend\app\ml\artifacts\timeline_model_v1_metadata.json`
- **SHA-256 Checksum:** `1f5309dffd431551d2729813b9a9c033ca3101eb0008b5f34a29aec9f1909e64`
- **Model Version:** 1.0.0
- **Feature Schema Version:** 1.0.0

## 18. Conclusion
Phase 7B.0 establishes the verified Machine Learning foundation for Timeline (Duration) Prediction in SE IntelliPlatform. The selected RandomForestRegressor pipeline outperforms the dummy baseline across all validation and test metrics. The serialized artifact, metadata, and safe loader are fully verified and ready for downstream integration into the Timeline Prediction Agent in Phase 7B.1.
