import {
  RequirementCreate,
  RequirementPriority,
  RequirementResponse,
  RequirementStatus,
  RequirementType,
  RequirementUpdate,
} from '../types/requirement';
import { apiClient } from './apiClient';

export interface ListRequirementsParams {
  skip?: number;
  limit?: number;
  type?: RequirementType;
  priority?: RequirementPriority;
  status?: RequirementStatus;
  include_archived?: boolean;
}

export const requirementsApi = {
  list: (projectId: string, params?: ListRequirementsParams): Promise<RequirementResponse[]> => {
    return apiClient.get<RequirementResponse[]>(`/projects/${projectId}/requirements`, {
      params: params as any,
    });
  },

  get: (projectId: string, requirementId: string): Promise<RequirementResponse> => {
    return apiClient.get<RequirementResponse>(`/projects/${projectId}/requirements/${requirementId}`);
  },

  create: (projectId: string, data: RequirementCreate): Promise<RequirementResponse> => {
    return apiClient.post<RequirementResponse>(`/projects/${projectId}/requirements`, data);
  },

  update: (projectId: string, requirementId: string, data: RequirementUpdate): Promise<RequirementResponse> => {
    return apiClient.patch<RequirementResponse>(`/projects/${projectId}/requirements/${requirementId}`, data);
  },

  archive: (projectId: string, requirementId: string): Promise<RequirementResponse> => {
    return apiClient.delete<RequirementResponse>(`/projects/${projectId}/requirements/${requirementId}`);
  },
};
