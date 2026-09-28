import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { TimelinePredictionOutput } from '../../types/artifacts';

interface TimelineArtifactProps {
  artifact: TimelinePredictionOutput;
}

export const TimelineArtifact: React.FC<TimelineArtifactProps> = ({ artifact }) => {
  const {
    summary,
    predicted_duration_months,
    estimated_duration_months,
    target_unit,
    feature_summary,
    limitations,
    model_provenance,
  } = artifact;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Duration Metrics Display */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1rem',
        }}
      >
        <div
          style={{
            padding: '1.25rem',
            background: 'var(--bg-surface)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
            Presentation Duration Estimate
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem' }}>
            <span style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
              {estimated_duration_months}
            </span>
            <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>{target_unit || 'months'}</span>
          </div>
        </div>

        <div
          style={{
            padding: '1.25rem',
            background: 'var(--bg-surface)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
            Continuous Model Point Estimate
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem' }}>
            <span style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {typeof predicted_duration_months === 'number'
                ? predicted_duration_months.toFixed(2)
                : predicted_duration_months}
            </span>
            <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>{target_unit || 'months'}</span>
          </div>
        </div>
      </div>

      {/* Summary */}
      <div>
        <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
          Duration Estimation Summary
        </h4>
        <p style={{ fontSize: '0.875rem', lineHeight: 1.6, color: 'var(--text-primary)' }}>
          {summary}
        </p>
      </div>

      {/* Feature Summary */}
      {feature_summary && Object.keys(feature_summary).length > 0 && (
        <div>
          <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
            Evaluated Function Point & Size Metrics
          </h4>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
              gap: '0.75rem',
            }}
          >
            {Object.entries(feature_summary).map(([k, v]) => (
              <div
                key={k}
                style={{
                  background: 'var(--bg-surface)',
                  padding: '0.6rem 0.8rem',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>{k}</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {String(v)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Model Limitations */}
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
            <span>Advisory Status & Limitations</span>
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

      {/* Provenance */}
      {model_provenance && (
        <div
          style={{
            fontSize: '0.75rem',
            color: 'var(--text-dim)',
            display: 'flex',
            flexWrap: 'wrap',
            gap: '1rem',
            borderTop: '1px solid var(--border-subtle)',
            paddingTop: '0.75rem',
          }}
        >
          <span>Model: {model_provenance.model_name} (v{model_provenance.model_version})</span>
          <span>Algorithm: {model_provenance.algorithm}</span>
          <span>Training Dataset: {model_provenance.training_dataset}</span>
        </div>
      )}
    </div>
  );
};
