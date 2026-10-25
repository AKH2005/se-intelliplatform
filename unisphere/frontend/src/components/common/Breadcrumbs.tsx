import React from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
}

export const Breadcrumbs: React.FC<BreadcrumbsProps> = ({ items }) => {
  return (
    <nav
      aria-label="Breadcrumb"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.45rem',
        fontSize: '0.8rem',
        color: 'var(--text-muted)',
        marginBottom: '1.25rem',
        flexWrap: 'wrap',
      }}
    >
      <Link
        to="/"
        style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', color: 'var(--text-dim)', transition: 'color 0.15s' }}
      >
        <Home size={14} />
      </Link>

      {items.map((item, index) => {
        const isLast = index === items.length - 1;
        return (
          <React.Fragment key={index}>
            <ChevronRight size={13} style={{ color: 'var(--text-dim)' }} />
            {isLast || !item.href ? (
              <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{item.label}</span>
            ) : (
              <Link to={item.href} style={{ color: 'var(--text-muted)', transition: 'color 0.15s' }}>
                {item.label}
              </Link>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
};
