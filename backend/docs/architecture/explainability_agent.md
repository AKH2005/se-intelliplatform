# Explainability & Engineering Insights Agent Architecture Specification

## 1. Purpose
The `ExplainabilityAgent` is the cross-domain explanatory synthesis intelligence agent in SE IntelliPlatform (`AgentType.ANALYSIS`, version `1.0.0`, id `explainability-insights`). It ingests already-generated and validated outputs from any subset of the existing 8 platform agents (`ExplainabilityInput`) along with canonical project context (`ProjectContextResponse`). It builds a deterministic source and fact index, invokes an `LLMProvider` for contextual explanation and cross-domain synthesis, and enforces rigorous deterministic source traceability (Zero Phantom Citations), epistemic boundary controls (`FACT`, `INTERPRETATION`, `RECOMMENDATION`, `LIMITATION`), sequential identifier normalization (`INSIGHT-001`, `INSIGHT-002`, ...), and authoritative summary metrics computation.

> **CRITICAL ARCHITECTURAL POLICY:**
> "The Explainability Agent is advisory and does not alter authoritative upstream outputs."
> It is an *Explanatory Synthesizer*, NOT a predictor, calculator, orchestrator, execution engine, code executor, or replacement for upstream platform agents. It never executes code, never calls other agents, and never recalculates upstream facts or predictions.

---

## 2. Agent Identity & Metadata
- **Agent ID:** `explainability-insights`
- **Agent Name:** `Explainability & Engineering Insights Agent`
- **Agent Type:** `AgentType.ANALYSIS`
- **Version:** `1.0.0`
- **Output Schema:** `ExplainabilityOutput`

---

## 3. Epistemic Boundary & Claim Types
To preserve scientific rigor and prevent hallucination, statements in an engineering insight are categorized into strict epistemic types:

- **`FACT`**: Authoritative, deterministic data points directly grounded in supplied upstream agent outputs or canonical project context (e.g. predicted risk scores, exact requirement UUIDs, code review finding IDs, test coverage metrics). Backend logic is authoritative for facts; the LLM is prohibited from manufacturing facts.
- **`INTERPRETATION`**: Qualitative contextual explanation, domain reasoning, and synthesis connecting multiple findings.
- **`RECOMMENDATION`**: Advisory, non-destructive engineering guidance and mitigation steps.
- **`LIMITATION`**: Explicit acknowledgment of assumptions, empirical dataset bounds, or platform scope boundaries.

---

## 4. Input Architecture & Boundaries
- **Representation:** Strongly typed Pydantic v2 DTO `ExplainabilityInput` passed via execution `kwargs`.
- **Preconditions:**
  - Accepts validated outputs from any of the 8 upstream platform agents:
    1. `RequirementAnalysisOutput` (Phase 4)
    2. `ArchitectureRecommendationOutput` (Phase 5)
    3. `DatabaseDesignOutput` (Phase 6)
    4. `RiskPredictionOutput` (Phase 7A)
    5. `TimelinePredictionOutput` (Phase 7B)
    6. `BugPredictionOutput` (Phase 7C)
    7. `TestCaseGenerationOutput` (Phase 8.0)
    8. `CodeReviewOutput` (Phase 8.1)
  - Accepts optional `target_scope` (focus area) and `user_query` (developer question).
  - **Invariant:** At least ONE upstream output must be supplied. Empty input fails deterministic validation.

---

## 5. Execution Lifecycle & Pipeline

```text
       ProjectContextResponse + ExplainabilityInput
                            │
                            ▼
              ┌───────────────────────────┐
              │    Hook 2: analyze()      │
              │  - Input validation       │
              │  - Build source fact index│
              │  - Collate valid entities │
              │  - Collate valid fields   │
              └─────────────┬─────────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │    Hook 3: generate()     │
              │  - Construct prompt       │
              │  - LLM generate candidate │
              │  - Zero phantom filter    │
              │  - Reject all-invalid     │
              │  - ID normalization       │
              │  - Reconcile metrics      │
              └─────────────┬─────────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │ Hook 4: validate_output() │
              │  - Summary non-empty      │
              │  - Insights non-empty     │
              │  - Traceability check     │
              │  - Mathematical metrics   │
              │  - Limitations check      │
              └─────────────┬─────────────┘
                            │
                            ▼
                   ExplainabilityOutput
```

