# Phase 11K Stage 2 — Implementation Report
## Deterministic Browser Journey Validation & Requirement Coverage Engine

**Phase:** Phase 11K — AI-Powered Browser Journey Generation  
**Stage:** Stage 2 — Deterministic Browser Journey Validation + Requirement Coverage Engine  
**Author:** Antigravity (Advanced Agentic AI Pair Programmer)  
**Date:** 2026-10-03  
**Status:** COMPLETE, VERIFIED & AUDITED  

---

## 1. Executive Summary & Baseline

Phase 11K Stage 1 established structured, typed contracts (`BrowserJourney`, `BrowserJourneyStep`, `BrowserJourneySuiteCandidate`, etc.) and the `BrowserJourneyGenerationAgent` which outputs candidate user test intent.

Stage 2 operationalizes the core architectural invariant:
> **AI proposes. Deterministic backend validates.**

The Stage 2 engine transforms an unverified, untrusted `BrowserJourneySuiteCandidate` into an authoritative `ValidatedBrowserJourneySuite`, computing a deterministic `RequirementCoverageReport` strictly in backend Python arithmetic without any LLM invocations.

### Strict Stage 2 Invariants Verified
1. **Zero LLM authority:** LLMs never decide whether a requirement exists, whether a route exists, whether actions are valid, or what coverage percentage was attained.
2. **Zero Execution:** No Playwright, Docker container startup, filesystem access, or shell command execution occurs in Stage 2.
3. **No Silent Redaction or Omission:** Invalid requirement references or non-existent routes raise deterministic validation errors rather than silently stripping invalid elements.
4. **Project Isolation:** Referencing a requirement belonging to another project fails with `CROSS_PROJECT_REQUIREMENT_FORBIDDEN`.
5. **No Persistence or Schema Mutations:** No database migrations, no mutations to `DevelopmentVersion` or its metadata.
6. **No API or Assistant additions:** REST APIs and Assistant action registration remain deferred to Stage 5.

---

## 2. Repository Findings & Architecture Re-use

1. **Active Requirement Semantics:** Inspected `backend/app/services/context_engine.py` and `backend/app/models/requirement.py`. Confirmed active requirement semantics are:
   - `not req.is_archived`
   - `req.status in {RequirementStatus.DRAFT, RequirementStatus.APPROVED, RequirementStatus.IMPLEMENTED}`
   Excluded statuses are `DEFERRED` and `REJECTED`.
2. **Authoritative Application Routes:** Routes are sourced from declared/discovered routes (`BoundedRouteInfo`), web application route manifests, and `ApplicationRuntimeManifest.health_check_path` (`backend/app/schemas/runtime.py`).
3. **Validation Architecture:** Followed the patterns established in `test_generation/validator.py` and `agents/validation.py`, implementing structured, categorized `ValidationIssue` records with machine-readable error codes and strict schema typing.

---

## 3. Files Created & Modified

### Created Files
1. `backend/app/browser/journey/__init__.py`: Package exports for the browser journey validation subsystem.
2. `backend/app/browser/journey/contracts.py`: Strongly typed Stage 2 data models (`ValidatedBrowserJourneySuite`, `ValidatedBrowserJourney`, `RequirementCoverageReport`, `ValidationContext`, `ValidationIssue`, `ValidationOutcome`, enums `ValidationCategory` and `ValidationSeverity`).
3. `backend/app/browser/journey/coverage.py`: `RequirementCoverageEngine` implementing deterministic requirement coverage math and bidirectional traceability mapping.
4. `backend/app/browser/journey/errors.py`: Exception classes (`BrowserJourneyValidationError`, `BrowserJourneyError`).
5. `backend/app/browser/journey/validator.py`: `BrowserJourneyValidator` implementing structural, requirement, route, action, target, security, and cross-journey validation.
6. `backend/tests/unit/test_browser_journey_coverage.py`: 6 unit tests covering 100%, partial, 0%, zero active requirements, and deduplication.
7. `backend/tests/unit/test_browser_journey_validator.py`: 13 unit tests covering structural checks, requirement isolation, parameterized route matching, security rejections, and complexity bounds.
8. `docs/architecture/Phase_11K_Stage2_Implementation_Report.md`: This comprehensive implementation report.

### Modified Files
1. `backend/app/browser/__init__.py`: Exported Stage 2 symbols (`BrowserJourneyValidator`, `RequirementCoverageEngine`, `ValidatedBrowserJourneySuite`, `RequirementCoverageReport`, etc.).

---

## 4. Validator Architecture

