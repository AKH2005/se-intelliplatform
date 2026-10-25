import { HttpClient } from './apiClient';
import {
  ExecutionEvent,
  ExecutionStateSnapshot,
} from '../types/telemetry';

export class TelemetryApiClient {
  private client: HttpClient;

  constructor(client?: HttpClient) {
    this.client = client || new HttpClient();
  }

  public async listActiveExecutions(projectId: string): Promise<ExecutionStateSnapshot[]> {
    return this.client.request<ExecutionStateSnapshot[]>(
      `/projects/${encodeURIComponent(projectId)}/telemetry/active`
    );
  }

  public async getExecutionStatus(
    projectId: string,
    executionId: string
  ): Promise<ExecutionStateSnapshot> {
    return this.client.request<ExecutionStateSnapshot>(
      `/projects/${encodeURIComponent(projectId)}/telemetry/executions/${encodeURIComponent(executionId)}/status`
    );
  }

  public async getExecutionEvents(
    projectId: string,
    executionId: string,
    sinceSequence: number = 0
  ): Promise<ExecutionEvent[]> {
    return this.client.request<ExecutionEvent[]>(
      `/projects/${encodeURIComponent(projectId)}/telemetry/executions/${encodeURIComponent(executionId)}/events`,
      {
        params: { since_sequence: sinceSequence },
      }
    );
  }

  public getWebSocketUrl(
    projectId: string,
    executionId?: string,
    sinceSequence: number = 0
  ): string {
    const rawBase = this.client.getBaseUrl();

    const wsBase = rawBase.replace(/^http:\/\//i, 'ws://').replace(/^https:\/\//i, 'wss://');
    let url = `${wsBase}/projects/${encodeURIComponent(projectId)}/telemetry/ws?since_sequence=${sinceSequence}`;
    if (executionId) {
      url += `&execution_id=${encodeURIComponent(executionId)}`;
    }
    return url;
  }
}

export const telemetryApi = new TelemetryApiClient();
