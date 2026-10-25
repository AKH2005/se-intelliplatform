import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { LiveExecutionBadge } from '../components/telemetry/LiveExecutionBadge';
import { LiveExecutionFeed } from '../components/telemetry/LiveExecutionFeed';
import { telemetryApi } from '../services/telemetryApi';
import { ExecutionEvent, ExecutionStateSnapshot } from '../types/telemetry';

describe('Phase 12 Real-Time Execution Telemetry', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  describe('LiveExecutionBadge', () => {
    it('renders RUNNING status with pulse indicator', () => {
      render(
        <LiveExecutionBadge
          status="RUNNING"
          isStreaming={true}
          totalEvents={5}
          latestEventType="WORKFLOW_STEP_STARTED"
        />
      );

      expect(screen.getByText('RUNNING')).toBeInTheDocument();
      expect(screen.getByText('(5 evts)')).toBeInTheDocument();
      expect(screen.getByText('[WORKFLOW_STEP_STARTED]')).toBeInTheDocument();
    });

    it('renders COMPLETED status accurately', () => {
      render(
        <LiveExecutionBadge
          status="COMPLETED"
          isStreaming={false}
          totalEvents={12}
        />
      );

      expect(screen.getByText('COMPLETED')).toBeInTheDocument();
      expect(screen.getByText('(12 evts)')).toBeInTheDocument();
    });

    it('renders FAILED and SAFETY_BLOCKED statuses', () => {
      const { rerender } = render(<LiveExecutionBadge status="FAILED" />);
      expect(screen.getByText('FAILED')).toBeInTheDocument();

      rerender(<LiveExecutionBadge status="SAFETY_BLOCKED" />);
      expect(screen.getByText('SAFETY_BLOCKED')).toBeInTheDocument();
    });
  });

  describe('TelemetryApiClient', () => {
    it('generates strictly project-isolated WebSocket URLs', () => {
      const wsUrl = telemetryApi.getWebSocketUrl('proj-alpha', 'exec-123', 5);
      expect(wsUrl).toContain('/projects/proj-alpha/telemetry/ws');
      expect(wsUrl).toContain('since_sequence=5');
      expect(wsUrl).toContain('execution_id=exec-123');
      expect(wsUrl.startsWith('ws://') || wsUrl.startsWith('wss://')).toBe(true);
    });
  });

  describe('LiveExecutionFeed Component', () => {
    it('hydrates initial REST events and renders monotonic sequences', async () => {
      const mockSnapshot: ExecutionStateSnapshot = {
        execution_id: 'exec-test-1',
        project_id: 'proj-123',
        execution_kind: 'WORKFLOW',
        status: 'RUNNING',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        latest_sequence: 2,
        total_events: 2,
        latest_event_type: 'WORKFLOW_STEP_COMPLETED',
        active_step: 'step-design',
        metadata: {},
      };

      const mockEvents: ExecutionEvent[] = [
        {
          event_id: 'evt-1',
          event_type: 'WORKFLOW_STARTED',
          timestamp: new Date().toISOString(),
          project_id: 'proj-123',
          execution_id: 'exec-test-1',
          execution_kind: 'WORKFLOW',
          source: 'WorkflowCoordinator',
          status: 'RUNNING',
          sequence: 1,
          payload: { steps: ['step-design'] },
          severity: 'INFO',
        },
        {
          event_id: 'evt-2',
          event_type: 'WORKFLOW_STEP_COMPLETED',
          timestamp: new Date().toISOString(),
          project_id: 'proj-123',
          execution_id: 'exec-test-1',
          execution_kind: 'WORKFLOW',
          source: 'WorkflowCoordinator',
          status: 'RUNNING',
          sequence: 2,
          payload: { step_id: 'step-design', success: true },
          severity: 'INFO',
        },
      ];

      vi.spyOn(telemetryApi, 'getExecutionStatus').mockResolvedValue(mockSnapshot);
      vi.spyOn(telemetryApi, 'getExecutionEvents').mockResolvedValue(mockEvents);

      render(
        <LiveExecutionFeed
          projectId="proj-123"
          executionId="exec-test-1"
          title="Workflow Live Telemetry"
        />
      );

      expect(screen.getByText('Workflow Live Telemetry')).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getByText('WORKFLOW_STARTED')).toBeInTheDocument();
        expect(screen.getByText('WORKFLOW_STEP_COMPLETED')).toBeInTheDocument();
      });

      expect(within(screen.getByTestId('telemetry-event-1')).getByText('#1')).toBeInTheDocument();
      expect(within(screen.getByTestId('telemetry-event-2')).getByText('#2')).toBeInTheDocument();

      // Safe payload inspection: clicking event expands payload in pre tag
      const eventRow = screen.getByTestId('telemetry-event-2');
      fireEvent.click(eventRow);

      expect(within(eventRow).getByText(/step-design/)).toBeInTheDocument();
    });

    it('displays empty/connecting message when no events exist', () => {
      vi.spyOn(telemetryApi, 'getExecutionStatus').mockRejectedValue(new Error('Not found'));
      vi.spyOn(telemetryApi, 'getExecutionEvents').mockResolvedValue([]);

      render(
        <LiveExecutionFeed
          projectId="proj-empty"
          title="Empty Telemetry"
        />
      );

      expect(screen.getByText(/Connecting to telemetry event stream...|Listening for live execution events.../)).toBeInTheDocument();
    });
  });
});
