import React from 'react';

export type BadgeVariant =
  | 'draft'
  | 'in-progress'
  | 'in_progress'
  | 'running'
  | 'pending'
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
  | 'neutral'
  | 'violet'
  | 'info';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant | string;
  withDot?: boolean;
  icon?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  withDot = false,
  icon,
  className = '',
  style,
}) => {
  const normalizedVariant = variant.toLowerCase().replace(/\s+/g, '_');
  const variantClass = `badge-${normalizedVariant}`;

  return (
    <span className={`badge ${variantClass} ${className}`.trim()} style={style}>
      {withDot && <span className="badge-dot" aria-hidden="true" />}
      {icon && <span style={{ display: 'inline-flex', alignItems: 'center' }}>{icon}</span>}
      {children}
    </span>
  );
};
