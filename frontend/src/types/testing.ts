/**
 * Phase 11L: Testing Intelligence & Regression Dashboard Types
 *
 * Defines TypeScript interfaces matching the authoritative backend contracts for:
 * - Unified Test Inventory (11L-1)
 * - Multi-Tier Coverage Intelligence (11L-2)
 * - AST Dependency Graph & Change Impact (11L-3)
 * - Selective Regression Planning (11L-4)
 * - Selective Regression Execution & Results (11L-5)
 * - REST API DTOs (11L-6)
 */

export type TestTier = 'UNIT' | 'AI_TEST' | 'BROWSER_SMOKE' | 'BROWSER_JOURNEY';

export type DiscoveryProvenance =
  | 'PYTEST_DISCOVERY'
  | 'AI_SYNTHESIS'
  | 'BROWSER_SMOKE_CONVENTION'
  | 'VALIDATED_BROWSER_JOURNEY';

export type AnalysisConfidence = 'HIGH' | 'MEDIUM' | 'LOW';

export type RegressionPlanMode = 'SELECTIVE' | 'BROAD' | 'FULL';

export type TestExecutionStatus = 'PASSED' | 'FAILED' | 'ERROR' | 'SKIPPED' | 'BLOCKED';

export type RegressionExecutionStatus =
  | 'PASSED'
  | 'FAILED'
  | 'PARTIAL_FAILURE'
  | 'BLOCKED'
  | 'ERROR'
  | 'TIMEOUT';

// ============================================================================
// 1. Unified Test Inventory (11L-1)
// ============================================================================

export interface UnifiedTestDefinition {
  test_id: string;
  name: string;
  tier: TestTier;
  provenance: DiscoveryProvenance;
  target_file: string;
  target_symbol?: string | null;
  requirement_links: string[]; // Authoritative requirement links
  inferred_requirement_links: string[]; // Inferred (non-authoritative) requirement links
  execution_metadata: Record<string, any>;
  is_validated_journey: boolean;
  deterministic_hash?: string | null;
}

export interface TestInventoryConflict {
  test_id: string;
  existing_source: string;
  conflicting_source: string;
  message: string;
}

export interface UnifiedTestInventory {
  inventory_id: string;
  project_id: string;
  total_tests: number;
  tests: UnifiedTestDefinition[];
  tier_counts: Record<string, number>;
  conflicts: TestInventoryConflict[];
  discovery_status: string;
  discovered_at: string;
  metadata: Record<string, any>;
}

// ============================================================================
// 2. Multi-Tier Coverage Intelligence (11L-2)
// ============================================================================

export interface TierCoverageSummary {
  tier: TestTier;
  total_active_requirements: number;
  covered_requirement_count: number;
  uncovered_requirement_count: number;
  coverage_percentage: number;
  covered_requirement_ids: string[];
  uncovered_requirement_ids: string[];
}

export interface RequirementTraceability {
  requirement_id: string;
  is_covered: boolean;
  covering_test_ids: string[];
  covering_tiers: TestTier[];
  is_authoritative: boolean;
}

export interface UnifiedCoverageReport {
  project_id: string;
  total_active_requirements: number;
  active_requirement_ids: string[];
  tier_coverages: Record<string, TierCoverageSummary>;
  combined_covered_requirement_ids: string[];
  combined_uncovered_requirement_ids: string[];
  combined_coverage_percentage: number;
  requirement_traceability: Record<string, RequirementTraceability>;
  calculated_at: string;
  metadata: Record<string, any>;
}

// ============================================================================
// 3. Coverage Gaps (11L-2 / 11L-6)
// ============================================================================

export interface CoverageGapItem {
  requirement_id: string;
  requirement_title: string;
  priority: string;
  status: string;
  covering_tiers: string[];
  associated_test_ids: string[];
  notes?: string | null;
}

export interface CoverageGapsResponse {
  project_id: string;
  total_active_requirements: number;
  uncovered_count: number;
  gaps: CoverageGapItem[];
  tier_uncovered_summary: Record<string, number>;
}

