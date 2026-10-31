import React from 'react';

export interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  style?: React.CSSProperties;
  variant?: 'glass' | 'solid' | 'elevated';
  interactive?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  onClick,
  style,
  variant = 'glass',
  interactive = false,
}) => {
  const variantClass = variant === 'solid' ? 'card-solid' : variant === 'elevated' ? 'card-elevated' : '';
  const interactiveClass = interactive || Boolean(onClick) ? 'card-interactive' : '';

  return (
    <div
      className={`card ${variantClass} ${interactiveClass} ${className}`.trim()}
      onClick={onClick}
      style={style}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<{
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}> = ({ children, className = '', style }) => (
  <div className={`card-header ${className}`.trim()} style={style}>
    {children}
  </div>
);

export const CardTitle: React.FC<{
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}> = ({ children, className = '', style }) => (
  <div className={`card-title ${className}`.trim()} style={style}>
    {children}
  </div>
);

export const CardSubtitle: React.FC<{
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}> = ({ children, className = '', style }) => (
  <div className={`card-subtitle ${className}`.trim()} style={style}>
    {children}
  </div>
);

export const CardBody: React.FC<{
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}> = ({ children, className = '', style }) => (
  <div className={`card-body ${className}`.trim()} style={style}>
    {children}
  </div>
);

export const CardFooter: React.FC<{
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}> = ({ children, className = '', style }) => (
  <div className={`card-footer ${className}`.trim()} style={style}>
    {children}
  </div>
);
