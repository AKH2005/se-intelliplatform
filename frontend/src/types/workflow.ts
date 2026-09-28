import { AgentErrorDetail } from './agent';

export type WorkflowStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'PARTIAL_SUCCESS' | 'FAILED';
export type WorkflowStepStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'SKIPPED';

export interface WorkflowStepMetadata {
  step_id: string;
  agent_id: string;
  required: boolean;
  depends_on: string[];
  description?: string | null;
}

export interface WorkflowMetadataResponse {
  workflow_id: string;
  version: string;
  name: string;
  description: string;
  step_count: number;
  steps: WorkflowStepMetadata[];
  required_inputs: string[];
  optional_inputs: string[];
}

export interface CodeFile {
  file_path: string;
  language: string;
  content: string;
  metadata?: Record<string, any>;
}

export interface CodeReviewInput {
  files: CodeFile[];
  review_scope?: string | null;
}

export interface WorkflowExecuteRequest {
  project_id: string;
  snapshot_id?: string | null;
  snapshot_version?: number | null;
  code_review_input?: CodeReviewInput | null;
  explainability_target_scope?: string | null;
  explainability_user_query?: string | null;
  options?: Record<string, any>;
}

export interface WorkflowStepResultResponse {
  step_id: string;
  agent_id: string;
  status: WorkflowStepStatus;
  execution_id?: string | null;
  error?: AgentErrorDetail | null;
  skip_reason?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface WorkflowResultResponse {
  workflow_execution_id: string;
  workflow_id: string;
  workflow_version: string;
  status: WorkflowStatus;
  started_at: string;
  completed_at: string;
  step_results: WorkflowStepResultResponse[];
  artifacts: Record<string, any>;
  errors: string[];
  warnings: string[];
  metadata: Record<string, any>;
}

export interface WorkflowExecutionSummaryResponse {
  workflow_execution_id: string;
  project_id: string;
  workflow_id: string;
  workflow_version: string;
  status: WorkflowStatus;
  started_at: string;
  completed_at?: string | null;
  context_snapshot_id?: string | null;
  context_version?: number | null;
  step_count: number;
  completed_steps: number;
  failed_steps: number;
  skipped_steps: number;
  error_count: number;
  warning_count: number;
  artifact_keys: string[];
}

export interface WorkflowHistoryListResponse {
  items: WorkflowExecutionSummaryResponse[];
  total: number;
  limit: number;
  offset: number;
}

export interface WorkflowExecutionDetailResponse {
  workflow_execution_id: string;
  project_id: string;
  workflow_id: string;
  workflow_version: string;
  status: WorkflowStatus;
  started_at: string;
  completed_at?: string | null;
  context_snapshot_id?: string | null;
  context_version?: number | null;
  step_count: number;
  completed_steps: number;
  failed_steps: number;
  skipped_steps: number;
  artifacts: Record<string, any>;
  errors: string[];
  warnings: string[];
  metadata: Record<string, any>;
}
