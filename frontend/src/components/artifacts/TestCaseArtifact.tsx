import React from 'react';
import { TestCaseGenerationOutput } from '../../types/artifacts';
import { Badge } from '../common/Badge';

interface TestCaseArtifactProps {
  artifact: TestCaseGenerationOutput;
}

export const TestCaseArtifact: React.FC<TestCaseArtifactProps> = ({ artifact }) => {
  const { summary, test_cases, total_test_cases, coverage } = artifact;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Summary */}
      <div>
        <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
          Test Suite Strategy
        </h4>
        <p style={{ fontSize: '0.875rem', lineHeight: 1.6, color: 'var(--text-primary)' }}>
          {summary}
        </p>
      </div>

      {/* Metrics */}
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
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Generated Test Cases</div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--accent-primary)' }}>
            {total_test_cases}
          </div>
        </div>

        {coverage && (
          <div
            style={{
              background: 'var(--bg-surface)',
              padding: '0.75rem 1rem',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Requirement Coverage</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--status-completed)' }}>
              {coverage.coverage_percentage?.toFixed(1) || '0.0'}%
            </div>
          </div>
        )}
      </div>

      {/* Test Cases List */}
      <div>
        <h4 style={{ fontSize: '0.9rem', marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
          Test Cases ({test_cases?.length || 0})
        </h4>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {test_cases?.map((tc) => (
            <div
              key={tc.test_case_id}
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
                  <Badge variant="draft">{tc.test_case_id}</Badge>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{tc.title}</span>
                </div>
                <div style={{ display: 'flex', gap: '0.4rem' }}>
                  <Badge variant="in-progress">{tc.test_type}</Badge>
                  <Badge variant={tc.priority}>{tc.priority}</Badge>
                </div>
              </div>

              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                {tc.description}
              </div>

              {/* Steps */}
              {tc.steps && tc.steps.length > 0 && (
                <div style={{ marginBottom: '0.5rem' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                    Steps:
                  </div>
                  <ol style={{ paddingLeft: '1.2rem', fontSize: '0.8rem', color: 'var(--text-primary)' }}>
                    {tc.steps.map((st) => (
                      <li key={st.step_number} style={{ marginBottom: '0.2rem' }}>
                        <span>{st.action}</span>
                        <span style={{ color: 'var(--text-muted)' }}> → Expected: {st.expected_behavior}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              )}

              <div style={{ fontSize: '0.8rem', color: '#10b981' }}>
                <span style={{ fontWeight: 600 }}>Expected Outcome:</span> {tc.expected_result}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
