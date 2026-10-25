export type RuntimeLifecycleStatus =
  | 'IDLE'
  | 'PREPARING'
  | 'BUILDING'
  | 'STARTING'
  | 'HEALTH_CHECKING'
  | 'READY'
  | 'RUNNING'
  | 'FAILED'
  | 'STOPPED'
  | 'UNAVAILABLE';

export interface RuntimeStatusResponse {
  status: RuntimeLifecycleStatus;
  port: number;
  preview_url: string;
  preview_token?: string;
  is_healthy: boolean;
  project_id?: string;
  project_name?: string;
  active_mode: 'taskflow' | 'eventhub' | string;
  detail: string;
}