```
BrowserJourneySuiteCandidate
        ↓
BrowserJourneyValidator
        ├── 1. Suite-Level Structure & Complexity Caps
        ├── 2. Journey-Level Structural & Identifier Validation
        ├── 3. Requirement Verification & Project Isolation
        ├── 4. Authoritative Route Manifest Matching (Static & Parameterized)
        ├── 5. Browser Action Semantics Validation
        ├── 6. Target Element & CSS Selector Safety Validation
        ├── 7. Test Data (Fill Value) Security & Secret Sniffing
        ├── 8. Duplicate Detection (IDs & Journey Signatures)
        └── 9. Cross-Journey Total Limits
        ↓
If Validation Fails: ValidationOutcome (is_valid=False, errors=[...])
If Validation Passes:
        ↓
RequirementCoverageEngine.compute_coverage()
        ↓
ValidatedBrowserJourneySuite (with RequirementCoverageReport)
```

---

## 5. Requirement Validation & Project Isolation

- **Authoritative Denominator:** Only canonical active requirements for the target project are eligible.
- **Project Isolation:** Candidate references to foreign project requirement IDs are flagged with `CROSS_PROJECT_REQUIREMENT_FORBIDDEN`.
- **Hallucination Rejection:** Requirement IDs not found in the project's requirement set are flagged with `HALLUCINATED_REQUIREMENT`.
- **Status Filter:** Requirement IDs that exist in the project but are `DEFERRED`, `REJECTED`, or archived are flagged with `INACTIVE_REQUIREMENT`.
- **No Silent Stripping:** Invalid IDs cause the validation outcome to fail; they are never silently ignored.

---

## 6. Route Validation & Parameterized Matching

- **Prohibited Schemes & Hosts:** Rejects external URLs (`http://`, `https://`) and dangerous schemes (`javascript:`, `data:`, `file:`, `blob:`, `chrome:`). All routes must be relative paths starting with `/`.
- **Authoritative Route Matching Strategy:**
  1. Exact matching: matches exact string paths (e.g. `/login` matches `/login` or `/login/`).
  2. Parameterized path matching: converts route manifest templates like `/projects/{project_id}` or `/items/{id}` into deterministic regex patterns (`^/projects/[^/]+/?$`).
  3. Rejection: Candidate routes not found in the authoritative application route manifest are rejected with `NONEXISTENT_ROUTE`.

---

## 7. Action & Target Validation

- **Controlled Action Types:** Permitted actions are strictly restricted to `BrowserActionType` (12 actions).
- **Action Completeness:**
  - `NAVIGATE`: requires `route`.
  - `CLICK`, `CHECK`, `UNCHECK`, `SUBMIT`, `ASSERT_VISIBLE`, `ASSERT_ELEMENT`: require `target`.
  - `FILL`, `SELECT`: require `target` and `value`.
  - `ASSERT_TEXT`: requires `target` and either `value` or `assertion`.
  - `ASSERT_URL`: requires `route` or `value`.
  - `WAIT`: requires `timeout_seconds` between 0.1s and 60.0s.
- **Target & CSS Selector Safety:**
  - Max CSS selector length: 200 characters.
  - Prohibits `<script>`, `javascript:`, `eval(`, `expression(`, `-moz-binding`, `@import`, `url(`, `document.`, `window.`, `Function(`.
  - Validates balanced brackets `()`, `[]`, `{}`. Unbalanced selectors are rejected with `DANGEROUS_CSS_SELECTOR`.

---

## 8. Test Data (Fill Value) & Security Validation

- **Length Bound:** Max fill value is 500 characters.
- **Control Characters:** Rejects null bytes `\x00` with `UNSAFE_FILL_VALUE`.
- **Secret & Key Sniffing:** Scans all text fields for private keys (`-----BEGIN ... KEY-----`), Bearer tokens, API keys, and access tokens. Candidates containing potential secrets are rejected with `UNSAFE_FILL_VALUE`.
- **Raw Playwright Code Sniffing:** Rejects `page.goto`, `page.click`, `page.fill`, `page.evaluate`, `browser.new_page`, `locator(`, `async def test_`, `import playwright`.

---

## 9. Complexity Limits & Duplicate Detection

### Complexity Limits
- Max journeys per suite: 15
- Max steps per journey: 30
- Max total steps across suite: 100
- Max journey ID length: 64
- Max title length: 150
- Max description length: 1000
- Max precondition / outcome length: 500
- Max target / fill value length: 500
- Max wait duration: 60.0s (min 0.1s)
Any limit violation produces `COMPLEXITY_LIMIT_EXCEEDED`.

### Duplicate Detection
- **Duplicate Journey IDs:** Detected and flagged with `DUPLICATE_JOURNEY_ID`.
- **Duplicate Step IDs:** Within a journey, detected and flagged with `DUPLICATE_STEP_ID`.
- **Duplicate Journey Content:** Computes a deterministic content signature `(title.lower(), category, steps_tuple)`. Identical journeys are flagged with `DUPLICATE_JOURNEY_CONTENT`.

---

## 10. Requirement Coverage Calculation

