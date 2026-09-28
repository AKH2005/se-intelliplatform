import {
  WorkflowExecutionDetailResponse,
  WorkflowHistoryListResponse,
  WorkflowStatus,
} from '../types/workflow';
import { apiClient } from './apiClient';

export interface ListProjectWorkflowHistoryParams {
  limit?: number;
  offset?: number;
  workflow_id?: string;
  status?: WorkflowStatus;
}

export const historyApi = {
  listProjectHistory: (
    projectId: string,
    params?: ListProjectWorkflowHistoryParams
  ): Promise<WorkflowHistoryListResponse> => {
    return apiClient.get<WorkflowHistoryListResponse>(`/projects/${projectId}/workflows/history`, {
      params: params as any,
    });
  },

  getExecutionDetail: (executionId: string): Promise<WorkflowExecutionDetailResponse> => {
    return apiClient.get<WorkflowExecutionDetailResponse>(`/workflows/executions/${executionId}`);
  },
};
