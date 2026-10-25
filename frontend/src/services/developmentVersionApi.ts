/**
 * API service for Phase 11H Development Versions & Continuous Engineering Loop.
 */

import { apiClient } from './apiClient';
import {
  DevelopmentChangeResponse,
  DevelopmentVersionListResponse,
  DevelopmentVersionResponse,
  VerificationSnapshot,
  VersionComparisonResponse,
} from '../types/developmentVersion';

export const developmentVersionApi = {
  listVersions: (projectId: string): Promise<DevelopmentVersionListResponse> => {
    return apiClient.get<DevelopmentVersionListResponse>(`/projects/${projectId}/versions`);
  },

  getActiveVersion: (projectId: string): Promise<DevelopmentVersionResponse | null> => {
    return apiClient.get<DevelopmentVersionResponse | null>(`/projects/${projectId}/versions/active`);
  },

  getVersion: (projectId: string, versionId: string): Promise<DevelopmentVersionResponse> => {
    return apiClient.get<DevelopmentVersionResponse>(`/projects/${projectId}/versions/${versionId}`);
  },

  getVersionFileContent: (
    projectId: string,
    versionId: string,
    filePath: string
  ): Promise<string> => {
    return apiClient.get<string>(
      `/projects/${projectId}/versions/${versionId}/files/${encodeURIComponent(filePath)}`
    );
  },

  getVersionVerification: (
    projectId: string,
    versionId: string
  ): Promise<VerificationSnapshot> => {
    return apiClient.get<VerificationSnapshot>(
      `/projects/${projectId}/versions/${versionId}/verification`
    );
  },

  getVersionChanges: (
    projectId: string,
    versionId: string
  ): Promise<DevelopmentChangeResponse[]> => {
    return apiClient.get<DevelopmentChangeResponse[]>(
      `/projects/${projectId}/versions/${versionId}/changes`
    );
  },

  compareVersions: (
    projectId: string,
    fromVersionId: string,
    toVersionId: string
  ): Promise<VersionComparisonResponse> => {
    return apiClient.get<VersionComparisonResponse>(
      `/projects/${projectId}/versions/compare`,
      {
        params: {
          from_version: fromVersionId,
          to_version: toVersionId,
        },
      }
    );
  },

  activateVersion: (
    projectId: string,
    versionId: string,
    reason?: string
  ): Promise<DevelopmentVersionResponse> => {
    return apiClient.post<DevelopmentVersionResponse>(
      `/projects/${projectId}/versions/${versionId}/activate`,
      reason ? { reason } : {}
    );
  },

  rollbackVersion: (
    projectId: string,
    versionId: string,
    reason?: string
  ): Promise<DevelopmentVersionResponse> => {
    return apiClient.post<DevelopmentVersionResponse>(
      `/projects/${projectId}/versions/${versionId}/rollback`,
      reason ? { reason } : {}
    );
  },

  reverifyVersion: (
    projectId: string,
    versionId: string
  ): Promise<VerificationSnapshot> => {
    return apiClient.post<VerificationSnapshot>(
      `/projects/${projectId}/versions/${versionId}/verify`,
      {}
    );
  },
};
