export type RequirementType = 'FUNCTIONAL' | 'NON_FUNCTIONAL' | 'CONSTRAINT';
export type RequirementPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type RequirementStatus = 'DRAFT' | 'APPROVED' | 'IMPLEMENTED' | 'DEFERRED' | 'REJECTED';

export interface RequirementResponse {
  id: string;
  project_id: string;
  title: string;
  description: string;
  type: RequirementType;
  priority: RequirementPriority;
  status: RequirementStatus;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface RequirementCreate {
  title: string;
  description: string;
  type?: RequirementType;
  priority?: RequirementPriority;
  status?: RequirementStatus;
}

export interface RequirementUpdate {
  title?: string;
  description?: string;
  type?: RequirementType;
  priority?: RequirementPriority;
  status?: RequirementStatus;
  is_archived?: boolean;
}