---

## 6. Source Traceability & Zero Phantom Citations
Every `EngineeringInsight` must contain at least one valid `SourceReference`:
- `agent_id`: Must match an agent whose output was actually supplied in `ExplainabilityInput`. Citing an unsupplied agent is strictly rejected.
- `source_entity_id`: Must match a known entity ID (e.g., requirement UUID, finding ID `CR-001`, test case ID `TC-001`, model identifier) indexed by the backend.
- `source_field`: Must match a known field from the supplied output schema.
- `claim_type`: Epistemic status (`FACT`, `INTERPRETATION`, `RECOMMENDATION`, `LIMITATION`).

Any candidate citation that fails these checks is deterministically discarded before output generation. If all citations in a candidate insight are invalid, the insight is discarded. If all insights are invalid (or none survive deterministic filtering), execution fails deterministically with an `AgentValidationError`; no synthetic baseline insight is fabricated or manufactured.

---

## 7. Deterministic vs. LLM Responsibilities

| Responsibility | Owner | Mechanism |
| :--- | :--- | :--- |
| Input validation & preconditions | Backend | Pydantic model validator + `validate_explainability_input` |
| Authoritative facts & model metrics | Backend | `build_source_fact_index` extracts truth from inputs |
| Citation existence & validation | Backend | Deterministic set membership check against fact index |
| Insight ID generation | Backend | Sequential indexing (`INSIGHT-001`, `INSIGHT-002`, ...) |
| Summary metrics computation | Backend | Strict mathematical counting over validated insights |
| Applicable limitations aggregation | Backend | Source-driven upstream limitations + platform limitations |
| Qualitative narrative & explanation | LLM | Structured JSON generation via `LLMProvider` |
| Cross-domain synthesis & trade-offs | LLM | Contextual reasoning across active requirements and findings |
| Advisory next steps | LLM | Non-destructive suggested engineering actions |

---

## 8. Hallucination Boundary & Grounded Causality
- **Forbidden:**
  - Unsupported causal claims (e.g. "Feature X caused project failure", "Team is incompetent").
  - Verification claims (e.g. "We executed the code and verified the bug").
  - Score recalculations or alterations.
- **Allowed:**
  - Grounded factual citations (e.g. "The risk prediction model produced a score of 7.4...").
  - Documented associations (e.g. "Historical training data exhibits empirical correlation between...").
  - Co-occurrence synthesis (e.g. "Both the static review and requirement analysis identify...").

---

## 9. ML & Code Review Explainability Boundaries
- **Machine Learning (Ridge, Random Forest, Logistic Regression):**
  - No external XAI libraries (no SHAP, LIME, TreeExplainer).
  - Explanations are strictly grounded in existing model outputs, feature summaries, risk bands, duration estimates, defect labels, and documented training limitations.
- **Code Review:**
  - Does not duplicate individual line-by-line findings.
  - Synthesizes findings across requirements, architectural impact, and defect risk where evidence exists.
- **Security & Privacy:**
  - Preserves secret redaction markers (`***REDACTED_SECRET***`) strictly. Never attempts unmasking or reconstruction.
  - Zero storage or persistence of raw source code in audits.

---

## 10. Strictly Deferred Features
The following capabilities are deferred from Phase 8.2:
- RAG (Retrieval-Augmented Generation) & vector database integrations
- SHAP, LIME, or dynamic feature attribution frameworks
- GitHub / GitLab pull-request commentary webhooks
- Automated code modifications or PR generation
- Dynamic sandbox or code execution engines
- Repository-wide background indexing or AST crawlers
