import { RequirementPriority, RequirementType } from './requirement';

// ==========================================
// 1. Requirement Analysis Artifact
// ==========================================
export type AnalysisSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface RequirementAmbiguity {
  requirement_id: string;
  issue: string;
  explanation: string;
  suggested_clarification: string;
  severity: AnalysisSeverity;
}

export interface RequirementConflict {
  requirement_id: string;
  related_requirement_id: string;
  issue: string;
  explanation: string;
  severity: AnalysisSeverity;
}

export interface MissingInformation {
  area: string;
  description: string;
  reason: string;
  severity: AnalysisSeverity;
}

export interface RequirementRefinement {
  requirement_id: string;
  suggestion: string;
  reason: string;
  suggested_type?: RequirementType | null;
  suggested_priority?: RequirementPriority | null;
}

export interface ScopeClarification {
  topic: string;
  question: string;
  rationale: string;
}

export interface RequirementAnalysisOutput {
  summary: string;
  ambiguities: RequirementAmbiguity[];
  conflicts: RequirementConflict[];
  missing_information: MissingInformation[];
  refinements: RequirementRefinement[];
  scope_clarifications: ScopeClarification[];
  completeness_score: number;
  active_requirements_count: number;
  total_requirements_count: number;
}

// ==========================================
// 2. Architecture Recommendation Artifact
// ==========================================
export type ArchitectureStyle =
  | 'MONOLITH'
  | 'MODULAR_MONOLITH'
  | 'LAYERED'
  | 'CLEAN_ARCHITECTURE'
  | 'HEXAGONAL'
  | 'MICROSERVICES'
  | 'EVENT_DRIVEN'
  | 'SERVERLESS';

export type TechnologyCategory =
  | 'FRONTEND'
  | 'BACKEND'
  | 'DATABASE'
  | 'CACHE'
  | 'MESSAGING'
  | 'DEPLOYMENT'
  | 'OBSERVABILITY'
  | 'AUTHENTICATION';

export interface ArchitectureStyleRecommendation {
  style: ArchitectureStyle;
  rationale: string;
  confidence: number; // Qualitative confidence assessment (0.0 to 1.0)
}

export interface ComponentRecommendation {
  name: string;
  responsibility: string;
  reason: string;
  related_requirement_ids: string[];
}

export interface DataFlowRecommendation {
  source_component: string;
  target_component: string;
  interaction: string;
  reason: string;
}

export interface TechnologyRecommendation {
  technology: string;
  category: TechnologyCategory;
  reason: string;
  trade_off: string;
}

export interface TradeOffAnalysis {
  decision_area: string;
  recommended_option: string;
  advantages: string[];
  disadvantages: string[];
  alternative: string;
  alternative_tradeoff: string;
}

export interface ArchitectureRequirementTrace {
  requirement_id: string;
  component_names: string[];
  rationale: string;
}

export interface ArchitectureRecommendationOutput {
  summary: string;
  architecture_styles: ArchitectureStyleRecommendation[];
  components: ComponentRecommendation[];
  data_flows: DataFlowRecommendation[];
  technologies: TechnologyRecommendation[];
  trade_offs: TradeOffAnalysis[];
  assumptions: string[];
  constraints: string[];
  unknowns: string[];
  traceability_matrix: ArchitectureRequirementTrace[];
}

// ==========================================
// 3. Database Design Artifact
// ==========================================
export type DatabaseParadigm = 'RELATIONAL' | 'DOCUMENT' | 'KEY_VALUE' | 'GRAPH' | 'SEARCH';
export type DataType =
  | 'STRING'
  | 'INTEGER'
  | 'DECIMAL'
  | 'BOOLEAN'
  | 'DATE'
  | 'DATETIME'
  | 'TIMESTAMP'
  | 'UUID'
  | 'JSON'
  | 'TEXT'
  | 'BINARY';

