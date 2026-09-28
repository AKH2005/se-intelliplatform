import React from 'react';
import { RequirementAnalysisOutput } from '../../types/artifacts';
import { Badge } from '../common/Badge';

interface RequirementAnalysisArtifactProps {
  artifact: RequirementAnalysisOutput;
}

export const RequirementAnalysisArtifact: React.FC<RequirementAnalysisArtifactProps> = ({
  artifact,
}) => {
  const {
    summary,
    ambiguities,
    conflicts,
    completeness_score,
    active_requirements_count,
    total_requirements_count,
  } = artifact;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Summary */}
      <div>
        <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
          Analysis Summary
        </h4>
        <p style={{ fontSize: '0.875rem', lineHeight: 1.6, color: 'var(--text-primary)' }}>
          {summary}
        </p>
      </div>

      {/* Metrics Header */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '0.75rem',
        }}
      >
        <div
          style={{
            background: 'var(--bg-surface)',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Deterministic Completeness</div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
            {completeness_score.toFixed(1)}%
          </div>
        </div>

        <div
          style={{
            background: 'var(--bg-surface)',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Evaluated Requirements</div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {active_requirements_count} / {total_requirements_count}
          </div>
        </div>
      </div>

      {/* Ambiguities */}
      {ambiguities && ambiguities.length > 0 && (
        <div>
          <h4 style={{ fontSize: '0.9rem', marginBottom: '0.6rem', color: 'var(--text-secondary)' }}>
            Detected Ambiguities ({ambiguities.length})
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {ambiguities.map((item, idx) => (
              <div
                key={idx}
                style={{
                  background: 'var(--bg-surface)',
                  padding: '0.85rem',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.85rem' }}>
                    {item.issue}
                  </span>
                  <Badge variant={item.severity}>{item.severity}</Badge>
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                  {item.explanation}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)' }}>
                  Suggested clarification: {item.suggested_clarification}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Conflicts */}
      {conflicts && conflicts.length > 0 && (
        <div>
          <h4 style={{ fontSize: '0.9rem', marginBottom: '0.6rem', color: 'var(--text-secondary)' }}>
            Requirement Conflicts ({conflicts.length})
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {conflicts.map((item, idx) => (
              <div
                key={idx}
                style={{
                  background: 'var(--bg-surface)',
                  padding: '0.85rem',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                  <span style={{ fontWeight: 600, color: '#f87171', fontSize: '0.85rem' }}>
                    {item.issue}
                  </span>
                  <Badge variant={item.severity}>{item.severity}</Badge>
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  {item.explanation}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
