import { apiClient } from './apiClient';
import {
  GeneralChatRequest,
  GeneralChatResponse,
  GuidedAppPlanRequest,
  GuidedAppPlanResponse,
} from '../types/chat';

export const chatApi = {
  sendMessage: async (request: GeneralChatRequest): Promise<GeneralChatResponse> => {
    return apiClient.post<GeneralChatResponse>('/chat', request);
  },

  synthesizeAppPlan: async (request: GuidedAppPlanRequest): Promise<GuidedAppPlanResponse> => {
    return apiClient.post<GuidedAppPlanResponse>('/chat/guided-app-plan', request);
  },
};