export type RelationshipType = 'ONE_TO_ONE' | 'ONE_TO_MANY' | 'MANY_TO_ONE' | 'MANY_TO_MANY';
export type ConstraintType = 'UNIQUE' | 'NOT_NULL' | 'CHECK' | 'PRIMARY_KEY' | 'FOREIGN_KEY';

export interface AttributeRecommendation {
  name: string;
  data_type: DataType;
  nullable: boolean;
  description: string;
  default_value?: string | null;
  unique: boolean;
}

export interface PrimaryKeyRecommendation {
  attributes: string[];
  is_composite: boolean;
}

export interface EntityRecommendation {
  name: string;
  description: string;
  attributes: AttributeRecommendation[];
  primary_key: PrimaryKeyRecommendation;
}

export interface RelationshipRecommendation {
  source_entity: string;
  target_entity: string;
  relationship_type: RelationshipType;
  foreign_key_attribute?: string | null;
  description: string;
}

export interface IndexRecommendation {
  entity_name: string;
  index_name: string;
  attributes: string[];
  is_unique: boolean;
  reason: string;
}

export interface ConstraintRecommendation {
  entity_name: string;
  constraint_name: string;
  constraint_type: ConstraintType;
  expression: string;
  description: string;
}

export interface DatabaseTradeOff {
  decision_area: string;
  recommended_approach: string;
  rationale: string;
  trade_offs: string[];
}

export interface DatabaseRequirementTrace {
  requirement_id: string;
  entity_names: string[];
  rationale: string;
}

export interface DatabaseArchitectureTrace {
  component_name: string;
  entity_names: string[];
  rationale: string;
}

export interface DatabaseDesignOutput {
  summary: string;
  database_paradigm: DatabaseParadigm;
  entities: EntityRecommendation[];
  relationships: RelationshipRecommendation[];
  indexes: IndexRecommendation[];
  constraints: ConstraintRecommendation[];
  trade_offs: DatabaseTradeOff[];
  assumptions: string[];
  constraints_notes: string[];
  unknowns: string[];
  requirement_traceability: DatabaseRequirementTrace[];
  architecture_traceability: DatabaseArchitectureTrace[];
}

// ==========================================
// 4. Risk Prediction Artifact
// ==========================================
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface RiskModelProvenance {
  model_name: string;
  model_version: string;
  algorithm: string;
  training_dataset: string;
  feature_schema_version: string;
  artifact_checksum: string;
}

export interface RiskPredictionOutput {
  summary: string;
  predicted_risk_score: number; // Scale: ~1.0 - 10.0
  risk_level: RiskLevel; // Deterministic band: LOW (<3.5), MEDIUM (3.5-<6.5), HIGH (6.5-<8.5), CRITICAL (>=8.5)
  feature_summary: Record<string, any>;
  model_provenance: RiskModelProvenance;
  limitations: string[];
}

// ==========================================
// 5. Timeline Prediction Artifact
// ==========================================
export interface TimelineModelProvenance {
  model_name: string;
  model_version: string;
  algorithm: string;
  training_dataset: string;
  feature_schema_version: string;
  artifact_checksum: string;
}

export interface TimelinePredictionOutput {
  agent_id?: string;
  agent_version?: string;
  summary: string;
  predicted_duration_months: number;
  estimated_duration_months: number;
  target: string; // "Duration"
  target_unit: string; // "months"
  model_provenance: TimelineModelProvenance;
  feature_names: string[];
  feature_summary: Record<string, any>;
  limitations: string[];
}

// ==========================================
// 6. Bug Prediction Artifact
// ==========================================
export type DefectPredictionLabel = 'DEFECTIVE' | 'NON_DEFECTIVE';

export interface BugModelProvenance {
  model_name: string;
  model_version: string;
  algorithm: string;
  training_dataset: string;
  feature_schema_version: string;
  artifact_checksum: string;
}

