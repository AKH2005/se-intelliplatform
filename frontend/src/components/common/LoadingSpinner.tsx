import React from 'react';

interface LoadingSpinnerProps {
  label?: string;
  size?: number;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  label = 'Loading platform data...',
  size = 32,
}) => {
  return (
    <div className="loading-container">
      <div className="spinner" style={{ width: size, height: size }} />
      {label && <p style={{ fontSize: '0.875rem' }}>{label}</p>}
    </div>
  );
};
