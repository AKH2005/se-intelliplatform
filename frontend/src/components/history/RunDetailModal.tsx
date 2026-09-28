import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { historyApi } from '../../services/historyApi';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';
import { ArtifactViewer } from '../artifacts/ArtifactViewer';

interface RunDetailModalProps {
  executionId: string | null;
  onClose: () => void;
}

export const RunDetailModal: React.FC<RunDetailModalProps> = ({ executionId, onClose }) => {
  const { data: detail, isLoading, error } = useQuery({
    queryKey: ['workflow-execution-detail', executionId],
    queryFn: () => historyApi.getExecutionDetail(executionId!),
    enabled: Boolean(executionId),
  });

  return (
    <Modal
      isOpen={Boolean(executionId)}
      onClose={onClose}
      title="Workflow Execution Run Detail"
      size="large"
      footer={
        <Button variant="secondary" onClick={onClose}>
          Close
        </Button>
      }
    >
      {isLoading && <LoadingSpinner label="Fetching execution detail..." />}

      {error && <ErrorAlert error={error as any} />}

      {detail && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0.85rem 1rem',
              background: 'var(--bg-surface)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '1rem' }}>
                {detail.workflow_id} (v{detail.workflow_version})
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                Run ID: {detail.workflow_execution_id}
              </div>
            </div>
            <Badge variant={detail.status}>{detail.status}</Badge>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
              gap: '0.75rem',
            }}
          >
            <div style={{ background: 'var(--bg-surface)', padding: '0.6rem 0.8rem', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>Started UTC</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-primary)' }}>
                {new Date(detail.started_at).toLocaleString()}
              </div>
            </div>
            <div style={{ background: 'var(--bg-surface)', padding: '0.6rem 0.8rem', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>Completed UTC</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-primary)' }}>
                {detail.completed_at ? new Date(detail.completed_at).toLocaleString() : 'In Progress'}
              </div>
            </div>
            <div style={{ background: 'var(--bg-surface)', padding: '0.6rem 0.8rem', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>Steps Summary</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-primary)' }}>
                {detail.completed_steps}/{detail.step_count} completed
              </div>
            </div>
          </div>

          {/* Errors and Warnings */}
          {detail.errors && detail.errors.length > 0 && (
            <div
              style={{
                padding: '0.75rem 1rem',
                background: 'rgba(239, 68, 68, 0.12)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: 'var(--radius-sm)',
                color: '#f87171',
                fontSize: '0.825rem',
              }}
            >
              <div style={{ fontWeight: 600 }}>Blocking Errors:</div>
              <ul style={{ paddingLeft: '1.2rem', marginTop: '0.25rem' }}>
                {detail.errors.map((e, idx) => (
                  <li key={idx}>{e}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Persisted Artifacts */}
          {detail.artifacts && Object.keys(detail.artifacts).length > 0 && (
            <div>
              <h4 style={{ fontSize: '0.9rem', marginBottom: '0.6rem', color: 'var(--text-secondary)' }}>
                Persisted Execution Artifacts
              </h4>
              <ArtifactViewer artifacts={detail.artifacts} />
            </div>
          )}
        </div>
      )}
    </Modal>
  );
};
