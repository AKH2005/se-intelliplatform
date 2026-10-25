import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  style?: React.CSSProperties;
}

export const Card: React.FC<CardProps> = ({ children, className = '', onClick, style }) => {
  return (
    <div className={`card ${className}`} onClick={onClick} style={style}>
      {children}
    </div>
  );
};

export const CardHeader: React.FC<{ children: React.ReactNode; className?: string; style?: React.CSSProperties }> = ({
  children,
  className = '',
  style,
}) => <div className={`card-header ${className}`} style={style}>{children}</div>;

export const CardTitle: React.FC<{ children: React.ReactNode; className?: string; style?: React.CSSProperties }> = ({
  children,
  className = '',
  style,
}) => <div className={`card-title ${className}`} style={style}>{children}</div>;

export const CardSubtitle: React.FC<{ children: React.ReactNode; className?: string; style?: React.CSSProperties }> = ({
  children,
  className = '',
  style,
}) => <div className={`card-subtitle ${className}`} style={style}>{children}</div>;

export const CardBody: React.FC<{ children: React.ReactNode; className?: string; style?: React.CSSProperties }> = ({
  children,
  className = '',
  style,
}) => <div className={`card-body ${className}`} style={style}>{children}</div>;

export const CardFooter: React.FC<{ children: React.ReactNode; className?: string; style?: React.CSSProperties }> = ({
  children,
  className = '',
  style,
}) => <div className={`card-footer ${className}`} style={style}>{children}</div>;
