import {
  ExecutionRequest,
  ExecutionResult,
  SandboxStatusResponse,
  StaticAnalysisRequest,
  StaticAnalysisResult,
} from '../types/sandbox';
import {
  FailureAnalysisApiRequest,
  FailureDiagnosis,
} from '../types/failureAnalysis';
import { apiClient } from './apiClient';

export const sandboxApi = {
  getStatus: (projectId: string): Promise<SandboxStatusResponse> => {
    return apiClient.get<SandboxStatusResponse>(`/projects/${projectId}/sandbox/status`);
  },

  execute: (projectId: string, request: ExecutionRequest): Promise<ExecutionResult> => {
    return apiClient.post<ExecutionResult>(`/projects/${projectId}/sandbox/execute`, request);
  },

  runStaticAnalysis: (projectId: string, request: StaticAnalysisRequest): Promise<StaticAnalysisResult> => {
    return apiClient.post<StaticAnalysisResult>(`/projects/${projectId}/analysis/static`, request);
  },

  getStaticAnalysis: (projectId: string, analysisId: string): Promise<StaticAnalysisResult> => {
    return apiClient.get<StaticAnalysisResult>(`/projects/${projectId}/analysis/static/${analysisId}`);
  },

  runFailureAnalysis: (projectId: string, request: FailureAnalysisApiRequest): Promise<FailureDiagnosis> => {
    return apiClient.post<FailureDiagnosis>(`/projects/${projectId}/analysis/failure`, request);
  },

  getFailureDiagnosis: (projectId: string, diagnosisId: string): Promise<FailureDiagnosis> => {
    return apiClient.get<FailureDiagnosis>(`/projects/${projectId}/analysis/failure/${diagnosisId}`);
  },
};


