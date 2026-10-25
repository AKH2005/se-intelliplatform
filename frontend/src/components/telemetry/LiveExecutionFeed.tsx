import React, { useState, useRef, useEffect } from 'react';
import { useExecutionTelemetry } from '../../hooks/useExecutionTelemetry';
import { LiveExecutionBadge } from './LiveExecutionBadge';
import { ExecutionEvent, EventSeverity } from '../../types/telemetry';

interface LiveExecutionFeedProps {
  projectId: string;
  executionId?: string;
  title?: string;
  maxHeight?: string;
  onClose?: () => void;
}

export const LiveExecutionFeed: React.FC<LiveExecutionFeedProps> = ({
  projectId,
  executionId,
  title = 'Real-Time Execution Telemetry',
  maxHeight = '450px',
  onClose,
}) => {
  const {
    events,
    snapshot,
    isConnected,
    isStreaming,
    error,
    clearEvents,
    reconnect,
  } = useExecutionTelemetry({
    projectId,
    executionId,
  });

  const [expandedEventId, setExpandedEventId] = useState<string | null>(null);
  const [autoScroll, setAutoScroll] = useState<boolean>(true);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  }, [events, autoScroll]);

  const toggleExpand = (eventId: string) => {
    setExpandedEventId((curr) => (curr === eventId ? null : eventId));
  };

  const getSeverityColor = (sev: EventSeverity): string => {
    switch (sev) {
      case 'ERROR':
      case 'CRITICAL':
        return 'var(--status-failed, #ef4444)';
      case 'WARNING':
        return 'var(--risk-high, #f97316)';
      case 'INFO':
      default:
        return 'var(--text-secondary, #94a3b8)';
    }
  };

  return (
    <div
      data-testid="live-execution-feed"
      style={{
        background: 'var(--bg-glass-card, rgba(22, 30, 52, 0.6))',
        border: '1px solid var(--border-glass, rgba(255, 255, 255, 0.12))',
        borderRadius: 'var(--radius-md, 8px)',
        backdropFilter: 'blur(16px)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        boxShadow: 'var(--shadow-md, 0 4px 12px -1px rgba(0, 0, 0, 0.5))',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '0.75rem 1rem',
          borderBottom: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'var(--bg-surface, #151b2d)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span
            style={{
              fontWeight: 600,
              fontSize: '0.9rem',
              color: 'var(--text-primary, #f8fafc)',
            }}
          >
            {title}
          </span>
          {snapshot && (
            <LiveExecutionBadge
              status={snapshot.status}
              isStreaming={isStreaming}
              totalEvents={events.length}
              latestEventType={snapshot.latest_event_type}
            />
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <label
            style={{
              fontSize: '0.75rem',
              color: 'var(--text-muted, #64748b)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.25rem',
              cursor: 'pointer',
            }}
          >
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
            />
            Auto-scroll
          </label>
          {!isConnected && (
            <button
              onClick={reconnect}
              style={{
                fontSize: '0.75rem',
                padding: '0.2rem 0.5rem',
                borderRadius: '4px',
                background: 'var(--bg-surface-hover, #1c243c)',
                color: 'var(--text-secondary, #94a3b8)',
                border: '1px solid var(--border-subtle)',
                cursor: 'pointer',
              }}
            >
              Reconnect
            </button>
          )}
          <button
            onClick={clearEvents}
            title="Clear buffer"
            style={{
              fontSize: '0.75rem',
              padding: '0.2rem 0.5rem',
              borderRadius: '4px',
              background: 'transparent',
              color: 'var(--text-muted, #64748b)',
              border: '1px solid var(--border-subtle)',
              cursor: 'pointer',
            }}
          >
            Clear
          </button>
          {onClose && (
            <button
              onClick={onClose}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                fontSize: '1rem',
                lineHeight: 1,
              }}
            >
              ×
            </button>
          )}
        </div>
      </div>

      {/* Snapshot Active Status Sub-bar */}
      {snapshot && (
        <div
          style={{
            padding: '0.4rem 1rem',
            background: 'rgba(15, 20, 34, 0.5)',
            borderBottom: '1px solid var(--border-subtle)',
            fontSize: '0.78rem',
            display: 'flex',
            alignItems: 'center',
            gap: '1.25rem',
            color: 'var(--text-secondary)',
          }}
        >
          {snapshot.active_step && (
            <span>
              <strong style={{ color: 'var(--text-primary)' }}>Step:</strong>{' '}
              <code style={{ color: 'var(--accent-cyan)' }}>{snapshot.active_step}</code>
            </span>
          )}
          {snapshot.execution_kind && (
            <span>
              <strong>Kind:</strong> {snapshot.execution_kind}
            </span>
          )}
          {snapshot.latest_sequence !== undefined && (
            <span>
              <strong>Seq:</strong> #{snapshot.latest_sequence}
            </span>
          )}
          {snapshot.error_message && (
            <span style={{ color: 'var(--status-failed)' }}>
              <strong>Error:</strong> {snapshot.error_message}
            </span>
          )}
        </div>
      )}

      {/* Notice / Warning Bar */}
      {error && (
        <div
          style={{
            padding: '0.4rem 1rem',
            background: 'rgba(239, 68, 68, 0.1)',
            borderBottom: '1px solid rgba(239, 68, 68, 0.25)',
            color: 'var(--status-failed)',
            fontSize: '0.75rem',
          }}
        >
          {error}
        </div>
      )}

      {/* Scrollable Event Feed */}
      <div
        ref={scrollContainerRef}
        style={{
          maxHeight,
          overflowY: 'auto',
          padding: '0.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.35rem',
          fontFamily: 'monospace',
          fontSize: '0.78rem',
        }}
      >
        {events.length === 0 ? (
          <div
            style={{
              padding: '2rem 1rem',
              textAlign: 'center',
              color: 'var(--text-muted)',
              fontStyle: 'italic',
            }}
          >
            {isConnected
              ? 'Listening for live execution events...'
              : 'Connecting to telemetry event stream...'}
          </div>
        ) : (
          events.map((evt: ExecutionEvent) => {
            const isExpanded = expandedEventId === evt.event_id;
            const timeStr = evt.timestamp
              ? new Date(evt.timestamp).toLocaleTimeString()
              : '--:--:--';

            return (
              <div
                key={evt.event_id}
                data-testid={`telemetry-event-${evt.sequence}`}
                onClick={() => toggleExpand(evt.event_id)}
                style={{
                  padding: '0.4rem 0.6rem',
                  borderRadius: '4px',
                  background: isExpanded
                    ? 'var(--bg-surface-active, #242e4d)'
                    : 'var(--bg-surface, #151b2d)',
                  border: '1px solid var(--border-subtle)',
                  cursor: 'pointer',
                  transition: 'background 0.15s ease',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: '0.5rem',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    <span style={{ color: 'var(--text-dim)', minWidth: '2.5rem' }}>
                      #{evt.sequence}
                    </span>
                    <span style={{ color: 'var(--text-muted)' }}>{timeStr}</span>
                    <span
                      style={{
                        color: getSeverityColor(evt.severity),
                        fontWeight: 600,
                      }}
                    >
                      {evt.event_type}
                    </span>
                    <span style={{ color: 'var(--text-dim)' }}>[{evt.source}]</span>
                  </div>

                  <span
                    style={{
                      fontSize: '0.7rem',
                      padding: '0.1rem 0.4rem',
                      borderRadius: '3px',
                      background: 'rgba(255, 255, 255, 0.05)',
                      color: 'var(--text-secondary)',
                    }}
                  >
                    {evt.status}
                  </span>
                </div>

                {/* Expanded Payload safely formatted */}
                {isExpanded && (
                  <div
                    style={{
                      marginTop: '0.5rem',
                      padding: '0.5rem',
                      background: 'rgba(0, 0, 0, 0.4)',
                      borderRadius: '4px',
                      overflowX: 'auto',
                    }}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <div style={{ color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                      Payload:
                    </div>
                    <pre
                      style={{
                        margin: 0,
                        fontSize: '0.72rem',
                        color: 'var(--text-secondary)',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-all',
                      }}
                    >
                      {JSON.stringify(evt.payload, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
