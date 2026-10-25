import React from 'react';
import { WorkflowStepMetadata } from '../../types/workflow';
import { CheckCircle2, GitBranch, ArrowRight } from 'lucide-react';

interface WorkflowDagViewProps {
  steps: WorkflowStepMetadata[];
  completedStepIds?: string[];
  activeStepId?: string | null;
}

export const WorkflowDagView: React.FC<WorkflowDagViewProps> = ({
  steps,
  completedStepIds = [],
  activeStepId,
}) => {
  if (!steps || steps.length === 0) {
    return (
      <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
        No DAG steps defined for this workflow.
      </div>
    );
  }

  return (
    <div
      style={{
        background: 'var(--bg-surface-subtle)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        padding: 'var(--space-md)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-sm)',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '0.78rem',
          fontWeight: 600,
          color: 'var(--text-secondary)',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '0.5rem',
        }}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <GitBranch size={14} color="var(--accent-primary)" />
          Execution DAG Topology ({steps.length} Steps)
        </span>
        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
          Synchronous Dependency Pipeline
        </span>
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          overflowX: 'auto',
          padding: 'var(--space-sm) 0',
        }}
      >
        {steps.map((step, index) => {
          const isCompleted = completedStepIds.includes(step.step_id);
          const isActive = activeStepId === step.step_id;

          return (
            <React.Fragment key={step.step_id}>
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.25rem',
                  padding: '0.65rem 0.85rem',
                  borderRadius: 'var(--radius-sm)',
                  background: isActive
                    ? 'var(--bg-surface-active)'
                    : isCompleted
                    ? 'rgba(16, 185, 129, 0.08)'
                    : 'var(--bg-surface)',
                  border: isActive
                    ? '1px solid var(--accent-primary)'
                    : isCompleted
                    ? '1px solid rgba(16, 185, 129, 0.3)'
                    : '1px solid var(--border-subtle)',
                  minWidth: '160px',
                  boxShadow: isActive ? '0 0 10px rgba(99, 102, 241, 0.3)' : undefined,
                  transition: 'all var(--transition-fast)',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '0.7rem',
                    color: 'var(--text-muted)',
                  }}
                >
                  <span style={{ fontWeight: 600 }}>Step {index + 1}</span>
                  {isCompleted ? (
                    <CheckCircle2 size={13} color="var(--status-completed)" />
                  ) : (
                    <span
                      style={{
                        fontSize: '0.62rem',
                        padding: '0.1rem 0.3rem',
                        borderRadius: '3px',
                        background: step.required ? 'rgba(99, 102, 241, 0.15)' : 'rgba(255, 255, 255, 0.05)',
                        color: step.required ? 'var(--accent-primary)' : 'var(--text-dim)',
                      }}
                    >
                      {step.required ? 'REQUIRED' : 'OPTIONAL'}
                    </span>
                  )}
                </div>

                <div
                  style={{
                    fontSize: '0.82rem',
                    fontWeight: 600,
                    color: 'var(--text-primary)',
                    fontFamily: 'monospace',
                  }}
                >
                  {step.agent_id}
                </div>

                <div
                  style={{
                    fontSize: '0.68rem',
                    color: 'var(--text-dim)',
                    marginTop: '0.2rem',
                  }}
                >
                  {step.depends_on.length > 0
                    ? `Depends on: ${step.depends_on.join(', ')}`
                    : 'Root entry step'}
                </div>
              </div>

              {index < steps.length - 1 && (
                <div style={{ display: 'flex', alignItems: 'center', color: 'var(--text-dim)' }}>
                  <ArrowRight size={16} />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