// ============================================================================
// 4. AST Dependency Graph & Change Impact (11L-3)
// ============================================================================

export interface ChangeImpactReport {
  project_id: string;
  changed_files: string[];
  directly_affected_files: string[];
  transitively_affected_files: string[];
  all_affected_files: string[];
  affected_tests: UnifiedTestDefinition[];
  affected_test_ids: string[];
  test_impact_reasons: Record<string, string[]>;
  affected_requirements: string[];
  requirement_impact_reasons: Record<string, string[]>;
  uncertain_files: string[];
  requires_broader_regression: boolean;
  uncertainty_reasons: string[];
  confidence: AnalysisConfidence;
  analyzed_at: string;
  metadata: Record<string, any>;
}

export interface ChangeImpactRequest {
  changed_files?: string[];
  base_version_id?: string;
  target_version_id?: string;
  files_map?: Record<string, string>;
}

// ============================================================================
// 5. Selective Regression Planning (11L-4)
// ============================================================================

export interface SelectedTest {
  test_id: string;
  tier: TestTier;
  selection_reasons: string[];
  selection_scope: string;
  target_file?: string | null;
  target_symbol?: string | null;
}

export interface RegressionPlan {
  project_id: string;
  mode: RegressionPlanMode;
  base_version_id?: string | null;
  target_version_id?: string | null;
  inventory_id: string;
  selected_test_ids: string[];
  selected_tests: SelectedTest[];
  selected_tests_by_tier: Record<string, string[]>;
  selected_requirement_ids: string[];
  affected_requirement_ids: string[];
  protected_requirement_ids: string[];
  uncovered_affected_requirement_ids: string[];
  unrelated_requirement_ids: string[];
  selection_reasons_by_test: Record<string, string[]>;
  broadening_reasons: string[];
  requires_broader_regression: boolean;
  is_execution_safe: boolean;
  plan_warnings: string[];
  total_inventory_tests: number;
  unselected_test_count: number;
  created_at: string;
  metadata: Record<string, any>;
}

export interface PlanRegressionRequest {
  base_version_id?: string;
  target_version_id?: string;
  changed_files?: string[];
  mode?: RegressionPlanMode;
  auto_broaden?: boolean;
}

// ============================================================================
// 6. Selective Regression Execution (11L-5)
// ============================================================================

export interface IndividualTestResult {
  test_id: string;
  tier: TestTier;
  status: TestExecutionStatus;
  duration_seconds: number;
  output_snippet: string;
  error_message?: string | null;
  is_infrastructure_failure: boolean;
  requirement_ids: string[];
}

export interface TierExecutionSummary {
  tier: TestTier;
  total_tests: number;
  passed: number;
  failed: number;
  errored: number;
  skipped: number;
  blocked: number;
  duration_seconds: number;
}

export interface RequirementExecutionResult {
  requirement_id: string;
  is_satisfied: boolean;
  covering_tiers: TestTier[];
  passed_test_ids: string[];
  failed_test_ids: string[];
}

export interface RegressionExecutionResult {
  execution_id: string;
  project_id: string;
  inventory_id: string;
  mode: RegressionPlanMode;
  status: RegressionExecutionStatus;
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  errored_tests: number;
  skipped_tests: number;
  blocked_tests: number;
  duration_seconds: number;
  tier_summaries: Record<string, TierExecutionSummary>;
  test_results: IndividualTestResult[];
  requirement_results: Record<string, RequirementExecutionResult>;
  executed_at: string;
  metadata: Record<string, any>;
}

export interface ExecuteRegressionRequest {
  plan?: RegressionPlan;
  base_version_id?: string;
  target_version_id?: string;
  changed_files?: string[];
  mode?: RegressionPlanMode;
  auto_broaden?: boolean;
  skip_browser_tests?: boolean;
  browser_base_url?: string;
  execution_timeout_seconds?: number;
}
