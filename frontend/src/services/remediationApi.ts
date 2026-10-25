import { apiClient } from './apiClient';
import {
  ApplyRemediationResponse,
  CreateProposalRequest,
  RejectProposalRequest,
  RemediationProposal,
} from '../types/remediation';

export const remediationApi = {
  createProposal: (
    projectId: string,
    request?: CreateProposalRequest
  ): Promise<RemediationProposal> => {
    return apiClient.post<RemediationProposal>(
      `/projects/${projectId}/remediation/proposals`,
      request || {}
    );
  },

  getLatestProposal: (projectId: string): Promise<RemediationProposal | null> => {
    return apiClient.get<RemediationProposal | null>(
      `/projects/${projectId}/remediation/proposals/latest`
    );
  },

  getProposal: (
    projectId: string,
    proposalId: string
  ): Promise<RemediationProposal> => {
    return apiClient.get<RemediationProposal>(
      `/projects/${projectId}/remediation/proposals/${proposalId}`
    );
  },

  approveProposal: (
    projectId: string,
    proposalId: string
  ): Promise<RemediationProposal> => {
    return apiClient.post<RemediationProposal>(
      `/projects/${projectId}/remediation/proposals/${proposalId}/approve`,
      {}
    );
  },

  rejectProposal: (
    projectId: string,
    proposalId: string,
    request?: RejectProposalRequest
  ): Promise<RemediationProposal> => {
    return apiClient.post<RemediationProposal>(
      `/projects/${projectId}/remediation/proposals/${proposalId}/reject`,
      request || {}
    );
  },

  applyProposal: (
    projectId: string,
    proposalId: string
  ): Promise<ApplyRemediationResponse> => {
    return apiClient.post<ApplyRemediationResponse>(
      `/projects/${projectId}/remediation/proposals/${proposalId}/apply`,
      {}
    );
  },
};
