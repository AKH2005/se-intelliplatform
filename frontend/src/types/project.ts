export type ProjectStatus = 'DRAFT' | 'IN_PROGRESS' | 'ARCHIVED';

export interface ProjectResponse {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  status: ProjectStatus;
  settings?: Record<string, any>;
  owner_id?: string | null;
  created_at: string;
  updated_at: string;
  requirements_count?: number;
}

export interface ProjectCreate {
  name: string;
  slug: string;
  description?: string | null;
  status?: ProjectStatus;
  settings?: Record<string, any>;
}

export interface ProjectUpdate {
  name?: string | null;
  description?: string | null;
  status?: ProjectStatus | null;
  settings?: Record<string, any> | null;
}
