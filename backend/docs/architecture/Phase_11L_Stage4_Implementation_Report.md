# Phase 11L — Stage 4 Implementation Report
## Selective Regression Planning Foundation

**Platform:** SE IntelliPlatform — AI-Powered Multi-Agent Platform for Smart Software Development  
**Phase:** 11L — Advanced Application Testing & Coverage Intelligence  
**Stage:** Stage 4 — Selective Regression Planning  
**Status:** IMPLEMENTATION COMPLETE — STAGE 4 ONLY (FROZEN & VERIFIED)  
**Date:** 2026-10-03  

---

## 1. Executive Summary

Phase 11L Stage 4 establishes the authoritative, deterministic regression planning capability for SE IntelliPlatform. It bridges deterministic change-impact intelligence (`ChangeImpactReport` from Stage 3), multi-tier coverage intelligence (`UnifiedCoverageReport` from Stage 2), and cataloged test inventory (`UnifiedTestInventory` from Stage 1) to synthesize a strongly typed, deterministic, and validated regression plan (`RegressionPlan`).

Stage 4 operates strictly as a **planning layer**:
- **Stage 4 plans. Stage 4 does NOT execute.**
- **Zero test execution:** No pytest invocations, no Docker container dispatch, no Playwright runner triggers, and no subprocess execution.
- **Zero AI / LLM test selection:** All candidate selection, requirement protection, conservative broadening, and safety evaluation are purely calculated via deterministic algorithms.
- **Mandatory Conservative Safety:** Any uncertainty (unknown dependencies, unsupported languages, dynamic imports, unresolvable mappings) strictly triggers broader regression (`BROAD` or `FULL`) or renders selective execution explicitly marked `is_execution_safe = False`. Under-selection under uncertainty is architecturally forbidden.

---

## 2. Existing Regression/Planning Architecture Inspection

Before implementation, an architectural inspection of the repository was conducted:
1. **Stage 1 Inventory Foundation (`app.testing.inventory`):**
   - Authoritative cataloging of all 4 test tiers: `UNIT`, `AI_TEST`, `BROWSER_SMOKE`, `BROWSER_JOURNEY`.
   - Clear distinction between authoritative `requirement_links` and heuristic/candidate `inferred_requirement_links`.
   - Deterministic test identification and indexing.
2. **Stage 2 Coverage Intelligence (`app.testing.coverage`):**
   - Pure set-union requirement coverage across tiers (zero tier averaging).
   - Identifies active requirements, covered requirements, and uncovered requirements (coverage gaps).
3. **Stage 3 AST Dependency Graph & Change Impact (`app.testing.impact`):**
   - Static AST dependency graph, transitive impact closures, conservative uncertainty flags (`requires_broader_regression`, `uncertain_dependencies`, `uncertain_files`), and affected test/requirement mapping.
4. **Existing Regression Planners:**
   - No duplicate regression planners or impact-based test filtering abstractions existed in the codebase. Existing services focused on single-tier execution or runtime verification without cross-tier selective planning.

---

## 3. Reuse vs. New Abstraction Decision

To maintain high cohesion and prevent code duplication:
- **Reused:** `UnifiedTestInventory` and `UnifiedTestDefinition` as authoritative test identities.
- **Reused:** `ChangeImpactReport` and `ImpactReason` for deterministic change impact signals.
- **Reused:** `UnifiedCoverageReport` for active requirement sets and coverage gap alignment.
- **Created:** `app.testing.regression` containing:
  - `contracts.py`: Defines `RegressionPlanMode`, `PlanSelectionReason`, `SelectedTest`, and `RegressionPlan`.
  - `validator.py`: Defines `RegressionPlanValidator` enforcing structural validity, project isolation, tier correctness, and conservative safety invariants.
  - `planner.py`: Defines `SelectiveRegressionPlanner` orchestrating deterministic candidate selection, requirement protection, conservative broadening, and plan synthesis.
  - `errors.py`: Strongly typed exception hierarchy (`RegressionPlanError`, `RegressionPlanIsolationError`, `RegressionPlanValidationError`).

---

## 4. Stage 3 Input Integration

