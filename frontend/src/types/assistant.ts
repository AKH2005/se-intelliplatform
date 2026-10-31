/**
 * Phase 11I Intelli Assistant TypeScript Contracts
 */

export type ActionCategory =
  | 'READ_ONLY'
  | 'ANALYSIS'
  | 'GENERATION'
  | 'EXECUTION'
  | 'MUTATING';

export type ActionStatus =
  | 'SUCCESS'
  | 'FAILED'
  | 'PENDING_CONFIRMATION'
  | 'REJECTED'
  | 'INVALID_PARAMETERS'
  | 'UNAUTHORIZED_TARGET';

export type AssistantRole = 'user' | 'assistant' | 'system';

export interface ActionResult {
  action_id: string;
  status: ActionStatus;
  summary: string;
  data?: Record<string, any> | null;
  requires_confirmation: boolean;
  confirmation_token?: string | null;
  confirmation_prompt?: string | null;
  warnings: string[];
  errors: string[];
  audit_reference?: string | null;
}

export interface AssistantMessage {
  message_id: string;
  conversation_id: string;
  role: AssistantRole;
  content: string;
  action_id?: string | null;
  action_status?: ActionStatus | null;
  action_result?: ActionResult | null;
  referenced_entity_type?: string | null;
  referenced_entity_id?: string | null;
  created_at: string;
}

export interface AssistantConversation {
  conversation_id: string;
  project_id: string;
  user_id?: string | null;
  title: string;
  messages: AssistantMessage[];
  created_at: string;
  updated_at: string;
}

export interface SendMessagePayload {
  content: string;
  conversation_id?: string | null;
  explicit_file_paths?: string[];
  error_message?: string;
}

export interface CreateConversationPayload {
  title?: string;
}

export interface ConfirmActionPayload {
  confirmation_token: string;
}

export interface DirectExecuteActionPayload {
  action_id: string;
  target_id?: string | null;
  parameters?: Record<string, any>;
  conversation_id?: string | null;
}

