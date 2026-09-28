import React from 'react';
import { GitCommit } from 'lucide-react';
import { WorkflowResultResponse } from '../../types/workflow';
import { Card, CardBody, CardHeader, CardTitle } from '../common/Card';
import { Badge } from '../common/Badge';
import { ArtifactViewer } from '../artifacts/ArtifactViewer';

interface WorkflowExecutionViewProps {
  result: WorkflowResultResponse;
}

export const WorkflowExecutionView: React.FC<WorkflowExecutionViewProps> = ({ result }) => {
  const {
    workflow_execution_id,
    workflow_id,
    workflow_version,
    status,
    started_at,
    completed_at,
    step_results,
    artifacts,
    errors,
    warnings,
  } = result;

  const startTime = new Date(started_at).getTime();
  const endTime = new Date(completed_at).getTime();
  const elapsedSec = !isNaN(startTime) && !isNaN(endTime) ? ((endTime - startTime) / 1000).toFixed(2) : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Run Summary Banner */}
      <Card>
        <CardHeader>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <CardTitle>
              <GitCommit size={18} color="var(--accent-primary)" />
              Execution Outcome: {workflow_id} (v{workflow_version})
            </CardTitle>
          </div>
          <Badge variant={status} style={{ fontSize: '0.85rem', padding: '0.3rem 0.75rem' }}>
            {status}
          </Badge>
        </CardHeader>

        <CardBody>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '1rem',
              marginBottom: '1rem',
            }}
          >
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Workflow Execution ID</div>
              <div style={{ fontSize: '0.8rem', fontFamily: 'monospace', color: 'var(--text-primary)', wordBreak: 'break-all' }}>
                {workflow_execution_id}
              </div>
            </div>

            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Started UTC</div>
              <div style={{ fontSize: '0.825rem', color: 'var(--text-primary)' }}>
                {new Date(started_at).toLocaleString()}
              </div>
            </div>

            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Duration</div>
              <div style={{ fontSize: '0.825rem', color: 'var(--text-primary)' }}>
                {elapsedSec !== null ? `${elapsedSec}s` : 'N/A'}
              </div>
            </div>

            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Step Completion</div>
              <div style={{ fontSize: '0.825rem', color: 'var(--text-primary)' }}>
                {step_results.filter((s) => s.status === 'COMPLETED').length} / {step_results.length} steps completed
              </div>
            </div>
          </div>

          {/* Errors & Warnings */}
          {errors && errors.length > 0 && (
            <div
              style={{
                marginBottom: '1rem',
                padding: '0.85rem 1rem',
                background: 'rgba(239, 68, 68, 0.12)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: 'var(--radius-sm)',
                color: '#f87171',
                fontSize: '0.85rem',
              }}
            >
              <div style={{ fontWeight: 600, marginBottom: '0.35rem' }}>Execution Errors:</div>
              <ul style={{ paddingLeft: '1.2rem' }}>
                {errors.map((err, idx) => (
                  <li key={idx}>{err}</li>
                ))}
              </ul>
            </div>
          )}

          {warnings && warnings.length > 0 && (
            <div
              style={{
                marginBottom: '1rem',
                padding: '0.85rem 1rem',
                background: 'rgba(245, 158, 11, 0.12)',
                border: '1px solid rgba(245, 158, 11, 0.3)',
                borderRadius: 'var(--radius-sm)',
                color: '#fbbf24',
                fontSize: '0.85rem',
              }}
            >
              <div style={{ fontWeight: 600, marginBottom: '0.35rem' }}>Execution Advisories / Warnings:</div>
              <ul style={{ paddingLeft: '1.2rem' }}>
                {warnings.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Steps List */}
          <div>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.6rem' }}>
              Step Execution Pipeline:
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {step_results.map((step) => (
                <div
                  key={step.step_id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.6rem 0.85rem',
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.825rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{step.step_id}</span>
                    <span style={{ color: 'var(--text-muted)' }}>({step.agent_id})</span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    {step.skip_reason && (
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        Skip reason: {step.skip_reason}
                      </span>
                    )}
                    {step.error && (
                      <span style={{ fontSize: '0.75rem', color: '#f87171' }}>
                        {step.error.message}
                      </span>
                    )}
                    <Badge variant={step.status}>{step.status}</Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Render Output Artifacts */}
      {artifacts && Object.keys(artifacts).length > 0 && (
        <ArtifactViewer artifacts={artifacts} />
      )}
    </div>
  );
};
