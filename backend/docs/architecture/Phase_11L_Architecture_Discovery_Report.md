# Phase 11L — Architecture Discovery & Implementation Plan
## Advanced Application Testing & Coverage Intelligence

**Date:** 2026-10-03  
**Status:** DISCOVERY COMPLETE / PLANNING ONLY (NO CODE IMPLEMENTATION)  
**Author:** Antigravity AI Engineering Assistant  
**Repository Baseline:** Phase 11K Complete (`RELEASE_GATE_PASS`)  

---

## 1. Executive Summary

Phase 11K successfully delivered containerized browser testing, AI-generated user journeys, deterministic validation, adapter translation, requirement coverage calculation, and failure diagnosis handoff with a 100% verified baseline (1,062 backend tests, 76 frontend tests, live Docker E2E pass, zero leaks).

Phase 11L transitions the platform from isolated test execution silos toward **Application-Wide Test Coverage Intelligence & Change-Aware Regression Selection**.

This discovery report conducts an exhaustive, empirical repository audit across:
- All 10 existing testing, analysis, and verification capabilities.
- Current requirement, version, and workflow persistence models.
- Code diffing, AST dependency analysis, and test discovery primitives.
- Deterministic vs. AI responsibility boundaries.
- Concrete architectural gaps preventing unified testing intelligence.

### Key Discovery Conclusion
**No new database migrations, runtime containers, or workflow execution engines are required.**  
SE IntelliPlatform already possesses:
1. AST parsing and dependency extraction (`ASTAnalyzer`, `DependencyAnalyzer`, `TestDiscovery`).
2. Version file diffing and requirement delta detection (`DevelopmentVersionService.compare_versions`).
3. Deterministic requirement coverage calculation (`RequirementCoverageEngine`).
4. Ephemeral sandbox and browser container runners (`DockerRuntimeExecutor`, `BrowserTestingService`).
5. Unified multi-stage verification aggregation (`DevelopmentVerificationService`).
6. Evidence-grounded root cause diagnosis (`FailureAnalysisAgent`).

The core gap is the absence of an **orchestrated correlation and selection layer** that links code changes to affected requirements and tests across test types (unit, AI, and browser). Phase 11L can be implemented cleanly through deterministic service additions and non-breaking REST/UI extensions using existing persistence channels.

---

## 2. Phase 11K Frozen Baseline

The following architectural components and prior stages are verified as frozen, immutable in authority, and strictly respected:

- **Phase 11J (Browser Sandbox & Containerization):** `BrowserTestingService`, `ApplicationRuntimeManager`, `DockerRuntimeExecutor`, `BrowserExecutor`, ephemeral bridge networking, non-root container isolation.
- **Phase 11K Stages 1–8 (Browser User Journeys):** `BrowserJourneyGenerationAgent`, `BrowserJourneyValidator`, `BrowserJourneyAdapter`, `BrowserJourneyWorkflowOrchestrator`, `BrowserJourneyService`, REST endpoints, frontend workspace integration.
- **Agent Governance:** `AgentExecutor` remains the sole single-agent execution authority.
- **Workflow Coordination:** `WorkflowCoordinator` remains the sole multi-agent execution authority.
- **Diagnostic Authority:** `FailureAnalysisAgent` remains the sole failure analysis authority (strictly read-only; zero autonomous remediation).
- **Version Snapshot Boundary:** `DevelopmentVersion` remains an immutable record of software artifacts.
- **Verification Baseline:**
  - Backend Suite: **1,062 / 1,062 passed**
  - Frontend Suite: **76 / 76 passed**
  - Production Build: **PASS (0 TypeScript errors)**
  - Live Docker E2E: **PASS**

---

## 3. Repository Inventory

An inspection of active platform components reveals the following structural landscape:

```
backend/app/
├── agents/
│   ├── base.py & contracts.py (Base agent abstractions & AgentExecutor)
│   ├── browser_journey/ (Phase 11K candidate generation agent & contracts)
│   ├── code_generation/ (Scaffold planning & code synthesis agents)
│   ├── failure_analysis/ (Phase 11D failure diagnosis agent & taxonomy)
│   ├── remediation/ (Phase 11E patch proposal agent)
│   └── test_generation/ (Phase 11F AI pytest suite generation agent)
├── browser/
│   ├── contracts.py (DeterministicBrowserTestDefinition, BrowserTestRun)
│   ├── service.py (BrowserTestingService - Phase 11J orchestrator)
│   ├── runtime.py (ApplicationRuntimeManager - container runner)
│   ├── browser_executor.py (BrowserExecutor - Playwright container runner)
│   └── journey/ (Phase 11K validator, adapter, orchestrator, coverage engine)
├── models/
│   ├── project.py (Project ORM entity)
│   ├── requirement.py (Requirement ORM entity)
│   ├── context_snapshot.py (ContextSnapshot ORM entity)
│   ├── workflow_execution.py (WorkflowExecution ORM entity & artifact store)
│   ├── development_version.py (DevelopmentVersion & DevelopmentChange ORM entities)
│   └── assistant.py (Assistant conversation & message ORM entities)
├── sandbox/
│   ├── contracts.py (ExecutionResult, ExecutionStatus)
│   ├── docker_executor.py (Docker unit test sandbox runner)
│   └── static_analysis/
│       ├── ast_analyzer.py (AST parsing, function/class/import extraction)
│       ├── dependency_analyzer.py (Imports vs requirements.txt analysis)
│       ├── ruff_analyzer.py (Linter & syntax analyzer)
│       ├── test_discovery.py (Static discovery of pytest files & functions)
│       └── service.py (StaticAnalysisService)
├── schemas/
│   ├── browser_journeys.py & browser_testing.py (DTOs for browser runs)
│   ├── context.py & project.py (Context and Project DTOs)
│   ├── development_version.py (Version, FileDiff, Verification DTOs)
│   └── requirement.py (Requirement DTOs)
└── services/
    ├── action_registry.py (Authoritative Assistant Action registry - 29 actions)
    ├── assistant_reasoning_service.py (Assistant conversational planner)
    ├── browser_journey_service.py (Browser journey transactional service)
    ├── context_engine.py (Canonical project context aggregation)
    ├── development_version_service.py (Version creation, comparison, rollback)
    ├── engineering_action_service.py (Assistant action execution dispatcher)
    ├── requirement_service.py (Requirement CRUD & status management)
    ├── verification_service.py (Multi-stage deterministic verification aggregator)
    └── workflow_service.py (WorkflowExecution database transaction service)
```

---

## 4. Current Testing Architecture

