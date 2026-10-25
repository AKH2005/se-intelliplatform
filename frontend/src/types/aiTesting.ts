export type TestCategory =
  | 'HAPPY_PATH'
  | 'EDGE_CASE'
  | 'VALIDATION'
  | 'ERROR_HANDLING'
  | 'BUSINESS_LOGIC'
  | 'API_BEHAVIOR';

export interface GeneratedTest {
  test_id: string;
  name: string;
  description: string;
  category: TestCategory;
  target_file: string;
  target_symbol?: string | null;
  requirement_ids: string[];
  architecture_component?: string | null;
  rationale: string;
  code: string;
  expected_behavior: string;
}

export interface AITestSuite {
  suite_id: string;
  project_id: string;
  workflow_execution_id?: string | null;
  summary: string;
  tests: GeneratedTest[];
  test_count: number;
  requirement_traceability: Record<string, string[]>;
  source_artifact_reference: string;
  static_analysis_reference?: string | null;
  test_files: Record<string, string>;
  created_at: string;
  metadata?: Record<string, unknown>;
}

export interface AITestCaseResult {
  name: string;
  status: string;
  duration_seconds: number;
  message?: string | null;
}

export interface AITestExecutionResult {
  execution_id: string;
  suite_id: string;
  project_id: string;
  workflow_execution_id?: string | null;
  status:
    | 'PASSED'
    | 'FAILED'
    | 'TIMEOUT'
    | 'RESOURCE_LIMIT'
    | 'SANDBOX_ERROR'
    | 'VALIDATION_ERROR'
    | 'SANDBOX_UNAVAILABLE';
  exit_code: number | null;
  duration_seconds: number;
  tests_total: number;
  tests_passed: number;
  tests_failed: number;
  tests_skipped: number;
  stdout: string;
  stderr: string;
  failure_summaries: string[];
  test_results: AITestCaseResult[];
  executed_at: string;
  metadata?: Record<string, unknown>;
}
