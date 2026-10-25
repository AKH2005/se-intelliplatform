import { apiClient } from './apiClient';
import { RuntimeStatusResponse } from '../types/previewRuntime';

export const previewRuntimeApi = {
  getStatus: (projectId: string): Promise<RuntimeStatusResponse> => {
    return apiClient.get<RuntimeStatusResponse>(`/projects/${projectId}/runtime/status`);
  },

  start: (projectId: string): Promise<RuntimeStatusResponse> => {
    return apiClient.post<RuntimeStatusResponse>(`/projects/${projectId}/runtime/start`, {});
  },

  restart: (projectId: string): Promise<RuntimeStatusResponse> => {
    return apiClient.post<RuntimeStatusResponse>(`/projects/${projectId}/runtime/restart`, {});
  },

  stop: (projectId: string): Promise<RuntimeStatusResponse> => {
    return apiClient.post<RuntimeStatusResponse>(`/projects/${projectId}/runtime/stop`, {});
  },
};
