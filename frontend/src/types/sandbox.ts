export type ExecutionType = 'STATIC_VALIDATE' | 'TEST' | 'LINT';

export type DiagnosticSeverity = 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';

export type DiagnosticCategory =
  | 'SECURITY'
  | 'SYNTAX'
  | 'LINT'
  | 'IMPORT'
  | 'DEPENDENCY'
  | 'TEST'
  | 'STRUCTURE';

export type StaticAnalysisStatus =
  | 'PASSED'
  | 'ISSUES_FOUND'
  | 'VALIDATION_ERROR'
  | 'ANALYSIS_ERROR';

export interface StaticDiagnostic {
  diagnostic_id: string;
  category: DiagnosticCategory;
  severity: DiagnosticSeverity;
  code: string;
  message: string;
  file_path?: string | null;
  line?: number | null;
  column?: number | null;
  source: string;
  evidence?: string | null;
  metadata?: Record<string, any>;
}

export interface StaticAnalysisRequest {
  project_id: string;
  workflow_execution_id?: string | null;
}

export interface StaticAnalysisResult {
  analysis_id: string;
  project_id: string;
  workflow_execution_id?: string | null;
  artifact_id?: string | null;
  status: StaticAnalysisStatus;
  duration_seconds: number;
  diagnostics: StaticDiagnostic[];
  files_analyzed: number;
  files_skipped: number;
  error_count: number;
  warning_count: number;
  info_count: number;
  security_issue_count: number;
  syntax_error_count: number;
  lint_issue_count: number;
  test_file_count: number;
  summary: string;
  metadata: Record<string, any>;
}

export type ExecutionStatus =
  | 'PASSED'
  | 'FAILED'
  | 'TIMEOUT'
  | 'RESOURCE_LIMIT'
  | 'SANDBOX_ERROR'
  | 'VALIDATION_ERROR'
  | 'SANDBOX_UNAVAILABLE';

export interface ResourceLimits {
  timeout_seconds: number;
  memory_limit: string;
  cpus: number;
  max_pids: number;
  max_output_bytes: number;
}

export interface ExecutionRequest {
  project_id: string;
  workflow_execution_id?: string | null;
  execution_type?: ExecutionType;
  test_target?: string | null;
  limits?: Partial<ResourceLimits>;
}

export interface ExecutionResult {
  execution_id: string;
  project_id: string;
  workflow_execution_id?: string | null;
  execution_type: ExecutionType;
  status: ExecutionStatus;
  exit_code?: number | null;
  duration_seconds: number;
  stdout: string;
  stderr: string;
  is_truncated: boolean;
  tests_passed: number;
  tests_failed: number;
  tests_total: number;
  validation_errors: string[];
  metadata: Record<string, any>;
}

export interface SandboxStatusResponse {
  available: boolean;
  runtime: string;
  image: string;
  security_policy: Record<string, string>;
}
