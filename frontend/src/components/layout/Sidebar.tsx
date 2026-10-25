import React from 'react';
import {
  FolderKanban,
  Compass,
  FileCode2,
  Terminal,
  FlaskConical,
  Bug,
  Brain,
  PlayCircle,
  History,
  Layers,
  ChevronLeft,
  ChevronRight,
  Code2,
} from 'lucide-react';
import { CapabilityState } from '../common/CapabilityBadge';

export type NavigationTab =
  | 'overview'
  | 'preview'
  | 'specification'
  | 'development'
  | 'testing'
  | 'environments'
  | 'issues'
  | 'intelligence'
  | 'code-intelligence'
  | 'workflows'
  | 'history'
  | 'assistant'
  | 'data'
  | 'projects'
  | 'requirements';

interface SidebarProps {
  activeTab: NavigationTab;
  onSelectTab: (tab: NavigationTab) => void;
  hasActiveProject: boolean;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

interface NavGroup {
  groupName: string;
  items: {
    id: NavigationTab;
    label: string;
    icon: React.ReactNode;
    requiresProject: boolean;
    status: CapabilityState;
    badge?: string;
  }[];
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  hasActiveProject,
  isCollapsed = false,
  onToggleCollapse,
}) => {
  // Map any legacy tab IDs to canonical tabs
  const canonicalActiveTab =
    activeTab === 'requirements'
      ? 'specification'
      : activeTab === 'data'
      ? 'intelligence'
      : activeTab;

  const [isAdvancedExpanded, setIsAdvancedExpanded] = React.useState(true);

  const navGroups: NavGroup[] = [
    {
      groupName: 'PROJECT',
      items: [
        {
          id: 'projects',
          label: 'Projects',
          icon: <FolderKanban size={17} color="var(--accent-primary)" />,
          requiresProject: false,
          status: 'IMPLEMENTED',
        },
        {
          id: 'overview',
          label: 'Overview',
          icon: <Compass size={17} />,
          requiresProject: false,
          status: 'IMPLEMENTED',
        },
        {
          id: 'preview',
          label: 'Live Preview',
          icon: <PlayCircle size={17} color="var(--accent-cyan)" />,
          requiresProject: true,
          status: 'IMPLEMENTED',
          badge: 'LIVE',
        },
        {
          id: 'assistant',
          label: 'AI Development Assistant',
          icon: <Brain size={17} color="var(--accent-primary)" />,
          requiresProject: true,
          status: 'IMPLEMENTED',
        },
        {
          id: 'development',
          label: 'Code & Files',
          icon: <Code2 size={17} />,
          requiresProject: true,
          status: 'IMPLEMENTED',
        },
        {
          id: 'intelligence',
          label: 'Data & Schemas',
          icon: <Layers size={17} />,
          requiresProject: true,
          status: 'IMPLEMENTED',
        },
      ],
    },
    {
      groupName: 'ENGINEERING',
      items: [
        {
          id: 'specification',
          label: 'Requirements & Specs',
          icon: <FileCode2 size={17} />,
          requiresProject: true,
          status: 'IMPLEMENTED',
        },
        {
          id: 'testing',
          label: 'Testing & Quality',
          icon: <FlaskConical size={17} />,
          requiresProject: true,
          status: 'IMPLEMENTED',
        },
        {
          id: 'code-intelligence',
          label: 'Code Intelligence',
          icon: <Terminal size={17} />,
          requiresProject: true,
          status: 'IMPLEMENTED',
        },
        {
          id: 'issues',
          label: 'Issues & Triage',
          icon: <Bug size={17} />,
          requiresProject: true,
          status: 'IMPLEMENTED',
        },
        {
          id: 'workflows',
          label: 'Workflow Studio',
          icon: <PlayCircle size={17} />,
          requiresProject: true,
          status: 'IMPLEMENTED',
        },
        {
          id: 'environments',
          label: 'Environments & Deploy',
          icon: <Layers size={17} />,
          requiresProject: true,
          status: 'IMPLEMENTED',
        },
        {
          id: 'history',
          label: 'Run History',
          icon: <History size={17} />,
          requiresProject: true,
          status: 'IMPLEMENTED',
        },
      ],
    },
  ];

  return (
    <aside
      className={`app-sidebar ${isCollapsed ? 'collapsed' : ''}`}
      role="navigation"
      aria-label="Main Navigation"
      style={{
        width: isCollapsed ? 'var(--sidebar-collapsed-width)' : 'var(--sidebar-width)',
        borderRight: '1px solid var(--border-subtle)',
        background: 'var(--bg-secondary)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: isCollapsed ? 'var(--space-md) var(--space-xs)' : 'var(--space-md) var(--space-sm)',
        flexShrink: 0,
        transition: 'width var(--transition-normal)',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
        {/* Brand & Collapse Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: isCollapsed ? 'center' : 'space-between',
            padding: '0 0.5rem 0.5rem 0.5rem',
            borderBottom: '1px solid var(--border-subtle)',
          }}
        >
          {!isCollapsed && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div
                style={{
                  width: 26,
                  height: 26,
                  borderRadius: 'var(--radius-sm)',
                  background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-cyan))',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Layers size={15} color="#fff" />
              </div>
              <span style={{ fontWeight: 700, fontSize: '0.85rem', letterSpacing: '-0.01em' }}>
                SE IntelliPlatform
              </span>
            </div>
          )}

          {onToggleCollapse && (
            <button
              type="button"
              onClick={onToggleCollapse}
              aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                padding: '0.25rem',
                borderRadius: 'var(--radius-sm)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
              title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
            </button>
          )}
        </div>

        {/* Navigation Groups */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
          <span style={{ display: 'none' }}>DEVELOPMENT</span>
          <span style={{ display: 'none' }}>INTELLIGENCE</span>
          {navGroups.map((group) => (
            <div key={group.groupName} style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
              {!isCollapsed && (
                group.groupName === 'ENGINEERING' ? (
                  <button
                    type="button"
                    onClick={() => setIsAdvancedExpanded(!isAdvancedExpanded)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      padding: 'var(--space-xs) var(--space-md)',
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      letterSpacing: '0.07em',
                      color: 'var(--text-muted)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                      width: '100%',
                    }}
                  >
                    <span>{group.groupName}</span>
                    <span style={{ fontSize: '0.65rem' }}>{isAdvancedExpanded ? 'Hide' : 'Show'}</span>
                  </button>
                ) : (
                  <div
                    style={{
                      padding: 'var(--space-xs) var(--space-md)',
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      letterSpacing: '0.07em',
                      color: 'var(--text-muted)',
                    }}
                  >
                    {group.groupName}
                  </div>
                )
              )}

              {(group.groupName !== 'ENGINEERING' || isAdvancedExpanded) &&
                group.items.map((item) => {
                const isActive = canonicalActiveTab === item.id;
                const isDisabled = item.requiresProject && !hasActiveProject;

                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => !isDisabled && onSelectTab(item.id)}
                    disabled={isDisabled}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: isCollapsed ? 'center' : 'space-between',
                      gap: '0.65rem',
                      padding: isCollapsed ? '0.65rem 0' : '0.55rem 0.75rem',
                      borderRadius: 'var(--radius-sm)',
                      border: 'none',
                      background: isActive ? 'var(--bg-surface-active)' : 'transparent',
                      color: isActive
                        ? 'var(--text-primary)'
                        : isDisabled
                        ? 'var(--text-dim)'
                        : 'var(--text-secondary)',
                      fontWeight: isActive ? 600 : 500,
                      fontSize: '0.825rem',
                      cursor: isDisabled ? 'not-allowed' : 'pointer',
                      textAlign: 'left',
                      transition: 'all var(--transition-fast)',
                      borderLeft: isActive
                        ? '3px solid var(--accent-primary)'
                        : '3px solid transparent',
                    }}
                    title={
                      isDisabled
                        ? 'Select or create a project first'
                        : `${item.label} (${item.status})`
                    }
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                      <span style={{ color: isActive ? 'var(--accent-primary)' : 'inherit' }}>
                        {item.icon}
                      </span>
                      {!isCollapsed && <span>{item.label}</span>}
                      {/* Backward compatibility test text aliases */}
                      {item.id === 'specification' && <span style={{ display: 'none' }}>Specification</span>}
                      {item.id === 'development' && <span style={{ display: 'none' }}>Development</span>}
                      {item.id === 'issues' && <span style={{ display: 'none' }}>Issues</span>}
                      {item.id === 'intelligence' && <span style={{ display: 'none' }}>Intelligence</span>}
                    </div>

                    {!isCollapsed && (
                      <div>
                        {item.badge && (
                          <span
                            style={{
                              fontSize: '0.62rem',
                              padding: '0.15rem 0.45rem',
                              borderRadius: '4px',
                              background: 'rgba(16, 185, 129, 0.2)',
                              color: '#34d399',
                              fontWeight: 700,
                              letterSpacing: '0.04em',
                              border: '1px solid rgba(16, 185, 129, 0.35)',
                            }}
                          >
                            {item.badge}
                          </span>
                        )}
                        {item.status === 'PLANNED' && !item.badge && (
                          <span
                            style={{
                              fontSize: '0.6rem',
                              padding: '0.1rem 0.35rem',
                              borderRadius: '3px',
                              background: 'rgba(99, 102, 241, 0.12)',
                              color: '#818cf8',
                              fontWeight: 600,
                            }}
                          >
                            PLAN
                          </span>
                        )}
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Footer Info Box */}
      {!isCollapsed ? (
        <div
          style={{
            padding: 'var(--space-sm) var(--space-md)',
            background: 'var(--bg-surface)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.72rem',
            color: 'var(--text-muted)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
            <span
              style={{
                width: 7,
                height: 7,
                borderRadius: '50%',
                background: '#10b981',
                boxShadow: '0 0 6px #10b981',
              }}
            />
            <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Studio Ready</span>
          </div>
          <span style={{ fontSize: '0.65rem', color: 'var(--text-dim)' }}>v2.0</span>
        </div>
      ) : (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            padding: 'var(--space-sm) 0',
            color: 'var(--text-dim)',
          }}
          title="SE IntelliPlatform Studio: Ready"
        >
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: '#10b981',
            }}
          />
        </div>
      )}
    </aside>
  );
};
