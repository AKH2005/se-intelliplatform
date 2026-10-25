import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useProject } from '../context/ProjectContext';
import { historyApi } from '../services/historyApi';
import { isProjectNotFoundError } from '../utils/projectRecovery';
import { ArtifactViewer } from '../components/artifacts/ArtifactViewer';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import {
  Brain,
  History,
  PlayCircle,
} from 'lucide-react';
import { NavigationTab } from '../components/layout/Sidebar';

interface IntelligenceWorkspaceProps {
  onNavigate?: (tab: NavigationTab) => void;
}

export const IntelligenceWorkspace: React.FC<IntelligenceWorkspaceProps> = ({ onNavigate }) => {
  const { selectedProjectId, handleStaleProject, openCreateProject } = useProject();
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null);

  // 1. Fetch recent project executions
  const {
    data: historyData,
    isLoading: isLoadingHistory,
    error: historyError,
    refetch: refetchHistory,
  } = useQuery({
    queryKey: ['project-workflow-history', selectedProjectId],
    queryFn: () => historyApi.listProjectHistory(selectedProjectId!, { limit: 20, offset: 0 }),
    enabled: Boolean(selectedProjectId),
  });

  // Automatically trigger project recovery if project not found
  useEffect(() => {
    if (historyError && isProjectNotFoundError(historyError)) {
      handleStaleProject?.(selectedProjectId || undefined);
    }
  }, [historyError, selectedProjectId, handleStaleProject]);

  const runsWithArtifacts = (historyData?.items || []).filter(
    (item) => item.artifact_keys && item.artifact_keys.length > 0
  );

  const activeExecutionId =
    selectedExecutionId || (runsWithArtifacts.length > 0 ? runsWithArtifacts[0].workflow_execution_id : null);

  // 2. Fetch full execution detail with artifacts
  const {
    data: executionDetail,
    isLoading: isLoadingDetail,
    error: detailError,
  } = useQuery({
    queryKey: ['execution-detail', activeExecutionId],
    queryFn: () => historyApi.getExecutionDetail(activeExecutionId!),
    enabled: Boolean(activeExecutionId),
  });

  if (!selectedProjectId) {
    return (
      <EmptyState
        title="No Active Project Selected"
        description="Select or create a project to inspect its multi-agent intelligence artifacts and engineering insights."
      />
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xl)' }}>
      {/* Workspace Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700 }}>Intelligence Workspace</h1>
          <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Unified analytical presentation layer for multi-agent requirements, architecture, database, risk, and quality insights.
          </p>
        </div>

        {onNavigate && (
          <Button
            variant="primary"
            icon={<PlayCircle size={15} />}
            onClick={() => onNavigate('workflows')}
          >
            Launch New Analysis
          </Button>
        )}
      </div>

      {historyError && (
        <ErrorAlert
          error={historyError as any}
          onRetry={() => refetchHistory()}
          onChooseAnotherProject={() => {
            if (handleStaleProject) {
              handleStaleProject(selectedProjectId || undefined);
            }
            if (onNavigate) {
              onNavigate('overview');
            }
          }}
          onCreateProject={() => {
            if (openCreateProject) {
              openCreateProject();
            } else if (onNavigate) {
              onNavigate('overview');
            }
          }}
        />
      )}
      {detailError && <ErrorAlert error={detailError as any} />}

      {isLoadingHistory ? (
        <LoadingSpinner label="Loading intelligence artifacts..." />
      ) : runsWithArtifacts.length === 0 ? (
        <EmptyState
          icon={<Brain size={36} />}
          title="No Intelligence Artifacts Generated Yet"
          description="Execute a workflow in Workflow Studio (such as Software Design or Project Estimation) to generate multi-agent intelligence artifacts."
          actionLabel="Go to Workflow Studio"
          onAction={() => onNavigate && onNavigate('workflows')}
        />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
          {/* Analysis Run Selector Strip */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0.65rem 1rem',
              background: 'var(--bg-surface-subtle)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              flexWrap: 'wrap',
              gap: '0.75rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              <History size={16} />
              <span>Select Analysis Run:</span>
              <select
                className="form-select"
                style={{ width: '320px', padding: '0.3rem 0.6rem', fontSize: '0.825rem' }}
                value={activeExecutionId || ''}
                onChange={(e) => setSelectedExecutionId(e.target.value)}
                aria-label="Select intelligence execution run"
              >
                {runsWithArtifacts.map((run) => (
                  <option key={run.workflow_execution_id} value={run.workflow_execution_id}>
                    {run.workflow_id} ({run.status}) — {new Date(run.started_at).toLocaleString()}
                  </option>
                ))}
              </select>
            </div>

            {executionDetail && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Badge variant={executionDetail.status}>{executionDetail.status}</Badge>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                  {executionDetail.workflow_execution_id}
                </span>
              </div>
            )}
          </div>

          {/* User-Centric Narrative Pillars */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: 'var(--space-md)',
            }}
          >
            <div
              style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.75rem 1rem',
                borderLeft: '3px solid var(--accent-primary)',
              }}
            >
              <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--accent-primary)', textTransform: 'uppercase' }}>
                1. What Was Analyzed
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                Canonical project requirements, architecture patterns, and domain constraints.
              </div>
            </div>

            <div
              style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.75rem 1rem',
                borderLeft: '3px solid var(--accent-cyan)',
              }}
            >
              <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--accent-cyan)', textTransform: 'uppercase' }}>
                2. What Was Found
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                Synthesized multi-agent design recommendations, schema definitions, and risk bands.
              </div>
            </div>

            <div
              style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.75rem 1rem',
                borderLeft: '3px solid var(--sdlc-design)',
              }}
            >
              <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--sdlc-design)', textTransform: 'uppercase' }}>
                3. Why It Matters
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                Establishes deterministic, verified system baselines prior to code generation.
              </div>
            </div>

            <div
              style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.75rem 1rem',
                borderLeft: '3px solid var(--status-completed)',
              }}
            >
              <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--status-completed)', textTransform: 'uppercase' }}>
                4. What To Do Next
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                Review artifact tabs below or adjust requirements in Specification workspace.
              </div>
            </div>
          </div>

          {/* Artifact Viewer Engine */}
          {isLoadingDetail ? (
            <LoadingSpinner label="Loading artifact details..." />
          ) : executionDetail?.artifacts && Object.keys(executionDetail.artifacts).length > 0 ? (
            <ArtifactViewer artifacts={executionDetail.artifacts} />
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              No structured artifacts found for this execution.
            </div>
          )}
        </div>
      )}
    </div>
  );
};
