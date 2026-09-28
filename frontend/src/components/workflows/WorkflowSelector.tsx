import React from 'react';
import { PlayCircle, GitFork } from 'lucide-react';
import { WorkflowMetadataResponse } from '../../types/workflow';
import { Card, CardBody, CardHeader } from '../common/Card';
import { Badge } from '../common/Badge';

interface WorkflowSelectorProps {
  workflows: WorkflowMetadataResponse[];
  selectedWorkflowId: string | null;
  onSelectWorkflow: (id: string) => void;
  isLoading?: boolean;
}

export const WorkflowSelector: React.FC<WorkflowSelectorProps> = ({
  workflows,
  selectedWorkflowId,
  onSelectWorkflow,
  isLoading,
}) => {
  if (isLoading) {
    return (
      <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
        Discovering available multi-agent workflows...
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      <h3 style={{ fontSize: '1rem', color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
        Discovered Multi-Agent Pipelines ({workflows.length})
      </h3>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
        {workflows.map((wf) => {
          const isSelected = wf.workflow_id === selectedWorkflowId;

          return (
            <Card
              key={wf.workflow_id}
              onClick={() => onSelectWorkflow(wf.workflow_id)}
              style={{
                cursor: 'pointer',
                borderColor: isSelected ? 'var(--accent-primary)' : 'var(--border-subtle)',
                background: isSelected ? 'var(--bg-surface-active)' : 'var(--bg-glass-card)',
                boxShadow: isSelected ? '0 0 15px -3px var(--accent-primary-glow)' : undefined,
              }}
            >
              <CardHeader>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <PlayCircle size={18} color={isSelected ? 'var(--accent-primary)' : 'var(--text-muted)'} />
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{wf.name}</span>
                </div>
                <Badge variant="draft">v{wf.version}</Badge>
              </CardHeader>
              <CardBody>
                <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginBottom: '1rem', minHeight: '38px' }}>
                  {wf.description}
                </p>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.775rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>
                    <GitFork size={13} style={{ display: 'inline', verticalAlign: '-1px', marginRight: 4 }} />
                    {wf.step_count} Steps
                  </span>
                  <span style={{ color: 'var(--text-dim)' }}>ID: {wf.workflow_id}</span>
                </div>
              </CardBody>
            </Card>
          );
        })}
      </div>
    </div>
  );
};
