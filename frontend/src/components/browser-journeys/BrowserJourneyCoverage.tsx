import React from 'react';
import { ShieldCheck, CheckCircle2, CircleDashed } from 'lucide-react';
import { BrowserJourneyWorkflowResponse } from '../../types/browserJourney';

interface BrowserJourneyCoverageProps {
  workflowResult: BrowserJourneyWorkflowResponse | null;
}

export const BrowserJourneyCoverage: React.FC<BrowserJourneyCoverageProps> = ({
  workflowResult,
}) => {
  if (!workflowResult) {
    return null;
  }

  // Authoritative backend percentage - NEVER recalculate in frontend!
  const coveragePct = workflowResult.coverage_percentage;
  const coveredIds = workflowResult.covered_requirement_ids || [];
  const uncoveredIds = workflowResult.uncovered_requirement_ids || [];

  // Safe mapping lookup from validation artifact if available
  const validationArt = workflowResult.artifacts?.browser_journey_validation;
  const reqMap: Record<string, string[]> =
    validationArt?.coverage_report?.requirement_to_journeys || {};

  return (
    <div
      data-testid="journey-coverage-panel"
      style={{
        background: 'var(--bg-glass-card)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border-subtle)',
        padding: 'var(--space-md)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-md)',
      }}
    >
      {/* Header and Progress Bar */}
      <div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '0.4rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <ShieldCheck size={18} color="var(--accent-cyan)" />
            <span style={{ fontWeight: 600, fontSize: '0.92rem', color: 'var(--text-primary)' }}>
              Authoritative Requirement Coverage
            </span>
          </div>

          <div
            data-testid="coverage-percentage-badge"
            style={{
              fontSize: '1rem',
              fontWeight: 700,
              color:
                coveragePct !== null && coveragePct >= 70
                  ? 'var(--status-completed)'
                  : coveragePct !== null && coveragePct > 0
                  ? 'var(--accent-cyan)'
                  : 'var(--text-muted)',
            }}
          >
            {coveragePct !== null ? `${coveragePct.toFixed(1)}%` : 'N/A'}
          </div>
        </div>

        {/* Progress Bar */}
        <div
          role="progressbar"
          aria-valuenow={coveragePct ?? 0}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Requirement coverage progress"
          style={{
            width: '100%',
            height: '8px',
            background: 'var(--bg-surface-elevated)',
            borderRadius: '4px',
            overflow: 'hidden',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div
            data-testid="coverage-progress-bar"
            style={{
              width: `${Math.min(100, Math.max(0, coveragePct ?? 0))}%`,
              height: '100%',
              background:
                coveragePct !== null && coveragePct >= 70
                  ? 'var(--status-completed)'
                  : 'linear-gradient(90deg, var(--accent-primary), var(--accent-cyan))',
              transition: 'width 0.4s ease-in-out',
            }}
          />
        </div>
      </div>

      {/* Covered and Uncovered Columns */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: 'var(--space-md)',
        }}
      >
        {/* Covered Requirements */}
        <div
          data-testid="covered-requirements-list"
          style={{
            background: 'var(--bg-surface-elevated)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-subtle)',
            padding: '0.75rem',
            fontSize: '0.8rem',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              fontWeight: 600,
              color: 'var(--status-completed)',
              marginBottom: '0.5rem',
            }}
          >
            <CheckCircle2 size={15} />
            <span>Covered Requirements ({coveredIds.length})</span>
          </div>

          {coveredIds.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              {coveredIds.map((reqId) => {
                const mappedJourneys = reqMap[reqId] || [];
                return (
                  <div
                    key={reqId}
                    data-testid={`covered-req-${reqId}`}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '0.3rem 0.5rem',
                      borderRadius: '3px',
                      background: 'rgba(16, 185, 129, 0.08)',
                      border: '1px solid rgba(16, 185, 129, 0.2)',
                    }}
                  >
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{reqId}</span>
                    {mappedJourneys.length > 0 && (
                      <span
                        style={{
                          fontSize: '0.7rem',
                          color: 'var(--text-muted)',
                        }}
                      >
                        {mappedJourneys.length} journey(s)
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{ color: 'var(--text-dim)', fontStyle: 'italic' }}>
              No requirements covered.
            </div>
          )}
        </div>

        {/* Uncovered Requirements */}
        <div
          data-testid="uncovered-requirements-list"
          style={{
            background: 'var(--bg-surface-elevated)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-subtle)',
            padding: '0.75rem',
            fontSize: '0.8rem',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              fontWeight: 600,
              color: 'var(--text-muted)',
              marginBottom: '0.5rem',
            }}
          >
            <CircleDashed size={15} />
            <span>Uncovered Requirements ({uncoveredIds.length})</span>
          </div>

          {uncoveredIds.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              {uncoveredIds.map((reqId) => (
                <div
                  key={reqId}
                  data-testid={`uncovered-req-${reqId}`}
                  style={{
                    padding: '0.3rem 0.5rem',
                    borderRadius: '3px',
                    background: 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-secondary)',
                  }}
                >
                  <span style={{ fontWeight: 600 }}>{reqId}</span>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: 'var(--status-completed)', fontStyle: 'italic' }}>
              All active requirements are covered by validated journeys.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
