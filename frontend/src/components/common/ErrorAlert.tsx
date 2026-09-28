import React from 'react';
import { AlertCircle } from 'lucide-react';
import { ApiError } from '../../types/api';

interface ErrorAlertProps {
  error: Error | ApiError | string | null;
  onRetry?: () => void;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({ error, onRetry }) => {
  if (!error) return null;

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

  return (
    <div
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
