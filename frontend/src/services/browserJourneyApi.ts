import { apiClient } from './apiClient';
import {
  BrowserJourneyWorkflowResponse,
  GenerateBrowserJourneysRequest,
} from '../types/browserJourney';

/**
 * REST API client for Intelligent Browser Journeys (Phase 11K).
 *
 * Communicates strictly with the Stage 5 project-scoped REST endpoints:
 * POST /api/v1/projects/{project_id}/browser-journeys
 * GET  /api/v1/projects/{project_id}/browser-journeys
 * GET  /api/v1/projects/{project_id}/browser-journeys/latest
 * GET  /api/v1/projects/{project_id}/browser-journeys/{workflow_execution_id}
 */
export const browserJourneyApi = {
  /**
   * Triggers the Stage 4 browser journey workflow (generation -> validation -> adaptation -> execution).
   */
  generateBrowserJourneys: (
    projectId: string,
    request: GenerateBrowserJourneysRequest = {}
  ): Promise<BrowserJourneyWorkflowResponse> => {
    return apiClient.post<BrowserJourneyWorkflowResponse>(
      `/projects/${projectId}/browser-journeys`,
      request
    );
  },

  /**
   * Retrieves a paginated list of historical browser journey workflow runs for a project.
   */
  getBrowserJourneys: (
    projectId: string,
    limit: number = 20,
    offset: number = 0
  ): Promise<BrowserJourneyWorkflowResponse[]> => {
    return apiClient.get<BrowserJourneyWorkflowResponse[]>(
      `/projects/${projectId}/browser-journeys`,
      { params: { limit, offset } }
    );
  },

  /**
   * Retrieves the latest browser journey workflow execution outcome and artifacts.
   */
  getLatestBrowserJourneys: (
    projectId: string
  ): Promise<BrowserJourneyWorkflowResponse> => {
    return apiClient.get<BrowserJourneyWorkflowResponse>(
      `/projects/${projectId}/browser-journeys/latest`
    );
  },

  /**
   * Retrieves a specific workflow execution result by correlation UUID (strictly read-only).
   */
  getBrowserJourney: (
    projectId: string,
    workflowExecutionId: string
  ): Promise<BrowserJourneyWorkflowResponse> => {
    return apiClient.get<BrowserJourneyWorkflowResponse>(
      `/projects/${projectId}/browser-journeys/${workflowExecutionId}`
    );
  },
};