The platform currently operates 4 separate test execution mechanisms, each initiated through distinct workflows and API endpoints:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               CURRENT TESTING ARCHITECTURE                             │
└────────────────────────────────────────────────────────────────────────────────────────┘

    1. STATIC ANALYSIS (Ruff, AST, Dependency Scanner)
       Input: Project Files Map
       Execution: In-Process Python AST + Subprocess Ruff
       Output: StaticAnalysisResult (Diagnostics, Syntax Errors, Lint Errors)
       Persistence: WorkflowExecution.artifacts["static_analysis"]

    2. SANDBOX UNIT TESTS (Scaffolded Unit Tests)
       Input: Scaffold Code Map (tests/test_*.py)
       Execution: Docker Sandbox Container (se-intelliplatform-sandbox)
       Output: ExecutionResult (exit_code, tests_passed, tests_failed, stdout, stderr)
       Persistence: WorkflowExecution.artifacts["sandbox_execution"]

    3. AI TEST GENERATION & EXECUTION (Targeted pytest Suite)
       Input: Code Manifest, Static Analysis, Requirements
       Generation: TestGenerationAgent (AgentExecutor) -> AITestSuite
       Execution: Docker Sandbox Container (se-intelliplatform-sandbox)
       Output: AITestExecutionResult (test_results, pass/fail counts, failure traces)
       Persistence: WorkflowExecution.artifacts["ai_test_suite"], ["ai_test_execution"]

    4. BROWSER TESTS & USER JOURNEYS (End-to-End Visual Verification)
       Input: Web Routes, Requirements, Application Code
       Generation: BrowserJourneyGenerationAgent (AgentExecutor) -> Candidate Suite
       Validation: BrowserJourneyValidator (Deterministic) -> Validated Suite
       Adaptation: BrowserJourneyAdapter (Deterministic) -> Deterministic Tests
       Execution: Dual Docker Containers (App Container + Playwright Container)
       Output: BrowserTestRun (case_results, screenshots, logs) + Coverage Report
       Persistence: WorkflowExecution.artifacts["browser_journey_suite"], ["browser_test_run"]
```

### TABLE 1 — Existing Testing Capabilities

| Capability | Owner Service | Input | Output | Persistence Channel | Execution Authority | Deterministic vs AI |
|---|---|---|---|---|---|---|
| **Static Analysis** | `StaticAnalysisService` | Project source files | `StaticAnalysisResult` | `WorkflowExecution.artifacts["static_analysis"]` | In-Process Python + Sandbox Ruff | Deterministic |
| **Sandbox Unit Tests** | `SandboxService` | Project test files | `ExecutionResult` | `WorkflowExecution.artifacts["sandbox_execution"]` | `DockerRuntimeExecutor` (Sandbox) | Deterministic |
| **AI Test Generation** | `TestGenerationAgent` | Code files + Requirements | `AITestSuite` | `WorkflowExecution.artifacts["ai_test_suite"]` | `AgentExecutor` | AI-Assisted + Deterministic Validation |
| **AI Test Execution** | `SandboxService` | `AITestSuite` | `AITestExecutionResult` | `WorkflowExecution.artifacts["ai_test_execution"]` | `DockerRuntimeExecutor` (Sandbox) | Deterministic |
| **Browser Smoke Tests** | `BrowserTestingService` | Route definitions + App code | `BrowserTestRun` | `WorkflowExecution.artifacts["browser_test_run"]` | `BrowserTestingService` (Dual Docker) | Deterministic |
| **Browser Journeys** | `BrowserJourneyWorkflowOrchestrator` | Requirements + Route manifest | `BrowserJourneyWorkflowResult` | `WorkflowExecution.artifacts["browser_journey_*"]` | `BrowserTestingService` (Dual Docker) | AI-Assisted + Deterministic Validation/Execution |
| **Failure Analysis** | `FailureAnalysisAgent` | Test runs + Raw logs + Source files | `FailureDiagnosis` | `WorkflowExecution.artifacts["failure_analysis"]` | `AgentExecutor` | AI-Assisted Reasoning on Deterministic Evidence |
| **Verification Gate** | `DevelopmentVerificationService` | All stage artifacts | `VerificationSnapshot` | `DevelopmentVersion.verification_summary` | Deterministic Evaluator | Deterministic |

---

## 5. Current Coverage Architecture

### Current Implementation (`RequirementCoverageEngine`)
- **Location:** `backend/app/browser/journey/coverage.py`
- **Scope:** Strictly restricted to Phase 11K **Browser User Journeys**.
- **Active Requirements Definition:** Sourced from `ValidationContext.from_project_context`, filtered where `is_archived == False` and status in (`APPROVED`, `IMPLEMENTED`, `DRAFT`).
- **Calculation Algorithm:**
  $$\text{Coverage Percentage} = \text{round}\left(\frac{|\text{Covered Active Requirement IDs}|}{|\text{Total Active Requirements}|} \times 100, 2\right)$$
  - Returns `0.0` if active requirements count is 0.
- **Traceability Mapping:**
  - `requirement_to_journeys_map: dict[str, list[str]]`
  - `journey_to_requirements_map: dict[str, list[str]]`
  - `uncovered_requirement_ids: list[str]`
- **Persistence:** Stored exclusively within `WorkflowExecution.artifacts["browser_journey_validation"]["coverage_report"]`.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               CURRENT COVERAGE ARCHITECTURE                            │
└────────────────────────────────────────────────────────────────────────────────────────┘

    Active Project Requirements ──────┐
                                      ▼
    Validated Browser Journeys  ──► RequirementCoverageEngine ──► RequirementCoverageReport
                                                                  ├── coverage_percentage
                                                                  ├── covered_requirement_ids
                                                                  ├── uncovered_requirement_ids
                                                                  └── requirement_to_journeys_map
    [CRITICAL GAP]:
    - Unit tests: EXCLUDED from coverage calculation
    - AI-generated tests: EXCLUDED from coverage calculation
    - API tests: EXCLUDED from coverage calculation
    - Historical version comparison: NOT SUPPORTED
```

### TABLE 2 — Existing Coverage Capabilities

| Aspect | Current Platform Behavior | Limitation / Gap |
|---|---|---|
| **Coverage Domain** | Browser Journeys only | Unit tests, AI tests, and API tests contribute 0% to requirement coverage |
| **Active Requirement Filter** | Unarchived requirements in project scope | Does not account for version-specific requirement scoping |
| **Mapping Granularity** | Journey ID $\leftrightarrow$ Requirement ID | No mapping from individual test assertions or source symbols to requirements |
| **Uncovered Exposure** | Lists uncovered requirement IDs in JSON payload | No automated risk categorization or gap explanation |
| **Version Association** | Version ID stored as metadata string | No historical version-over-version coverage comparison or trend tracking |
| **Cross-Test Correlation** | Non-existent | No capability to know if an uncovered browser requirement is covered by a unit test |

---

## 6. Requirement Model Audit

Inspection of `backend/app/models/requirement.py` and `backend/app/schemas/requirement.py`:

- **Identity & Ownership:** Strongly typed UUID primary key (`id`), strictly scoped to `project_id` with foreign key and cascade deletion.
- **Attributes:** `title` (str 255), `description` (Text), `type` (FUNCTIONAL, NON_FUNCTIONAL, CONSTRAINT), `priority` (LOW, MEDIUM, HIGH, CRITICAL), `status` (DRAFT, APPROVED, IMPLEMENTED, DEFERRED, REJECTED), `is_archived` (Boolean).
- **Version Relationship:** Requirements table has **NO direct column** linking to `development_version_id`. Instead, `DevelopmentVersion.requirement_ids` stores a JSON list of satisfied requirement IDs.
- **Traceability Attributes:**
  - Source file links: **NOT PRESENT** in database model.
  - Function / symbol links: **NOT PRESENT** in database model.
  - Test links: **NOT PRESENT** in database model.
  - Failure links: **NOT PRESENT** in database model (only correlated dynamically in `FailureDiagnosis.requirement_links`).

