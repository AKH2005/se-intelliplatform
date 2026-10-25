import React from 'react';
import { ChevronRight, Layers, FileCheck } from 'lucide-react';
import { BrowserJourney } from '../../types/browserJourney';

interface BrowserJourneyListProps {
  journeys: BrowserJourney[];
  selectedJourneyId?: string | null;
  onSelectJourney: (journey: BrowserJourney) => void;
}

export const BrowserJourneyList: React.FC<BrowserJourneyListProps> = ({
  journeys,
  selectedJourneyId,
  onSelectJourney,
}) => {
  if (!journeys || journeys.length === 0) {
    return (
      <div
        data-testid="journey-list-empty"
        style={{
          padding: 'var(--space-md)',
          textAlign: 'center',
          color: 'var(--text-muted)',
          fontSize: '0.85rem',
        }}
      >
        No candidate journeys found in workflow artifacts.
      </div>
    );
  }

  return (
    <div
      data-testid="journey-list"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '0.4rem',
      }}
    >
      {journeys.map((j) => {
        const isSelected = selectedJourneyId === j.journey_id;
        return (
          <div
            key={j.journey_id}
            data-testid={`journey-card-${j.journey_id}`}
            role="button"
            tabIndex={0}
            aria-selected={isSelected}
            onClick={() => onSelectJourney(j)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onSelectJourney(j);
              }
            }}
            style={{
              padding: '0.65rem 0.85rem',
              borderRadius: 'var(--radius-sm)',
              background: isSelected
                ? 'rgba(56, 189, 248, 0.1)'
                : 'var(--bg-surface-elevated)',
              border: `1px solid ${
                isSelected ? 'var(--accent-cyan)' : 'var(--border-subtle)'
              }`,
              cursor: 'pointer',
              transition: 'border-color 0.15s, background-color 0.15s',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '0.5rem',
            }}
          >
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  flexWrap: 'wrap',
                }}
              >
                <span
                  style={{
                    fontWeight: 600,
                    fontSize: '0.85rem',
                    color: isSelected ? 'var(--accent-cyan)' : 'var(--text-primary)',
                  }}
                >
                  {j.title}
                </span>
                <span
                  style={{
                    fontSize: '0.68rem',
                    padding: '0.1rem 0.35rem',
                    borderRadius: '3px',
                    background: 'rgba(99, 102, 241, 0.1)',
                    color: 'var(--accent-primary)',
                    fontWeight: 600,
                  }}
                >
                  {j.category}
                </span>
              </div>

              <div
                style={{
                  fontSize: '0.74rem',
                  color: 'var(--text-secondary)',
                  marginTop: '0.2rem',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {j.description}
              </div>

              {/* Badges footer */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.65rem',
                  marginTop: '0.35rem',
                  fontSize: '0.7rem',
                  color: 'var(--text-muted)',
                }}
              >
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <Layers size={12} />
                  {j.steps?.length || 0} steps
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <FileCheck size={12} />
                  {j.requirement_ids?.length || 0} reqs
                </span>
                <span>{j.routes?.length || 0} routes</span>
              </div>
            </div>

            <ChevronRight
              size={16}
              color={isSelected ? 'var(--accent-cyan)' : 'var(--text-dim)'}
              style={{ flexShrink: 0 }}
            />
          </div>
        );
      })}
    </div>
  );
};
