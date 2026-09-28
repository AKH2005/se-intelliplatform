import React from 'react';
import { Eye, History } from 'lucide-react';
import { WorkflowExecutionSummaryResponse } from '../../types/workflow';
import { Card, CardBody, CardHeader, CardTitle } from '../common/Card';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { EmptyState } from '../common/EmptyState';

interface RunHistoryListProps {
  items: WorkflowExecutionSummaryResponse[];
  total: number;
  onSelectRun: (executionId: string) => void;
  isLoading?: boolean;
}

export const RunHistoryList: React.FC<RunHistoryListProps> = ({
  items,
  total,
  onSelectRun,
}) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <History size={18} color="var(--accent-primary)" />
          Execution Run History ({total})
        </CardTitle>
      </CardHeader>

      <CardBody>
        {items.length === 0 ? (
          <EmptyState
            title="No workflow executions yet"
            description="Run a workflow from Workflow Studio to record execution audit history."
          />
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Workflow</th>
                  <th>Snapshot</th>
                  <th>Started UTC</th>
                  <th>Step Summary</th>
                  <th>Artifacts</th>
                  <th style={{ textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.workflow_execution_id}>
                    <td>
                      <Badge variant={item.status}>{item.status}</Badge>
                    </td>
                    <td>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                        {item.workflow_id}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        v{item.workflow_version}
                      </div>
                    </td>
                    <td>
                      {item.context_version ? (
                        <Badge variant="draft">Snapshot v{item.context_version}</Badge>
                      ) : (
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Latest</span>
                      )}
                    </td>
                    <td style={{ fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
                      {new Date(item.started_at).toLocaleString()}
                    </td>
                    <td style={{ fontSize: '0.825rem' }}>
                      <span style={{ color: '#10b981' }}>{item.completed_steps} ok</span>
                      {item.failed_steps > 0 && (
                        <span style={{ color: '#ef4444', marginLeft: 6 }}>
                          {item.failed_steps} failed
                        </span>
                      )}
                      {item.skipped_steps > 0 && (
                        <span style={{ color: '#94a3b8', marginLeft: 6 }}>
                          {item.skipped_steps} skipped
                        </span>
                      )}
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {item.artifact_keys?.length || 0} artifacts
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={<Eye size={14} />}
                        onClick={() => onSelectRun(item.workflow_execution_id)}
                      >
                        Details
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardBody>
    </Card>
  );
};