---

## 7. Test Traceability Audit

### Current Traceability Chains

```
Traceability Chain A (Browser Journeys):
Requirement (ID/Title) ──► Candidate Journey ──► Validated Journey ──► DeterministicBrowserTestDefinition ──► BrowserTestRun ──► WorkflowExecution

Traceability Chain B (AI Tests):
Requirement (ID/Title) ──► GeneratedTest.requirement_ids ──► AITestSuite.requirement_traceability ──► AITestExecutionResult ──► WorkflowExecution

Traceability Chain C (Scaffold Unit Tests):
Source File ──► Test File (tests/test_*.py) ──► ExecutionResult ──► WorkflowExecution (NO REQUIREMENT LINK)
```

### TABLE 3 — Traceability Matrix (Current vs. Target)

| Linkage | Current Status | Supporting Component | Missing Capability |
|---|---|---|---|
| **Requirement $\rightarrow$ Implementation** | **PARTIAL** | `DevelopmentVersion.files_manifest[].req_ids`, `GeneratedFile.requirement_ids` | No symbol-level or AST-level mapping |
| **Requirement $\rightarrow$ Unit Test** | **MISSING** | None (tests scaffolded without requirement IDs) | Unit test requirement tagging or discovery |
| **Requirement $\rightarrow$ AI Test** | **EXISTS** | `AITestSuite.requirement_traceability` | Not aggregated into global coverage report |
| **Requirement $\rightarrow$ Browser Journey** | **EXISTS** | `RequirementCoverageEngine` | Restricted to browser runs |
| **Test $\rightarrow$ Test Execution** | **EXISTS** | `ExecutionResult`, `AITestExecutionResult`, `BrowserTestRun` | Isolated execution records; no unified test run entity |
| **Test Execution $\rightarrow$ Failure** | **EXISTS** | `FailureAnalysisAgent`, `FailureDiagnosis.evidence` | Grounded to test exit codes and traces |
| **Failure $\rightarrow$ Requirement** | **EXISTS** | `FailureDiagnosis.requirement_links` | Heuristic correlation via LLM diagnosis |
| **Code Change $\rightarrow$ Affected Test** | **MISSING** | `DevelopmentVersionService.compare_versions` (diff only) | No dependency link from modified file to test |

---

## 8. Version-Aware Testing Audit

The platform tracks versions via `DevelopmentVersion` (`backend/app/models/development_version.py`):

- **What tests belong to this version?**
  - **Partially Answerable:** An inspection of `WorkflowExecution` records associated with `version_id` reveals the test runs executed during that version's lifecycle.
- **What requirements changed?**
  - **Fully Answerable:** `DevelopmentVersionService.compare_versions(project_id, from_v, to_v)` returns `reqs_added` and `reqs_removed`.
- **What tests are affected by a requirement change?**
  - **NOT CURRENTLY PRESENT:** No service queries `reqs_added` or `reqs_removed` against test traceability maps to flag affected tests.
- **What failed because of this version?**
  - **Fully Answerable:** `DevelopmentVersion.verification_summary` records stage-by-stage failures; `FailureDiagnosis` references originating versions.
- **What should be rerun after a change?**
  - **NOT CURRENTLY PRESENT:** When a version is updated or remediated, all tests are re-run indiscriminately.

---

## 9. Change Impact Capabilities Audit

The platform contains rich, dormant building blocks for change impact analysis:

1. **File & Requirement Diffing:**
   - `DevelopmentVersionService.compare_versions` uses Python `difflib` to produce:
     - `files_added: list[VersionFileDiff]`
     - `files_modified: list[VersionFileDiff]` (with `unified_diff`)
     - `files_removed: list[VersionFileDiff]`
     - `reqs_added: list[str]`
     - `reqs_removed: list[str]`
2. **Static AST Analysis:**
   - `ASTAnalyzer` (`backend/app/sandbox/static_analysis/ast_analyzer.py`) extracts:
     - `data.imports`: `(module, [imported_names], line)`
     - `data.functions`: `(function_name, line)`
     - `data.classes`: `(class_name, line)`
3. **Dependency Mapping:**
   - `DependencyAnalyzer` (`backend/app/sandbox/static_analysis/dependency_analyzer.py`) identifies internal vs. third-party namespace trees.
4. **Test Discovery:**
   - `TestDiscovery` (`backend/app/sandbox/static_analysis/test_discovery.py`) statically detects test files and test functions matching `test_*`.

### The Missing Impact Engine
What does NOT exist is an engine connecting these primitives:
$$\text{Modified File Paths} \xrightarrow{\text{AST Import Graph}} \text{Dependent Files} \xrightarrow{\text{Test Discovery}} \text{Affected Test Functions / Suites}$$

---

## 10. Regression Capabilities Audit

- **Current Regression Trigger:** User clicks "Run Sandbox", "Run AI Tests", or "Generate Browser Journeys" in the frontend, or Assistant executes `RUN_SANDBOX` / `RUN_AI_TESTS` / `RUN_BROWSER_TESTS`.
- **Execution Mode:** **ALL-RUN ONLY**. Every execution runs the entire test suite from start to finish.
- **Selective Execution:** **NOT SUPPORTED**. There is no parameter or flag to run a subset of pytest functions or a subset of browser journeys.
- **Historical Comparison:** Test runs are recorded independently in `workflow_executions`. No endpoint or view compares test pass rates across version $N$ and version $N-1$.

---

## 11. Failure Intelligence Audit

Inspection of `FailureAnalysisAgent` (`backend/app/agents/failure_analysis/`):

- **Input Evidence:** Receives `execution_result` (sandbox), `ai_test_execution_result` (AI tests), `browser_test_run` (browser), `static_analysis_result` (Ruff/AST), and source files.
- **Taxonomy:** Categorizes into 16 structured `FailureType` values (e.g. `ASSERTION_FAILURE`, `SYNTAX_ERROR`, `IMPORT_ERROR`, `TIMEOUT`, `RUNTIME_ERROR`).
- **Grounding:** Generates `EvidenceReference` records linking claims to line numbers and snippets.
- **Correlations:** Emits `affected_files`, `requirement_links`, `architecture_links`, `database_links`.
- **Constraint:** Purely diagnostic. Does not patch code, retry tests, or trigger autonomous execution.

---

## 12. AI Boundary Audit

The system strictly enforces the principle:
> **"AI proposes and explains. Deterministic backend validates, calculates, and executes."**

### Operational Classification for Phase 11L:

