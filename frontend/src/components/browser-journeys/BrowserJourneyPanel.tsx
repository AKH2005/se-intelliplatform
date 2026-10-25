import React from 'react';
import { Card, CardHeader, CardBody } from '../common/Card';
import { CapabilityBadge } from '../common/CapabilityBadge';
import { Button } from '../common/Button';
import {
  Compass,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  XCircle,
  Loader2,
} from 'lucide-react';
import { BrowserJourneyWorkflowResponse } from '../../types/browserJourney';

interface BrowserJourneyPanelProps {
  workflowResult: BrowserJourneyWorkflowResponse | null;
  onGenerate: () => void;
  onViewResults?: () => void;
  isGenerating?: boolean;
}

export const BrowserJourneyPanel: React.FC<BrowserJourneyPanelProps> = ({
  workflowResult,
  onGenerate,
  onViewResults,
  isGenerating = false,
}) => {
  return (
    <div data-testid="browser-journey-dev-panel">
      <Card
        style={{
          background: 'var(--bg-glass-card)',
          border: '1px solid var(--border-subtle)',
        }}
      >
      <CardHeader>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Compass size={18} color="var(--accent-cyan)" />
          <span style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
            Intelligent Browser Journeys
          </span>
        </div>
        <CapabilityBadge status="IMPLEMENTED" size="sm" />
      </CardHeader>
      <CardBody>
        <p
          style={{
            margin: '0 0 var(--space-md) 0',
            fontSize: '0.85rem',
            color: 'var(--text-secondary)',
            lineHeight: 1.5,
          }}
        >
          Synthesizes and executes deterministic multi-step user journeys from canonical requirements
          and active application routes.
        </p>

        {/* Latest Execution Summary if present */}
        {workflowResult ? (
          <div
            data-testid="dev-panel-latest-summary"
            style={{
              padding: '0.75rem',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-subtle)',
              marginBottom: 'var(--space-md)',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.35rem',
              fontSize: '0.8rem',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                {workflowResult.status === 'COMPLETED' ? (
                  <CheckCircle2 size={15} color="var(--status-completed)" />
                ) : (
                  <XCircle size={15} color="var(--status-failed)" />
                )}
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                  Latest Run: {workflowResult.status}
                </span>
              </div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                {workflowResult.duration_seconds > 0
                  ? `${workflowResult.duration_seconds.toFixed(1)}s`
                  : ''}
              </span>
            </div>

            <div
              style={{
                display: 'flex',
                gap: '1rem',
                fontSize: '0.75rem',
                color: 'var(--text-secondary)',
                marginTop: '0.2rem',
              }}
            >
              <span>
                <strong>{workflowResult.journey_count}</strong> journeys
              </span>
              <span>
                Coverage:{' '}
                <strong
                  style={{
                    color:
                      workflowResult.coverage_percentage && workflowResult.coverage_percentage >= 70
                        ? 'var(--status-completed)'
                        : 'var(--accent-cyan)',
                  }}
                >
                  {workflowResult.coverage_percentage !== null
                    ? `${workflowResult.coverage_percentage.toFixed(0)}%`
                    : 'N/A'}
                </strong>
              </span>
              {workflowResult.browser_tests_executed && (
                <span>
                  Browser Tests:{' '}
                  <strong
                    style={{
                      color: workflowResult.browser_tests_passed
                        ? 'var(--status-completed)'
                        : 'var(--status-failed)',
                    }}
                  >
                    {workflowResult.browser_tests_passed ? 'Passed' : 'Failed'}
                  </strong>
                </span>
              )}
            </div>
          </div>
        ) : (
          <div
            data-testid="dev-panel-no-runs"
            style={{
              padding: '0.65rem 0.75rem',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--bg-surface-elevated)',
              border: '1px dashed var(--border-subtle)',
              marginBottom: 'var(--space-md)',
              fontSize: '0.78rem',
              color: 'var(--text-muted)',
            }}
          >
            No journey runs recorded for this project yet.
          </div>
        )}

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <Button
            data-testid="dev-panel-generate-btn"
            variant="primary"
            size="sm"
            onClick={onGenerate}
            disabled={isGenerating}
            icon={
              isGenerating ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <Sparkles size={14} />
              )
            }
          >
            {isGenerating ? 'Generating Journeys...' : 'Generate Journeys'}
          </Button>

          {onViewResults && (
            <Button
              data-testid="dev-panel-view-results-btn"
              variant="secondary"
              size="sm"
              onClick={onViewResults}
              icon={<ArrowRight size={14} />}
            >
              View in Testing Workspace
            </Button>
          )}
        </div>
      </CardBody>
    </Card>
    </div>
  );
};
