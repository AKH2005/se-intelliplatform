/**
 * API service for Phase 13 Multi-Environment Development & Deployment.
 */

import { apiClient } from './apiClient';
import {
  DeploymentRecord,
  DeployVersionPayload,
  Environment,
  EnvironmentType,
  PromoteVersionPayload,
  PromotionEligibilityResult,
  RollbackEnvironmentPayload,
} from '../types/environment';

export const environmentApi = {
  listEnvironments: (projectId: string): Promise<Environment[]> => {
    return apiClient.get<Environment[]>(`/projects/${projectId}/environments`);
  },

  getEnvironment: (projectId: string, envIdOrType: string): Promise<Environment> => {
    return apiClient.get<Environment>(`/projects/${projectId}/environments/${envIdOrType}`);
  },

  checkPromotionEligibility: (
    projectId: string,
    versionId: string,
    targetEnv: EnvironmentType,
    sourceEnv?: EnvironmentType
  ): Promise<PromotionEligibilityResult> => {
    const params = new URLSearchParams({
      version_id: versionId,
      target_environment: targetEnv,
    });
    if (sourceEnv) {
      params.append('source_environment', sourceEnv);
    }
    return apiClient.get<PromotionEligibilityResult>(
      `/projects/${projectId}/environments/eligibility?${params.toString()}`
    );
  },

  promoteVersion: (
    projectId: string,
    payload: PromoteVersionPayload
  ): Promise<DeploymentRecord> => {
    return apiClient.post<DeploymentRecord>(
      `/projects/${projectId}/environments/promote`,
      payload
    );
  },

  deployVersion: (
    projectId: string,
    envIdOrType: string,
    payload: DeployVersionPayload
  ): Promise<DeploymentRecord> => {
    return apiClient.post<DeploymentRecord>(
      `/projects/${projectId}/environments/${envIdOrType}/deploy`,
      payload
    );
  },

  rollbackEnvironment: (
    projectId: string,
    envIdOrType: string,
    payload: RollbackEnvironmentPayload
  ): Promise<DeploymentRecord> => {
    return apiClient.post<DeploymentRecord>(
      `/projects/${projectId}/environments/${envIdOrType}/rollback`,
      payload
    );
  },

  listDeployments: (
    projectId: string,
    envIdOrType?: string,
    limit: number = 50
  ): Promise<DeploymentRecord[]> => {
    if (envIdOrType) {
      return apiClient.get<DeploymentRecord[]>(
        `/projects/${projectId}/environments/${envIdOrType}/deployments?limit=${limit}`
      );
    }
    return apiClient.get<DeploymentRecord[]>(
      `/projects/${projectId}/environments/deployments/all?limit=${limit}`
    );
  },
};
