export interface ChatMessage {
  id: string;
  role: 'system' | 'user' | 'assistant';
  content: string;
  timestamp: string;
  isError?: boolean;
}

export interface GeneralChatRequest {
  message: string;
  conversation_history?: Array<{ role: 'system' | 'user' | 'assistant'; content: string }>;
  context?: Record<string, any>;
}

export interface GeneralChatResponse {
  response: string;
  provider: string;
  model: string;
}

export interface AppRequirementItem {
  title: string;
  description: string;
  type: 'FUNCTIONAL' | 'NON_FUNCTIONAL';
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface GuidedAppPlanRequest {
  prompt: string;
}

export interface GuidedAppPlanResponse {
  name: string;
  slug: string;
  description: string;
  requirements: AppRequirementItem[];
  suggested_features: string[];
}
