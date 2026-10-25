/**
 * Browser Journey Contracts for Phase 11K Stage 6.
 *
 * Strictly mirrors the Stage 5 backend contracts defined in:
 * backend/app/schemas/browser_journeys.py
 * backend/app/browser/journey/contracts.py
 */

export type BrowserJourneyWorkflowStatus =
  | 'PENDING'
  | 'RUNNING'
  | 'COMPLETED'
  | 'WORKFLOW_GENERATION_FAILED'
  | 'WORKFLOW_VALIDATION_FAILED'
  | 'WORKFLOW_ADAPTATION_FAILED'
  | 'WORKFLOW_BROWSER_EXECUTION_FAILED';

export type BrowserJourneyCategory =
  | 'AUTHENTICATION'
  | 'NAVIGATION'
  | 'FORM_SUBMISSION'
  | 'CRUD_WORKFLOW'
  | 'SEARCH_FILTER'
  | 'ERROR_RECOVERY'
  | 'MULTI_STEP_INTERACTION';

export type BrowserJourneyPriority = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export type BrowserActionType =
  | 'NAVIGATE'
  | 'CLICK'
  | 'FILL'
  | 'SELECT'
  | 'ASSERT_TEXT'
  | 'ASSERT_VISIBLE'
  | 'ASSERT_URL'
  | 'WAIT';

export interface BrowserJourneyStep {
  step_number: number;
  action: BrowserActionType;
  target_role?: string | null;
  target_label?: string | null;
  target_selector_candidate?: string | null;
  value?: string | null;
  assertion_type?: string | null;
  expected_value?: string | null;
  wait_condition?: string | null;
  timeout_ms?: number;
}

export interface BrowserJourney {
  journey_id: string;
  title: string;
  description: string;
  category: BrowserJourneyCategory | string;
  priority: BrowserJourneyPriority | string;
  requirement_ids: string[];
  routes: string[];
  preconditions: string[];
  steps: BrowserJourneyStep[];
  expected_outcomes: string[];
}

export interface BrowserJourneySuite {
  suite_id: string;
  project_id: string;
  journeys: BrowserJourney[];
  metadata?: Record<string, any>;
}

export interface RequirementCoverageReport {
  coverage_percentage: number;
  covered_requirement_ids: string[];
  uncovered_requirement_ids: string[];
  requirement_to_journeys?: Record<string, string[]>;
}

export interface FailureDiagnosisSection {
  summary: string;
  likely_cause?: string | null;
  evidence?: string[] | null;
  affected_journey_id?: string | null;
  affected_step_number?: number | null;
  remediation_hint?: string | null;
}

export interface BrowserJourneyWorkflowResponse {
  workflow_execution_id: string;
  project_id: string;
  status: BrowserJourneyWorkflowStatus | string;
  stage_reached: string;
  journey_count: number;
  validation_passed: boolean;
  coverage_percentage: number | null;
  covered_requirement_ids: string[];
  uncovered_requirement_ids: string[];
  test_definitions_count: number;
  browser_tests_executed: boolean;
  browser_tests_passed: boolean | null;
  browser_test_run_id: string | null;
  failure_reason: string | null;
  failure_diagnosis: Record<string, any> | null;
  artifacts: Record<string, any>;
  started_at: string;
  completed_at: string | null;
  duration_seconds: number;
}

export interface GenerateBrowserJourneysRequest {
  development_version_id?: string | null;
  execute_browser_tests?: boolean;
  max_journeys?: number;
}