| Operation | Authority | Justification |
|---|---|---|
| **Coverage Percentage Calculation** | **DETERMINISTIC** | Strict mathematical ratio ($N_{\text{covered}} / N_{\text{total}}$). Must never be approximated by LLM. |
| **Active Requirement Verification** | **DETERMINISTIC** | Database state query (`is_archived == False`). Must never be hallucinatory. |
| **AST Import & Symbol Graph** | **DETERMINISTIC** | Python `ast` parsing. Exact syntax tree analysis. |
| **Diff & File Delta Detection** | **DETERMINISTIC** | Python `difflib`. Absolute byte/line equality checks. |
| **Affected Test Selection** | **DETERMINISTIC** | Graph traversal matching modified symbols/files to test imports. |
| **Test Execution** | **DETERMINISTIC** | Docker sandbox / Playwright container execution. |
| **Pass / Fail Evaluation** | **DETERMINISTIC** | Pytest exit codes, assertions, HTTP status codes. |
| **Coverage Gap Explanation** | **AI-ASSISTED** | Natural language synthesis explaining why a business requirement lacks tests. |
| **Regression Risk Summarization** | **AI-ASSISTED** | High-level engineering explanation of change blast radius. |
| **Test Prioritization Heuristic Explanation** | **AI-ASSISTED** | Explaining why certain tests are scheduled ahead of others. |

---

## 13. Data Model Audit

Can Phase 11L be implemented without modifying database schemas or creating Alembic migrations?

### Audit of Database Entities:
1. `projects`: Retains project boundaries and isolation.
2. `requirements`: Retains canonical functional specifications.
3. `development_versions`: Already has `files_manifest` (JSONB) and `metadata_payload` (JSONB).
4. `development_changes`: Already tracks `resulting_version_id`, `parent_version_id`, and `reason`.
5. `workflow_executions`: Already possesses open-ended, indexed `artifacts` (JSONB) and `metadata_payload` (JSONB).

### Verdict: **ZERO DATABASE MIGRATIONS REQUIRED**
All Phase 11L intelligence data structures (Unified Test Inventories, Cross-Test Coverage Reports, Change Impact Matrices, and Selective Regression Plans) can be stored within `WorkflowExecution.artifacts["test_coverage_intelligence"]` or derived on-demand from existing records.

---

## 14. Frontend Audit

Inspection of frontend workspaces (`frontend/src/`):

- **TestingWorkspace (`frontend/src/views/TestingWorkspace.tsx`):**
  - Current tabs: `analysis`, `browser`, `journeys`, `execution`.
  - Natural Phase 11L Placement: A dedicated 5th tab: **`coverage-intelligence`** (Coverage & Regression Intelligence) displaying unified test inventory, multi-layer requirement coverage, and coverage gaps.
- **DevelopmentWorkspace (`frontend/src/views/DevelopmentWorkspace.tsx`):**
  - Current tabs: `manifest`, `verification`, `compare`, `changes`.
  - Natural Phase 11L Placement: An enhancement to `compare` or a 5th tab **`impact`** (Change Impact & Affected Tests) displaying affected test suites and change blast radius when comparing versions.
- **AssistantDock (`frontend/src/components/assistant/AssistantDock.tsx`):**
  - Action preview chips for coverage analysis and selective regression execution.

---

## 15. Assistant Audit

Phase 11L candidate Assistant actions to register in `ACTION_REGISTRY`:

1. `GET_TEST_INVENTORY`:
   - Category: `READ_ONLY` | Confirmation: `False` | LLM: `False` | Target: `project`, `version`
2. `GET_COVERAGE_INTELLIGENCE`:
   - Category: `READ_ONLY` | Confirmation: `False` | LLM: `False` | Target: `project`, `version`
3. `ANALYZE_COVERAGE_GAPS`:
   - Category: `ANALYSIS` | Confirmation: `False` | LLM: `True` (for advisory explanations) | Target: `project`
4. `ANALYZE_REGRESSION_IMPACT`:
   - Category: `ANALYSIS` | Confirmation: `False` | LLM: `False` | Target: `version`
5. `RUN_SELECTIVE_REGRESSION`:
   - Category: `EXECUTION` | Confirmation: `False` | LLM: `False` | Target: `version`

---

## 16. API Audit

Conventions established in `backend/app/api/v1/endpoints/`:
- Project scoping: `/api/v1/projects/{project_id}/...`
- HTTP Methods: GET for queries, POST for actions/executions.
- Response wrapper: Strongly typed Pydantic models.
- Error handling: RFC 7807 Problem Details via `app.core.exceptions`.

### Recommended Phase 11L Endpoint Shapes:
- `GET /api/v1/projects/{project_id}/testing/inventory`: Unified list of all discovered tests across unit, AI, and browser categories.
- `GET /api/v1/projects/{project_id}/testing/coverage`: Multi-layer requirement coverage report.
- `GET /api/v1/projects/{project_id}/testing/coverage/gaps`: Detailed breakdown of uncovered requirements.
- `GET /api/v1/projects/{project_id}/versions/{version_id}/impact`: Change impact analysis and affected test set compared to parent version.
- `POST /api/v1/projects/{project_id}/testing/selective-run`: Execute only the affected test subset.

---

## 17. Security Audit

Potential security risks and existing defenses:

- **Cross-Project Test Leakage:** Prevented by enforcing project UUID foreign key checks on all DB queries and file maps.
- **Arbitrary Code Execution in Test Selection:** Pytest selectors and arguments passed to Docker containers must be strictly constrained to validated test IDs or file paths matching regex `^[a-zA-Z0-9_\-\./:]+$`.
- **Command Injection via Test Arguments:** No raw shell strings (`shell=False` strictly enforced in Docker execution).
- **Prompt Injection via Test Docstrings:** Telemetry and test descriptions treated strictly as plain text data; sanitized before LLM context ingestion.
- **Docker Socket & Host Exposure:** Remains completely prohibited. Containers execute as non-root on ephemeral networks.

---

## 18. Performance / Scale Audit

Estimated scale bounds for typical projects:
- Requirements: 10 – 100 items
- Files per version: 5 – 50 files
- Unit / AI test cases: 10 – 100 tests
- Browser journeys: 5 – 20 journeys
- Execution runs: 10 – 50 runs per project

### Performance Analysis:
- **AST Parsing:** Parsing 50 Python files via `ast.parse` requires $< 15\text{ ms}$ (in-memory, highly efficient).
- **Dependency Graph Traversal:** Traversal of 50 nodes requires $< 5\text{ ms}$.
- **Diff Calculation:** `difflib` comparison across 50 files requires $< 20\text{ ms}$.
- **Container Execution:** Running full regression takes $\sim 30\text{--}60\text{s}$.
- **Benefit of Selective Regression:** Executing only 2 affected tests instead of 20 reduces test duration by $70\text{--}90\%$.

---

## 19. Traceability Matrix

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              TARGET TRACEABILITY MODEL                                 │
└────────────────────────────────────────────────────────────────────────────────────────┘

    Requirement (ID, Title, Category, Priority)
         │
         ├──► Implementation Symbol (Module / Class / Function)
         │         │
         │         └──► Modified in Version N (Change Impact)
         │                   │
         │                   └──► Triggers Selective Regression
         │
         └──► Unified Test Case
                   ├── Type: UNIT | AI_TEST | BROWSER_SMOKE | BROWSER_JOURNEY
                   ├── Test Target: Symbol / Endpoint / Route
                   ├── Last Execution: PASSED | FAILED | NOT_RUN
                   └── Associated Failure Diagnosis (if failed)
