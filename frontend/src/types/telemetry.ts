/**
 * Telemetry TypeScript Contracts for Phase 12 Real-Time Execution & Telemetry.
 *
 * Mirrors backend/app/telemetry/contracts.py with strict typing,
 * project-isolated subscriptions, and monotonic sequence tracking.
 */

export type ExecutionEventType =
  | 'EXECUTION_CREATED'
  | 'EXECUTION_STARTED'
  | 'EXECUTION_QUEUED'
  | 'EXECUTION_PROGRESS'
  | 'EXECUTION_LOG'
  | 'EXECUTION_STATE_CHANGED'
  | 'AGENT_STARTED'
  | 'AGENT_PROGRESS'
  | 'AGENT_COMPLETED'
  | 'AGENT_FAILED'
  | 'WORKFLOW_STARTED'
  | 'WORKFLOW_STEP_STARTED'
  | 'WORKFLOW_STEP_COMPLETED'
  | 'WORKFLOW_STEP_FAILED'
  | 'WORKFLOW_COMPLETED'
  | 'WORKFLOW_FAILED'
  | 'SANDBOX_STARTED'
  | 'SANDBOX_PROGRESS'
  | 'SANDBOX_COMPLETED'
  | 'SANDBOX_FAILED'
  | 'BROWSER_STARTED'
  | 'BROWSER_PROGRESS'
  | 'BROWSER_COMPLETED'
  | 'BROWSER_FAILED'
  | 'TEST_STARTED'
  | 'TEST_COMPLETED'
  | 'REGRESSION_STARTED'
  | 'REGRESSION_PROGRESS'
  | 'REGRESSION_COMPLETED'
  | 'REGRESSION_FAILED'
  | 'DEPLOYMENT_STARTED'
  | 'DEPLOYMENT_PROGRESS'
  | 'DEPLOYMENT_COMPLETED'
  | 'DEPLOYMENT_FAILED'
  | 'PROMOTION_STARTED'
  | 'PROMOTION_COMPLETED'
  | 'PROMOTION_FAILED'
  | 'ROLLBACK_STARTED'
  | 'ROLLBACK_COMPLETED'
  | 'ROLLBACK_FAILED'
  | 'FAILURE_DETECTED'
  | 'SAFETY_BLOCKED'
  | 'EXECUTION_CANCELLED'
  | 'EXECUTION_COMPLETED'
  | 'EXECUTION_FAILED';

export type ExecutionKind =
  | 'AGENT'
  | 'WORKFLOW'
  | 'SANDBOX'
  | 'BROWSER'
  | 'TEST'
  | 'REGRESSION'
  | 'ENGINEERING_ACTION'
  | 'DEPLOYMENT';

export type EventSeverity = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';

export interface ExecutionEvent {
  event_id: string;
  event_type: ExecutionEventType;
  timestamp: string;
  project_id: string;
  execution_id: string;
  correlation_id?: string | null;
  parent_execution_id?: string | null;
  execution_kind: ExecutionKind;
  source: string;
  status: string;
  sequence: number;
  payload: Record<string, unknown>;
  severity: EventSeverity;
}

export interface ExecutionStateSnapshot {
  execution_id: string;
  project_id: string;
  execution_kind: ExecutionKind;
  status: string;
  created_at: string;
  updated_at: string;
  latest_sequence: number;
  total_events: number;
  latest_event_type?: ExecutionEventType | null;
  active_step?: string | null;
  error_message?: string | null;
  metadata: Record<string, unknown>;
}

export interface TelemetrySubscriptionOptions {
  projectId: string;
  executionId?: string;
  sinceSequence?: number;
  onEvent?: (event: ExecutionEvent) => void;
  onError?: (error: unknown) => void;
  autoReconnect?: boolean;
}
