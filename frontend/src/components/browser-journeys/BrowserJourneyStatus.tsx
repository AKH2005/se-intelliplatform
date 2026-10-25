import React from 'react';
import {
  CheckCircle2,
  XCircle,
  Loader2,
} from 'lucide-react';
import { BrowserJourneyWorkflowResponse } from '../../types/browserJourney';

interface BrowserJourneyStatusProps {
  workflowResult: BrowserJourneyWorkflowResponse | null;
  isGenerating?: boolean;
}

export const BrowserJourneyStatus: React.FC<BrowserJourneyStatusProps> = ({
  workflowResult,
  isGenerating = false,
}) => {
  if (isGenerating) {
    return (
      <div
        data-testid="workflow-status-generating"
        style={{
          padding: 'var(--space-md)',
          borderRadius: 'var(--radius-md)',
          background: 'rgba(56, 189, 248, 0.08)',
          border: '1px solid rgba(56, 189, 248, 0.35)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          fontSize: '0.88rem',
          color: 'var(--accent-cyan)',
        }}
      >
        <Loader2 size={20} className="animate-spin" />
        <div>
          <strong style={{ color: 'var(--text-primary)' }}>
            Executing Intelligent Browser Journey Pipeline...
          </strong>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
            Synthesizing candidate journeys, running deterministic validation, adapting to Playwright specs, and executing container tests.
          </div>
        </div>
      </div>
    );
  }

  if (!workflowResult) return null;

  const isCompleted = workflowResult.status === 'COMPLETED';

  function getStatusLabel(status: string) {
    switch (status) {
      case 'COMPLETED':
        return 'Workflow Completed Successfully';
      case 'WORKFLOW_GENERATION_FAILED':
        return 'Journey Generation Failed';
      case 'WORKFLOW_VALIDATION_FAILED':
        return 'Deterministic Validation Failed';
      case 'WORKFLOW_ADAPTATION_FAILED':
        return 'Deterministic Adaptation Failed';
      case 'WORKFLOW_BROWSER_EXECUTION_FAILED':
        return 'Browser Container Execution Failed';
      default:
        return `Status: ${status}`;
    }
  }

  return (
    <div
      data-testid="workflow-status-banner"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-sm)',
      }}
    >
      {/* Primary Banner */}
      <div
        style={{
          padding: '0.75rem var(--space-md)',
          borderRadius: 'var(--radius-md)',
          background: isCompleted ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
          border: `1px solid ${isCompleted ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '0.75rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          {isCompleted ? (
            <CheckCircle2 size={20} color="var(--status-completed)" />
          ) : (
            <XCircle size={20} color="var(--status-failed)" />
          )}
          <div>
            <div style={{ fontWeight: 700, fontSize: '0.92rem', color: 'var(--text-primary)' }}>
              {getStatusLabel(workflowResult.status)}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              Stage reached: <strong style={{ color: 'var(--text-primary)' }}>{workflowResult.stage_reached}</strong>
              {workflowResult.duration_seconds > 0 && ` • Duration: ${workflowResult.duration_seconds.toFixed(2)}s`}
            </div>
          </div>
        </div>

        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
          ID: {workflowResult.workflow_execution_id?.slice(0, 8)}...
        </div>
      </div>

      {/* Metrics Row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
          gap: '0.5rem',
        }}
      >
        {/* Metric: Journeys */}
        <div
          data-testid="metric-journey-count"
          style={{
            background: 'var(--bg-glass-card)',
            padding: '0.6rem 0.75rem',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600 }}>JOURNEYS</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {workflowResult.journey_count}
          </div>
        </div>

        {/* Metric: Coverage */}
        <div
          data-testid="metric-coverage"
          style={{
            background: 'var(--bg-glass-card)',
            padding: '0.6rem 0.75rem',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600 }}>REQ COVERAGE</div>
          <div
            style={{
              fontSize: '1.1rem',
              fontWeight: 700,
              color:
                workflowResult.coverage_percentage !== null && workflowResult.coverage_percentage >= 70
                  ? 'var(--status-completed)'
                  : 'var(--accent-cyan)',
            }}
          >
            {workflowResult.coverage_percentage !== null
              ? `${workflowResult.coverage_percentage.toFixed(1)}%`
              : 'N/A'}
          </div>
        </div>

        {/* Metric: Validation */}
        <div
          data-testid="metric-validation"
          style={{
            background: 'var(--bg-glass-card)',
            padding: '0.6rem 0.75rem',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600 }}>VALIDATION</div>
          <div
            style={{
              fontSize: '0.85rem',
              fontWeight: 700,
              color: workflowResult.validation_passed ? 'var(--status-completed)' : 'var(--status-failed)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.25rem',
              marginTop: '0.2rem',
            }}
          >
            {workflowResult.validation_passed ? (
              <>
                <CheckCircle2 size={14} /> Passed
              </>
            ) : (
              <>
                <XCircle size={14} /> Failed
              </>
            )}
          </div>
        </div>

        {/* Metric: Browser Execution */}
        <div
          data-testid="metric-browser-tests"
          style={{
            background: 'var(--bg-glass-card)',
            padding: '0.6rem 0.75rem',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600 }}>BROWSER TESTS</div>
          <div
            style={{
              fontSize: '0.85rem',
              fontWeight: 700,
              marginTop: '0.2rem',
              color: !workflowResult.browser_tests_executed
                ? 'var(--text-muted)'
                : workflowResult.browser_tests_passed
                ? 'var(--status-completed)'
                : 'var(--status-failed)',
            }}
          >
            {!workflowResult.browser_tests_executed
              ? 'Not Executed'
              : workflowResult.browser_tests_passed
              ? 'Passed'
              : 'Failed'}
          </div>
        </div>
      </div>
    </div>
  );
};
