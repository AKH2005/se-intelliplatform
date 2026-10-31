export type RuntimeLifecycleStatus =
  | 'NOT_STARTED'
  | 'IDLE'
  | 'PREPARING'
  | 'BUILDING'
  | 'BUILD_FAILED'
  | 'STARTING'
  | 'START_FAILED'
  | 'HEALTH_CHECKING'
  | 'READY'
  | 'RUNNING'
  | 'FAILED'
  | 'STOPPED'
  | 'BLOCKED'
  | 'UNKNOWN'
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
  execution_type?: 'domain_prototype' | 'isolated_container';
  container_status?: RuntimeLifecycleStatus;
  container_detail?: string;
  active_version_id?: string;
  active_version_number?: number;
}

