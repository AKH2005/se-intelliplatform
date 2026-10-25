import { DiagnosticSeverity } from './sandbox';

export type FailureSource =
  | 'AI_TEST'
  | 'STATIC_ANALYSIS'
  | 'SANDBOX'
  | 'APPLICATION'
  | 'VALIDATION'
  | 'ENVIRONMENT'
  | 'DEPENDENCY';

export type FailureType =
  | 'SYNTAX_ERROR'
  | 'IMPORT_ERROR'
  | 'DEPENDENCY_ERROR'
  | 'LINT_ERROR'
  | 'TEST_FAILURE'
  | 'ASSERTION_FAILURE'
  | 'TEST_ERROR'
  | 'APPLICATION_ERROR'
  | 'STATIC_ANALYSIS_ISSUE'
  | 'RUNTIME_ERROR'
  | 'TIMEOUT'
  | 'RESOURCE_LIMIT'
  | 'SANDBOX_ERROR'
  | 'VALIDATION_ERROR'
  | 'ENVIRONMENT_ERROR'
  | 'UNKNOWN';

export type ClaimType = 'FACT' | 'INTERPRETATION' | 'RECOMMENDATION' | 'LIMITATION';

export type FailureConfidence = 'HIGH' | 'MEDIUM' | 'LOW' | 'UNKNOWN';

export interface EvidenceReference {
  evidence_id: string;
  source: string;
  code?: string | null;
  file_path?: string | null;
  line?: number | null;
  snippet?: string | null;
  description?: string | null;
}

export interface DiagnosticClaim {
  claim_type: ClaimType;
  statement: string;
  evidence_ids: string[];
}

export interface FailureDiagnosis {
  diagnosis_id: string;
  failure_type: FailureType;
  failure_source?: FailureSource | null;
  title: string;
  summary: string;
  root_cause: string;
  severity: DiagnosticSeverity;
  affected_files: string[];
  evidence: EvidenceReference[];
  claims: DiagnosticClaim[];
  requirement_links: string[];
  architecture_links: string[];
  database_links: string[];
  suggested_remediation: string;
  limitations: string[];
  confidence: FailureConfidence;
  model_metadata: Record<string, any>;
}

export interface FailureAnalysisApiRequest {
  workflow_execution_id?: string | null;
  force?: boolean;
  failure_source?: FailureSource | null;
}