The planner directly consumes `ChangeImpactReport`:
- `affected_tests`: Seeds initial candidate tests.
- `test_impact_reasons`: Determines whether tests are impacted via `DIRECT_CHANGE`, `DEPENDENCY_CLOSURE`, `BROWSER_ROUTE_OVERLAP`, or `UNKNOWN_DEPENDENCY`.
- `all_affected_files`: Populates `affected_files` on each `SelectedTest`.
- `affected_requirements`: Drives requirement protection logic.
- `requires_broader_regression`: Dictates conservative broadening and execution safety predicates.

---

## 5. Stage 2 Coverage Integration

The planner seamlessly consumes `UnifiedCoverageReport`:
- `active_requirement_ids`: Provides authoritative baseline of active project requirements.
- Distinguishes affected requirements that are protected by the plan versus requirements that have coverage gaps.
- Calculates `unrelated_requirement_ids` (active requirements completely unaffected and not selected in the plan).
- Preserves the Stage 2 set-union rule: requirement coverage of the plan is computed as the set union of authoritative links across selected tests without averaging tier percentages.

---

## 6. Test Selection Algorithm

The selection algorithm follows a deterministic pipeline:
1. **Mode Dispatch:**
   - **`FULL` Mode:** Selects all valid tests in the inventory across all four tiers, assigning reason `FULL_REGRESSION` and scope `"FULL"`.
   - **`SELECTIVE` / `BROAD` Modes:**
     - **Direct & Transitive Code Impact:** Tests in `impact_report.affected_tests` are included with reasons corresponding to their impact (`DIRECT_CHANGE`, `DEPENDENCY_IMPACT`, `BROWSER_ROUTE_IMPACT`, `CONSERVATIVE_FALLBACK`).
     - **Requirement Protection:** For each requirement in `impact_report.affected_requirements`, authoritative tests are looked up via `inventory.get_tests_for_requirement(req_id)` and included with reason `REQUIREMENT_PROTECTION` and scope `"REQUIREMENT"`.
     - **Broadening (when in `BROAD` mode):** All `UNIT` and `BROWSER_SMOKE` tests are added as a conservative safety perimeter with reason `BROAD_REGRESSION`.
2. **Deterministic Ordering:**
   - Selected tests are sorted first by tier execution priority (`UNIT` → `AI_TEST` → `BROWSER_SMOKE` → `BROWSER_JOURNEY`), and secondarily by `test_id`.
3. **Partitioning:**
   - Tests are mapped into `selected_tests_by_tier` for each of the four tiers with sorted test ID lists.

---

## 7. Requirement Protection

- **Authoritative Links Only:** Only tests possessing authoritative `requirement_links` linked to affected requirements are selected for requirement protection.
- **Inferred Links Excluded:** Tests with only `inferred_requirement_links` are strictly excluded from requirement protection. Heuristic associations never drive test selection.
- **Provenance:** Selected tests store the exact affected requirements they protect in `SelectedTest.affected_requirements`.

---

## 8. Selective Mode

- Selects the minimal deterministic set of tests required to verify modified code and protect affected active requirements.
- Permitted as safe (`is_execution_safe = True`) **only** when change impact analysis is high confidence and free of dynamic imports, unsupported files, syntax errors, or unresolved dependencies.

---

## 9. Broad Mode

- An intermediate conservative plan between `SELECTIVE` and `FULL`.
- Includes all directly and transitively affected tests, requirement protection tests, and extends coverage to all `UNIT` and `BROWSER_SMOKE` tests across the project.
- Activated either explicitly by user/system request or automatically via `auto_broaden=True` when uncertainty is flagged.

---

## 10. Full Regression Fallback

- Preserves the ability to run all tests across all four tiers (`RegressionPlanMode.FULL`).
- Selected tests encompass 100% of non-conflicting valid inventory tests.
- Every test receives the `FULL_REGRESSION` selection reason.
- Execution safety is guaranteed (`is_execution_safe = True`).

---

## 11. Uncertainty Handling

Uncertainty sources identified in Stage 3:
1. Dynamic imports (`__import__`, `importlib`, `eval`, `exec`).
2. Unsupported source languages (e.g., TypeScript/JavaScript files in backend analysis).
3. Files modified outside the static dependency graph.
4. Syntax errors preventing AST parsing.

