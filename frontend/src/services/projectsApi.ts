import { ProjectCreate, ProjectResponse, ProjectStatus, ProjectUpdate } from '../types/project';
import { apiClient } from './apiClient';

export interface ListProjectsParams {
  skip?: number;
  limit?: number;
  status?: ProjectStatus;
}

export const projectsApi = {
  list: (params?: ListProjectsParams): Promise<ProjectResponse[]> => {
    return apiClient.get<ProjectResponse[]>('/projects', { params: params as any });
  },

  get: (projectId: string): Promise<ProjectResponse> => {
    return apiClient.get<ProjectResponse>(`/projects/${projectId}`);
  },

  create: (data: ProjectCreate): Promise<ProjectResponse> => {
    return apiClient.post<ProjectResponse>('/projects', data);
  },

  update: (projectId: string, data: ProjectUpdate): Promise<ProjectResponse> => {
    return apiClient.patch<ProjectResponse>(`/projects/${projectId}`, data);
  },

  archive: (projectId: string): Promise<ProjectResponse> => {
    return apiClient.delete<ProjectResponse>(`/projects/${projectId}`);
  },
};
