export interface AgentMetadata {
  agent_id: string;
  name: string;
  description: string;
  category: string;
  version: string;
}

export interface AgentErrorDetail {
  error_type: string;
  message: string;
  details?: Record<string, any> | null;
}
