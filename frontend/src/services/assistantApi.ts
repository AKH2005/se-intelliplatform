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
    const url = `${apiClient.getBaseUrl()}/projects/${projectId}/assistant/messages/stream`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      body: JSON.stringify(payload),
      signal: options?.signal,
    });

    if (!response.ok) {
      let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
      try {
        const errJson = await response.json();
        errorDetail = errJson.detail || errorDetail;
      } catch {
        // ignore
      }
      throw new Error(errorDetail);
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
