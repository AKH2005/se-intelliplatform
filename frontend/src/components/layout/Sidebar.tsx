import React from 'react';
import {
  FolderKanban,
  FileText,
  PlayCircle,
  History,
  Info,
} from 'lucide-react';

export type NavigationTab = 'projects' | 'requirements' | 'workflows' | 'history';

interface SidebarProps {
  activeTab: NavigationTab;
  onSelectTab: (tab: NavigationTab) => void;
  hasActiveProject: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  hasActiveProject,
}) => {
  const navItems = [
    {
      id: 'projects' as NavigationTab,
      label: 'Projects & Context',
      icon: <FolderKanban size={18} />,
      requiresProject: false,
    },
    {
      id: 'requirements' as NavigationTab,
      label: 'Requirements',
      icon: <FileText size={18} />,
      requiresProject: true,
    },
    {
      id: 'workflows' as NavigationTab,
      label: 'Workflow Studio',
      icon: <PlayCircle size={18} />,
      requiresProject: true,
    },
    {
      id: 'history' as NavigationTab,
      label: 'Run History',
      icon: <History size={18} />,
      requiresProject: true,
    },
  ];

  return (
    <aside
      style={{
        width: '240px',
        borderRight: '1px solid var(--border-subtle)',
        background: 'var(--bg-secondary)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: 'var(--space-md) var(--space-sm)',
        flexShrink: 0,
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xs)' }}>
        <div
          style={{
            padding: 'var(--space-xs) var(--space-md)',
            fontSize: '0.75rem',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            color: 'var(--text-muted)',
            marginBottom: '0.5rem',
          }}
        >
          Workspace
        </div>

        {navItems.map((item) => {
          const isActive = activeTab === item.id;
          const isDisabled = item.requiresProject && !hasActiveProject;

          return (
            <button
              key={item.id}
              onClick={() => !isDisabled && onSelectTab(item.id)}
              disabled={isDisabled}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.65rem 0.85rem',
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                background: isActive ? 'var(--bg-surface-active)' : 'transparent',
                color: isActive
                  ? 'var(--text-primary)'
                  : isDisabled
                  ? 'var(--text-dim)'
                  : 'var(--text-secondary)',
                fontWeight: isActive ? 600 : 500,
                fontSize: '0.875rem',
                cursor: isDisabled ? 'not-allowed' : 'pointer',
                textAlign: 'left',
                transition: 'all var(--transition-fast)',
                borderLeft: isActive
                  ? '3px solid var(--accent-primary)'
                  : '3px solid transparent',
              }}
              title={isDisabled ? 'Select or create a project first' : undefined}
            >
              <span style={{ color: isActive ? 'var(--accent-primary)' : 'inherit' }}>
                {item.icon}
              </span>
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>

      <div
        style={{
          padding: 'var(--space-md)',
          background: 'var(--bg-surface)',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-subtle)',
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.4rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--text-secondary)' }}>
          <Info size={14} />
          <span style={{ fontWeight: 600 }}>Architecture Mode</span>
        </div>
        <div>FastAPI Python Backend</div>
        <div>Synchronous Multi-Agent Pipelines</div>
      </div>
    </aside>
  );
};
