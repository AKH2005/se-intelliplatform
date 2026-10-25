import React from 'react';
import {
  Compass,
  MousePointer,
  FileEdit,
  CheckCircle,
  Eye,
  Link as LinkIcon,
  Clock,
  HelpCircle,
  ListFilter,
} from 'lucide-react';
import { BrowserJourneyStep, BrowserActionType } from '../../types/browserJourney';

interface BrowserJourneyStepsProps {
  steps: BrowserJourneyStep[];
}

function getActionIcon(action: BrowserActionType | string) {
  switch (action) {
    case 'NAVIGATE':
      return <Compass size={16} color="var(--accent-cyan)" />;
    case 'CLICK':
      return <MousePointer size={16} color="var(--accent-primary)" />;
    case 'FILL':
      return <FileEdit size={16} color="var(--sdlc-design)" />;
    case 'SELECT':
      return <ListFilter size={16} color="var(--sdlc-design)" />;
    case 'ASSERT_TEXT':
      return <CheckCircle size={16} color="var(--status-completed)" />;
    case 'ASSERT_VISIBLE':
      return <Eye size={16} color="var(--status-completed)" />;
    case 'ASSERT_URL':
      return <LinkIcon size={16} color="var(--accent-cyan)" />;
    case 'WAIT':
      return <Clock size={16} color="var(--text-muted)" />;
    default:
      return <HelpCircle size={16} color="var(--text-dim)" />;
  }
}

export const BrowserJourneySteps: React.FC<BrowserJourneyStepsProps> = ({ steps }) => {
  if (!steps || steps.length === 0) {
    return (
      <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontStyle: 'italic' }}>
        No steps defined for this journey.
      </div>
    );
  }

  return (
    <div
      data-testid="journey-steps-timeline"
      style={{
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        paddingLeft: '1.25rem',
      }}
    >
      {/* Vertical connection line */}
      <div
        style={{
          position: 'absolute',
          top: '12px',
          bottom: '12px',
          left: '11px',
          width: '2px',
          background: 'var(--border-subtle)',
          zIndex: 1,
        }}
      />

      {steps.map((step, idx) => {
        const isLast = idx === steps.length - 1;
        return (
          <div
            key={`step-${step.step_number || idx + 1}`}
            data-testid={`journey-step-${step.step_number || idx + 1}`}
            style={{
              position: 'relative',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.75rem',
              paddingBottom: isLast ? 0 : '1.25rem',
              zIndex: 2,
            }}
          >
            {/* Step Icon Badge */}
            <div
              style={{
                width: 24,
                height: 24,
                borderRadius: '50%',
                background: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-subtle)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                marginTop: '2px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
              }}
            >
              {getActionIcon(step.action)}
            </div>

            {/* Step Body */}
            <div
              style={{
                flex: 1,
                background: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.5rem 0.75rem',
                fontSize: '0.82rem',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: '0.2rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                    Step {step.step_number || idx + 1}:
                  </span>
                  <span
                    style={{
                      fontSize: '0.7rem',
                      fontWeight: 700,
                      padding: '0.1rem 0.35rem',
                      borderRadius: '3px',
                      background: 'rgba(56, 189, 248, 0.1)',
                      color: 'var(--accent-cyan)',
                      textTransform: 'uppercase',
                    }}
                  >
                    {step.action}
                  </span>
                </div>
                {step.timeout_ms && (
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                    {step.timeout_ms}ms
                  </span>
                )}
              </div>

              {/* Semantic details - Escaped text only */}
              <div style={{ color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                {step.target_role && (
                  <span>
                    Role: <strong style={{ color: 'var(--text-primary)' }}>{step.target_role}</strong>{' '}
                  </span>
                )}
                {step.target_label && (
                  <span>
                    Label: <strong style={{ color: 'var(--text-primary)' }}>"{step.target_label}"</strong>{' '}
                  </span>
                )}
                {step.value && (
                  <span>
                    Value: <strong style={{ color: 'var(--text-primary)' }}>"{step.value}"</strong>{' '}
                  </span>
                )}
                {(step.assertion_type || step.expected_value) && (
                  <span>
                    Assert {step.assertion_type || 'Expected'}:{' '}
                    <strong style={{ color: 'var(--status-completed)' }}>
                      "{step.expected_value ?? 'true'}"
                    </strong>{' '}
                  </span>
                )}
                {step.wait_condition && (
                  <span>
                    Wait: <em>{step.wait_condition}</em>
                  </span>
                )}
              </div>

              {/* Candidate selector hint if present */}
              {step.target_selector_candidate && (
                <div
                  style={{
                    marginTop: '0.35rem',
                    fontSize: '0.72rem',
                    fontFamily: 'monospace',
                    color: 'var(--text-muted)',
                    background: 'rgba(0,0,0,0.15)',
                    padding: '0.15rem 0.4rem',
                    borderRadius: '3px',
                    display: 'inline-block',
                  }}
                >
                  Target Selector: {step.target_selector_candidate}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
