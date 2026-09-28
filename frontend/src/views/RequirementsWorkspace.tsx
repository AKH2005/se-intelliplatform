import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useProject } from '../context/ProjectContext';
import { requirementsApi } from '../services/requirementsApi';
import { RequirementList } from '../components/requirements/RequirementList';
import { CreateRequirementModal } from '../components/requirements/CreateRequirementModal';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { EmptyState } from '../components/common/EmptyState';
import { RequirementCreate } from '../types/requirement';

export const RequirementsWorkspace: React.FC = () => {
  const queryClient = useQueryClient();
  const { selectedProjectId } = useProject();

  const [isCreateOpen, setIsCreateOpen] = useState(false);

  // Fetch requirements for active project
  const {
    data: requirements = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ['project-requirements', selectedProjectId],
    queryFn: () => requirementsApi.list(selectedProjectId!),
    enabled: Boolean(selectedProjectId),
  });

  // Create requirement mutation
  const createMutation = useMutation({
    mutationFn: (data: RequirementCreate) => requirementsApi.create(selectedProjectId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project-requirements', selectedProjectId] });
      queryClient.invalidateQueries({ queryKey: ['project-context', selectedProjectId] });
    },
  });

  // Archive requirement mutation
  const archiveMutation = useMutation({
    mutationFn: (reqId: string) => requirementsApi.archive(selectedProjectId!, reqId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project-requirements', selectedProjectId] });
      queryClient.invalidateQueries({ queryKey: ['project-context', selectedProjectId] });
    },
  });

  if (!selectedProjectId) {
    return (
      <div className="view-content">
        <EmptyState
          title="No Active Project Selected"
          description="Select or create a project to inspect and manage its software requirements."
        />
      </div>
    );
  }

  return (
    <div className="view-content">
      <div>
        <h1>Requirements Workspace</h1>
        <p>
          Manage functional, non-functional, and constraint requirements that compose the canonical Project Context.
        </p>
      </div>

      {error && <ErrorAlert error={error as any} />}

      {isLoading ? (
        <LoadingSpinner label="Loading project requirements..." />
      ) : (
        <RequirementList
          requirements={requirements}
          onOpenCreate={() => setIsCreateOpen(true)}
          onArchive={async (reqId) => {
            await archiveMutation.mutateAsync(reqId);
          }}
          isLoading={isLoading}
        />
      )}

      <CreateRequirementModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSubmit={async (data) => {
          await createMutation.mutateAsync(data);
        }}
      />
    </div>
  );
};
