/**
 * Types and DTOs for Phase 11H Development Versions & Continuous Engineering Loop.
 */

export type DevelopmentVersionStatus =
  | 'UNVERIFIED'
  | 'VERIFIED'
  | 'FAILED_VERIFICATION'
  | 'ACTIVE'
  | 'SUPERSEDED'
  | 'ROLLED_BACK'
  | 'DEPRECATED';

export type ChangeCategory = 'CODE_PRODUCING' | 'LIFECYCLE_EVENT';

export type ChangeType =
  | 'INITIAL_CREATION'
  | 'REMEDIATION_PATCH'
  | 'ACTIVATION'
  | 'ROLLBACK'
  | 'BRANCH_FORK';

export type VerificationStatus =
  | 'PASSED'
  | 'FAILED'
  | 'PENDING'
  | 'INCOMPLETE'
  | 'NOT_RUN';

export type VerificationRequirementLevel =
  | 'REQUIRED'
  | 'OPTIONAL'
  | 'NOT_APPLICABLE';

export interface StageVerificationResult {
  stage: string;
  requirement_level: VerificationRequirementLevel;
  status: VerificationStatus;
  details: string;
  error_count: number;
  warning_count: number;
  blocking_issues: string[];
}

export interface VerificationSnapshot {
  verification_status: VerificationStatus;
  is_verified: boolean;
  summary: string;
  static_analysis: StageVerificationResult;
  sandbox_execution: StageVerificationResult;
  ai_tests: StageVerificationResult;
  failure_analysis: StageVerificationResult;
  verified_at: string;
}

export interface VersionFileSummary {
  path: string;
  size_bytes: number;
  language: string;
  architecture_component?: string | null;
  requirement_ids: string[];
}

export interface DevelopmentVersionResponse {
  version_id: string;
  project_id: string;
  version_number: number;
  parent_version_id?: string | null;
  workflow_execution_id?: string | null;
  artifact_key: string;
  status: DevelopmentVersionStatus;
  is_active: boolean;
  content_hash: string;
  manifest_hash: string;
  file_count: number;
  total_size_bytes: number;
  source_reason: string;
  created_by: string;
  requirement_ids: string[];
  files_manifest: VersionFileSummary[];
  verification_summary?: VerificationSnapshot | null;
  diagnosis_reference?: string | null;
  remediation_reference?: string | null;
  created_at: string;
}

export interface DevelopmentVersionListResponse {
  items: DevelopmentVersionResponse[];
  total: number;
  active_version_id?: string | null;
}

export interface DevelopmentChangeResponse {
  change_id: string;
  project_id: string;
  parent_version_id?: string | null;
  resulting_version_id: string;
  change_category: ChangeCategory;
  change_type: ChangeType;
  reason: string;
  diagnosis_id?: string | null;
  remediation_proposal_id?: string | null;
  approved_by?: string | null;
  approved_at?: string | null;
  created_at: string;
}

export interface VersionFileDiff {
  path: string;
  change_type: 'ADDED' | 'MODIFIED' | 'REMOVED';
  size_delta_bytes: number;
  unified_diff?: string | null;
}

export interface VersionComparisonResponse {
  from_version_id: string;
  to_version_id: string;
  from_version_number: number;
  to_version_number: number;
  files_added: VersionFileDiff[];
  files_removed: VersionFileDiff[];
  files_modified: VersionFileDiff[];
  files_unchanged_count: number;
  requirements_added: string[];
  requirements_removed: string[];
  verification_change_summary: string;
  diagnosis_reference?: string | null;
  remediation_proposal_id?: string | null;
}

export interface ActivateVersionRequest {
  reason?: string;
}

export interface RollbackVersionRequest {
  reason?: string;
}
