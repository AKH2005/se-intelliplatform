import {
  ContextSnapshotCreate,
  ContextSnapshotResponse,
  ProjectContextResponse,
} from '../types/context';
import { apiClient } from './apiClient';

export interface ListSnapshotsParams {
  skip?: number;
  limit?: number;
}

export const contextApi = {
  getContext: (projectId: string): Promise<ProjectContextResponse> => {
    return apiClient.get<ProjectContextResponse>(`/projects/${projectId}/context`);
  },

  createSnapshot: (projectId: string, data: ContextSnapshotCreate): Promise<ContextSnapshotResponse> => {
    return apiClient.post<ContextSnapshotResponse>(`/projects/${projectId}/context/snapshots`, data);
  },

  listSnapshots: (projectId: string, params?: ListSnapshotsParams): Promise<ContextSnapshotResponse[]> => {
    return apiClient.get<ContextSnapshotResponse[]>(`/projects/${projectId}/context/snapshots`, {
      params: params as any,
    });
  },

  getSnapshotByVersion: (projectId: string, version: number): Promise<ContextSnapshotResponse> => {
    return apiClient.get<ContextSnapshotResponse>(`/projects/${projectId}/context/snapshots/${version}`);
  },
};
