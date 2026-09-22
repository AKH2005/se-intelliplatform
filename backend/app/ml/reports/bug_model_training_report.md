# Software Bug / Defect Prediction ML Foundation Training Report (Phase 7C.0)

## 1. Dataset
The training pipeline utilizes the NASA JM1 software defect dataset in ARFF format (`jm1.arff`). JM1 consists of static code metrics collected from NASA flight software written in C/C++.

## 2. Dataset Version / Source
- **File**: `jm1.arff`
- **Source Location**: `C:\Users\DELL\OneDrive\Documents\SE Intellplatform\jm1.arff`
- **Donor / Origin**: NASA Metrics Data Program (MDP), curated via PROMISE Software Engineering Repository.

## 3. Original Dataset Shape
- **Original Rows**: 10,885
- **Original Attributes**: 22 (21 static-code metric predictors + 1 binary target `defects`)

## 4. Duplicate Analysis
- **Exact Duplicate Rows**: 1,973
- **Feature Vector Duplicates (ignoring label)**: 2,061
- **Audit Observation**: 1,973 rows are 100% identical in both all 21 features and the defect label.

## 5. Duplicate Policy
- **Policy (Frozen)**: Exact duplicate rows (identical features AND identical label) are removed BEFORE the train/test split.
- **Rows Removed**: 1,973
- **Resulting Post-Deduplication Rows**: 8,912
- **Feature-Only Duplicates**: Retained if the defect outcome differs, reflecting identical static metrics across distinct software modules with different defect histories.

## 6. Missing-Value Analysis
- **Missing Values Audit**:
{
  "uniq_Op": 5,
  "uniq_Opnd": 5,
  "total_Op": 5,
  "total_Opnd": 5,
  "branchCount": 5
}
- **Policy**: 5 metric fields each exhibit 5 missing values. Missing values are NOT filled before splitting. Instead, `SimpleImputer(strategy="median")` is executed strictly inside scikit-learn pipelines to prevent CV data leakage.

## 7. Target Distribution
- **Raw Dataset Target Distribution**:
  - Non-defective (`false`): 8,779 (80.65%)
  - Defective (`true`): 2,106 (19.35%)
- **Post-Deduplication Target Distribution**:
  - Non-defective (`false`): 6,905 (77.48%)
  - Defective (`true`): 2,007 (22.52%)

## 8. Feature List
Exactly 21 approved numerical predictors:
`loc, v(g), ev(g), iv(g), n, v, l, d, i, e, b, t, lOCode, lOComment, lOBlank, locCodeAndComment, uniq_Op, uniq_Opnd, total_Op, total_Opnd, branchCount`

## 9. Feature Semantics
- **McCabe Complexity**:
  - `loc`: Lines of code
  - `v(g)`: Cyclomatic complexity (linearly independent paths)
  - `ev(g)`: Essential complexity (unstructured control flow)
  - `iv(g)`: Design complexity (subsystem integration complexity)
- **Halstead Metrics**:
  - `n`: Total operators and operands ($N = N_1 + N_2$)
  - `v`: Program volume ($V = N \log_2 \eta$)
  - `l`: Program level / length ($L = V^* / V$)
  - `d`: Difficulty ($D = 1 / L$)
  - `i`: Intelligence content ($I = L \cdot V$)
  - `e`: Effort ($E = V / L$)
  - `b`: Delivered bugs estimate ($B = V / 3000$)
  - `t`: Implementation time ($T = E / 18$)
- **Line Counts**:
  - `lOCode`: Source lines of code
  - `lOComment`: Lines of comments
  - `lOBlank`: Blank lines
  - `locCodeAndComment`: Lines containing both executable code and comments
- **Raw Operator & Operand Counts**:
  - `uniq_Op`: Unique operators ($\eta_1$)
  - `uniq_Opnd`: Unique operands ($\eta_2$)
  - `total_Op`: Total operators ($N_1$)
  - `total_Opnd`: Total operands ($N_2$)
- **Branch Metric**:
  - `branchCount`: Number of branches in the module flowgraph

## 10. Leakage Analysis
- Verified: `defects NOT IN X.columns`.
- Verified: No target-derived metrics or ID proxies exist in the feature set.
- All imputation and scaling transformations are encapsulated inside `sklearn.pipeline.Pipeline`, ensuring every CV fold fits strictly on its training subset.

## 11. Preprocessing
- **Numerical Imputation**: `SimpleImputer(strategy="median")`
- **Numerical Scaling**: `StandardScaler()` (applied to linear classifiers)
- **Tree Models**: Tested with `SimpleImputer(strategy="median")`