When uncertainty exists (`requires_broader_regression = True`):
- If `mode == SELECTIVE` and `auto_broaden == False`: The plan is generated, but `is_execution_safe` is set to `False`, and a warning is logged in `plan_warnings`.
- If `mode == SELECTIVE` and `auto_broaden == True`: The plan automatically upgrades to `RegressionPlanMode.BROAD`, adding all unit and smoke tests, setting `is_execution_safe = True`, and logging the broadening rationale in `broadening_reasons`.

---

## 12. Conservative Safety Model

The core safety invariant is strictly enforced:
$$\text{UNKNOWN / UNCERTAIN} \implies \text{BROADER REGRESSION}$$
$$\text{UNKNOWN} \not\implies \text{SAFE TO SKIP}$$

The `RegressionPlanValidator` actively enforces that any plan with `requires_broader_regression == True` and `mode == SELECTIVE` will raise a `RegressionPlanValidationError` if `is_execution_safe` is claimed to be `True`.

---

## 13. Browser Smoke Handling

- `BROWSER_SMOKE` tests are identified by `TestTier.BROWSER_SMOKE`.
- Tests targeting routes or symbols matching modified backend routes or controllers receive reason `PlanSelectionReason.BROWSER_ROUTE_IMPACT` with scope `"BROWSER_ROUTE"`.
- In `BROAD` mode, all browser smoke tests are selected to guard core navigation and entrypoints.

---

## 14. Browser Journey Handling

- `BROWSER_JOURNEY` tests represent multi-step user scenarios.
- **Safety Invariant:** Only tests originating from `DiscoveryProvenance.VALIDATED_BROWSER_JOURNEY` (and where `metadata.get("is_validated") is not False`) may enter the plan.
- Raw Playwright scripts, unvalidated AI journey candidates, and arbitrary scripts are rejected by the planner and blocked by `RegressionPlanValidator`.

---

## 15. AI Test Handling

- `AI_TEST` is treated as a first-class deterministic test tier.
- AI tests are selected through deterministic change impact closures or requirement links.
- Stage 4 performs zero AI test generation and invokes zero LLMs.

---

## 16. Plan Validation

The `RegressionPlanValidator` verifies:
1. **Project Isolation:** `plan.project_id == inventory.project_id` and all tests belong to `plan.project_id`.
2. **Test ID Existence:** Every selected test ID exists in `inventory.tests_by_id`.
3. **No Duplicates:** `selected_test_ids` and `selected_tests` have no duplicate entries.
4. **Tier Consistency:** All test tiers match valid `TestTier` enum values and agree with inventory definitions.
5. **Validated Browser Journeys:** Rejects any journey with unvalidated provenance.
6. **Requirement Integrity:** Rejects empty or whitespace-only requirement IDs.
7. **Conservative Safety Invariant:** Rejects plans claiming safe selective execution when broader regression is required.
8. **Inventory Count Consistency:** Confirms `total_inventory_tests` and `unselected_test_count` arithmetic matches inventory.

---

## 17. Determinism

- Stable ordering across all collections:
  - Tests sorted by tier execution priority (`UNIT` → `AI_TEST` → `BROWSER_SMOKE` → `BROWSER_JOURNEY`), then by `test_id`.
  - Requirements, file lists, and reasons sorted alphabetically.
- **Logical Equivalence:** The `__eq__` operator on `RegressionPlan` compares all logical attributes while excluding volatile execution timestamps (`created_at`). Repeated planning on identical inputs produces `plan_1 == plan_2`.

---

## 18. Project Isolation

All planning operations enforce strict project boundaries:
- Any cross-project inventory, impact report, coverage report, or test reference raises `RegressionPlanIsolationError`.
- Validated through dedicated isolation test cases.

---

## 19. Performance

- In-memory processing using dictionary lookups and sets.
- Time complexity: $O(|T| + |R|)$ where $T$ is the test inventory and $R$ is the requirement set.
- Zero network I/O, zero database queries, and zero container overhead.

---

## 20. Security

Stage 4 additions are 100% pure planning logic and contain zero:
- `shell=True`
- `os.system`
- `subprocess` execution
- `eval` or `exec`
- Docker daemon connections or container creation
- Playwright browser execution
- Direct LLM or cloud API calls
- Secret handling or credential exposure

---

## 21. Files Created

