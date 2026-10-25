import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { BrowserJourneyWorkflowResponse } from '../../types/browserJourney';

interface BrowserJourneyFailureProps {
  workflowResult: BrowserJourneyWorkflowResponse | null;
}

export const BrowserJourneyFailure: React.FC<BrowserJourneyFailureProps> = ({
  workflowResult,
}) => {
  if (!workflowResult) return null;

  const hasFailed =
    workflowResult.status !== 'COMPLETED' ||
    workflowResult.browser_tests_passed === false ||
    Boolean(workflowResult.failure_reason) ||
    Boolean(workflowResult.failure_diagnosis);

  if (!hasFailed) return null;

  const diagnosis = workflowResult.failure_diagnosis;
  const failureReason = workflowResult.failure_reason;

  return (
    <div
      data-testid="journey-failure-panel"
      style={{
        background: 'rgba(239, 68, 68, 0.05)',
        border: '1px solid rgba(239, 68, 68, 0.3)',
        borderRadius: 'var(--radius-md)',
        padding: 'var(--space-md)',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--status-failed)' }}>
        <AlertTriangle size={18} />
        <span style={{ fontWeight: 700, fontSize: '0.92rem' }}>
          Workflow Diagnostics & Root Cause Analysis
        </span>
      </div>

      {/* Primary Failure Reason */}
      {failureReason && (
        <div
          data-testid="failure-reason-text"
          style={{
            background: 'var(--bg-surface-elevated)',
            border: '1px solid rgba(239, 68, 68, 0.2)',
            borderRadius: 'var(--radius-sm)',
            padding: '0.6rem 0.75rem',
            fontSize: '0.82rem',
            color: 'var(--text-primary)',
            lineHeight: 1.4,
          }}
        >
          <strong style={{ color: 'var(--status-failed)' }}>Error: </strong>
          {failureReason}
        </div>
      )}

      {/* Structured Diagnosis from FailureAnalysisAgent */}
      {diagnosis && (
        <div
          data-testid="structured-failure-diagnosis"
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem',
            fontSize: '0.8rem',
            background: 'var(--bg-surface-elevated)',
            padding: '0.75rem',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          {diagnosis.summary && (
            <div>
              <span style={{ fontWeight: 600, color: 'var(--text-muted)' }}>DIAGNOSIS SUMMARY:</span>
              <div style={{ marginTop: '0.2rem', color: 'var(--text-primary)' }}>
                {diagnosis.summary}
              </div>
            </div>
          )}

          {diagnosis.likely_cause && (
            <div>
              <span style={{ fontWeight: 600, color: 'var(--text-muted)' }}>LIKELY CAUSE:</span>
              <div style={{ marginTop: '0.2rem', color: 'var(--text-secondary)' }}>
                {diagnosis.likely_cause}
              </div>
            </div>
          )}

          {diagnosis.affected_journey_id && (
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <div>
                <span style={{ fontWeight: 600, color: 'var(--text-muted)' }}>AFFECTED JOURNEY: </span>
                <span style={{ color: 'var(--text-primary)', fontFamily: 'monospace' }}>
                  {diagnosis.affected_journey_id}
                </span>
              </div>
              {diagnosis.affected_step_number !== undefined && (
                <div>
                  <span style={{ fontWeight: 600, color: 'var(--text-muted)' }}>STEP: </span>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 700 }}>
                    #{diagnosis.affected_step_number}
                  </span>
                </div>
              )}
            </div>
          )}

          {Array.isArray(diagnosis.evidence) && diagnosis.evidence.length > 0 && (
            <div>
              <span style={{ fontWeight: 600, color: 'var(--text-muted)' }}>OBSERVED EVIDENCE:</span>
              <ul style={{ margin: '0.25rem 0 0 0', paddingLeft: '1.25rem', color: 'var(--text-secondary)' }}>
                {diagnosis.evidence.map((ev: any, idx: number) => (
                  <li key={idx}>{String(ev)}</li>
                ))}
              </ul>
            </div>
          )}

          {diagnosis.remediation_hint && (
            <div
              style={{
                marginTop: '0.25rem',
                padding: '0.4rem 0.6rem',
                borderRadius: '3px',
                background: 'rgba(99, 102, 241, 0.08)',
                border: '1px solid rgba(99, 102, 241, 0.25)',
                color: 'var(--accent-primary)',
              }}
            >
              <strong>Remediation Recommendation: </strong>
              {diagnosis.remediation_hint}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
