export type ChangeOperation = 'MODIFY' | 'ADD' | 'DELETE';

export type RemediationProposalStatus =
  | 'DRAFT'
  | 'VALIDATED'
  | 'AWAITING_APPROVAL'
  | 'APPROVED'
  | 'REJECTED'
  | 'APPLIED'
  | 'VERIFICATION_FAILED'
  | 'VERIFIED'
  | 'EXPIRED';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

export interface ProposedChange {
  file_path: string;
  operation: ChangeOperation;
  original_region: string;
  proposed_region: string;
  reason: string;
  evidence_ids: string[];
}

export interface RemediationProposal {
  proposal_id: string;
  diagnosis_id: string;
  project_id: string;
  workflow_execution_id?: string | null;
  title: string;
  summary: string;
  rationale: string;
  changes: ProposedChange[];
  affected_files: string[];
  unified_diff: string;
  expected_effect: string;
  verification_plan: string;
  risk_level: RiskLevel;
  status: RemediationProposalStatus;
  requirement_links: string[];
  architecture_links: string[];
  database_links: string[];
  model_metadata: Record<string, any>;
  parent_artifact_version: number;
  resulting_artifact_version?: number | null;
  created_at: string;
  approved_at?: string | null;
  rejected_at?: string | null;
  rejection_reason?: string | null;
  applied_at?: string | null;
}

export interface RemediationVerificationResult {
  proposal_id: string;
  status: RemediationProposalStatus;
  static_analysis_passed: boolean;
  sandbox_passed: boolean;
  resolved_diagnostic_codes: string[];
  new_critical_or_error_diagnostics: string[];
  summary: string;
  static_analysis_result?: any;
  execution_result?: any;
  verified_at: string;
}

export interface ApplyRemediationResponse {
  proposal: RemediationProposal;
  verification: RemediationVerificationResult;
}

export interface CreateProposalRequest {
  workflow_execution_id?: string | null;
}

export interface RejectProposalRequest {
  reason?: string | null;
}