1. `backend/app/testing/regression/__init__.py`
2. `backend/app/testing/regression/contracts.py`
3. `backend/app/testing/regression/errors.py`
4. `backend/app/testing/regression/planner.py`
5. `backend/app/testing/regression/validator.py`
6. `backend/tests/unit/test_regression_planner.py`
7. `backend/tests/unit/test_regression_plan_validation.py`
8. `docs/architecture/Phase_11L_Stage4_Implementation_Report.md`

---

## 22. Files Modified

None. All Phase 1–11L Stage 3 modules and frontend files remained untouched.

---

## 23. Tests Added

A total of **30 new unit tests** were added covering all scenarios A–AD:

### `backend/tests/unit/test_regression_planner.py` (21 tests)
- `test_scenario_a_empty_change_set`
- `test_scenario_b_no_affected_tests`
- `test_scenario_c_one_directly_changed_unit_test`
- `test_scenario_d_direct_dependency_impact`
- `test_scenario_e_transitive_dependency_impact`
- `test_scenario_f_requirement_protection`
- `test_scenario_gh_four_tier_selection`
- `test_scenario_i_inferred_requirement_links_ignored`
- `test_scenario_j_affected_uncovered_requirement_coverage_gap`
- `test_critical_safety_unknown_dependency_blocks_selective_safe`
- `test_critical_safety_auto_broaden_promotes_to_broad_and_safe`
- `test_scenario_modes_full_regression`
- `test_scenario_modes_broad_regression`
- `test_scenario_s_deterministic_repeated_planning_equivalence`
- `test_scenario_t_duplicate_test_prevention`
- `test_scenario_v_cross_project_isolation`
- `test_scenario_wx_browser_journey_selection_and_unvalidated_exclusion`
- `test_scenario_y_browser_smoke_route_impact`
- `test_scenario_z_ai_test_deterministic_selection`
- `test_scenario_aa_requirement_coverage_accounting`
- `test_scenario_ac_stage_3_service_integration`
- `test_scenario_ad_no_execution_side_effects`

### `backend/tests/unit/test_regression_plan_validation.py` (9 tests)
- `test_valid_plan_passes_validation`
- `test_rejection_of_unknown_test_id`
- `test_rejection_of_duplicate_test_ids`
- `test_rejection_of_project_isolation_mismatch`
- `test_rejection_of_foreign_test_in_plan`
- `test_rejection_of_unvalidated_browser_journey`
- `test_rejection_of_unsafe_selective_execution_invariant`
- `test_rejection_of_inventory_count_mismatch`

---

## 24. Regression Results

| Suite | Previous Baseline | Stage 4 Result | Status |
|---|---|---|---|
| Stage 4 Tests | 0 | 30 / 30 | PASS |
| Phase 11L Cumulative (Stages 1–4) | 59 / 59 | 89 / 89 | PASS |
| Full Backend Regression | 1,121 / 1,121 | 1,151 / 1,151 | PASS |
| Frontend Unit/Integration | 76 / 76 | 76 / 76 | PASS |
| Frontend Production Build | PASS | PASS | PASS |
| Security Audit | PASS | Clean (0 violations) | PASS |
| Database Migrations | None | None | PASS |
| Git Commits / Pushes | None | None | PASS |

---

## 25. Known Limitations

1. **Static Route Resolution:** Browser smoke route mapping relies on explicit route references in test metadata (`routes` list or `target_symbol` starting with `/`). Ambiguous route resolution falls back to conservative broadening.
2. **In-Memory Plans:** Stage 4 produces in-memory Pydantic plans. Persistence to database or workflow execution artifacts is intentionally deferred.
3. **Execution Delegation:** Stage 4 strictly plans; it does not dispatch tests to executors. Stage 5 owns execution dispatch.

---

## 26. Explicit Stage 5 Boundary

Stage 4 is strictly decoupled from test execution:
- **Stage 4:** Generates and validates `RegressionPlan` containing ordered `SelectedTest` items and safety indicators.
- **Stage 5 (Deferred):** Consumes `RegressionPlan`, coordinates dispatch across runners (pytest for unit/AI, Playwright in Docker for smoke/journeys), collects results, and analyzes regression outcomes.
- Under no circumstances does Stage 4 execute code or invoke test harnesses.

---

## 27. Git Status

- No git commits were made.
- No git pushes were executed.
- All modifications are strictly confined to authorized Stage 4 files in `backend/app/testing/regression/`, corresponding unit tests in `backend/tests/unit/`, and this documentation artifact.
