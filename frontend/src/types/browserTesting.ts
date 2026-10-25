/**
 * Browser Testing and UI Automation Contracts for Phase 11J Stage 5.
 */

export type BrowserTestStatus =
  | 'PENDING'
  | 'RUNNING'
  | 'PASSED'
  | 'FAILED'
  | 'STARTUP_FAILED'
  | 'BROWSER_ERROR'
  | 'TIMEOUT'
  | 'RESOURCE_LIMIT'
  | 'VALIDATION_ERROR'
  | 'SANDBOX_ERROR';

export type BrowserArtifactType =
  | 'SCREENSHOT'
  | 'CONSOLE_LOG'
  | 'NETWORK_LOG'
  | 'DOM_SNAPSHOT'
  | 'TRACE';

export interface BrowserArtifactReference {
  artifact_id: string;
  artifact_type: BrowserArtifactType;
  file_path: string;
  size_bytes: number;
  content_type: string;
  caption?: string | null;
  step_number?: number | null;
  created_at: string;
}

export interface BrowserConsoleError {
  message: string;
  level: string;
  source?: string | null;
  line_number?: number | null;
  column_number?: number | null;
  timestamp: string;
}

export interface BrowserNetworkRecord {
  url: string;
  method: string;
  status_code: number;
  failure_text?: string | null;
  response_time_ms: number;
  timestamp: string;
}

export interface BrowserTestCaseResult {
  test_id: string;
  name: string;
  status: BrowserTestStatus;
  duration_seconds: number;
  failed_step?: string | null;
  assertion_summary?: string | null;
  screenshots: BrowserArtifactReference[];
  console_errors: BrowserConsoleError[];
  network_errors: BrowserNetworkRecord[];
}

export interface BrowserTestRun {
  run_id: string;
  project_id: string;
  version_id?: string | null;
  workflow_execution_id?: string | null;
  status: BrowserTestStatus;
  tests_total: number;
  tests_passed: number;
  tests_failed: number;
  tests_skipped: number;
  duration_seconds: number;
  test_cases: BrowserTestCaseResult[];
  failure_reason?: string | null;
  summary: string;
  artifacts: BrowserArtifactReference[];
  started_at: string;
  completed_at?: string | null;
  metadata?: Record<string, any>;
}

export interface RunBrowserTestsRequest {
  development_version_id?: string | null;
}
