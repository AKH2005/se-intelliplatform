import { apiClient } from './apiClient';
import {
  AITestExecutionResult,
  AITestSuite,
  TestCategory,
} from '../types/aiTesting';
import { FailureDiagnosis } from '../types/failureAnalysis';

export interface GenerateAITestsRequest {
  workflow_execution_id?: string | null;
  allowed_categories?: TestCategory[] | null;
}

export interface ExecuteAITestsRequest {
  workflow_execution_id?: string | null;
  timeout_seconds?: number;
}

export const aiTestingApi = {
  generateTests: (
    projectId: string,
    request?: GenerateAITestsRequest
  ): Promise<AITestSuite> => {
    return apiClient.post<AITestSuite>(
      `/projects/${projectId}/tests/ai/generate`,
      request || {}
    );
  },

  getLatestTestSuite: (projectId: string): Promise<AITestSuite | null> => {
    return apiClient.get<AITestSuite | null>(
      `/projects/${projectId}/tests/ai/latest`
    );
  },

  getTestSuite: (
    projectId: string,
    suiteId: string
  ): Promise<AITestSuite> => {
    return apiClient.get<AITestSuite>(
      `/projects/${projectId}/tests/ai/${suiteId}`
    );
  },

  executeTests: (
    projectId: string,
    suiteId: string,
    request?: ExecuteAITestsRequest
  ): Promise<AITestExecutionResult> => {
    return apiClient.post<AITestExecutionResult>(
      `/projects/${projectId}/tests/ai/${suiteId}/execute`,
      request || {}
    );
  },

  analyzeTestFailure: (
    projectId: string,
    suiteId: string,
    workflowExecutionId?: string | null
  ): Promise<FailureDiagnosis> => {
    return apiClient.post<FailureDiagnosis>(
      `/projects/${projectId}/tests/ai/${suiteId}/analyze-failure`,
      { workflow_execution_id: workflowExecutionId || null }
    );
  },
};
