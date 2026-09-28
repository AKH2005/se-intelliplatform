import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useProject } from '../context/ProjectContext';
import { projectsApi } from '../services/projectsApi';
import { contextApi } from '../services/contextApi';
import { ProjectContextPanel } from '../components/projects/ProjectContextPanel';
import { CreateProjectModal } from '../components/projects/CreateProjectModal';
import { SnapshotModal } from '../components/requirements/SnapshotModal';
import { Card, CardBody, CardHeader } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { FolderKanban, Plus } from 'lucide-react';
import { ProjectCreate } from '../types/project';
import { ContextSnapshotCreate } from '../types/context';

export const ProjectWorkspace: React.FC = () => {
  const queryClient = useQueryClient();
  const { selectedProjectId, setSelectedProjectId, setSelectedProject } = useProject();

  const [isCreateProjectOpen, setIsCreateProjectOpen] = useState(false);
  const [isSnapshotOpen, setIsSnapshotOpen] = useState(false);

  // 1. Fetch projects
  const {
    data: projects = [],
    isLoading: isLoadingProjects,
    error: projectsError,
  } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(),
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
  const { data: snapshots = [] } = useQuery({
    queryKey: ['project-snapshots', selectedProjectId],
    queryFn: () => contextApi.listSnapshots(selectedProjectId!),
    enabled: Boolean(selectedProjectId),
  });

  // Mutations
  const createProjectMutation = useMutation({
    mutationFn: (data: ProjectCreate) => projectsApi.create(data),
    onSuccess: (newProject) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setSelectedProjectId(newProject.id);
      setSelectedProject(newProject);
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

  return (
    <div className="view-content">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1>Projects & Context Workspace</h1>
          <p>
            Inspect canonical project context, deterministic progress metrics, and versioned snapshots.
          </p>
        </div>
        <Button
          variant="primary"
          icon={<Plus size={16} />}
          onClick={() => setIsCreateProjectOpen(true)}
        >
          Create Project
        </Button>
      </div>

      {projectsError && <ErrorAlert error={projectsError as any} />}
      {contextError && <ErrorAlert error={contextError as any} />}

      {isLoadingProjects ? (
        <LoadingSpinner label="Loading projects..." />
      ) : projects.length === 0 ? (
        <EmptyState
          icon={<FolderKanban size={36} />}
          title="Create your first project to begin"
          description="Projects represent bounded system domains with versioned requirements and multi-agent workflow capabilities."
          actionLabel="Create Project"
          onAction={() => setIsCreateProjectOpen(true)}
        />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xl)' }}>
          {/* Projects Overview Carousel/Grid */}
          <div>
            <h3 style={{ fontSize: '1rem', marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
              All Projects ({projects.length})
            </h3>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '1rem',
              }}
            >
              {projects.map((proj) => {
                const isSelected = proj.id === selectedProjectId;
                return (
                  <Card
                    key={proj.id}
                    onClick={() => {
                      setSelectedProjectId(proj.id);
                      setSelectedProject(proj);
                    }}
                    style={{
                      cursor: 'pointer',
                      borderColor: isSelected ? 'var(--accent-primary)' : 'var(--border-subtle)',
                      background: isSelected ? 'var(--bg-surface-active)' : 'var(--bg-glass-card)',
                      boxShadow: isSelected ? '0 0 15px -3px var(--accent-primary-glow)' : undefined,
                    }}
                  >
                    <CardHeader>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{proj.name}</div>
                      <Badge variant={proj.status}>{proj.status}</Badge>
                    </CardHeader>
                    <CardBody>
                      <p
                        style={{
                          fontSize: '0.825rem',
                          color: 'var(--text-secondary)',
                          marginBottom: '0.75rem',
                          minHeight: '36px',
                        }}
                      >
                        {proj.description || 'No description provided.'}
                      </p>
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          fontSize: '0.75rem',
                          color: 'var(--text-muted)',
                        }}
                      >
                        <span>Created: {new Date(proj.created_at).toLocaleDateString()}</span>
                        {isSelected && <span style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>Active</span>}
                      </div>
                    </CardBody>
                  </Card>
                );
              })}
            </div>
          </div>

          {/* Canonical Context Panel for Selected Project */}
          {selectedProjectId && (
            <ProjectContextPanel
              context={context || null}
              snapshots={snapshots}
              onOpenCreateSnapshot={() => setIsSnapshotOpen(true)}
              isLoading={isLoadingContext}
            />
          )}
        </div>
      )}

      {/* Modals */}
      <CreateProjectModal
        isOpen={isCreateProjectOpen}
        onClose={() => setIsCreateProjectOpen(false)}
        onSubmit={async (data) => {
          await createProjectMutation.mutateAsync(data);
        }}
      />

      <SnapshotModal
        isOpen={isSnapshotOpen}
        onClose={() => setIsSnapshotOpen(false)}
        onSubmit={async (data) => {
          await createSnapshotMutation.mutateAsync(data);
        }}
      />
    </div>
  );
};
