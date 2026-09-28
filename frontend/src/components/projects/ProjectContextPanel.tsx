import React from 'react';
import { Camera, Layers } from 'lucide-react';
import { ProjectContextResponse, ContextSnapshotResponse } from '../../types/context';
import { Card, CardHeader, CardTitle, CardBody } from '../common/Card';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';

interface ProjectContextPanelProps {
  context: ProjectContextResponse | null;
  snapshots: ContextSnapshotResponse[];
  onOpenCreateSnapshot: () => void;
  isLoading?: boolean;
}

export const ProjectContextPanel: React.FC<ProjectContextPanelProps> = ({
  context,
  snapshots,
  onOpenCreateSnapshot,
  isLoading,
}) => {
  if (isLoading || !context) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Canonical Project Context</CardTitle>
        </CardHeader>
        <CardBody>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Loading canonical project context...
          </div>
        </CardBody>
      </Card>
    );
  }

  const { statistics, context_version, generated_at } = context;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
      <Card>
        <CardHeader>
          <div>
            <CardTitle>
              <Layers size={18} color="var(--accent-primary)" />
              Canonical Project Context
            </CardTitle>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Generated UTC: {new Date(generated_at).toLocaleString()}
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Badge variant="in-progress">v{context_version} Active</Badge>
            <Button
              variant="secondary"
              size="sm"
              icon={<Camera size={14} />}
              onClick={onOpenCreateSnapshot}
            >
              Take Snapshot
            </Button>
          </div>
        </CardHeader>

        <CardBody>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
              gap: '1rem',
              marginBottom: '1.5rem',
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
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Completion</div>
              <div
                style={{
                  fontSize: '1.4rem',
                  fontWeight: 700,
                  color: statistics.completion_percentage === 100 ? '#10b981' : '#f8fafc',
                }}
              >
                {statistics.completion_percentage.toFixed(1)}%
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
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Total Requirements</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#f8fafc' }}>
                {statistics.total_requirements}
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
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Active Requirements</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                {statistics.active_requirements}
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
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Functional / Non-Func</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 600, color: '#f8fafc' }}>
                {statistics.functional_count} / {statistics.non_functional_count}
              </div>
            </div>
          </div>

          <div>
            <h4 style={{ fontSize: '0.875rem', marginBottom: '0.6rem', color: 'var(--text-secondary)' }}>
              Historical Context Snapshots ({snapshots.length})
            </h4>
            {snapshots.length === 0 ? (
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                No immutable snapshots created yet. Snapshots provide pinned point-in-time context for workflows.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {snapshots.slice(0, 5).map((snap) => (
                  <div
                    key={snap.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      background: 'var(--bg-surface)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '0.5rem 0.75rem',
                      fontSize: '0.825rem',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <Badge variant="draft">v{snap.version}</Badge>
                      <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                        {snap.summary || 'Snapshot freeze'}
                      </span>
                    </div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                      {new Date(snap.created_at).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardBody>
      </Card>
    </div>
  );
};
