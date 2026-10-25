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

  resolvePreviewUrl: (projectId: string, rawUrl?: string, app?: string, previewToken?: string): string => {
    const base = apiClient.getBaseUrl();
    const rootBase = base.replace(/\/api\/v1\/?$/, '');

    let url = rawUrl || `${base}/projects/${encodeURIComponent(projectId)}/runtime/preview`;

    // If relative path from API root
    if (url.startsWith('/')) {
      url = `${rootBase}${url}`;
    } else if (
      (typeof window !== 'undefined' && window.location.protocol === 'https:') ||
      (typeof import.meta !== 'undefined' && import.meta.env?.PROD)
    ) {
      // In production or on HTTPS, convert any residual loopback URL to the backend HTTPS endpoint preserving query string
      if (url.includes('127.0.0.1:8001') || url.includes('localhost:8001')) {
        const queryPart = url.includes('?') ? url.substring(url.indexOf('?')) : '';
        url = `${base}/projects/${encodeURIComponent(projectId)}/runtime/preview${queryPart}`;
      }
    }

    const params: string[] = [];
    if (app && !url.includes('app=')) {
      params.push(`app=${encodeURIComponent(app)}`);
    }
    if (previewToken && !url.includes('preview_token=')) {
      params.push(`preview_token=${encodeURIComponent(previewToken)}`);
    }

    if (params.length > 0) {
      const sep = url.includes('?') ? '&' : '?';
      url = `${url}${sep}${params.join('&')}`;
    }
    return url;
  },
};


