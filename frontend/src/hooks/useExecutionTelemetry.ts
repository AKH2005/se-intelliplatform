import { useState, useEffect, useRef, useCallback } from 'react';
import {
  ExecutionEvent,
  ExecutionStateSnapshot,
} from '../types/telemetry';
import { telemetryApi } from '../services/telemetryApi';

interface UseExecutionTelemetryProps {
  projectId: string;
  executionId?: string;
  enabled?: boolean;
}

interface UseExecutionTelemetryReturn {
  events: ExecutionEvent[];
  snapshot: ExecutionStateSnapshot | null;
  isConnected: boolean;
  isStreaming: boolean;
  error: string | null;
  clearEvents: () => void;
  reconnect: () => void;
}

export function useExecutionTelemetry({
  projectId,
  executionId,
  enabled = true,
}: UseExecutionTelemetryProps): UseExecutionTelemetryReturn {
  const [events, setEvents] = useState<ExecutionEvent[]>([]);
  const [snapshot, setSnapshot] = useState<ExecutionStateSnapshot | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const seenEventIdsRef = useRef<Set<string>>(new Set());
  const latestSequenceRef = useRef<number>(0);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const pingIntervalRef = useRef<number | null>(null);

  const clearEvents = useCallback(() => {
    setEvents([]);
    seenEventIdsRef.current.clear();
    latestSequenceRef.current = 0;
  }, []);

  const handleIncomingEvent = useCallback((event: ExecutionEvent) => {
    if (!event || !event.event_id) return;

    if (seenEventIdsRef.current.has(event.event_id)) {
      return; // Deduplicate
    }
    seenEventIdsRef.current.add(event.event_id);

    if (event.sequence > latestSequenceRef.current) {
      latestSequenceRef.current = event.sequence;
    }

    setEvents((prev) => {
      const updated = [...prev, event];
      updated.sort((a, b) => a.sequence - b.sequence);
      return updated;
    });

    setSnapshot((prev) => {
      if (!prev) {
        return {
          execution_id: event.execution_id,
          project_id: event.project_id,
          execution_kind: event.execution_kind,
          status: event.status,
          created_at: event.timestamp,
          updated_at: event.timestamp,
          latest_sequence: event.sequence,
          total_events: 1,
          latest_event_type: event.event_type,
          active_step: (event.payload?.step_id as string) || (event.payload?.active_step as string) || null,
          error_message: (event.payload?.error as string) || null,
          metadata: event.payload || {},
        };
      }
      return {
        ...prev,
        status: event.status,
        updated_at: event.timestamp,
        latest_sequence: Math.max(prev.latest_sequence, event.sequence),
        total_events: prev.total_events + 1,
        latest_event_type: event.event_type,
        active_step:
          (event.payload?.step_id as string) ||
          (event.payload?.active_step as string) ||
          prev.active_step,
        error_message: (event.payload?.error as string) || prev.error_message,
        metadata: { ...prev.metadata, ...event.payload },
      };
    });
  }, []);

  const connectWebSocket = useCallback(() => {
    if (!enabled || !projectId) return;

    try {
      const url = telemetryApi.getWebSocketUrl(
        projectId,
        executionId,
        latestSequenceRef.current
      );

      const ws = new WebSocket(url);
      socketRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        setIsStreaming(true);
        setError(null);

        // Setup ping heartbeat every 15 seconds
        if (pingIntervalRef.current) {
          window.clearInterval(pingIntervalRef.current);
        }
        pingIntervalRef.current = window.setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 15000);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data && data.type === 'pong') {
            return;
          }
          if (data && data.event_id) {
            handleIncomingEvent(data as ExecutionEvent);
          }
        } catch {
          // Ignore invalid message
        }
      };

      ws.onerror = () => {
        // Non-fatal telemetry transport notice
        setError('Real-time connection interrupted. Telemetry falling back.');
      };

      ws.onclose = () => {
        setIsConnected(false);
        setIsStreaming(false);
        if (pingIntervalRef.current) {
          window.clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }

        // Auto-reconnect after 3s if still enabled
        if (enabled) {
          reconnectTimeoutRef.current = window.setTimeout(() => {
            connectWebSocket();
          }, 3000);
        }
      };
    } catch (err) {
      setError(err instanceof Error ? err.message : 'WebSocket failed to initialize');
    }
  }, [enabled, projectId, executionId, handleIncomingEvent]);

  // Initial REST hydration
  useEffect(() => {
    let cancelled = false;

    async function hydrate() {
      if (!enabled || !projectId) return;
      if (executionId) {
        try {
          const snap = await telemetryApi.getExecutionStatus(projectId, executionId);
          if (!cancelled && snap) {
            setSnapshot(snap);
            latestSequenceRef.current = snap.latest_sequence;
          }
        } catch {
          // May not exist yet, which is fine
        }

        try {
          const initialEvents = await telemetryApi.getExecutionEvents(
            projectId,
            executionId,
            0
          );
          if (!cancelled && initialEvents?.length) {
            initialEvents.forEach((evt) => {
              if (!seenEventIdsRef.current.has(evt.event_id)) {
                seenEventIdsRef.current.add(evt.event_id);
              }
              if (evt.sequence > latestSequenceRef.current) {
                latestSequenceRef.current = evt.sequence;
              }
            });
            setEvents(initialEvents);
          }
        } catch {
          // Initial events may be empty
        }
      }
    }

    hydrate();

    return () => {
      cancelled = true;
    };
  }, [projectId, executionId, enabled]);

  // WebSocket lifecycle
  useEffect(() => {
    connectWebSocket();

    return () => {
      if (reconnectTimeoutRef.current) {
        window.clearTimeout(reconnectTimeoutRef.current);
      }
      if (pingIntervalRef.current) {
        window.clearInterval(pingIntervalRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
    };
  }, [connectWebSocket]);

  return {
    events,
    snapshot,
    isConnected,
    isStreaming,
    error,
    clearEvents,
    reconnect: connectWebSocket,
  };
}