```

---

## 20. Candidate Phase 11L Capabilities

### TABLE 4 — Phase 11L Candidate Capabilities Evaluation

| Candidate Capability | Current Status | Feasibility | Proposed Architecture Approach |
|---|---|---|---|
| **A. Unified Test Inventory** | Missing | **High** | Aggregates discovered scaffold tests, AI tests, and browser test definitions into a normalized catalog. |
| **B. Requirement-to-Test Traceability** | Partial | **High** | Merges AI test traceability and browser journey traceability into a unified mapping. |
| **C. Coverage Gap Detection** | Partial | **High** | Extends `RequirementCoverageEngine` to categorize uncovered requirements by business priority and type. |
| **D. Cross-Test-Type Coverage** | Missing | **High** | Unified coverage engine calculating combined coverage across Unit + AI + Browser test types. |
| **E. Change Impact Analysis** | Missing | **High** | Combines `compare_versions` file diffs with `ASTAnalyzer` import graph to determine modified symbols. |
| **F. Affected Test Detection** | Missing | **High** | Traverses dependency graph from changed symbols to identify tests importing or targeting them. |
| **G. Intelligent Test Selection** | Missing | **High** | Filters execution suite to only affected tests, reducing Docker runtime. |
| **H. Regression Planning** | Missing | **Medium** | Produces a prioritized regression test execution plan (high priority / changed components first). |
| **I. Historical Test Comparison** | Missing | **Medium** | Queries past `WorkflowExecution` test runs to display pass/fail transitions between versions. |
| **J. Failure/Test Correlation** | Exists | **High** | Reuses `FailureAnalysisAgent` evidence references to tie test failures back to originating requirements. |
| **K. Coverage Trend Analysis** | Missing | **Medium** | Computes coverage delta between Version $N$ and Version $N-1$. |
| **L. Risk-Aware Prioritization** | Missing | **Medium** | Deterministic prioritization weighting failure history + requirement priority + code change size. |

---

## 21. Architecture Options Analysis

### Major Decision: Storage and Calculation of Coverage Intelligence

| Evaluation Criteria | Option A: New Database Tables (`test_cases`, `test_coverages`) | Option B: WorkflowExecution Artifact Store | Option C: Derived On-Demand Computation (Recommended) |
|---|---|---|---|
| **Database Migrations** | Requires Alembic migration | **Zero migrations** | **Zero migrations** |
| **Storage Overhead** | High (relational rows per test case) | Medium (JSON artifacts) | **Zero persistent storage overhead** |
| **Staleness Risk** | High (can drift out of sync with code) | Low (tied to workflow run) | **Zero (always computed from active state)** |
| **Query Performance** | Fast SQL indexing | Fast JSON retrieval | Very Fast ($< 30\text{ ms}$ in-memory AST scan) |
| **Architecture Fit** | Violates immutable version snapshot pattern | Aligns with existing workflow persistence | **Perfect alignment with existing service patterns** |

**Recommendation:** Adopt **Option C (Derived On-Demand Computation)** with cached serialization into `WorkflowExecution.artifacts["test_coverage_intelligence"]` whenever a test workflow runs.

---

## 22. Proposed Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              PROPOSED PHASE 11L ARCHITECTURE                           │
└────────────────────────────────────────────────────────────────────────────────────────┘

                                    Active Project
                                          │
                   ┌──────────────────────┴──────────────────────┐
                   ▼                                             ▼
        DevelopmentVersion (Files Map)              Requirements (Authoritative Reqs)
                   │                                             │
                   ▼                                             │
      ┌─────────────────────────┐                                │
      │   ASTDependencyGraph    │ ◄── ASTAnalyzer + TestDiscovery │
      │   (Imports & Symbols)   │                                │
      └────────────┬────────────┘                                │
                   │                                             │
                   ▼                                             ▼
      ┌─────────────────────────┐                   ┌─────────────────────────┐
      │   ChangeImpactEngine    │                   │ UnifiedCoverageEngine   │
      │  (Diff + Graph Match)   │                   │ (Unit + AI + Browser)   │
      └────────────┬────────────┘                   └────────────┬────────────┘
                   │                                             │
                   ▼                                             ▼
      ┌─────────────────────────┐                   ┌─────────────────────────┐
      │  SelectiveTestPlanner   │                   │  CoverageIntelligence   │
      │  (Affected Test Suite)  │                   │  (Gaps + Traceability)  │
      └────────────┬────────────┘                   └────────────┬────────────┘
                   │                                             │
                   ▼                                             ▼
      ┌─────────────────────────┐                   ┌─────────────────────────┐
      │ Existing Test Runners   │                   │ Unified REST API / UI   │
      │ (Sandbox & Browser)     │                   │ (Testing & Dev Spaces)  │
      └─────────────────────────┘                   └─────────────────────────┘
```

### TABLE 5 — Existing Component Reuse

| Existing Component | Location | Phase 11L Reuse Purpose |
|---|---|---|
| `ASTAnalyzer` | `backend/app/sandbox/static_analysis/ast_analyzer.py` | Extract imports, functions, classes for dependency graph. |
| `TestDiscovery` | `backend/app/sandbox/static_analysis/test_discovery.py` | Statically identify test files and test functions. |
| `compare_versions` | `backend/app/services/development_version_service.py` | Identify modified files and requirement deltas between versions. |
| `RequirementCoverageEngine` | `backend/app/browser/journey/coverage.py` | Foundation for mathematical coverage calculation. |
| `DockerRuntimeExecutor` | `backend/app/sandbox/docker_executor.py` | Execute selective pytest suites with targeted test arguments. |
| `BrowserTestingService` | `backend/app/browser/service.py` | Execute selective browser journeys matching affected routes. |
| `FailureAnalysisAgent` | `backend/app/agents/failure_analysis/` | Analyze failures arising from selective regression runs. |
| `DevelopmentVerificationService` | `backend/app/services/verification_service.py` | Incorporate coverage intelligence into version verification gates. |

### TABLE 6 — Proposed New Components (Phase 11L)

| Proposed Component | Type | Responsibility |
|---|---|---|
| `UnifiedTestInventoryService` | Service | Discovers and catalogs Unit, AI, and Browser tests into a single normalized model. |
| `UnifiedCoverageEngine` | Engine | Computes combined requirement coverage across all test tiers. |
| `ASTDependencyGraph` | Utility | In-memory directed graph of project files and module imports. |
| `ChangeImpactService` | Service | Computes blast radius of file modifications and maps to affected requirements. |
| `SelectiveRegressionPlanner` | Engine | Selects minimum sufficient test set targeting affected code and requirements. |
| `CoverageIntelligencePanel` | Frontend | React component displaying unified coverage, gaps, and test traceability. |
| `ChangeImpactPanel` | Frontend | React component displaying modified files, affected requirements, and tests. |

---