export interface BugPredictionOutput {
  agent_id?: string;
  agent_version?: string;
  summary: string;
  prediction_label: DefectPredictionLabel; // Strictly DEFECTIVE or NON_DEFECTIVE
  predicted_probability: number; // 0.0 to 1.0
  target: string; // "defects"
  model_provenance: BugModelProvenance;
  feature_names: string[];
  feature_summary: Record<string, number>;
  limitations: string[];
}

// ==========================================
// 7. Test Case Generation Artifact
// ==========================================
export type TestType =
  | 'FUNCTIONAL'
  | 'NEGATIVE'
  | 'EDGE_CASE'
  | 'VALIDATION'
  | 'SECURITY'
  | 'PERFORMANCE'
  | 'INTEGRATION';

export type TestPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface TestStep {
  step_number: number;
  action: string;
  expected_behavior: string;
}

export interface TestCase {
  test_case_id: string;
  title: string;
  description: string;
  test_type: TestType;
  priority: TestPriority;
  preconditions: string[];
  steps: TestStep[];
  expected_result: string;
  requirement_ids: string[];
}

export interface TestCaseCoverage {
  total_requirements_evaluated: number;
  covered_requirement_ids: string[];
  uncovered_requirement_ids: string[];
  coverage_percentage: number;
}

export interface TestCaseGenerationOutput {
  agent_id?: string;
  agent_version?: string;
  summary: string;
  test_cases: TestCase[];
  total_test_cases: number;
  coverage: TestCaseCoverage;
  limitations: string[];
}

// ==========================================
// 8. Code Review Artifact
// ==========================================
export type FindingSeverity = 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type FindingCategory =
  | 'CORRECTNESS'
  | 'SECURITY'
  | 'PERFORMANCE'
  | 'MAINTAINABILITY'
  | 'READABILITY'
  | 'ERROR_HANDLING'
  | 'ARCHITECTURE';

export type FindingSource = 'STATIC_ANALYSIS' | 'AI_REVIEW' | 'HYBRID';

export interface CodeReviewFinding {
  finding_id: string;
  file_path: string;
  line_start?: number | null;
  line_end?: number | null;
  severity: FindingSeverity;
  category: FindingCategory;
  source: FindingSource;
  title: string;
  description: string;
  evidence?: string | null;
  suggestion?: string | null;
}

export interface CodeReviewSummary {
  total_findings: number;
  by_severity: Record<string, number>;
  by_category: Record<string, number>;
  by_source: Record<string, number>;
  files_with_findings: number;
}

export interface CodeReviewOutput {
  agent_id?: string;
  agent_version?: string;
  summary: string;
  files_reviewed: string[];
  findings: CodeReviewFinding[];
  metrics: CodeReviewSummary;
  limitations: string[];
}

// ==========================================
// 9. Explainability & Engineering Insights Artifact
// ==========================================
export type InsightCategory =
  | 'REQUIREMENT'
  | 'ARCHITECTURE'
  | 'DATABASE'
  | 'RISK'
  | 'TIMELINE'
  | 'DEFECT'
  | 'TESTING'
  | 'CODE_REVIEW'
  | 'CROSS_CUTTING';

export type ClaimType = 'FACT' | 'INTERPRETATION' | 'RECOMMENDATION' | 'LIMITATION';

export interface SourceReference {
  agent_id: string;
  source_entity_id?: string | null;
  source_field?: string | null;
  claim_type: ClaimType;
}

export interface EngineeringInsight {
  insight_id: string;
  category: InsightCategory;
  title: string;
  summary: string;
  explanation: string;
  source_references: SourceReference[];
  suggested_actions: string[];
}

export interface ExplainabilitySummary {
  analyzed_agents: string[];
  total_insights: number;
  insights_by_category: Record<string, number>;
  claims_count_by_type: Record<string, number>;
}

export interface ExplainabilityOutput {
  agent_id?: string;
  agent_version?: string;
  summary: string;
  insights: EngineeringInsight[];
  metrics: ExplainabilitySummary;
  limitations: string[];
}
