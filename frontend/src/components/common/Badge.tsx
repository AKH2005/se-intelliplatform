import React from 'react';

export type BadgeVariant =
  | 'draft'
  | 'in-progress'
  | 'in_progress'
  | 'running'
  | 'completed'
  | 'approved'
  | 'implemented'
  | 'success'
  | 'partial'
  | 'partial_success'
  | 'deferred'
  | 'failed'
  | 'rejected'
  | 'critical'
  | 'low'
  | 'medium'
  | 'high'
  | 'fact'
  | 'interpretation'
  | 'recommendation'
  | 'limitation'
  | 'neutral';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant | string;
  className?: string;
  style?: React.CSSProperties;
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'neutral', className = '', style }) => {
  const normalizedVariant = variant.toLowerCase().replace(/\s+/g, '_');
  const variantClass = `badge-${normalizedVariant}`;

  return <span className={`badge ${variantClass} ${className}`} style={style}>{children}</span>;
};