## 23. Proposed Phase 11L Staged Roadmap

A disciplined 8-stage roadmap ensuring incremental validation without breaking frozen baselines:

```
Stage 11L-1: Unified Test Inventory & Traceability Foundation
Stage 11L-2: Multi-Tier Requirement Coverage Intelligence
Stage 11L-3: AST Dependency Graph & Change Impact Engine
Stage 11L-4: Change-Aware Selective Test Planner
Stage 11L-5: Selective Execution Orchestration (Sandbox & Browser)
Stage 11L-6: REST API & Assistant Integration
Stage 11L-7: Frontend Testing & Development Workspace Integration
Stage 11L-8: Live Containerized E2E Validation & Final Release Gate
```

---

## 24. Stage-by-Stage Definitions

### Stage 11L-1: Unified Test Inventory & Traceability Foundation
- **Objective:** Establish normalized data contracts for test cases regardless of tier (Unit, AI, Browser Smoke, Browser Journey).
- **Inputs:** Source files, `tests/test_*.py`, `AITestSuite`, `ValidatedBrowserJourneySuite`.
- **Outputs:** `UnifiedTestInventory` containing normalized `TestDefinition` items.
- **Persistence:** None (Derived on-demand or stored in workflow artifacts).
- **Zero Migrations:** Yes.

### Stage 11L-2: Multi-Tier Requirement Coverage Intelligence
- **Objective:** Extend coverage calculation beyond browser journeys to aggregate Unit, AI, and Browser tests.
- **Inputs:** `UnifiedTestInventory`, active project requirements.
- **Outputs:** `UnifiedCoverageReport` with tier breakdown (Unit %, AI %, Browser %, Combined %).
- **Zero Migrations:** Yes.

### Stage 11L-3: AST Dependency Graph & Change Impact Engine
- **Objective:** Deterministically map project files to their import dependencies using `ast.parse`.
- **Inputs:** Project source files, file diffs from `compare_versions`.
- **Outputs:** `ChangeImpactReport` (modified files $\rightarrow$ dependent files $\rightarrow$ impacted symbols).
- **Zero Migrations:** Yes.

### Stage 11L-4: Change-Aware Selective Test Planner
- **Objective:** Deterministically identify which tests must be re-run based on `ChangeImpactReport`.
- **Inputs:** `ChangeImpactReport`, `UnifiedTestInventory`.
- **Outputs:** `SelectiveRegressionPlan` (selected test IDs, skipped test IDs, selection rationale).
- **Zero Migrations:** Yes.

### Stage 11L-5: Selective Execution Orchestration
- **Objective:** Pass selective test targets to existing `DockerRuntimeExecutor` (pytest `-k` or file arguments) and `BrowserTestingService`.
- **Inputs:** `SelectiveRegressionPlan`.
- **Outputs:** `SelectiveExecutionResult` recording passed/failed tests and execution time savings.
- **Zero Migrations:** Yes.

### Stage 11L-6: REST API & Assistant Integration
- **Objective:** Expose Phase 11L endpoints under `/api/v1/projects/{project_id}/testing/` and register Assistant actions.
- **Inputs:** Project ID, Version ID.
- **Outputs:** REST DTOs matching backend contracts.
- **Zero Migrations:** Yes.

### Stage 11L-7: Frontend Workspace Integration
- **Objective:** Build UI panels in `TestingWorkspace` (Coverage Intelligence) and `DevelopmentWorkspace` (Change Impact).
- **Inputs:** REST API payloads.
- **Outputs:** Interactive React visualization components.
- **Zero Migrations:** Yes.

### Stage 11L-8: Live Containerized E2E Validation & Final Release Gate
- **Objective:** Full regression, Docker verification, cleanup audit, zero leaks, release gate decision.
- **Inputs:** Live Docker daemon, complete test suites.
- **Outputs:** `Phase_11L_Stage8_Final_Hardening_Report.md`.
- **Zero Migrations:** Yes.

---

## 25. Persistence Strategy

### TABLE 7 — Persistence Impact

| Entity / Concern | Existing Storage Channel | Proposed Phase 11L Treatment | Database Schema Change? |
|---|---|---|---|
| **Unified Test Inventory** | Computed on-demand from files & artifacts | Derived in-memory; optionally cached in `WorkflowExecution.artifacts["test_inventory"]` | **NO** |
| **Combined Coverage Report** | `artifacts["browser_journey_validation"]` | Cached in `WorkflowExecution.artifacts["coverage_intelligence"]` | **NO** |
| **Change Impact Matrix** | Computed on-demand from version diff | Returned directly via API response; cached on `WorkflowExecution` | **NO** |
| **Selective Regression Plan** | Stored during regression workflow run | Persisted in `WorkflowExecution.artifacts["selective_regression_plan"]` | **NO** |
| **Selective Test Results** | `WorkflowExecution.artifacts` | Persisted in `WorkflowExecution.artifacts["selective_execution_result"]` | **NO** |

---

## 26. API Strategy

### TABLE 8 — API Impact

| Endpoint | Method | Purpose | Authority / Service |
|---|---|---|---|
| `/api/v1/projects/{project_id}/testing/inventory` | GET | List normalized test inventory across all tiers | `UnifiedTestInventoryService` |
| `/api/v1/projects/{project_id}/testing/coverage` | GET | Retrieve combined requirement coverage report | `UnifiedCoverageService` |
| `/api/v1/projects/{project_id}/testing/coverage/gaps` | GET | Retrieve uncovered requirements and risk analysis | `UnifiedCoverageService` |
| `/api/v1/projects/{project_id}/versions/{version_id}/impact` | GET | Retrieve change impact and affected tests vs. parent | `ChangeImpactService` |
| `/api/v1/projects/{project_id}/testing/selective-run` | POST | Trigger selective regression run targeting affected tests | `SelectiveRegressionService` |

---

## 27. Frontend Strategy

### TABLE 9 — Frontend Impact

| Workspace | View / Component | Proposed Addition | User Capability |
|---|---|---|---|
| **TestingWorkspace** | Tab: `coverage-intelligence` | `CoverageIntelligencePanel` | View unified coverage percentage, tier breakdown, and coverage gap list. |
| **TestingWorkspace** | Tab: `coverage-intelligence` | `TestInventoryList` | Search and filter tests by category (Unit, AI, Browser), target symbol, and status. |
| **DevelopmentWorkspace** | Tab: `compare` | `ChangeImpactView` | View modified files mapped to affected requirements and affected test cases. |
| **DevelopmentWorkspace** | Action Bar | "Run Affected Tests" Button | Trigger selective regression for the active version change. |
| **AssistantDock** | Action Preview Card | Coverage & Impact Cards | Inspect coverage summaries and trigger selective runs via conversational chips. |

---

## 28. Assistant Strategy

### TABLE 10 — Assistant Impact

