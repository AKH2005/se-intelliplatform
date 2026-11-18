import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useProject } from '../context/ProjectContext';
import { requirementsApi } from '../services/requirementsApi';
import { contextApi } from '../services/contextApi';
import { RequirementList } from '../components/requirements/RequirementList';
import { CreateRequirementModal } from '../components/requirements/CreateRequirementModal';
import { SnapshotModal } from '../components/requirements/SnapshotModal';
import { ProjectContextPanel } from '../components/projects/ProjectContextPanel';
import { ArchitectureTopologyView } from '../components/visualization/ArchitectureTopologyView';
import { ErdPreview } from '../components/visualization/ErdPreview';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { NavigationTab } from '../components/layout/Sidebar';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { EmptyState } from '../components/common/EmptyState';
import { Button } from '../components/common/Button';
import { RequirementCreate } from '../types/requirement';
import { ContextSnapshotCreate } from '../types/context';
import { isProjectNotFoundError } from '../utils/projectRecovery';
import {
  FileText,
  Sliders,
  Camera,
  Layers,
  Plus,
  Sparkles,
} from 'lucide-react';
import { CreateTaskModal } from '../components/requirements/CreateTaskModal';

type SpecTab = 'requirements' | 'context' | 'snapshots' | 'blueprints';

interface SpecificationWorkspaceProps {
  onNavigate?: (tab: NavigationTab) => void;
}

