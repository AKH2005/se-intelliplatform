import React, { useEffect, useState, useCallback } from 'react';
import { useProject } from '../context/ProjectContext';
import { environmentApi } from '../services/environmentApi';
import { developmentVersionApi } from '../services/developmentVersionApi';
import {
  Environment,
  EnvironmentType,
  DeploymentRecord,
} from '../types/environment';
import { DevelopmentVersionResponse } from '../types/developmentVersion';
import { NavigationTab } from '../components/layout/Sidebar';
import { Button } from '../components/common/Button';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import {
  EnvironmentCard,
  PromotionModal,
  RollbackModal,
  DeployModal,
  DeploymentHistoryFeed,
} from '../components/environments';
import {
  Layers,
  RefreshCw,
  Server,
  ShieldCheck,
  Activity,
  Code2,
} from 'lucide-react';

interface EnvironmentWorkspaceProps {
  onNavigate?: (tab: NavigationTab) => void;
}

export const EnvironmentWorkspace: React.FC<EnvironmentWorkspaceProps> = ({
  onNavigate,
}) => {
  const { selectedProjectId } = useProject();

  const [environments, setEnvironments] = useState<Environment[]>([]);
  const [versions, setVersions] = useState<DevelopmentVersionResponse[]>([]);
  const [deployments, setDeployments] = useState<DeploymentRecord[]>([]);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Modals state
  const [promoteModalOpen, setPromoteModalOpen] = useState<boolean>(false);
  const [promotionSourceEnv, setPromotionSourceEnv] = useState<Environment | null>(null);
  const [promotionTargetType, setPromotionTargetType] = useState<EnvironmentType>('STAGING');
  const [candidateVersionId, setCandidateVersionId] = useState<string>('');
  const [candidateVersionNumber, setCandidateVersionNumber] = useState<number>(0);

  const [deployModalOpen, setDeployModalOpen] = useState<boolean>(false);
  const [selectedEnvForDeploy, setSelectedEnvForDeploy] = useState<Environment | null>(null);

  const [rollbackModalOpen, setRollbackModalOpen] = useState<boolean>(false);
  const [selectedEnvForRollback, setSelectedEnvForRollback] = useState<Environment | null>(null);

  const loadData = useCallback(async () => {
    if (!selectedProjectId) {
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const [envsData, versionsData, deploymentsData] = await Promise.all([
        environmentApi.listEnvironments(selectedProjectId),
        developmentVersionApi.listVersions(selectedProjectId),
        environmentApi.listDeployments(selectedProjectId, undefined, 50),
      ]);

      setEnvironments(envsData);
      setVersions(versionsData.items || []);
      setDeployments(deploymentsData);
    } catch (err: any) {
      setError(err.message || 'Failed to load environment workspace data');
    } finally {
      setIsLoading(false);
    }
  }, [selectedProjectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Action Handlers
  const handleOpenPromote = (env: Environment) => {
    if (!env.current_version_id) return;
    const targetType: EnvironmentType =
      env.environment_type === 'DEVELOPMENT' ? 'STAGING' : 'PRODUCTION';

    setPromotionSourceEnv(env);
    setPromotionTargetType(targetType);
    setCandidateVersionId(env.current_version_id);
    setCandidateVersionNumber(env.current_version_number ?? 0);
    setPromoteModalOpen(true);
  };

  const handleOpenDeploy = (env: Environment) => {
    setSelectedEnvForDeploy(env);
    setDeployModalOpen(true);
  };

  const handleOpenRollback = (env: Environment) => {
    setSelectedEnvForRollback(env);
    setRollbackModalOpen(true);
  };

  // Metrics calculation
  const prodEnv = environments.find((e) => e.environment_type === 'PRODUCTION');
  const healthyCount = environments.filter((e) => e.status === 'HEALTHY').length;

  if (!selectedProjectId) {
    return (
      <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-secondary)' }}>
        <Layers size={48} style={{ margin: '0 auto 16px', opacity: 0.5 }} />
        <h2>Select a project to view multi-environment deployment topology</h2>
      </div>
    );
  }

  return (
    <div
      style={{
        padding: '24px 32px',
        display: 'flex',
        flexDirection: 'column',
        gap: '24px',
        maxWidth: '1400px',
        margin: '0 auto',
        width: '100%',
      }}
    >
      {/* Workspace Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '20px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <Layers size={24} style={{ color: 'var(--accent-primary)' }} />
            <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Environments & Continuous Deployment
            </h1>
          </div>
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Independent, project-scoped environments (Development, Staging, Production) with deterministic
            promotion gates, decoupled immutable version pointers, and non-destructive rollback.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {onNavigate && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onNavigate('development')}
              icon={<Code2 size={14} />}
            >
              Development Versions
            </Button>
          )}
          <Button
            variant="secondary"
            size="sm"
            onClick={loadData}
            disabled={isLoading}
            icon={<RefreshCw size={14} />}
          >
            Refresh
          </Button>
        </div>
      </div>

      {error && <ErrorAlert error={error} onRetry={loadData} />}

      {/* Summary KPI Strip */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '16px',
        }}
      >
        <div
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '8px',
            padding: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
          }}
        >
          <div
            style={{
              padding: '10px',
              borderRadius: '8px',
              background: 'rgba(99, 102, 241, 0.1)',
              color: 'var(--accent-primary)',
            }}
          >
            <Server size={20} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Environments
            </div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {environments.length} Active ({healthyCount} Healthy)
            </div>
          </div>
        </div>

        <div
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '8px',
            padding: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
          }}
        >
          <div
            style={{
              padding: '10px',
              borderRadius: '8px',
              background: 'rgba(239, 68, 68, 0.1)',
              color: '#f87171',
            }}
          >
            <ShieldCheck size={20} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Production Release
            </div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {prodEnv?.current_version_number != null
                ? `v${prodEnv.current_version_number}`
                : 'Not Deployed'}
            </div>
          </div>
        </div>

        <div
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '8px',
            padding: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
          }}
        >
          <div
            style={{
              padding: '10px',
              borderRadius: '8px',
              background: 'rgba(16, 185, 129, 0.1)',
              color: 'var(--status-completed)',
            }}
          >
            <Activity size={20} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Total Operations
            </div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {deployments.length} Recorded
            </div>
          </div>
        </div>
      </div>

      {/* Environment Cards Grid */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
          <Server size={18} style={{ color: 'var(--text-secondary)' }} />
          <h2 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 600 }}>Active Environments</h2>
        </div>

        {isLoading && environments.length === 0 ? (
          <div style={{ padding: '40px', display: 'flex', justifyContent: 'center' }}>
            <LoadingSpinner />
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: '20px',
            }}
          >
            {environments.map((env) => (
              <EnvironmentCard
                key={env.id}
                environment={env}
                onPromote={handleOpenPromote}
                onDeploy={handleOpenDeploy}
                onRollback={handleOpenRollback}
                isLoading={isLoading}
              />
            ))}
          </div>
        )}
      </div>

      {/* Deployment & Promotion History */}
      <DeploymentHistoryFeed
        deployments={deployments}
        isLoading={isLoading}
        onRefresh={loadData}
      />

      {/* Modals */}
      <PromotionModal
        isOpen={promoteModalOpen}
        onClose={() => setPromoteModalOpen(false)}
        projectId={selectedProjectId}
        sourceEnvironment={promotionSourceEnv}
        targetEnvironmentType={promotionTargetType}
        candidateVersionId={candidateVersionId}
        candidateVersionNumber={candidateVersionNumber}
        onPromoteSuccess={loadData}
      />

      <DeployModal
        isOpen={deployModalOpen}
        onClose={() => setDeployModalOpen(false)}
        projectId={selectedProjectId}
        environment={selectedEnvForDeploy}
        availableVersions={versions}
        onDeploySuccess={loadData}
      />

      <RollbackModal
        isOpen={rollbackModalOpen}
        onClose={() => setRollbackModalOpen(false)}
        projectId={selectedProjectId}
        environment={selectedEnvForRollback}
        availableVersions={versions}
        onRollbackSuccess={loadData}
      />
    </div>
  );
};
