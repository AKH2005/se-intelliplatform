import React from 'react';
import {
  Compass,
  CheckCircle2,
  Layers,
} from 'lucide-react';
import { BrowserJourney } from '../../types/browserJourney';
import { BrowserJourneySteps } from './BrowserJourneySteps';

interface BrowserJourneyDetailProps {
  journey: BrowserJourney | null;
  executionStatus?: string | null;
}

function getPriorityColor(priority: string) {
  switch (priority.toUpperCase()) {
    case 'CRITICAL':
      return 'var(--status-failed)';
    case 'HIGH':
      return 'var(--accent-primary)';
    case 'MEDIUM':
      return 'var(--sdlc-design)';
    default:
      return 'var(--text-muted)';
  }
}

export const BrowserJourneyDetail: React.FC<BrowserJourneyDetailProps> = ({
  journey,
  executionStatus,
}) => {
  if (!journey) {
    return (
      <div
        data-testid="journey-detail-empty"
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 'var(--space-xl)',
          color: 'var(--text-dim)',
          textAlign: 'center',
          minHeight: '280px',
        }}
      >
        <Compass size={32} style={{ marginBottom: '0.75rem', opacity: 0.4 }} />
        <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>Select a Journey</div>
        <div style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>
          Select any journey from the list to inspect steps, assertions, and requirement linkages.
        </div>
      </div>
    );
  }

  return (
    <div
      data-testid="journey-detail-panel"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-md)',
      }}
    >
      {/* Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem', flexWrap: 'wrap' }}>
          <h3
            data-testid="journey-detail-title"
            style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}
          >
            {journey.title}
          </h3>
          <div style={{ display: 'flex', gap: '0.35rem', alignItems: 'center' }}>
            <span
              style={{
                fontSize: '0.7rem',
                fontWeight: 700,
                padding: '0.15rem 0.5rem',
                borderRadius: 'var(--radius-sm)',
                background: 'rgba(99, 102, 241, 0.1)',
                color: 'var(--accent-primary)',
              }}
            >
              {journey.category}
            </span>
            <span
              style={{
                fontSize: '0.7rem',
                fontWeight: 700,
                padding: '0.15rem 0.5rem',
                borderRadius: 'var(--radius-sm)',
                border: `1px solid ${getPriorityColor(journey.priority)}`,
                color: getPriorityColor(journey.priority),
              }}
            >
              {journey.priority}
            </span>
            {executionStatus && (
              <span
                data-testid="journey-detail-execution-status"
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  padding: '0.15rem 0.5rem',
                  borderRadius: 'var(--radius-sm)',
                  background:
                    executionStatus === 'PASSED'
                      ? 'rgba(16, 185, 129, 0.12)'
                      : 'rgba(239, 68, 68, 0.12)',
                  color:
                    executionStatus === 'PASSED'
                      ? 'var(--status-completed)'
                      : 'var(--status-failed)',
                }}
              >
                {executionStatus}
              </span>
            )}
          </div>
        </div>

        <p
          data-testid="journey-detail-description"
          style={{
            margin: '0.4rem 0 0 0',
            fontSize: '0.85rem',
            color: 'var(--text-secondary)',
            lineHeight: 1.5,
          }}
        >
          {journey.description}
        </p>
      </div>

      {/* Metadata Badges Strip */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '0.5rem',
          background: 'var(--bg-surface-elevated)',
          padding: '0.75rem',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-subtle)',
          fontSize: '0.8rem',
        }}
      >
        {/* Requirements */}
        <div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600 }}>
            LINKED REQUIREMENTS
          </div>
          <div
            data-testid="journey-detail-requirements"
            style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem', marginTop: '0.25rem' }}
          >
            {journey.requirement_ids && journey.requirement_ids.length > 0 ? (
              journey.requirement_ids.map((reqId) => (
                <span
                  key={reqId}
                  style={{
                    fontSize: '0.72rem',
                    padding: '0.1rem 0.4rem',
                    borderRadius: '3px',
                    background: 'rgba(16, 185, 129, 0.12)',
                    color: 'var(--status-completed)',
                    fontWeight: 600,
                  }}
                >
                  {reqId}
                </span>
              ))
            ) : (
              <span style={{ color: 'var(--text-dim)' }}>None</span>
            )}
          </div>
        </div>

        {/* Routes */}
        <div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600 }}>
            TARGET ROUTES
          </div>
          <div
            data-testid="journey-detail-routes"
            style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem', marginTop: '0.25rem' }}
          >
            {journey.routes && journey.routes.length > 0 ? (
              journey.routes.map((route) => (
                <span
                  key={route}
                  style={{
                    fontSize: '0.72rem',
                    padding: '0.1rem 0.4rem',
                    borderRadius: '3px',
                    background: 'rgba(56, 189, 248, 0.12)',
                    color: 'var(--accent-cyan)',
                    fontFamily: 'monospace',
                  }}
                >
                  {route}
                </span>
              ))
            ) : (
              <span style={{ color: 'var(--text-dim)' }}>None</span>
            )}
          </div>
        </div>
      </div>

      {/* Preconditions */}
      {journey.preconditions && journey.preconditions.length > 0 && (
        <div style={{ fontSize: '0.8rem' }}>
          <div style={{ fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
            PRECONDITIONS
          </div>
          <ul
            data-testid="journey-detail-preconditions"
            style={{ margin: 0, paddingLeft: '1.25rem', color: 'var(--text-secondary)' }}
          >
            {journey.preconditions.map((pre, i) => (
              <li key={i}>{pre}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Steps Timeline */}
      <div>
        <div
          style={{
            fontWeight: 600,
            fontSize: '0.85rem',
            color: 'var(--text-primary)',
            marginBottom: '0.75rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
          }}
        >
          <Layers size={15} color="var(--accent-cyan)" />
          <span>Execution Steps ({journey.steps?.length || 0})</span>
        </div>
        <BrowserJourneySteps steps={journey.steps || []} />
      </div>

      {/* Expected Outcomes */}
      {journey.expected_outcomes && journey.expected_outcomes.length > 0 && (
        <div
          style={{
            marginTop: '0.5rem',
            padding: '0.75rem',
            borderRadius: 'var(--radius-sm)',
            background: 'rgba(16, 185, 129, 0.05)',
            border: '1px solid rgba(16, 185, 129, 0.2)',
            fontSize: '0.8rem',
          }}
        >
          <div
            style={{
              fontWeight: 600,
              color: 'var(--status-completed)',
              marginBottom: '0.25rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
            }}
          >
            <CheckCircle2 size={14} />
            <span>Expected Outcomes</span>
          </div>
          <ul
            data-testid="journey-detail-outcomes"
            style={{ margin: 0, paddingLeft: '1.25rem', color: 'var(--text-secondary)' }}
          >
            {journey.expected_outcomes.map((outcome, i) => (
              <li key={i}>{outcome}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