export const SpecificationWorkspace: React.FC<SpecificationWorkspaceProps> = ({
  onNavigate: _onNavigate,
}) => {
  const queryClient = useQueryClient();
  const { selectedProjectId, selectedProject, handleStaleProject } = useProject();

  const [activeTab, setActiveTab] = useState<SpecTab>(() => {
    if (typeof window !== 'undefined' && window.location.hash === '#blueprints') {
      return 'blueprints';
    }
    return 'requirements';
  });

  useEffect(() => {
    const handleHashChange = () => {
      if (typeof window !== 'undefined' && window.location.hash === '#blueprints') {
        setActiveTab('blueprints');
      }
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);
  const [isCreateReqOpen, setIsCreateReqOpen] = useState(false);
  const [isCreateTaskOpen, setIsCreateTaskOpen] = useState(false);
  const [isSnapshotOpen, setIsSnapshotOpen] = useState(false);

  // 1. Fetch requirements for active project
  const {
    data: requirements = [],
    isLoading: isLoadingRequirements,
    error: reqError,
  } = useQuery({
    queryKey: ['project-requirements', selectedProjectId],
    queryFn: () => requirementsApi.list(selectedProjectId!),
    enabled: Boolean(selectedProjectId),
  });

  // 2. Fetch context for active project
  const {
    data: context,
    isLoading: isLoadingContext,
    error: contextError,
  } = useQuery({
    queryKey: ['project-context', selectedProjectId],
    queryFn: () => contextApi.getContext(selectedProjectId!),
    enabled: Boolean(selectedProjectId),
  });

  // 3. Fetch snapshots for active project
  const {
    data: snapshots = [],
    isLoading: isLoadingSnapshots,
    error: snapshotsError,
  } = useQuery({
    queryKey: ['project-snapshots', selectedProjectId],
    queryFn: () => contextApi.listSnapshots(selectedProjectId!),
    enabled: Boolean(selectedProjectId),
  });

  React.useEffect(() => {
    if (
      (reqError && isProjectNotFoundError(reqError)) ||
      (contextError && isProjectNotFoundError(contextError))
    ) {
      handleStaleProject?.(selectedProjectId || undefined);
    }
  }, [reqError, contextError, selectedProjectId, handleStaleProject]);

  // Mutations
  const createRequirementMutation = useMutation({
    mutationFn: (data: RequirementCreate) => requirementsApi.create(selectedProjectId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project-requirements', selectedProjectId] });
      queryClient.invalidateQueries({ queryKey: ['project-context', selectedProjectId] });
    },
  });

  const archiveRequirementMutation = useMutation({
    mutationFn: (reqId: string) => requirementsApi.archive(selectedProjectId!, reqId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project-requirements', selectedProjectId] });
      queryClient.invalidateQueries({ queryKey: ['project-context', selectedProjectId] });
    },
  });

  const createSnapshotMutation = useMutation({
    mutationFn: (data: ContextSnapshotCreate) =>
      contextApi.createSnapshot(selectedProjectId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project-snapshots', selectedProjectId] });
      queryClient.invalidateQueries({ queryKey: ['project-context', selectedProjectId] });
    },
  });

  if (!selectedProjectId) {
    return (
      <EmptyState
        title="No Active Project Selected"
        description="Select or create a project to inspect and manage its software requirements and system specifications."
      />
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xl)' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700 }}>
            Specification & Context Workspace
          </h1>
          <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Source of truth for system requirements, canonical context snapshots, and architectural blueprints.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <Button
            variant="secondary"
            icon={<Sparkles size={15} color="var(--accent-cyan)" />}
            onClick={() => setIsCreateTaskOpen(true)}
            style={{ fontWeight: 600 }}
          >
            Add Feature with AI
          </Button>
          <Button
            variant="secondary"
            icon={<Camera size={15} />}
            onClick={() => setIsSnapshotOpen(true)}
          >
            Create Snapshot
          </Button>
          <Button
            variant="primary"
            icon={<Plus size={15} />}
            onClick={() => setIsCreateReqOpen(true)}
          >
            New Requirement
          </Button>
        </div>
      </div>

      {reqError && <ErrorAlert error={reqError as any} />}
      {contextError && <ErrorAlert error={contextError as any} />}
      {snapshotsError && <ErrorAlert error={snapshotsError as any} />}

      {/* Tabs navigation */}
      <div className="tabs-nav" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'requirements'}
          className={`tab-btn ${activeTab === 'requirements' ? 'active' : ''}`}
          onClick={() => setActiveTab('requirements')}
        >
          <FileText size={16} />
          <span>Requirements ({requirements.length})</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'context'}
          className={`tab-btn ${activeTab === 'context' ? 'active' : ''}`}
          onClick={() => setActiveTab('context')}
        >
          <Sliders size={16} />
          <span>Canonical Context & Stats</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'snapshots'}
          className={`tab-btn ${activeTab === 'snapshots' ? 'active' : ''}`}
          onClick={() => setActiveTab('snapshots')}
        >
          <Camera size={16} />
          <span>Versioned Snapshots ({snapshots.length})</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'blueprints'}
          className={`tab-btn ${activeTab === 'blueprints' ? 'active' : ''}`}
          onClick={() => setActiveTab('blueprints')}
        >
          <Layers size={16} />
          <span>Architecture & ERD Blueprints</span>
        </button>
      </div>

      {/* Tab 1: Requirements List */}
      {activeTab === 'requirements' && (
        <>
          {isLoadingRequirements ? (
            <LoadingSpinner label="Loading project requirements..." />
          ) : (
            <RequirementList
              requirements={requirements}
              onOpenCreate={() => setIsCreateReqOpen(true)}
              onArchive={async (reqId) => {
                await archiveRequirementMutation.mutateAsync(reqId);
              }}
              isLoading={isLoadingRequirements}
            />
          )}
        </>
      )}

      {/* Tab 2: Canonical Context Panel */}
      {activeTab === 'context' && (
        <ProjectContextPanel
          context={context || null}
          snapshots={snapshots}
          onOpenCreateSnapshot={() => setIsSnapshotOpen(true)}
          isLoading={isLoadingContext}
        />
      )}

      {/* Tab 3: Snapshots List */}
      {activeTab === 'snapshots' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ fontSize: '0.95rem', fontWeight: 600 }}>
              Immutable Context Snapshots ({snapshots.length})
            </div>
            <Button
              variant="secondary"
              size="sm"
              icon={<Camera size={14} />}
              onClick={() => setIsSnapshotOpen(true)}
            >
              Take Snapshot
            </Button>
          </div>

          {isLoadingSnapshots ? (
            <LoadingSpinner label="Loading snapshots..." />
          ) : snapshots.length === 0 ? (
            <EmptyState
              icon={<Camera size={32} />}
              title="No Snapshots Recorded"
              description="Snapshots freeze project requirements and metadata for deterministic, reproducible workflow runs."
              actionLabel="Create Snapshot"
              onAction={() => setIsSnapshotOpen(true)}
            />
          ) : (
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Version</th>
                    <th>Snapshot ID</th>
                    <th>Reason / Label</th>
                    <th>Requirements Count</th>
                    <th>Created At</th>
                  </tr>
                </thead>
                <tbody>
                  {snapshots.map((snap) => (
                    <tr key={snap.id}>
                      <td style={{ fontWeight: 600 }}>v{snap.version}</td>
                      <td style={{ fontFamily: 'monospace', fontSize: '0.78rem' }}>{snap.id}</td>
                      <td style={{ color: 'var(--text-secondary)' }}>
                        {snap.summary || 'Context Snapshot'}
                      </td>
                      <td>{snap.context_data?.requirements?.length ?? 0} requirements</td>
                      <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                        {new Date(snap.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Architecture & ERD Blueprints */}
      {activeTab === 'blueprints' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xl)' }}>
          <ArchitectureTopologyView />
          <ErdPreview />
        </div>
      )}

      {/* Modals */}
      <CreateRequirementModal
        isOpen={isCreateReqOpen}
        onClose={() => setIsCreateReqOpen(false)}
        onSubmit={async (data) => {
          await createRequirementMutation.mutateAsync(data);
        }}
      />

      <SnapshotModal
        isOpen={isSnapshotOpen}
        onClose={() => setIsSnapshotOpen(false)}
        onSubmit={async (data) => {
          await createSnapshotMutation.mutateAsync(data);
        }}
      />

      {selectedProjectId && (
        <CreateTaskModal
          isOpen={isCreateTaskOpen}
          onClose={() => setIsCreateTaskOpen(false)}
          projectId={selectedProjectId}
          projectName={selectedProject?.name}
          onTaskCreated={() => {
            queryClient.invalidateQueries({ queryKey: ['project-requirements', selectedProjectId] });
            queryClient.invalidateQueries({ queryKey: ['project-context', selectedProjectId] });
          }}
        />
      )}
    </div>
  );
};
