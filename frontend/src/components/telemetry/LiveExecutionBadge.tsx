import React from 'react';
import { ExecutionEventType } from '../../types/telemetry';

interface LiveExecutionBadgeProps {
  status: string;
  isStreaming?: boolean;
  totalEvents?: number;
  latestEventType?: ExecutionEventType | null;
  size?: 'sm' | 'md';
}

export const LiveExecutionBadge: React.FC<LiveExecutionBadgeProps> = ({
  status,
  isStreaming = false,
  totalEvents,
  latestEventType,
  size = 'sm',
}) => {
  const normStatus = (status || 'UNKNOWN').toUpperCase();

  let statusBg = 'rgba(100, 116, 139, 0.2)';
  let statusColor = 'var(--text-secondary)';
  let border = '1px solid var(--border-subtle)';

  if (normStatus === 'RUNNING' || normStatus === 'IN_PROGRESS') {
    statusBg = 'rgba(56, 189, 248, 0.15)';
    statusColor = 'var(--status-running)';
    border = '1px solid rgba(56, 189, 248, 0.4)';
  } else if (normStatus === 'COMPLETED' || normStatus === 'SUCCESS' || normStatus === 'PASSED') {
    statusBg = 'rgba(16, 185, 129, 0.15)';
    statusColor = 'var(--status-completed)';
    border = '1px solid rgba(16, 185, 129, 0.4)';
  } else if (normStatus === 'FAILED' || normStatus === 'ERROR') {
    statusBg = 'rgba(239, 68, 68, 0.15)';
    statusColor = 'var(--status-failed)';
    border = '1px solid rgba(239, 68, 68, 0.4)';
  } else if (normStatus === 'BLOCKED' || normStatus === 'SAFETY_BLOCKED') {
    statusBg = 'rgba(249, 115, 22, 0.15)';
    statusColor = 'var(--risk-high)';
    border = '1px solid rgba(249, 115, 22, 0.4)';
  }

  const isSmall = size === 'sm';

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.45rem',
        padding: isSmall ? '0.2rem 0.55rem' : '0.35rem 0.8rem',
        borderRadius: 'var(--radius-sm, 6px)',
        background: statusBg,
        color: statusColor,
        border,
        fontSize: isSmall ? '0.75rem' : '0.85rem',
        fontWeight: 600,
        fontFamily: 'monospace',
      }}
    >
      {isStreaming && (
        <span
          title="Streaming live events via WebSocket"
          style={{
            display: 'inline-block',
            width: isSmall ? '7px' : '9px',
            height: isSmall ? '7px' : '9px',
            borderRadius: '50%',
            backgroundColor: 'var(--status-completed, #10b981)',
            boxShadow: '0 0 6px var(--status-completed, #10b981)',
            animation: 'pulse 1.8s infinite ease-in-out',
          }}
        />
      )}
      <span>{normStatus}</span>
      {totalEvents !== undefined && totalEvents > 0 && (
        <span
          style={{
            color: 'var(--text-muted)',
            fontSize: isSmall ? '0.7rem' : '0.75rem',
            marginLeft: '0.2rem',
          }}
        >
          ({totalEvents} evt{totalEvents > 1 ? 's' : ''})
        </span>
      )}
      {latestEventType && (
        <span
          style={{
            color: 'var(--text-dim)',
            fontSize: isSmall ? '0.68rem' : '0.75rem',
            marginLeft: '0.2rem',
          }}
        >
          [{latestEventType}]
        </span>
      )}
    </div>
  );
};
