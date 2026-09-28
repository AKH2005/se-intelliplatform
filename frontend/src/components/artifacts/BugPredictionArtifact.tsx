import React from 'react';
import { AlertOctagon, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { BugPredictionOutput } from '../../types/artifacts';

interface BugPredictionArtifactProps {
  artifact: BugPredictionOutput;
}

export const BugPredictionArtifact: React.FC<BugPredictionArtifactProps> = ({ artifact }) => {
  const {
    summary,
    prediction_label,
    predicted_probability,
    feature_summary,
    limitations,
    model_provenance,
  } = artifact;

  const isDefective = prediction_label === 'DEFECTIVE';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Classification Card */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '1.25rem',
          background: 'var(--bg-surface)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: 'var(--radius-sm)',
              background: isDefective ? 'rgba(239, 68, 68, 0.18)' : 'rgba(16, 185, 129, 0.18)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {isDefective ? (
              <AlertOctagon size={24} color="#ef4444" />
            ) : (
              <CheckCircle2 size={24} color="#10b981" />
            )}
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Static-Code Defect Classification
            </div>
            <div
              style={{
                fontSize: '1.6rem',
                fontWeight: 800,
                color: isDefective ? 'var(--risk-critical)' : 'var(--risk-low)',
              }}
            >
              {prediction_label}
            </div>
          </div>
        </div>

        {typeof predicted_probability === 'number' && (
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>
              Classifier Probability
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {(predicted_probability * 100).toFixed(1)}%
            </div>
          </div>
        )}
      </div>

      {/* Summary */}
      <div>
        <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
          Defect Assessment Summary
        </h4>
        <p style={{ fontSize: '0.875rem', lineHeight: 1.6, color: 'var(--text-primary)' }}>
          {summary}
        </p>
      </div>

      {/* Feature Summary */}
      {feature_summary && Object.keys(feature_summary).length > 0 && (
        <div>
          <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
            Evaluated Complexity Metrics (NASA JM1)
          </h4>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
              gap: '0.75rem',
            }}
          >
            {Object.entries(feature_summary).map(([k, v]) => (
              <div
                key={k}
                style={{
                  background: 'var(--bg-surface)',
                  padding: '0.5rem 0.75rem',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{k}</div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {typeof v === 'number' ? Number(v).toFixed(2) : String(v)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

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
            <span>Advisory Quality Indicator Status</span>
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

      {/* Model Provenance */}
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
          <span>Dataset: {model_provenance.training_dataset}</span>
        </div>
      )}
    </div>
  );
};
