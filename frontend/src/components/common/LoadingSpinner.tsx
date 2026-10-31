import React from 'react';

export interface LoadingSpinnerProps {
  label?: string;
  description?: string;
  size?: number;
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  label = 'Loading platform data...',
  description,
  size = 32,
  className = '',
}) => {
  return (
    <div className={`loading-container ${className}`.trim()} role="status" aria-live="polite">
      <div
        className="spinner"
        style={{ width: size, height: size }}
        aria-hidden="true"
      />
      {label && (
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontSize: '0.875rem', fontWeight: 550, color: 'var(--text-primary)' }}>
            {label}
          </p>
          {description && (
            <p style={{ fontSize: '0.775rem', color: 'var(--text-muted)', marginTop: 2 }}>
              {description}
            </p>
          )}
        </div>
      )}
    </div>
  );
};
