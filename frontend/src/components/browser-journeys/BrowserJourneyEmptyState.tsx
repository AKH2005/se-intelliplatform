import React from 'react';
import { Compass, Sparkles, Loader2 } from 'lucide-react';
import { Button } from '../common/Button';

interface BrowserJourneyEmptyStateProps {
  onGenerate: () => void;
  isGenerating?: boolean;
}

export const BrowserJourneyEmptyState: React.FC<BrowserJourneyEmptyStateProps> = ({
  onGenerate,
  isGenerating = false,
}) => {
  return (
    <div
      data-testid="journey-empty-state"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '3rem 2rem',
        borderRadius: 'var(--radius-md)',
        background: 'var(--bg-glass-card)',
        border: '1px dashed var(--border-subtle)',
        textAlign: 'center',
        gap: '1rem',
      }}
    >
      <div
        style={{
          width: 52,
          height: 52,
          borderRadius: '50%',
          background: 'rgba(56, 189, 248, 0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--accent-cyan)',
        }}
      >
        <Compass size={28} />
      </div>

      <div style={{ maxWidth: '440px' }}>
        <h3
          style={{
            margin: 0,
            fontSize: '1.1rem',
            fontWeight: 700,
            color: 'var(--text-primary)',
          }}
        >
          No Browser Journeys Generated Yet
        </h3>
        <p
          style={{
            margin: '0.4rem 0 0 0',
            fontSize: '0.85rem',
            color: 'var(--text-secondary)',
            lineHeight: 1.5,
          }}
        >
          Synthesize deterministic, multi-step browser user journeys directly from your project's
          requirements and application routes.
        </p>
      </div>

      <Button
        data-testid="empty-generate-journeys-btn"
        variant="primary"
        onClick={onGenerate}
        disabled={isGenerating}
        icon={
          isGenerating ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <Sparkles size={16} />
          )
        }
      >
        {isGenerating ? 'Generating Journeys...' : 'Generate Browser Journeys'}
      </Button>
    </div>
  );
};
