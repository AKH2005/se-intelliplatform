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

  restore: (projectId: string): Promise<ProjectResponse> => {
    return apiClient.post<ProjectResponse>(`/projects/${projectId}/restore`);
  },

  duplicate: (projectId: string): Promise<ProjectResponse> => {
    return apiClient.post<ProjectResponse>(`/projects/${projectId}/duplicate`);
  },

  deletePermanent: (projectId: string): Promise<void> => {
    return apiClient.delete<void>(`/projects/${projectId}/permanent`);
  },

  getActivity: (projectId: string): Promise<any[]> => {
    return apiClient.get<any[]>(`/projects/${projectId}/activity`);
  },

  download: async (projectId: string, filename?: string): Promise<void> => {
    const token = localStorage.getItem('se_auth_token');
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(`/api/v1/projects/${projectId}/download`, {
      method: 'GET',
      headers,
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Failed to download project ZIP' }));
      throw new Error(err.detail || `Download failed with HTTP ${response.status}`);
    }
    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename || `project-${projectId}.zip`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  },
};
