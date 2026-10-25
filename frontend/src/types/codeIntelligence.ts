/**
 * Types for Phase 14 Polyglot Code Intelligence.
 */

export interface LanguageInventoryResponse {
  project_id: string;
  total_files: number;
  counts: Record<string, number>;
  percentages: Record<string, number>;
  supported_languages: string[];
}

export interface CodeIntelligenceSummaryResponse {
  project_id: string;
  version_id?: string;
  version_number?: number;
  total_files: number;
  total_symbols: number;
  total_edges: number;
  total_diagnostics: number;
  language_breakdown: Record<string, number>;
  unresolved_imports_count: number;
  uncertain_dependencies_count: number;
  analyzed_at: string;
}

export interface DependencyGraphResponse {
  project_id: string;
  files_count: number;
  edges_count: number;
  forward_adjacency: Record<string, string[]>;
  reverse_adjacency: Record<string, string[]>;
  language_breakdown: Record<string, number>;
  unresolved_imports: string[];
  uncertain_dependencies: Array<{
    file_path: string;
    reason: string;
    line_number?: number;
    raw_statement?: string;
  }>;
  diagnostics_count: number;
}

export interface CodeSymbolDto {
  name: string;
  kind: string;
  qualified_name?: string;
  line_number?: number;
  is_exported: boolean;
  signature?: string;
  parent_symbol?: string;
}

export interface CodeImportDto {
  module: string;
  imported_symbols: string[];
  is_dynamic: boolean;
  is_relative: boolean;
  line_number?: number;
  raw_statement?: string;
}

export interface CodeExportDto {
  name: string;
  symbol_kind?: string;
  is_default: boolean;
  line_number?: number;
}

export interface CodeDiagnosticDto {
  file_path: string;
  language: string;
  error_type: string;
  message: string;
  line?: number;
  severity: string;
}

export interface FileCodeIntelligenceResponse {
  file_path: string;
  language: string;
  is_test_file: boolean;
  content_hash: string;
  symbols: CodeSymbolDto[];
  imports: CodeImportDto[];
  exports: CodeExportDto[];
  dependencies: Array<{
    source_file: string;
    target_file: string;
    relation: string;
    is_resolved: boolean;
  }>;
  diagnostics: CodeDiagnosticDto[];
  has_syntax_error: boolean;
  has_dynamic_constructs: boolean;
}

export type TechnologyCategory =
  | 'PROGRAMMING_LANGUAGE'
  | 'WEB_TECHNOLOGY'
  | 'DATABASE_ENGINE'
  | 'DATABASE_DIALECT';

export type DatabaseParadigm = 'RELATIONAL' | 'DOCUMENT' | 'KEY_VALUE' | 'GRAPH';

export interface TechnologyCapabilityDto {
  can_detect: boolean;
  can_syntax_highlight: boolean;
  can_inspect_source: boolean;
  can_ast_analyze: boolean;
  can_dependency_analyze: boolean;
  can_generate_code: boolean;
  can_execute: boolean;
  can_live_preview: boolean;
}

export interface TechnologyDetectionDto {
  name: string;
  category: TechnologyCategory;
  paradigm?: DatabaseParadigm | null;
  confidence: number;
  evidence: string[];
  detected_frameworks: string[];
  detected_drivers: string[];
  file_paths: string[];
  capabilities: TechnologyCapabilityDto;
  schema_info?: Record<string, unknown> | null;
}

export interface ProjectTechnologiesResponse {
  project_id: string;
  technologies: TechnologyDetectionDto[];
}