## 12. Class Imbalance Handling
- The dataset exhibits an approximate 77.5% / 22.5% imbalance.
- Candidate imbalance strategies:
  - `DummyClassifier`: No class balancing (predicts majority class)
  - `LogisticRegression`: `class_weight="balanced"`
  - `RandomForestClassifier`: `class_weight="balanced"`
  - `GradientBoostingClassifier`: Native/default weighting (does not support `class_weight`)

## 13. Train / Test Methodology
- **Split Ratio**: 80% Training (7,129 samples), 20% Held-Out Test (1,783 samples)
- **Stratification**: `stratify = y`
- **Random State**: `42`
- **Isolation Guarantee**: The 20% test partition remained untouched until final evaluation.

## 14. CV Methodology
- **Folds**: 5-Fold Cross-Validation
- **Strategy**: `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`
- **Scope**: Training partition only (7,129 rows).

## 15. Candidate Models
1. `DummyClassifier(strategy="most_frequent")`
2. `LogisticRegression(class_weight="balanced", max_iter=2000, random_state=42)`
3. `RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42)`
4. `GradientBoostingClassifier(random_state=42)`

## 16. CV Results

| Model | CV Recall | CV F1 | CV PR-AUC | CV ROC-AUC | CV Precision |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Dummy | 0.0000 | 0.0000 | 0.2251 | 0.5000 | 0.0000 |
| Logistic Regression | 0.5072 | 0.4407 | 0.4173 | 0.6822 | 0.3903 |
| Random Forest | 0.3664 | 0.3899 | 0.3756 | 0.6787 | 0.4171 |
| Gradient Boosting | 0.1352 | 0.2155 | 0.4093 | 0.6914 | 0.5392 |

## 17. Held-Out Test Results

| Model | Test Recall | Test F1 | Test PR-AUC | Test ROC-AUC | Test Precision | Test Accuracy |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Dummy | 0.0000 | 0.0000 | 0.2255 | 0.5000 | 0.0000 | 0.7745 |
| Logistic Regression | 0.4851 | 0.4333 | 0.4254 | 0.6915 | 0.3916 | 0.7140 |
| Random Forest | 0.3657 | 0.4000 | 0.3713 | 0.6725 | 0.4414 | 0.7527 |
| Gradient Boosting | 0.1517 | 0.2460 | 0.4258 | 0.7105 | 0.6489 | 0.7902 |

## 18. Confusion Matrices (Held-Out Test Set)

- **LogisticRegression (Selected)**:
  - True Negatives (TN): 1078
  - False Positives (FP): 303
  - False Negatives (FN): 207
  - True Positives (TP): 195

## 19. Model Selection
- **Selected Model**: `LogisticRegression`
- **Selection Hierarchy Applied**:
  1. Primary: Highest 5-fold CV positive-class Recall
  2. Secondary: If tied, highest CV positive-class F1
  3. Tertiary: If tied, highest CV PR-AUC
  4. Final: Simplicity & Interpretability
- **Selection Rationale**: Selected 'LogisticRegression' according to the authoritative hierarchy: Highest CV positive-class Recall (0.5072), CV F1 (0.4407), and CV PR-AUC (0.4173).
- Notice: The model was selected strictly on 5-fold cross-validation performance. The held-out test set was evaluated exclusively after selection for unbiased generalization reporting.

## 20. Limitations
- Defect prediction on NASA JM1 is challenging due to class imbalance and the inherent noise in module-level static code metrics.
- High false-positive rate is accepted to maximize positive-class defect detection (Recall).
- Static metrics reflect syntactic and structural complexity, not semantic correctness or developer competency.

## 21. Reproducibility
- **Random Seed**: 42 (Train/Test split and StratifiedKFold)
- **Deterministic Preprocessing**: Pipelines with fixed random states
- **Python / Library Versions**: Verified reproducible on scikit-learn >= 1.4.

## 22. Artifact Provenance
- **Artifact Path**: `backend/app/ml/artifacts/bug_model_v1.joblib`
- **Metadata Path**: `backend/app/ml/artifacts/bug_model_v1_metadata.json`
- **Artifact SHA-256 Checksum**: `563b2b0ffd522df7ff8f50b0a025a9e64a678fb917ac7bbddc2f15e2035e430e`

## 23. Conclusion
Phase 7C.0 establishes an audited, reproducible, and leakage-free ML foundation for Bug / Defect Prediction. The pipeline, model artifact, checksum integrity, and safe loader are complete, verified, and ready for future agent consumption in Phase 7C.1.
