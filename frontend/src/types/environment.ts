/**
 * Phase 13 Multi-Environment Development & Deployment TypeScript Contracts.
 */

export type EnvironmentType = 'DEVELOPMENT' | 'STAGING' | 'PRODUCTION';

export type EnvironmentStatus = 'HEALTHY' | 'DEGRADED' | 'DEPLOYING' | 'FAILED' | 'MAINTENANCE';

export type DeploymentStatus =
  | 'REQUESTED'
  | 'VALIDATING'
  | 'DEPLOYING'
  | 'VERIFYING'
  | 'SUCCEEDED'
  | 'FAILED'
  | 'ROLLED_BACK'
  | 'CANCELLED';

export type DeploymentOperation = 'DEPLOYMENT' | 'PROMOTION' | 'ROLLBACK';

export interface Environment {
  id: string;
  project_id: string;
  environment_type: EnvironmentType;
  name: string;
  status: EnvironmentStatus;
  current_version_id: string | null;
  current_version_number?: number | null;
  current_version_status?: string | null;
  current_version_hash?: string | null;
  is_production: boolean;
  configuration: Record<string, any>;
  last_deployed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface DeploymentRecord {
  id: string;
  project_id: string;
  environment_id: string;
  environment_type: EnvironmentType;
  version_id: string;
  version_number?: number | null;
  previous_version_id?: string | null;
  previous_version_number?: number | null;
  operation: DeploymentOperation;
  source_environment_id?: string | null;
  source_environment_type?: EnvironmentType | null;
  status: DeploymentStatus;
  requested_by: string;
  started_at: string;
  completed_at?: string | null;
  verification_summary?: Record<string, any> | null;
  failure_reason?: string | null;
  rollback_target_deployment_id?: string | null;
  metadata_payload?: Record<string, any>;
  created_at: string;
}

export interface PromotionEligibilityResult {
  eligible: boolean;
  version_id: string;
  version_number: number;
  source_environment: EnvironmentType;
  target_environment: EnvironmentType;
  reasons: string[];
  passed_checks: string[];
  failed_checks: string[];
  warnings: string[];
  requires_confirmation: boolean;
}

export interface PromoteVersionPayload {
  version_id: string;
  target_environment: EnvironmentType;
  source_environment?: EnvironmentType;
  requested_by?: string;
  notes?: string;
}

export interface DeployVersionPayload {
  version_id: string;
  requested_by?: string;
  notes?: string;
}

export interface RollbackEnvironmentPayload {
  target_version_id: string;
  requested_by?: string;
  reason: string;
}
