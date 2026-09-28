import React from 'react';
import { ArchitectureRecommendationOutput } from '../../types/artifacts';
import { Badge } from '../common/Badge';

interface ArchitectureArtifactProps {
  artifact: ArchitectureRecommendationOutput;
}

export const ArchitectureArtifact: React.FC<ArchitectureArtifactProps> = ({ artifact }) => {
  const {
    summary,
    architecture_styles,
    components,
    technologies,
    trade_offs,
  } = artifact;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* High-level Summary */}
      <div>
        <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
          Architecture Overview
        </h4>
        <p style={{ fontSize: '0.875rem', lineHeight: 1.6, color: 'var(--text-primary)' }}>
          {summary}
        </p>
      </div>

      {/* Recommended Architecture Styles */}
      {architecture_styles && architecture_styles.length > 0 && (
        <div>
          <h4 style={{ fontSize: '0.9rem', marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
            Recommended Architectural Styles
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {architecture_styles.map((styleRec, idx) => (
              <div
                key={idx}
                style={{
                  background: 'var(--bg-surface)',
                  padding: '1rem',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
                  <Badge variant="in-progress">{styleRec.style}</Badge>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{styleRec.rationale}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Logical Components */}
      {components && components.length > 0 && (
        <div>
          <h4 style={{ fontSize: '0.9rem', marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
            Recommended Logical Components ({components.length})
          </h4>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
              gap: '0.75rem',
            }}
          >
            {components.map((comp, idx) => (
              <div
                key={idx}
                style={{
                  background: 'var(--bg-surface)',
                  padding: '0.85rem 1rem',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                  {comp.name}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                  {comp.responsibility}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Reason: {comp.reason}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Technologies */}
      {technologies && technologies.length > 0 && (
        <div>
          <h4 style={{ fontSize: '0.9rem', marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
            Candidate Technology Stack
          </h4>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
              gap: '0.75rem',
            }}
          >
            {technologies.map((tech, idx) => (
              <div
                key={idx}
                style={{
                  background: 'var(--bg-surface)',
                  padding: '0.85rem 1rem',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{tech.technology}</span>
                  <Badge variant="draft">{tech.category}</Badge>
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
                  {tech.reason}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#f59e0b' }}>
                  Trade-off: {tech.trade_off}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Trade-Off Analyses */}
      {trade_offs && trade_offs.length > 0 && (
        <div>
          <h4 style={{ fontSize: '0.9rem', marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
            Architectural Trade-Off Analysis
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {trade_offs.map((item, idx) => (
              <div
                key={idx}
                style={{
                  background: 'var(--bg-surface)',
                  padding: '1rem',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                  {item.decision_area}: Favors {item.recommended_option}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                  Alternative considered: {item.alternative} ({item.alternative_tradeoff})
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', fontSize: '0.775rem' }}>
                  <div>
                    <span style={{ color: '#10b981', fontWeight: 600 }}>Advantages:</span>
                    <ul style={{ paddingLeft: '1.2rem', marginTop: '0.2rem' }}>
                      {item.advantages.map((adv, aIdx) => (
                        <li key={aIdx}>{adv}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <span style={{ color: '#f87171', fontWeight: 600 }}>Disadvantages / Risks:</span>
                    <ul style={{ paddingLeft: '1.2rem', marginTop: '0.2rem' }}>
                      {item.disadvantages.map((dis, dIdx) => (
                        <li key={dIdx}>{dis}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
