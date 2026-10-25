import React, { useState } from 'react';
import {
  AlertCircle,
  ChevronDown,
  ChevronRight,
  FolderX,
  Plus,
  RefreshCw,
} from 'lucide-react';
import { ApiError } from '../../types/api';
import { isProjectNotFoundError } from '../../utils/projectRecovery';
import { useProjectSafe } from '../../context/ProjectContext';
import { Button } from './Button';

interface ErrorAlertProps {
  error: Error | ApiError | string | null;
  onRetry?: () => void;
  onChooseAnotherProject?: () => void;
  onCreateProject?: () => void;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  error,
  onRetry,
  onChooseAnotherProject,
  onCreateProject,
}) => {
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  const projectContext = useProjectSafe();

  if (!error) return null;

  const isProject404 = isProjectNotFoundError(error);

  let message = 'An unexpected error occurred.';
  let correlationId: string | undefined;
  let status: number | undefined;

  if (typeof error === 'string') {
    message = error;
  } else if (error instanceof ApiError) {
    message = error.message;
    correlationId = error.correlationId;
    status = error.status;
  } else if (error instanceof Error) {
    message = error.message;
  }

  // Graceful Handling for Missing / Stale Project (HTTP 404)
  if (isProject404) {
    const hasExistingProjects = (projectContext?.projects?.length ?? 0) > 0;
    const showChooseAnother = Boolean(onChooseAnotherProject) || hasExistingProjects;

    const handleChooseAnother = () => {
      if (onChooseAnotherProject) {
        onChooseAnotherProject();
      } else if (projectContext?.handleStaleProject) {
        projectContext.handleStaleProject();
      }
    };

    const handleCreateNew = () => {
      if (onCreateProject) {
        onCreateProject();
      } else if (projectContext?.openCreateProject) {
        projectContext.openCreateProject();
      }
    };

    return (
      <div
        className="project-not-found-alert"
        role="alert"
        style={{
          background: 'rgba(239, 68, 68, 0.08)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: 'var(--radius-md)',
          padding: '1.25rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.85rem',
          color: '#fca5a5',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
          <FolderX size={22} style={{ color: '#ef4444', flexShrink: 0, marginTop: 2 }} />
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 600, color: '#f87171', fontSize: '0.95rem', marginBottom: 2 }}>
              Project Not Available
            </div>
            <div style={{ fontSize: '0.875rem', color: '#cbd5e1' }}>
              That project is no longer available.
            </div>
          </div>
        </div>

        {/* Action Buttons: Choose Another Project or Create New Project */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
          {showChooseAnother && (
            <Button
              variant="secondary"
              size="sm"
              onClick={handleChooseAnother}
            >
              Choose Another Project
            </Button>
          )}

          <Button
            variant={showChooseAnother ? 'primary' : 'primary'}
            size="sm"
            icon={<Plus size={14} />}
            onClick={handleCreateNew}
          >
            Create New Project
          </Button>

          {onRetry && (
            <Button
              variant="secondary"
              size="sm"
              icon={<RefreshCw size={13} />}
              onClick={onRetry}
            >
              Retry
            </Button>
          )}
        </div>

        {/* Expandable Technical Details (Raw UUID and HTTP details hidden by default) */}
        <div style={{ borderTop: '1px solid rgba(239, 68, 68, 0.15)', paddingTop: '0.5rem' }}>
          <button
            type="button"
            onClick={() => setShowTechnicalDetails((prev) => !prev)}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              fontSize: '0.75rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: 0,
            }}
            aria-expanded={showTechnicalDetails}
            aria-label="Toggle technical error details"
          >
            {showTechnicalDetails ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            <span>Technical error details</span>
          </button>

          {showTechnicalDetails && (
            <div
              style={{
                marginTop: '0.5rem',
                fontSize: '0.75rem',
                fontFamily: 'monospace',
                background: 'rgba(0, 0, 0, 0.35)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                padding: '0.65rem 0.85rem',
                borderRadius: 'var(--radius-sm)',
                color: '#e2e8f0',
                lineHeight: 1.5,
              }}
            >
              <div>Status: HTTP 404 (Not Found)</div>
              <div>Detail: {message}</div>
              {correlationId && <div>Correlation ID: {correlationId}</div>}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Standard Error Presentation for general errors
  return (
    <div
      role="alert"
      style={{
        background: 'rgba(239, 68, 68, 0.12)',
        border: '1px solid rgba(239, 68, 68, 0.35)',
        borderRadius: 'var(--radius-md)',
        padding: '1rem',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '0.75rem',
        color: '#fca5a5',
      }}
    >
      <AlertCircle size={20} style={{ color: '#ef4444', flexShrink: 0, marginTop: 2 }} />
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 600, color: '#f87171', marginBottom: 2 }}>
          {status ? `Request Failed (HTTP ${status})` : 'Operation Error'}
        </div>
        <div style={{ fontSize: '0.875rem' }}>{message}</div>
        {correlationId && (
          <div
            style={{
              fontSize: '0.75rem',
              color: '#94a3b8',
              marginTop: '0.4rem',
              fontFamily: 'monospace',
            }}
          >
            Correlation ID: {correlationId}
          </div>
        )}
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="btn btn-sm btn-secondary"
          style={{ borderColor: 'rgba(239, 68, 68, 0.4)', color: '#fca5a5' }}
        >
          Retry
        </button>
      )}
    </div>
  );
};
