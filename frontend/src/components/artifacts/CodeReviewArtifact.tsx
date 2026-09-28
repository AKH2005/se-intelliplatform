import React from 'react';
import { CodeReviewOutput } from '../../types/artifacts';
import { Badge } from '../common/Badge';

interface CodeReviewArtifactProps {
  artifact: CodeReviewOutput;
}

export const CodeReviewArtifact: React.FC<CodeReviewArtifactProps> = ({ artifact }) => {
  const { summary, files_reviewed, findings, metrics } = artifact;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Summary */}
      <div>
        <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
          Review Summary
        </h4>
        <p style={{ fontSize: '0.875rem', lineHeight: 1.6, color: 'var(--text-primary)' }}>
          {summary}
        </p>
      </div>

      {/* Metrics */}
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
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Total Findings</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--accent-primary)' }}>
              {metrics.total_findings}
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
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Files Reviewed</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {files_reviewed?.length || 0}
            </div>
          </div>
        </div>
      )}

      {/* Findings */}
      <div>
        <h4 style={{ fontSize: '0.9rem', marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
          Review Findings ({findings?.length || 0})
        </h4>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {findings?.map((finding) => (
            <div
              key={finding.finding_id}
              style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '1rem',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: '0.4rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Badge variant="draft">{finding.finding_id}</Badge>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                    {finding.title}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '0.4rem' }}>
                  <Badge variant="in-progress">{finding.category}</Badge>
                  <Badge variant={finding.severity}>{finding.severity}</Badge>
                </div>
              </div>

              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
                {finding.file_path}
                {finding.line_start ? ` (line ${finding.line_start})` : ''}
              </div>

              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                {finding.description}
              </div>

              {finding.evidence && (
                <div style={{ marginBottom: '0.5rem' }}>
                  <pre style={{ fontSize: '0.8rem', padding: '0.5rem' }}>{finding.evidence}</pre>
                </div>
              )}

              {finding.suggestion && (
                <div style={{ fontSize: '0.8rem', color: '#10b981' }}>
                  <span style={{ fontWeight: 600 }}>Suggested Fix:</span> {finding.suggestion}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
