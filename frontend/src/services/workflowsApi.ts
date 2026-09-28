import {
  WorkflowExecuteRequest,
  WorkflowMetadataResponse,
  WorkflowResultResponse,
} from '../types/workflow';
import { apiClient } from './apiClient';

export const workflowsApi = {
  list: (): Promise<WorkflowMetadataResponse[]> => {
    return apiClient.get<WorkflowMetadataResponse[]>('/workflows');
  },

  get: (workflowId: string): Promise<WorkflowMetadataResponse> => {
    return apiClient.get<WorkflowMetadataResponse>(`/workflows/${workflowId}`);
  },

  execute: (workflowId: string, request: WorkflowExecuteRequest): Promise<WorkflowResultResponse> => {
    return apiClient.post<WorkflowResultResponse>(`/workflows/${workflowId}/execute`, request);
  },
};
