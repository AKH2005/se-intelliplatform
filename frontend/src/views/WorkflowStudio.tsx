import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useProject } from '../context/ProjectContext';
import { workflowsApi } from '../services/workflowsApi';
import { contextApi } from '../services/contextApi';
import { WorkflowSelector } from '../components/workflows/WorkflowSelector';
import { WorkflowRunner } from '../components/workflows/WorkflowRunner';
import { WorkflowExecutionView } from '../components/workflows/WorkflowExecutionView';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { EmptyState } from '../components/common/EmptyState';
import { WorkflowExecuteRequest, WorkflowResultResponse } from '../types/workflow';

export const WorkflowStudio: React.FC = () => {
  const queryClient = useQueryClient();
  const { selectedProjectId } = useProject();

  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);
  const [executionResult, setExecutionResult] = useState<WorkflowResultResponse | null>(null);
  const [executionError, setExecutionError] = useState<any>(null);

  // 1. Discover workflows dynamically from backend
  const {
    data: workflows = [],
    isLoading: isLoadingWorkflows,
    error: workflowsError,
  } = useQuery({
    queryKey: ['workflows'],
    queryFn: () => workflowsApi.list(),
  });

  // 2. Fetch context snapshots for active project
  const { data: snapshots = [] } = useQuery({
    queryKey: ['project-snapshots', selectedProjectId],
    queryFn: () => contextApi.listSnapshots(selectedProjectId!),
    enabled: Boolean(selectedProjectId),
  });

  // Selected workflow definition
  const selectedWorkflow =
    workflows.find((w) => w.workflow_id === selectedWorkflowId) || (workflows.length > 0 ? workflows[0] : null);

  // Synchronous execution mutation
  const executeMutation = useMutation({
    mutationFn: (request: WorkflowExecuteRequest) =>
      workflowsApi.execute(selectedWorkflow!.workflow_id, request),
    onSuccess: (data) => {
      setExecutionResult(data);
      setExecutionError(null);
      // Invalidate project workflow history so Run History updates immediately
      queryClient.invalidateQueries({
        queryKey: ['project-workflow-history', selectedProjectId],
      });
    },
    onError: (err) => {
      setExecutionError(err);
      setExecutionResult(null);
    },
  });

  if (!selectedProjectId) {
    return (
      <div className="view-content">
        <EmptyState
          title="No Active Project Selected"
          description="Please select or create an active project to configure and execute multi-agent workflows."
        />
      </div>
    );
  }

  return (
    <div className="view-content">
      <div>
        <h1>Workflow Studio</h1>
        <p>
          Discover and synchronously orchestrate deterministic multi-agent SDLC workflows against project context.
        </p>
      </div>

      {workflowsError && <ErrorAlert error={workflowsError as any} />}
      {executionError && <ErrorAlert error={executionError} />}

      {isLoadingWorkflows ? (
        <LoadingSpinner label="Discovering workflow definitions..." />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xl)' }}>
          {/* Dynamic Workflow Selector */}
          <WorkflowSelector
            workflows={workflows}
            selectedWorkflowId={selectedWorkflow ? selectedWorkflow.workflow_id : null}
            onSelectWorkflow={(id) => {
              setSelectedWorkflowId(id);
              setExecutionResult(null);
              setExecutionError(null);
            }}
          />

          {/* Workflow Runner Configuration */}
          {selectedWorkflow && (
            <WorkflowRunner
              workflow={selectedWorkflow}
              projectId={selectedProjectId}
              snapshots={snapshots}
              onExecute={async (req) => {
                await executeMutation.mutateAsync(req);
              }}
              isExecuting={executeMutation.isPending}
            />
          )}

          {/* Execution Result & Artifacts */}
          {executionResult && <WorkflowExecutionView result={executionResult} />}
        </div>
      )}
    </div>
  );
};
