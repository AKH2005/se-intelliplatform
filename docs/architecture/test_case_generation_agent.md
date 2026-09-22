# Test Case Generation Agent Architecture Specification

## 1. Purpose
The `TestCaseGenerationAgent` is the AI generation agent in SE IntelliPlatform (`AgentType.GENERATION`, version `1.0.0`, id `test-case-generation`). It ingests canonical project context (`ProjectContextResponse`) and produces comprehensive, structured, and requirement-traceable software test case specifications.

> **CRITICAL ARCHITECTURAL POLICY:**  
> The LLM is strictly used for creative scenario ideation, edge case identification, negative path exploration, and step formulation. The LLM is NEVER the authority for requirement existence, UUID validity, or requirement coverage calculations. All coverage statistics and validation invariants are calculated and enforced deterministically by the backend.

---

## 2. Agent Identity & Metadata
- **Agent ID:** `test-case-generation`
- **Agent Name:** `Test Case Generation Agent`
- **Agent Type:** `AgentType.GENERATION`
- **Version:** `1.0.0`
- **Output Schema:** `TestCaseGenerationOutput`

---

## 3. Input & Context Processing
The agent consumes the canonical `ProjectContextResponse`:
1. **Active Requirement Filtering:**
   - Active requirement statuses: `DRAFT`, `APPROVED`, `IMPLEMENTED`.
   - Inactive requirement statuses: `DEFERRED`, `REJECTED`.
   - Inactive requirements are strictly excluded from testing scope. Test cases referencing inactive requirements are rejected during backend validation.
2. **Context Integrity:**
   - Read-only execution: Database records (projects, requirements) are never modified.
   - Versioned Context Snapshot: Snapshots (`ContextSnapshot`) retain cryptographic provenance when provided.

---

## 4. Execution Lifecycle & Pipeline

```text
                  ProjectContextResponse
                            │
                            ▼
              ┌───────────────────────────┐
              │    Hook 2: analyze()      │
              │  - Filter active reqs     │
              │  - Exclude DEFERRED/REJ   │
              │  - Collate test scope     │
              └─────────────┬─────────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │    Hook 3: generate()     │
              │  - Construct prompt       │
              │  - LLM generate candidate │
              │  - Deterministic coverage │
              └─────────────┬─────────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │ Hook 4: validate_output() │
              │  - Step numbering 1..N    │
              │  - Requirement exist & act│
              │  - Semantic deduplication │
              │  - Coverage verification  │
              └─────────────┬─────────────┘
                            │
                            ▼
                 TestCaseGenerationOutput
```

---

## 5. Deterministic Validation Invariants
The backend `validate_test_case_generation_output()` enforces:
1. **Total Count Consistency:** `total_test_cases == len(test_cases)`.
2. **Suite-Unique Identifiers:** Every `test_case_id` must be non-empty and unique across the suite.
3. **Field Completeness:** `title`, `description`, and `expected_result` must be non-empty strings.
4. **Step Sequencing:** Every test case must have $\ge 1$ step; `step_number` must strictly sequence $1, 2, \dots, N$ without skips or restarts. Each step's `action` and `expected_behavior` must be non-empty.
5. **Requirement Traceability:**
   - Every test case must cite $\ge 1$ requirement UUID.
   - All cited requirement UUIDs must exist in canonical project context.
   - Cited requirements must be in active status (`DRAFT`, `APPROVED`, `IMPLEMENTED`). Citing `DEFERRED` or `REJECTED` requirements triggers immediate validation failure.
6. **Semantic Deduplication:** Cases sharing normalized title, requirement references, and action sequences are rejected.
7. **Authoritative Coverage Metrics:**
   - `total_active_requirements`: Count of active requirements in project context.
   - `requirements_with_tests`: Count of active requirements referenced by $\ge 1$ test case.
   - `requirements_without_tests`: Count of active requirements with no test cases.
   - `coverage_percentage`: `(requirements_with_tests / total_active) * 100.0` ($0.0$ if no active requirements).
8. **Limitations Enforcement:** Suite must contain non-empty advisory scope limitations ($\ge 3$ items).

---

## 6. Audit & Provenance
Every invocation dispatched through `AgentExecutor` creates an immutable `AgentExecutionAudit` record containing:
- `execution_id`: Unique UUID
- `project_id`: Target project
- `agent_id`: `test-case-generation`
- `agent_version`: `1.0.0`
- `status`: `COMPLETED` or `FAILED`
- `context_snapshot_id` and `context_version`: Null for live context, populated for snapshot runs
- `output_summary`: Serialized summary including `total_test_cases` and `coverage`
- `duration_ms`: Execution latency
