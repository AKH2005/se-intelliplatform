/**
 * Code Studio API Service Client
 * Provides authenticated operations for file tree browsing, file inspection, and safe saving.
 */

import { apiClient } from './apiClient';
import {
  FileContentResponse,
  FileTreeResponse,
  SaveFileRequest,
  SaveFileResponse,
} from '../types/codeStudio';

export const codeStudioApi = {
  /**
   * Fetch hierarchical file tree for project's active or specified version
   */
  async getFileTree(projectId: string, versionId?: string): Promise<FileTreeResponse> {
    const params = versionId ? { version_id: versionId } : undefined;
    return apiClient.get<FileTreeResponse>(`/projects/${projectId}/files`, { params });
  },

  /**
   * Fetch individual file content and metadata
   */
  async getFileContent(
    projectId: string,
    filePath: string,
    versionId?: string
  ): Promise<FileContentResponse> {
    const cleanPath = filePath.replace(/^\/+/, '');
    const params = versionId ? { version_id: versionId } : undefined;
    return apiClient.get<FileContentResponse>(`/projects/${projectId}/files/${cleanPath}`, {
      params,
    });
  },

  /**
   * Safely edit and save a file, creating an immutable child version
   */
  async saveFileContent(
    projectId: string,
    filePath: string,
    request: SaveFileRequest
  ): Promise<SaveFileResponse> {
    const cleanPath = filePath.replace(/^\/+/, '');
    return apiClient.put<SaveFileResponse>(`/projects/${projectId}/files/${cleanPath}`, request);
  },
};
