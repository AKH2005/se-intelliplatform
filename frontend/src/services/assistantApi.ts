/**
 * API service for Phase 11I Intelli Assistant & Engineering Action Layer.
 */

import { apiClient } from './apiClient';
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

export const assistantApi = {
  sendMessage: (
    projectId: string,
    payload: SendMessagePayload
  ): Promise<AssistantMessage> => {
    return apiClient.post<AssistantMessage>(
      `/projects/${projectId}/assistant/messages`,
      payload
    );
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
    payload: ConfirmActionPayload
  ): Promise<ActionResult> => {
    return apiClient.post<ActionResult>(
      `/projects/${projectId}/assistant/actions/confirm`,
      payload
    );
  },

  executeActionDirect: (
    projectId: string,
    payload: DirectExecuteActionPayload
  ): Promise<ActionResult> => {
    return apiClient.post<ActionResult>(
      `/projects/${projectId}/assistant/actions/execute`,
      payload
    );
  },
};
