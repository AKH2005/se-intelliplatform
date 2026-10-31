/**
 * Frontend TypeScript contracts and models for Code Studio
 */

export type FileNodeType = 'file' | 'directory';

export interface FileNode {
  id: string;
  name: string;
  path: string;
  type: FileNodeType;
  size_bytes?: number;
  language?: string;
  children?: FileNode[];
}

export interface FileTreeResponse {
  project_id: string;
  version_id?: string | null;
  version_number?: number | null;
  has_generated_code: boolean;
  total_files: number;
  root_nodes: FileNode[];
}

export interface FileContentResponse {
  path: string;
  name: string;
  language: string;
  content: string;
  size_bytes: number;
  version_id: string;
  version_number: number;
  content_hash: string;
}

export interface SaveFileRequest {
  content: string;
  parent_version_id: string;
  expected_content_hash?: string;
  reason?: string;
}

export interface ValidationStageOutcome {
  stage: string;
  status: 'PASSED' | 'FAILED' | 'SKIPPED';
  message: string;
  errors: string[];
  warnings: string[];
}

export interface SaveFileResponse {
  success: boolean;
  project_id: string;
  version_id: string;
  version_number: number;
  parent_version_id: string;
  path: string;
  size_bytes: number;
  content_hash: string;
  version_content_hash: string;
  validation: ValidationStageOutcome;
  message: string;
}
