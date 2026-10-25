import React from 'react';

export type CapabilityState = 'IMPLEMENTED' | 'PLANNED' | 'COMING SOON' | 'UNAVAILABLE';

interface CapabilityBadgeProps {
  status: CapabilityState;
  size?: 'sm' | 'md';
}

export const CapabilityBadge: React.FC<CapabilityBadgeProps> = ({ status, size = 'sm' }) => {
  let className = 'badge-implemented';
  if (status === 'PLANNED') {
    className = 'badge-planned';
  } else if (status === 'COMING SOON') {
    className = 'badge-coming-soon';
  } else if (status === 'UNAVAILABLE') {
    className = 'badge-unavailable';
  }

  const fontSize = size === 'sm' ? '0.7rem' : '0.8rem';
  const padding = size === 'sm' ? '0.15rem 0.45rem' : '0.25rem 0.65rem';

  return (
    <span
      className={className}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding,
        borderRadius: 'var(--radius-sm)',
        fontSize,
        fontWeight: 600,
        letterSpacing: '0.04em',
        textTransform: 'uppercase',
      }}
    >
      {status}
    </span>
  );
};
