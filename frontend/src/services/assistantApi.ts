/**
 * API service for Phase 11I Intelli Assistant & Engineering Action Layer.
 */

import { apiClient, RequestOptions } from './apiClient';
import {
  ActionResult,
  AssistantConversation,
  AssistantMessage,
  ConfirmActionPayload,
  DirectExecuteActionPayload,
  SendMessagePayload,
} from '../types/assistant';

export interface AssistantConversationListResponse {
  items: AssistantConversation[];
  total: number;
}

export interface StreamCallbacks {
  onStart?: (data: { intent?: string; persona?: string; conversation_id?: string }) => void;
  onChunk?: (chunk: string) => void;
  onStatus?: (status: string) => void;
  onDone?: (message: AssistantMessage) => void;
  onError?: (error: string) => void;
}

export const assistantApi = {
  createConversation: (
    projectId: string,
    payload?: { title?: string }
  ): Promise<AssistantConversation> => {
    return apiClient.post<AssistantConversation>(
      `/projects/${projectId}/assistant/conversations`,
      payload || {}
    );
  },

  deleteConversation: (
    projectId: string,
    conversationId: string
  ): Promise<void> => {
    return apiClient.delete<void>(
      `/projects/${projectId}/assistant/conversations/${conversationId}`
    );
  },

  sendMessage: (
    projectId: string,
    payload: SendMessagePayload,
    options?: RequestOptions
  ): Promise<AssistantMessage> => {
    return apiClient.post<AssistantMessage>(
      `/projects/${projectId}/assistant/messages`,
      payload,
      { timeoutMs: 90000, ...options }
    );
  },

  sendMessageStream: async (
    projectId: string,
    payload: SendMessagePayload,
    callbacks?: StreamCallbacks,
    options?: { signal?: AbortSignal }
  ): Promise<AssistantMessage> => {
    const baseUrl = apiClient.getBaseUrl();
    const url = `${baseUrl}/projects/${projectId}/assistant/messages/stream`;
    const headers = apiClient.getAuthHeaders({
      Accept: 'text/event-stream',
    });

    let response: Response;
    try {
      response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
        signal: options?.signal,
      });
    } catch (netErr: any) {
      if (netErr?.name === 'AbortError' || netErr?.code === 'ERR_CANCELED') {
        throw netErr;
      }
      const isMixedContent =
        typeof window !== 'undefined' &&
        window.location.protocol === 'https:' &&
        baseUrl.startsWith('http:');

      let diagnosticMsg = `Unable to connect to backend service at ${baseUrl}. `;
      if (isMixedContent) {
        diagnosticMsg +=
          'Mixed Content Security Block: HTTPS pages cannot connect to insecure HTTP endpoints. Please configure a secure HTTPS API endpoint.';
      } else {
        diagnosticMsg +=
          'Please verify that the backend server is running and reachable from your network.';
      }

      const err: any = new Error(diagnosticMsg);
      err.isNetworkError = true;
      err.targetUrl = url;
      err.originalError = netErr;
      throw err;
    }

    if (!response.ok) {
      let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
      let errorData: any = null;
      try {
        errorData = await response.json();
        errorDetail = errorData.detail || errorData.title || errorDetail;
      } catch {
        // ignore JSON parse failure on non-JSON error pages
      }

      const structuredErr: any = new Error(errorDetail);
      structuredErr.status = response.status;
      structuredErr.statusText = response.statusText;
      structuredErr.response = { status: response.status, data: errorData };
      structuredErr.detail = errorDetail;

      if (response.status === 401) {
        structuredErr.userMessage =
          'Authentication session expired or invalid. Please refresh the page or log in again.';
      } else if (response.status === 403) {
        structuredErr.userMessage =
          'You do not have permission to access or modify this project in the AI Development Assistant.';
      } else if (response.status === 404) {
        structuredErr.userMessage = `Project context not found on server (${projectId}). Please verify project selection.`;
      } else if (response.status === 500) {
        structuredErr.userMessage =
          'Backend server encountered an internal error while generating assistant response. Please try again.';
      } else if (response.status === 502 || response.status === 503 || response.status === 504) {
        structuredErr.userMessage =
          'Backend service is temporarily unavailable or restarting. Please retry in a few moments.';
      }

      throw structuredErr;
    }

    if (!response.body) {
      throw new Error('Streaming response body is null');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let finalMessage: AssistantMessage | null = null;

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const events = buffer.split('\n\n');
        buffer = events.pop() || '';

        for (const eventBlock of events) {
          if (!eventBlock.trim()) continue;
          const lines = eventBlock.split('\n');
          let eventType = 'message';
          let dataStr = '';

          for (const line of lines) {
            if (line.startsWith('event: ')) {
              eventType = line.slice(7).trim();
            } else if (line.startsWith('data: ')) {
              dataStr = line.slice(6);
            }
          }

          try {
            const parsed = JSON.parse(dataStr);
            if (eventType === 'start') {
              callbacks?.onStart?.(parsed);
            } else if (eventType === 'content') {
              callbacks?.onChunk?.(parsed.chunk);
            } else if (eventType === 'status') {
              callbacks?.onStatus?.(parsed.status);
            } else if (eventType === 'done') {
              finalMessage = parsed as AssistantMessage;
              callbacks?.onDone?.(finalMessage);
            } else if (eventType === 'error') {
              callbacks?.onError?.(parsed.error);
              throw new Error(parsed.error);
            }
          } catch (e: any) {
            if (eventType === 'error') throw e;
          }
        }
      }
    } catch (streamErr: any) {
      if (streamErr?.name === 'AbortError') {
        throw streamErr;
      }
      if (!finalMessage) {
        const err: any = new Error(
          `Streaming interrupted: ${streamErr.message || 'Connection lost before completion'}`
        );
        err.originalError = streamErr;
        throw err;
      }
    } finally {
      reader.releaseLock();
    }

    if (!finalMessage) {
      throw new Error('Stream finished without completion event');
    }
    return finalMessage;
  },

  listConversations: (
    projectId: string
  ): Promise<AssistantConversationListResponse> => {
    return apiClient.get<AssistantConversationListResponse>(
      `/projects/${projectId}/assistant/conversations`
    );
  },

  getConversation: (
    projectId: string,
    conversationId: string
  ): Promise<AssistantConversation> => {
    return apiClient.get<AssistantConversation>(
      `/projects/${projectId}/assistant/conversations/${conversationId}`
    );
  },


  confirmAction: (
    projectId: string,
    payload: ConfirmActionPayload,
    options?: RequestOptions
  ): Promise<ActionResult> => {
    return apiClient.post<ActionResult>(
      `/projects/${projectId}/assistant/actions/confirm`,
      payload,
      { timeoutMs: 90000, ...options }
    );
  },

  executeActionDirect: (
    projectId: string,
    payload: DirectExecuteActionPayload,
    options?: RequestOptions
  ): Promise<ActionResult> => {
    return apiClient.post<ActionResult>(
      `/projects/${projectId}/assistant/actions/execute`,
      payload,
      { timeoutMs: 90000, ...options }
    );
  },
};
