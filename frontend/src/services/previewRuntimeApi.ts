import { apiClient } from './apiClient';
import { RuntimeStatusResponse } from '../types/previewRuntime';

export interface PreviewTokenResponse {
  preview_token: string;
  token_type: string;
  expires_in: number;
  project_id: string;
  scope: string;
}

export const previewRuntimeApi = {
  getStatus: (projectId: string): Promise<RuntimeStatusResponse> => {
    return apiClient.get<RuntimeStatusResponse>(`/projects/${projectId}/runtime/status`);
  },

  getPreviewToken: (projectId: string): Promise<PreviewTokenResponse> => {
    return apiClient.post<PreviewTokenResponse>(`/projects/${projectId}/runtime/preview-token`, {});
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

    // If projectId is present, sanitize any stale app= parameter from url
    // to prevent cross-project archetype leakage.
    if (projectId && url.includes('app=')) {
      url = url.replace(/([?&])app=[^&]*(&|$)/, (_match, p1, p2) => {
        return p2 === '&' ? p1 : '';
      }).replace(/\?$/, '');
    }

    const params: string[] = [];
    // Only attach app mode query param if there is NO projectId (standalone archetype preview),
    // to prevent URL pollution from overriding authoritative project version files.
    if (app && !projectId && !url.includes('app=')) {
      params.push(`app=${encodeURIComponent(app)}`);
    }

    // Security Hardening:
    // Only attach a dedicated short-lived, project-scoped preview token.
    // NEVER fall back to or place the user's long-lived main access token in the iframe URL!
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