| Action ID | Category | Parameters | Execution Behavior | Confirmation Required? |
|---|---|---|---|---|
| `GET_TEST_INVENTORY` | `READ_ONLY` | `version_id` (optional) | Queries normalized test catalog | No |
| `GET_COVERAGE_INTELLIGENCE` | `READ_ONLY` | `version_id` (optional) | Queries multi-tier requirement coverage | No |
| `ANALYZE_COVERAGE_GAPS` | `ANALYSIS` | None | Evaluates uncovered requirements and provides engineering explanations | No |
| `ANALYZE_REGRESSION_IMPACT` | `ANALYSIS` | `version_id`, `parent_version_id` | Computes affected tests for code modifications | No |
| `RUN_SELECTIVE_REGRESSION` | `EXECUTION` | `version_id`, `test_ids` (optional) | Executes affected test subset in Docker sandbox | No |

---

## 29. Security Strategy

### TABLE 11 — Security Risks & Countermeasures

| Threat / Risk | Impact | Existing Defense | Proposed Phase 11L Mitigation |
|---|---|---|---|
| **Cross-Project Test Leakage** | Information disclosure | Project scoping on all DB queries | Strict `project_id` matching in all test inventory and coverage services. |
| **Pytest Argument Injection** | Remote code execution | `docker_executor.py` runs fixed cmd | Strict regex validation (`^[a-zA-Z0-9_\-\./:]+$`) on all selective test arguments. |
| **Prompt Injection via Test Names** | LLM hijacking | Structured prompts with clear bounds | All test names and code snippets escaped and sanitized before LLM context injection. |
| **Container Escape / Host Mount** | Container vulnerability | Non-root users, no Docker socket | Ephemeral containers, read-only root filesystems where applicable. |
| **Credential Ingestion in Tests** | Secret leakage | `RE_SECRET_PATTERNS` regex | Rejection of secrets in test definitions and selective run parameters. |

---

## 30. Testing Strategy

1. **Unit Tests:**
   - Test AST dependency graph construction with complex Python import patterns (`from . import`, `import as`, aliased modules).
   - Test mathematical correctness of combined coverage calculation.
   - Test change impact symbol resolution with various unified diff formats.
   - Test deterministic test filtering and selection rules.
2. **Integration Tests:**
   - Verify selective pytest invocation in Docker sandbox container.
   - Verify selective browser journey invocation in Docker Playwright container.
   - Verify project isolation across all new endpoints (HTTP 404 on cross-project access).
3. **Regression Tests:**
   - Full backend suite (1,062 tests) must remain 100% green.
   - Full frontend suite (76 tests) must remain 100% green.
   - Frontend production build (`npm run build`) must pass with 0 errors.

---

## 31. Migration Strategy

- **Database Changes:** **NONE (0 migrations)**.
- **Breaking API Changes:** **NONE**. All Phase 11K REST endpoints and schemas remain unchanged.
- **Backward Compatibility:** Projects with existing versions will automatically support coverage intelligence upon on-demand calculation.

---

## 32. Key Risks & Mitigations

1. **Risk:** Highly dynamic Python imports (e.g. `importlib.import_module`, `getattr`) may not be discovered by AST.
   - **Mitigation:** When dynamic imports are detected, conservatively mark the module as "dynamically coupled", causing dependent tests to be included in selective regression rather than omitted.
2. **Risk:** Unanchored pytest test discovery missing non-standard test naming.
   - **Mitigation:** Adhere strictly to canonical pytest standards (`test_*.py`, `*_test.py`, `def test_*`).
3. **Risk:** Selective test runs skipping a failing test that has an indirect, unmodeled side effect.
   - **Mitigation:** Offer an explicit "Run All Tests" fallback button alongside "Run Affected Tests" in the UI.

---

## 33. Dependencies

- Phase 11K frozen backend and frontend baseline.
- Python standard library `ast`, `difflib`, `re`.
- Existing `StaticAnalysisService`, `DevelopmentVersionService`, `DockerRuntimeExecutor`, `BrowserTestingService`.

---

## 34. Definition of Done (Phase 11L)

A Phase 11L stage is declared DONE only when:
1. All newly introduced services and engines are covered by comprehensive unit tests.
2. Endpoints strictly enforce project scoping and return RFC 7807 problem details on error.
3. Backend regression suite maintains 100% pass rate.
4. Frontend build passes with 0 TypeScript errors.
5. Live Docker execution is verified without orphaned containers or networks.
6. Zero database migrations introduced.

---

## 35. Recommended Next Implementation Stage

### Recommended First Implementation Stage: **Phase 11L Stage 1**
**Scope of Stage 1:**
1. Define unified test inventory domain models and contracts (`UnifiedTestDefinition`, `UnifiedTestInventory`, `TestTier`).
2. Implement `UnifiedTestInventoryService` parsing scaffold unit tests, AI tests, and browser journeys.
3. Implement `UnifiedCoverageEngine` calculating combined multi-tier requirement coverage.
4. Comprehensive unit test suite verifying contracts, discovery, and deterministic coverage math.
5. Zero modifications to existing execution engines or frontend.

---

## 36. Architecture Diagrams

### Diagram 1: Current Testing Architecture
```
[User / Workspace]
       │
       ├──► POST /projects/{id}/sandbox/run ──────────► Docker Sandbox (Scaffold Unit Tests)
       ├──► POST /projects/{id}/tests/ai/generate ────► TestGenerationAgent -> AITestSuite
       │    └──► POST /projects/{id}/tests/ai/execute ─► Docker Sandbox (AI Generated Tests)
       ├──► POST /projects/{id}/browser/run ──────────► BrowserTestingService (Smoke Tests)
       └──► POST /projects/{id}/browser-journeys ─────► Orchestrator -> Dual Containers (Journeys)
                                                               │
                                                               └──► RequirementCoverageEngine
                                                                    (BROWSER ONLY)
```

### Diagram 2: Current Coverage Architecture
```
+-------------------------------------------------------+
|  Active Requirements: [REQ-1, REQ-2, REQ-3, REQ-4]   |
+-------------------------------------------------------+
                           │
                           ▼
+-------------------------------------------------------+
|  Validated Browser Journeys                           |
|  - Journey 1: covers [REQ-1, REQ-2]                   |
|  - Journey 2: covers [REQ-2]                          |
+-------------------------------------------------------+
                           │
                           ▼
+-------------------------------------------------------+
|  RequirementCoverageEngine                            |
|  Covered:   [REQ-1, REQ-2] (50.0%)                    |
|  Uncovered: [REQ-3, REQ-4] (50.0%)                    |
+-------------------------------------------------------+
  * NOTE: Even if REQ-3 is tested by Unit Tests, it is reported as 0% covered!
```

### Diagram 3: Current Requirement Traceability
```
Requirement ──────► Browser Journey ──────► BrowserTestRun ──────► WorkflowExecution
      │
      ├───► AI Test Case ───────────────► AITestExecution ──────► WorkflowExecution
      │
      └───► Unit Test (NO LINK) ────────► SandboxExecution ─────► WorkflowExecution
```

