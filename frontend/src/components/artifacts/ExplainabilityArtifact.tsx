import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { ExplainabilityOutput } from '../../types/artifacts';
import { Badge } from '../common/Badge';

interface ExplainabilityArtifactProps {
  artifact: ExplainabilityOutput;
}

export const ExplainabilityArtifact: React.FC<ExplainabilityArtifactProps> = ({ artifact }) => {
  const { summary, insights, metrics, limitations } = artifact;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Summary */}
      <div>
        <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
          Executive Synthesis
        </h4>
        <p style={{ fontSize: '0.875rem', lineHeight: 1.6, color: 'var(--text-primary)' }}>
          {summary}
        </p>
      </div>

      {/* Metrics Header */}
      {metrics && (
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
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Total Insights</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--accent-primary)' }}>
              {metrics.total_insights}
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
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Analyzed Agents</div>
            <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '0.25rem' }}>
              {metrics.analyzed_agents?.join(', ') || 'None'}
            </div>
          </div>
        </div>
      )}

      {/* Insights Collection */}
      <div>
        <h4 style={{ fontSize: '0.9rem', marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
          Grounded Engineering Insights ({insights.length})
        </h4>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {insights.map((insight) => (
            <div
              key={insight.insight_id}
              style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '1.25rem',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: '0.5rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Badge variant="draft">{insight.insight_id}</Badge>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                    {insight.title}
                  </span>
                </div>
                <Badge variant="in-progress">{insight.category}</Badge>
              </div>

              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                {insight.explanation}
              </div>

              {/* Source References */}
              {insight.source_references && insight.source_references.length > 0 && (
                <div style={{ marginBottom: '0.75rem' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                    Grounded Source References:
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {insight.source_references.map((ref, rIdx) => (
                      <div
                        key={rIdx}
                        style={{
                          background: 'rgba(0, 0, 0, 0.25)',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: 'var(--radius-sm)',
                          padding: '0.25rem 0.55rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.4rem',
                          fontSize: '0.75rem',
                        }}
                      >
                        <Badge variant={ref.claim_type}>{ref.claim_type}</Badge>
                        <span style={{ color: 'var(--text-muted)' }}>{ref.agent_id}</span>
                        {ref.source_entity_id && (
                          <span style={{ color: 'var(--text-primary)' }}>({ref.source_entity_id})</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Suggested Actions */}
              {insight.suggested_actions && insight.suggested_actions.length > 0 && (
                <div
                  style={{
                    background: 'rgba(99, 102, 241, 0.08)',
                    border: '1px solid rgba(99, 102, 241, 0.2)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '0.6rem 0.8rem',
                    fontSize: '0.8rem',
                  }}
                >
                  <div style={{ color: 'var(--accent-primary)', fontWeight: 600, marginBottom: '0.25rem' }}>
                    Suggested Actions:
                  </div>
                  <ul style={{ paddingLeft: '1.2rem', color: 'var(--text-secondary)' }}>
                    {insight.suggested_actions.map((act, aIdx) => (
                      <li key={aIdx}>{act}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Limitations */}
      {limitations && limitations.length > 0 && (
        <div
          style={{
            padding: '1rem',
            background: 'rgba(234, 179, 8, 0.08)',
            border: '1px solid rgba(234, 179, 8, 0.25)',
            borderRadius: 'var(--radius-sm)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              color: '#facc15',
              fontWeight: 600,
              fontSize: '0.85rem',
              marginBottom: '0.5rem',
            }}
          >
            <AlertTriangle size={16} />
            <span>Platform & Source Limitations</span>
          </div>
          <ul style={{ paddingLeft: '1.25rem', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
            {limitations.map((lim, idx) => (
              <li key={idx} style={{ marginBottom: '0.35rem' }}>
                {lim}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