The `RequirementCoverageEngine` calculates coverage metrics deterministically:
$$\text{coverage\_percentage} = \begin{cases} \text{round}\left(\frac{\text{covered\_requirement\_count}}{\text{total\_active\_requirements}} \times 100, 2\right), & \text{if total\_active\_requirements} > 0 \\ 0.0, & \text{otherwise} \end{cases}$$

- **Covered Requirement:** An active project requirement is covered if and only if at least one authoritatively validated journey references it.
- **Uncovered Requirements:** Deterministically computed as `active_requirement_ids - covered_requirement_ids`.
- **Traceability:** Emits bidirectional dictionaries:
  - `requirement_to_journeys_map`: `Requirement ID -> list[Journey IDs]`
  - `journey_to_requirements_map`: `Journey ID -> list[Requirement IDs]`

---

## 11. Security Audit Results

A comprehensive static audit was performed across `backend/app/browser/journey/` searching for forbidden execution and container primitives:
- `subprocess`: **0 occurrences (CLEAN)**
- `shell=True`: **0 occurrences (CLEAN)**
- `os.system`: **0 occurrences (CLEAN)**
- `eval(`: **0 occurrences (CLEAN)**
- `exec(`: **0 occurrences (CLEAN)**
- `docker.sock`: **0 occurrences (CLEAN)**
- `--privileged`: **0 occurrences (CLEAN)**
- `--network host`: **0 occurrences (CLEAN)**

The Stage 2 engine contains **zero execution authority**.

---

## 12. Verification & Regression Metrics

### Stage 2 Unit Tests
- `tests/unit/test_browser_journey_coverage.py`: **6 passed**
- `tests/unit/test_browser_journey_validator.py`: **13 passed**
- Total Stage 2 Tests: **19 passed**

### Combined Browser Journey Subsystem Tests
- `test_browser_journey_contracts.py` (Stage 1): 50 passed
- `test_browser_journey_agent.py` (Stage 1): 12 passed
- `test_browser_journey_coverage.py` (Stage 2): 6 passed
- `test_browser_journey_validator.py` (Stage 2): 13 passed
- Total Browser Journey Tests: **81 passed**

### Full Backend Regression Suite
- Command: `pytest tests/ -q`
- Previous Baseline: **964 passed**
- Stage 2 Added Tests: **19 passed**
- Total Collected & Passed: **983 passed, 0 failed, 0 errors**
- Exit Code: **0**

### Frontend Regression Suite
- Command: `npm test -- --run`
- Test Files: **14 passed**
- Tests: **59 passed, 0 failed**

---

## 13. Deferred Work (Stage 3+)

- **Stage 3:** `BrowserJourneyAdapter` transforming `ValidatedBrowserJourneySuite` into executable Phase 11J `DeterministicBrowserTestDefinition` objects.
- **Stage 4:** Multi-agent pipeline orchestration via `WorkflowCoordinator`.
- **Stage 5:** REST endpoints (`/projects/{id}/browser-journeys`), DTO schemas, and Intelli Assistant action integration (`GENERATE_BROWSER_JOURNEYS`).
- **Stage 6:** Frontend UI views (Testing Workspace journeys tab, review dialogs, coverage meters).

---

## 14. Definition of Done Checklist — Stage 2

- [x] `BrowserJourneyValidator` exists and is purely deterministic
- [x] `ValidatedBrowserJourneySuite` exists and contains validated journeys
- [x] `RequirementCoverageReport` exists with exact coverage math
- [x] Requirement IDs are deterministically validated against active project context
- [x] Project isolation is enforced (`CROSS_PROJECT_REQUIREMENT_FORBIDDEN`)
- [x] Active requirement semantics match platform rules (non-archived DRAFT/APPROVED/IMPLEMENTED)
- [x] Route validation uses authoritative application route information (static & parameterized)
- [x] External URLs and unsafe URI schemes are rejected
- [x] Browser action semantics are deterministically validated
- [x] Target types and CSS selectors are validated for safety and balanced brackets
- [x] Security violations and secrets in fill values are rejected (`UNSAFE_FILL_VALUE`)
- [x] Complexity limits (journeys, steps, total steps, string lengths) are enforced
- [x] Duplicate journeys and step IDs are detected
- [x] Requirement traceability mapping is deterministic
- [x] Uncovered requirements list is deterministic
- [x] Coverage percentage is calculated only by backend code
- [x] LLM never calculates coverage or validates candidates
- [x] Invalid candidates cannot become validated suites
- [x] Zero browser or Docker execution occurs in Stage 2
- [x] Zero REST APIs added
- [x] Zero Assistant modifications
- [x] Zero frontend modifications
- [x] Zero database migrations or mutations to `DevelopmentVersion`
- [x] All 19 Stage 2 unit tests pass
- [x] All 81 browser journey subsystem unit tests pass
- [x] Complete backend regression suite passes (983 tests)
- [x] Complete frontend regression suite passes (59 tests)
- [x] Security audit passes with zero forbidden execution primitives
- [x] Working tree clean; zero git commits or pushes made
