import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useProject } from '../context/ProjectContext';
import { historyApi } from '../services/historyApi';
import { RunHistoryList } from '../components/history/RunHistoryList';
import { RunDetailModal } from '../components/history/RunDetailModal';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { EmptyState } from '../components/common/EmptyState';

export const RunHistory: React.FC = () => {
  const { selectedProjectId } = useProject();
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null);

  // Fetch project-scoped workflow execution history
  const {
    data: historyData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['project-workflow-history', selectedProjectId],
    queryFn: () => historyApi.listProjectHistory(selectedProjectId!, { limit: 50, offset: 0 }),
    enabled: Boolean(selectedProjectId),
  });

  if (!selectedProjectId) {
    return (
      <div className="view-content">
        <EmptyState
          title="No Active Project Selected"
          description="Select a project to review historical multi-agent workflow execution runs."
        />
      </div>
    );
  }

  return (
    <div className="view-content">
      <div>
        <h1>Run History & Audit Trail</h1>
        <p>
          Authoritative audit records of multi-agent pipeline executions, artifact provenance, and terminal statuses.
        </p>
      </div>

      {error && <ErrorAlert error={error as any} />}

      {isLoading ? (
        <LoadingSpinner label="Loading execution history..." />
      ) : (
        <RunHistoryList
          items={historyData?.items || []}
          total={historyData?.total || 0}
          onSelectRun={(id) => setSelectedExecutionId(id)}
          isLoading={isLoading}
        />
      )}

      <RunDetailModal
        executionId={selectedExecutionId}
        onClose={() => setSelectedExecutionId(null)}
      />
    </div>
  );
};
