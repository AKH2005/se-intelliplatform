import { ProjectResponse } from './project';
import { RequirementResponse } from './requirement';

export interface RequirementStatistics {
  total_requirements: intOrNumber;
  active_requirements: intOrNumber;
  functional_count: intOrNumber;
  non_functional_count: intOrNumber;
  constraint_count: intOrNumber;
  by_priority: Record<string, number>;
  by_status: Record<string, number>;
  completion_percentage: number;
}

type intOrNumber = number;

export interface ProjectContextResponse {
  project: ProjectResponse;
  requirements: RequirementResponse[];
  statistics: RequirementStatistics;
  context_version: number;
  generated_at: string;
}

export interface ContextSnapshotCreate {
  summary?: string | null;
}

export interface ContextSnapshotResponse {
  id: string;
  project_id: string;
  version: number;
  context_data: Record<string, any>;
  summary?: string | null;
  created_at: string;
}