### Diagram 4: Proposed Phase 11L Architecture
```
                         Project Source & Requirements
                                       │
                 ┌─────────────────────┴─────────────────────┐
                 ▼                                           ▼
      [UnifiedTestInventory]                      [UnifiedCoverageEngine]
      ├── Unit Tests                              ├── Unit Coverage %
      ├── AI Generated Tests                      ├── AI Test Coverage %
      └── Browser Journeys                        ├── Browser Coverage %
                 │                                └── COMBINED COVERAGE %
                 │                                           │
                 ▼                                           ▼
      [ChangeImpactEngine]                        [CoverageIntelligence]
      ├── File / AST Graph Match                  ├── Uncovered Gap Analysis
      └── Affected Test Set                       └── Traceability Matrix
                 │                                           │
                 ▼                                           ▼
      [SelectiveRegressionPlanner]                [REST API & Frontend UI]
      └── Execute ONLY Affected Tests             ├── Coverage Dashboard
                                                  └── Change Impact View
```

### Diagram 5: Proposed Test-Selection Flow
```
Code Modification (v1 -> v2)
       │
       ▼
DevelopmentVersionService.compare_versions (files_modified, files_added)
       │
       ▼
ASTAnalyzer: Extract modified functions/classes in changed files
       │
       ▼
ASTDependencyGraph: Identify all project files importing modified modules
       │
       ▼
TestDiscovery + Inventory: Find test cases targeting modified or dependent files
       │
       ▼
SelectiveRegressionPlan: [test_calc_add, test_calc_sub] (2 of 30 tests selected)
       │
       ▼
Docker Execution: pytest tests/test_calc.py -k "test_calc_add or test_calc_sub"
```

### Diagram 6: Proposed Change-Impact Flow
```
Git/Version Diff: File 'app/auth.py' modified (Function: 'verify_password')
       │
       ├──► AST Analysis: 'app/api/login.py' imports 'verify_password' from 'app/auth'
       │
       ├──► Requirement Mapping: 'app/auth.py' satisfies REQ-AUTH-01
       │
       └──► Affected Test Selection:
            - Unit: tests/test_auth.py::test_verify_password
            - AI: tests/test_ai_auth.py::test_login_invalid_password
            - Journey: journey_login_flow
```

### Diagram 7: AI vs. Deterministic Boundary
```
┌───────────────────────────────────────┬───────────────────────────────────────┐
│        DETERMINISTIC BACKEND          │           AI-ASSISTED LAYER           │
├───────────────────────────────────────┼───────────────────────────────────────┤
│ - AST parsing and symbol extraction   │ - Natural language gap explanation    │
│ - Exact diff and line change tracking │ - Business risk summarization         │
│ - Dependency graph traversal          │ - Suggesting new journey scenarios    │
│ - Combined coverage math calculation  │ - Root cause hypothesis (FA Agent)    │
│ - Selective test filtering            │ - Conceptual fix guidance             │
│ - Docker container test execution     │                                       │
│ - Pass / Fail / Error evaluation      │                                       │
└───────────────────────────────────────┴───────────────────────────────────────┘
```

### Diagram 8: Persistence Flow
```
On-Demand / Workflow Execution
       │
       ▼
UnifiedCoverageEngine / ChangeImpactService
       │
       ├──► Direct REST Response (JSON DTO)
       │
       └──► Persisted in WorkflowExecution.artifacts:
            ├── "test_inventory"
            ├── "coverage_intelligence"
            ├── "change_impact"
            └── "selective_regression_plan"
       │
       └──► Aggregated into DevelopmentVersion.verification_summary
```

### Diagram 9: Assistant Flow
```
User: "What tests are affected by my changes in version 2?"
       │
       ▼
AssistantReasoningService -> Dispatches 'ANALYZE_REGRESSION_IMPACT'
       │
       ▼
EngineeringActionService -> Calls ChangeImpactService
       │
       ▼
ChangeImpactService -> Returns 3 affected tests out of 40
       │
       ▼
AssistantDock -> Displays Affected Tests Card with "Run Affected Tests" button
       │
       ▼ (User Clicks)
EngineeringActionService -> Dispatches 'RUN_SELECTIVE_REGRESSION'
```

---

## 37. Final Phase 11L Summary

```text
============================================================
PHASE 11L DISCOVERY STATUS:
COMPLETE

CURRENT SYSTEM:
Fully operational Phase 11K baseline with 4 separate test execution silos
(Static Analysis, Sandbox Unit Tests, AI Tests, Browser Journeys).
Requirement coverage currently exists ONLY for Browser Journeys.

KEY GAPS:
1. Fragmented test inventories (no unified queryable catalog of all tests).
2. Single-type coverage calculation (Unit and AI tests excluded from requirement coverage).
3. No change impact analysis linking modified code to dependent tests.
4. No selective regression execution (always executes 100% of tests).
5. No historical coverage or regression comparison across versions.

REUSABLE EXISTING COMPONENTS:
1. ASTAnalyzer & DependencyAnalyzer (Static AST and import extraction)
2. TestDiscovery (Static pytest file and function discovery)
3. DevelopmentVersionService.compare_versions (File diffs and requirement deltas)
4. RequirementCoverageEngine (Deterministic coverage math foundation)
5. DockerRuntimeExecutor & BrowserTestingService (Isolated runtime containers)
6. FailureAnalysisAgent (Evidence-grounded root cause diagnosis)
7. DevelopmentVerificationService (Multi-stage verification snapshot aggregation)

PROPOSED ARCHITECTURE:
A zero-migration, on-demand intelligence layer consisting of:
- UnifiedTestInventoryService (Normalized catalog across all 4 test tiers)
- UnifiedCoverageEngine (Combined multi-tier requirement coverage)
- ASTDependencyGraph & ChangeImpactService (Diff -> AST -> Affected Tests)
- SelectiveRegressionPlanner (Targeted test execution via existing Docker runners)

PROPOSED STAGES:
Stage 11L-1: Unified Test Inventory & Traceability Foundation
Stage 11L-2: Multi-Tier Requirement Coverage Intelligence
Stage 11L-3: AST Dependency Graph & Change Impact Engine
Stage 11L-4: Change-Aware Selective Test Planner
Stage 11L-5: Selective Execution Orchestration (Sandbox & Browser)
Stage 11L-6: REST API & Assistant Integration
Stage 11L-7: Frontend Testing & Development Workspace Integration
Stage 11L-8: Live Containerized E2E Validation & Final Release Gate

FIRST IMPLEMENTATION STAGE:
Stage 11L-1: Unified Test Inventory & Traceability Foundation

FIRST IMPLEMENTATION STAGE SCOPE:
- Normalized test definition models and contracts.
- Inventory discovery service scanning scaffold tests, AI tests, and browser journeys.
- Bidirectional traceability engine connecting tests to requirements.
- Unit test suite validating contracts and discovery.

OUT OF SCOPE:
- Database schema changes or migrations.
- Autonomous remediation or self-healing loops.
- Modifications to AgentExecutor or WorkflowCoordinator.
- New Docker infrastructure or third-party LLM providers.

MIGRATION REQUIREMENT:
ZERO (0) database migrations required.

CRITICAL RISKS:
- Dynamic Python imports bypassing static AST detection (mitigated via conservative coupling heuristics).
- Flaky tests in selective execution (mitigated via "Run All" fallback options).
============================================================
```
