import React from 'react';
import { DeploymentOperation, DeploymentRecord, DeploymentStatus } from '../../types/environment';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { EmptyState } from '../common/EmptyState';
import {
  History,
  RotateCcw,
  ArrowUpRight,
  UploadCloud,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';

interface DeploymentHistoryFeedProps {
  deployments: DeploymentRecord[];
  isLoading: boolean;
  onRefresh?: () => void;
}

export const DeploymentHistoryFeed: React.FC<DeploymentHistoryFeedProps> = ({
  deployments,
  isLoading,
  onRefresh,
}) => {
  const getOperationBadge = (op: DeploymentOperation) => {
    switch (op) {
      case 'PROMOTION':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#818cf8', fontWeight: 600, fontSize: '0.75rem' }}>
            <ArrowUpRight size={13} /> PROMOTION
          </span>
        );
      case 'ROLLBACK':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#f87171', fontWeight: 600, fontSize: '0.75rem' }}>
            <RotateCcw size={13} /> ROLLBACK
          </span>
        );
      case 'DEPLOYMENT':
      default:
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#38bdf8', fontWeight: 600, fontSize: '0.75rem' }}>
            <UploadCloud size={13} /> DEPLOYMENT
          </span>
        );
    }
  };

  const getStatusBadge = (status: DeploymentStatus) => {
    switch (status) {
      case 'SUCCEEDED':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: 'var(--status-completed)', fontSize: '0.75rem', fontWeight: 600 }}>
            <CheckCircle size={13} /> SUCCEEDED
          </span>
        );
      case 'FAILED':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: 'var(--status-failed)', fontSize: '0.75rem', fontWeight: 600 }}>
            <XCircle size={13} /> FAILED
          </span>
        );
      case 'ROLLED_BACK':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: 'var(--status-partial)', fontSize: '0.75rem', fontWeight: 600 }}>
            <AlertCircle size={13} /> ROLLED BACK
          </span>
        );
      case 'DEPLOYING':
      case 'VALIDATING':
      case 'VERIFYING':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: 'var(--status-running)', fontSize: '0.75rem', fontWeight: 600 }}>
            <Clock size={13} /> {status}
          </span>
        );
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        borderRadius: '8px',
        border: '1px solid var(--border-subtle)',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '12px 16px',
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <History size={16} style={{ color: 'var(--text-secondary)' }} />
          <h3 style={{ margin: 0, fontSize: '0.9375rem', fontWeight: 600 }}>
            Append-Only Deployment History
          </h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            ({deployments.length} records)
          </span>
        </div>
        {onRefresh && (
          <Button size="sm" variant="ghost" onClick={onRefresh} disabled={isLoading} icon={<RefreshCw size={13} />}>
            Refresh
          </Button>
        )}
      </div>

      {isLoading ? (
        <div style={{ padding: '32px', display: 'flex', justifyContent: 'center' }}>
          <LoadingSpinner />
        </div>
      ) : deployments.length === 0 ? (
        <div style={{ padding: '32px' }}>
          <EmptyState
            title="No deployments recorded yet"
            description="Deployments, promotions, and rollbacks will appear here in chronological order."
          />
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem' }}>
            <thead>
              <tr
                style={{
                  borderBottom: '1px solid var(--border-subtle)',
                  background: 'var(--bg-secondary)',
                  textAlign: 'left',
                  color: 'var(--text-muted)',
                }}
              >
                <th style={{ padding: '10px 14px', fontWeight: 600 }}>Timestamp</th>
                <th style={{ padding: '10px 14px', fontWeight: 600 }}>Operation</th>
                <th style={{ padding: '10px 14px', fontWeight: 600 }}>Environment</th>
                <th style={{ padding: '10px 14px', fontWeight: 600 }}>Version Transition</th>
                <th style={{ padding: '10px 14px', fontWeight: 600 }}>Status</th>
                <th style={{ padding: '10px 14px', fontWeight: 600 }}>Requested By</th>
                <th style={{ padding: '10px 14px', fontWeight: 600 }}>Notes / Reason</th>
              </tr>
            </thead>
            <tbody>
              {deployments.map((record) => {
                const dateStr = new Date(record.created_at).toLocaleString();
                const notes =
                  record.failure_reason ||
                  record.metadata_payload?.reason ||
                  record.metadata_payload?.notes ||
                  '—';

                return (
                  <tr
                    key={record.id}
                    style={{
                      borderBottom: '1px solid var(--border-subtle)',
                      transition: 'background 0.15s ease',
                    }}
                  >
                    <td style={{ padding: '10px 14px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                      {dateStr}
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      {getOperationBadge(record.operation)}
                    </td>
                    <td style={{ padding: '10px 14px', fontWeight: 600 }}>
                      <span
                        style={{
                          color:
                            record.environment_type === 'PRODUCTION'
                              ? '#f87171'
                              : record.environment_type === 'STAGING'
                              ? '#facc15'
                              : '#818cf8',
                        }}
                      >
                        {record.environment_type}
                      </span>
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      <span style={{ color: 'var(--text-muted)' }}>
                        {record.previous_version_number != null
                          ? `v${record.previous_version_number}`
                          : '—'}
                      </span>
                      <span style={{ margin: '0 6px', color: 'var(--text-secondary)' }}>→</span>
                      <span style={{ fontWeight: 700, color: 'var(--accent-primary)' }}>
                        {record.version_number != null
                          ? `v${record.version_number}`
                          : `[${record.version_id.substring(0, 8)}]`}
                      </span>
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      {getStatusBadge(record.status)}
                    </td>
                    <td style={{ padding: '10px 14px', color: 'var(--text-secondary)' }}>
                      {record.requested_by}
                    </td>
                    <td
                      style={{
                        padding: '10px 14px',
                        color: record.failure_reason ? '#f87171' : 'var(--text-secondary)',
                        maxWidth: '280px',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                      title={typeof notes === 'string' ? notes : JSON.stringify(notes)}
                    >
                      {typeof notes === 'string' ? notes : JSON.stringify(notes)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
