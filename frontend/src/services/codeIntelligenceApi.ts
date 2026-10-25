/**
 * API client service for Phase 14 Polyglot Code Intelligence.
 */

import { apiClient } from './apiClient';
import {
  CodeIntelligenceSummaryResponse,
  DependencyGraphResponse,
  FileCodeIntelligenceResponse,
  LanguageInventoryResponse,
  ProjectTechnologiesResponse,
} from '../types/codeIntelligence';

export const codeIntelligenceApi = {
  getLanguages: (projectId: string, versionId?: string): Promise<LanguageInventoryResponse> => {
    const url = versionId
      ? `/projects/${projectId}/code-intelligence/languages?version_id=${encodeURIComponent(versionId)}`
      : `/projects/${projectId}/code-intelligence/languages`;
    return apiClient.get<LanguageInventoryResponse>(url);
  },

  getTechnologies: (projectId: string, versionId?: string): Promise<ProjectTechnologiesResponse> => {
    const url = versionId
      ? `/projects/${projectId}/code-intelligence/technologies?version_id=${encodeURIComponent(versionId)}`
      : `/projects/${projectId}/code-intelligence/technologies`;
    return apiClient.get<ProjectTechnologiesResponse>(url);
  },

  getSummary: (projectId: string, versionId?: string): Promise<CodeIntelligenceSummaryResponse> => {
    const url = versionId
      ? `/projects/${projectId}/code-intelligence/summary?version_id=${encodeURIComponent(versionId)}`
      : `/projects/${projectId}/code-intelligence/summary`;
    return apiClient.get<CodeIntelligenceSummaryResponse>(url);
  },

  getGraph: (projectId: string, versionId?: string): Promise<DependencyGraphResponse> => {
    const url = versionId
      ? `/projects/${projectId}/code-intelligence/graph?version_id=${encodeURIComponent(versionId)}`
      : `/projects/${projectId}/code-intelligence/graph`;
    return apiClient.get<DependencyGraphResponse>(url);
  },

  getFileDetails: (
    projectId: string,
    filePath: string,
    versionId?: string
  ): Promise<FileCodeIntelligenceResponse> => {
    const params = new URLSearchParams({ file_path: filePath });
    if (versionId) {
      params.append('version_id', versionId);
    }
    return apiClient.get<FileCodeIntelligenceResponse>(
      `/projects/${projectId}/code-intelligence/file?${params.toString()}`
    );
  },
};
