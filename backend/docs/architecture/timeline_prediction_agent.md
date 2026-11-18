# Timeline Prediction Agent Architecture Specification

## 1. Purpose
The `TimelinePredictionAgent` is the second supervised Machine Learning agent in SE IntelliPlatform. It provides automated, empirical software project duration estimation in elapsed months based on verified historical function point metrics.

> **CRITICAL ARCHITECTURAL POLICY:**  
> The model is an empirical duration-estimation model trained on 499 historical China software projects. Its held-out test R² is 0.2362 and MAE is 4.5926 months. It should be treated as an advisory point estimate, not a guaranteed project deadline.

---

## 2. Inputs
The agent consumes the canonical `ProjectContextResponse` from the Phase 2 `ProjectContextEngine`:
- **Context Source:** `context.project.settings["ml_timeline_inputs"]` (or top-level in settings).
- **Requirement:** All 7 planning-stage predictors must be explicitly configured and positive/non-negative.
- **Zero Imputation Invariant:** If any predictor is missing, `TimelineFeatureUnavailableError` is raised immediately.

---

## 3. Feature Extraction
Feature extraction is handled by `app.ml.features.timeline_features.extract_timeline_features()`:
- `afp`: Adjusted Function Points ($> 0.0$)
- `input_count`: Number of external inputs ($\ge 0.0$)
- `output_count`: Number of external outputs ($\ge 0.0$)
- `enquiry_count`: Number of external inquiries ($\ge 0.0$)
- `file_count`: Number of internal logical files ($\ge 0.0$)
- `interface_count`: Number of external interface files ($\ge 0.0$)
- `resource_level`: Organization resource/staffing tier (1, 2, 3, or 4)

Strictly excluded to prevent post-delivery data leakage: `ID`, `Changed`, `Deleted`, `PDR_AFP`, `PDR_UFP`, `NPDR_AFP`, `NPDU_UFP`, `Dev.Type`, `N_effort`, `Effort`, `Added`.

---

## 4. Model
- **Algorithm:** Random Forest Regressor (`RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)`)
- **Version:** `1.0.0`
- **Feature Schema Version:** `1.0.0`
- **Artifact:** `backend/app/ml/artifacts/timeline_model_v1.joblib`
- **Integrity Validation:** Recalculates SHA-256 hash (`1f5309dffd431551d2729813b9a9c033ca3101eb0008b5f34a29aec9f1909e64`) against authoritative metadata (`timeline_model_v1_metadata.json`) prior to deserialization.

---

## 5. Prediction Flow
```text
                 ProjectContextResponse
                          │
                          ▼
                Timeline Feature Schema
                          │
                          ▼
                 Timeline Feature Extractor
                          │
                          ▼
                 Timeline Model Loader
                          │
                          ▼
                 RandomForestRegressor
                          │
                          ▼
             TimelinePredictionCandidate
                          │
                          ▼
               Deterministic Validation
                          │
                          ▼
                TimelinePredictionOutput
                          │
                          ▼
                    AgentExecutor
                          │
                          ▼
                  AgentResult + Audit
```

---

## 6. Output
Emits `TimelinePredictionOutput`:
- `agent_id`: `timeline-prediction`
- `agent_version`: `1.0.0`
- `summary`: Descriptive limitation-acknowledging assessment summary
- `predicted_duration_months`: Continuous float (full model precision)
- `estimated_duration_months`: Presentation rounded estimate (2 decimal places)
- `target`: `Duration`
- `target_unit`: `months`
- `model_provenance`: `TimelineModelProvenance`
- `feature_names`: List of 7 approved feature names
- `feature_summary`: Dictionary of validated human-readable inputs
- `limitations`: List of acknowledged model limitations

---

## 7. Validation
Validated via `validate_timeline_prediction_output()`:
1. `predicted_duration_months` is numeric, finite, and strictly $> 0.0$.
2. `target == "Duration"` and `target_unit == "months"`.
3. `feature_names` exactly equals approved 7 predictors.
4. `feature_summary` contains all required keys.
5. `model_provenance` corresponds to verified artifact.
6. `limitations` non-empty ($\ge 3$).
7. Prohibited language: No claims of "guaranteed", "highly accurate", "high confidence", "% accurate", "% confident", or "probability".

---

## 8. Error Handling
- **Missing Features:** Raises `TimelineFeatureUnavailableError` (an `AgentValidationError`); `AgentExecutor` records `status=FAILED`, `error_code="VALIDATION_FAILED"`, 0 retries.
- **Corrupted Artifact / Mismatch:** Raises `TimelineModelChecksumMismatchError`.
- **Missing Artifact / Metadata:** Raises `TimelineModelUnavailableError`.

---

## 9. Provenance
Every prediction audit record captures:
- Model name: `se_timeline_regressor` (`RandomForestRegressor`)
- Model version: `1.0.0`
- Training dataset: `China` (499 records)
- Artifact checksum: SHA-256 hash
- Context provenance: `context_snapshot_id` and `context_version` (or `NULL` for live context)

---

## 10. Limitations
1. Scope is derived from 499 historical software development projects from the China metrics repository.
2. Predictions reflect empirical functional size associations; they do not imply direct causal levers.
3. Unmodelled human, organizational, and technical volatility accounts for remaining timeline variance.
4. Continuous regression point estimate in elapsed months; strictly not an infallible schedule guarantee or contractual deadline.

---

## 11. Security Considerations
- Model loaded from trusted backend directory only (`backend/app/ml/artifacts/`).
- Byte-level SHA-256 checksum verification prevents tampered artifact deserialization.
- No secrets, credentials, or provider payloads in audit records.
- Read-only execution: does not write to project context or database settings.

---

## 12. Non-Goals
This agent strictly does NOT perform:
- Project scheduling or Gantt chart generation
- Milestone or deadline generation
- Probability or confidence interval calculations
- LLM-based timeline estimation or prompt reasoning
- Automatic requirement changes or scope alterations
