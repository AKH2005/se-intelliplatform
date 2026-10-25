import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  label?: string;
  size?: number;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  label = 'Loading data...',
  size = 28,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0.75rem',
        padding: '2.5rem 1rem',
        color: 'var(--text-muted)',
      }}
    >
      <Loader2 size={size} className="animate-spin" color="var(--accent-primary)" />
      {label && <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>{label}</span>}
    </div>
  );
};
