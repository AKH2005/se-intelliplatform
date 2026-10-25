import { apiClient } from './apiClient';
import { BrowserTestRun, RunBrowserTestsRequest } from '../types/browserTesting';

export const browserTestingApi = {
  runBrowserTests: (
    projectId: string,
    request: RunBrowserTestsRequest = {}
  ): Promise<BrowserTestRun> => {
    return apiClient.post<BrowserTestRun>(`/projects/${projectId}/browser/tests/run`, request);
  },

  getLatestBrowserTestRun: (
    projectId: string,
    versionId?: string
  ): Promise<BrowserTestRun> => {
    const params = versionId ? { version_id: versionId } : undefined;
    return apiClient.get<BrowserTestRun>(`/projects/${projectId}/browser/tests/latest`, { params });
  },

  getBrowserTestRun: (
    projectId: string,
    runId: string
  ): Promise<BrowserTestRun> => {
    return apiClient.get<BrowserTestRun>(`/projects/${projectId}/browser/tests/${runId}`);
  },

  getScreenshotUrl: (
    projectId: string,
    runId: string,
    filename: string
  ): string => {
    const baseUrl = apiClient.getBaseUrl() || 'http://localhost:8000/api/v1';
    const cleanFile = encodeURIComponent(filename.replace(/^.*[\\\/]/, ''));
    return `${baseUrl}/projects/${projectId}/browser/tests/${runId}/screenshots/${cleanFile}`;
  },
};
