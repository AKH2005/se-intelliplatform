import React from 'react';
import { Environment, EnvironmentType } from '../../types/environment';
import { Card, CardBody, CardHeader, CardTitle, CardFooter } from '../common/Card';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import {
  Server,
  ArrowUpRight,
  RotateCcw,
  UploadCloud,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  ShieldCheck,
  Tag,
} from 'lucide-react';

interface EnvironmentCardProps {
  environment: Environment;
  onPromote?: (environment: Environment) => void;
  onDeploy?: (environment: Environment) => void;
  onRollback?: (environment: Environment) => void;
  isLoading?: boolean;
}

export const EnvironmentCard: React.FC<EnvironmentCardProps> = ({
  environment,
  onPromote,
  onDeploy,
  onRollback,
  isLoading = false,
}) => {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'HEALTHY':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: 'var(--status-completed)', fontSize: '0.8125rem', fontWeight: 600 }}>
            <CheckCircle size={14} /> Healthy
          </span>
        );
      case 'DEPLOYING':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: 'var(--status-running)', fontSize: '0.8125rem', fontWeight: 600 }}>
            <Clock size={14} /> Deploying
          </span>
        );
      case 'FAILED':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: 'var(--status-failed)', fontSize: '0.8125rem', fontWeight: 600 }}>
            <XCircle size={14} /> Failed
          </span>
        );
      case 'DEGRADED':
        return (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: 'var(--status-partial)', fontSize: '0.8125rem', fontWeight: 600 }}>
            <AlertTriangle size={14} /> Degraded
          </span>
        );
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  const getEnvBadge = (type: EnvironmentType) => {
    if (type === 'PRODUCTION') {
      return (
        <span
          style={{
            background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(168, 85, 247, 0.2))',
            color: '#f87171',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            padding: '2px 8px',
            borderRadius: '4px',
            fontSize: '0.75rem',
            fontWeight: 700,
            letterSpacing: '0.05em',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
          }}
        >
          <ShieldCheck size={12} /> PROD
        </span>
      );
    }
    if (type === 'STAGING') {
      return (
        <span
          style={{
            background: 'rgba(234, 179, 8, 0.15)',
            color: '#facc15',
            border: '1px solid rgba(234, 179, 8, 0.3)',
            padding: '2px 8px',
            borderRadius: '4px',
            fontSize: '0.75rem',
            fontWeight: 700,
            letterSpacing: '0.05em',
          }}
        >
          STAGING
        </span>
      );
    }
    return (
      <span
        style={{
          background: 'rgba(99, 102, 241, 0.15)',
          color: '#818cf8',
          border: '1px solid rgba(99, 102, 241, 0.3)',
          padding: '2px 8px',
          borderRadius: '4px',
          fontSize: '0.75rem',
          fontWeight: 700,
          letterSpacing: '0.05em',
        }}
      >
        DEV
      </span>
    );
  };

  const formattedDate = environment.last_deployed_at
    ? new Date(environment.last_deployed_at).toLocaleString()
    : 'Never deployed';

  return (
    <Card
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        border: environment.is_production
          ? '1px solid rgba(239, 68, 68, 0.3)'
          : '1px solid var(--border-subtle)',
        background: 'var(--bg-surface)',
        borderRadius: '8px',
        overflow: 'hidden',
      }}
    >
      <CardHeader
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid var(--border-subtle)',
          padding: '12px 16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Server size={18} style={{ color: 'var(--text-secondary)' }} />
          <CardTitle style={{ fontSize: '1rem', fontWeight: 600, margin: 0 }}>
            {environment.name}
          </CardTitle>
          {getEnvBadge(environment.environment_type)}
        </div>
        {getStatusBadge(environment.status)}
      </CardHeader>

      <CardBody style={{ flex: 1, padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Version pointer display */}
        <div
          style={{
            background: 'var(--bg-secondary)',
            borderRadius: '6px',
            padding: '12px',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Current Deployed Version
          </div>
          {environment.current_version_id ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Tag size={16} style={{ color: 'var(--accent-primary)' }} />
                <span style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  v{environment.current_version_number ?? '?'}
                </span>
                {environment.current_version_status && (
                  <Badge variant={environment.current_version_status.toLowerCase()}>
                    {environment.current_version_status}
                  </Badge>
                )}
              </div>
              {environment.current_version_hash && (
                <code
                  style={{
                    fontSize: '0.75rem',
                    background: 'var(--bg-surface)',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    color: 'var(--text-secondary)',
                  }}
                >
                  {environment.current_version_hash.substring(0, 8)}
                </code>
              )}
            </div>
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem', fontStyle: 'italic' }}>
              No version currently deployed
            </div>
          )}
        </div>

        {/* Deployment metadata */}
        <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Last Deployed:</span>
            <span style={{ color: 'var(--text-primary)' }}>{formattedDate}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Environment ID:</span>
            <code style={{ fontSize: '0.75rem' }}>{environment.id.substring(0, 8)}...</code>
          </div>
        </div>
      </CardBody>

      <CardFooter
        style={{
          borderTop: '1px solid var(--border-subtle)',
          padding: '12px 16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '8px',
          background: 'var(--bg-secondary)',
        }}
      >
        <div style={{ display: 'flex', gap: '8px' }}>
          {onDeploy && (
            <Button
              size="sm"
              variant="secondary"
              onClick={() => onDeploy(environment)}
              disabled={isLoading}
              icon={<UploadCloud size={14} />}
            >
              Deploy
            </Button>
          )}
          {onRollback && environment.current_version_id && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onRollback(environment)}
              disabled={isLoading}
              icon={<RotateCcw size={14} />}
            >
              Rollback
            </Button>
          )}
        </div>

        {onPromote && environment.environment_type !== 'PRODUCTION' && (
          <Button
            size="sm"
            variant="primary"
            onClick={() => onPromote(environment)}
            disabled={isLoading || !environment.current_version_id}
            icon={<ArrowUpRight size={14} />}
          >
            Promote to {environment.environment_type === 'DEVELOPMENT' ? 'Staging' : 'Production'}
          </Button>
        )}
      </CardFooter>
    </Card>
  );
};
