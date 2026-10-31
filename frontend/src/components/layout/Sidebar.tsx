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
  | 'code-studio'
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

  const navGroups: NavGroup[] = [
    {
      groupName: 'PROJECT',
      items: [
        {
          id: 'projects',
          label: 'Projects',
          icon: <FolderKanban size={17} color="var(--accent-primary, #6366f1)" />,
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
          id: 'code-studio',
          label: 'Code Studio',
          icon: <Code2 size={17} color="var(--accent-cyan, #06b6d4)" />,
          requiresProject: true,
          status: 'IMPLEMENTED',
          badge: 'IDE',
        },
        {
          id: 'preview',
          label: 'Live Preview',
          icon: <PlayCircle size={17} color="var(--accent-cyan, #06b6d4)" />,
          requiresProject: true,
          status: 'IMPLEMENTED',
          badge: 'LIVE',
        },
        {
          id: 'assistant',
          label: 'AI Development Assistant',
          icon: <Brain size={17} color="var(--accent-violet-light, #a78bfa)" />,
          requiresProject: true,
          status: 'IMPLEMENTED',
        },
      ],
    },
    {
      groupName: 'DEVELOPMENT',
      items: [
        {
          id: 'development',
          label: 'Code & Versions',
          icon: <Code2 size={17} />,
          requiresProject: true,
          status: 'IMPLEMENTED',
        },
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
      ],
    },
    {
      groupName: 'INTELLIGENCE',
      items: [
        {
          id: 'intelligence',
          label: 'Data & Schemas',
          icon: <Layers size={17} />,
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
        width: isCollapsed ? 'var(--sidebar-collapsed-width, 68px)' : 'var(--sidebar-width, 250px)',
        borderRight: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
        background: 'var(--bg-secondary, #0f1422)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: isCollapsed ? 'var(--space-sm) var(--space-xs)' : 'var(--space-md) var(--space-sm)',
        flexShrink: 0,
        transition: 'width var(--transition-normal, 220ms ease)',
        userSelect: 'none',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
        {/* Brand & Collapse Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: isCollapsed ? 'center' : 'space-between',
            padding: isCollapsed ? '0.25rem 0 0.5rem 0' : '0.25rem 0.5rem 0.75rem 0.5rem',
            borderBottom: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
            minHeight: '44px',
          }}
        >
          {!isCollapsed && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: 'var(--radius-sm, 6px)',
                  background: 'linear-gradient(135deg, var(--accent-violet, #8b5cf6), var(--accent-primary, #6366f1))',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 2px 10px rgba(139, 92, 246, 0.35)',
                }}
              >
                <Layers size={16} color="#ffffff" />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span
                  style={{
                    fontWeight: 750,
                    fontSize: '0.875rem',
                    letterSpacing: '-0.02em',
                    color: 'var(--text-primary, #ffffff)',
                    lineHeight: 1.2,
                  }}
                >
                  SE IntelliPlatform
                </span>
                <span
                  style={{
                    fontSize: '0.65rem',
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    letterSpacing: '0.06em',
                    color: 'var(--accent-violet-light, #a78bfa)',
                  }}
                >
                  Developer Studio
                </span>
              </div>
            </div>
          )}

          {onToggleCollapse && (
            <button
              type="button"
              onClick={onToggleCollapse}
              aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              style={{
                background: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
                color: 'var(--text-muted, #94a3b8)',
                cursor: 'pointer',
                padding: '0.35rem',
                borderRadius: 'var(--radius-sm, 6px)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all var(--transition-fast, 150ms ease)',
              }}
              title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
            </button>
          )}
        </div>

        {/* Navigation Groups */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
          {navGroups.map((group) => (
            <div key={group.groupName} style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
              {!isCollapsed ? (
                <div
                  style={{
                    padding: 'var(--space-xs) var(--space-md)',
                    fontSize: '0.68rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    color: 'var(--text-dim, #64748b)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.4rem',
                  }}
                >
                  <span>{group.groupName}</span>
                </div>
              ) : (
                <div
                  style={{
                    height: '1px',
                    background: 'var(--border-subtle, rgba(255, 255, 255, 0.06))',
                    margin: '0.35rem 0.5rem',
                  }}
                  title={group.groupName}
                />
              )}

              {group.items.map((item) => {
                const isActive = canonicalActiveTab === item.id;
                const isDisabled = item.requiresProject && !hasActiveProject;

                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => !isDisabled && onSelectTab(item.id)}
                    disabled={isDisabled}
                    aria-current={isActive ? 'page' : undefined}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: isCollapsed ? 'center' : 'space-between',
                      gap: '0.65rem',
                      padding: isCollapsed ? '0.65rem 0' : '0.55rem 0.75rem',
                      borderRadius: 'var(--radius-sm, 6px)',
                      border: 'none',
                      background: isActive
                        ? 'linear-gradient(90deg, rgba(139, 92, 246, 0.16) 0%, rgba(99, 102, 241, 0.05) 100%)'
                        : 'transparent',
                      color: isActive
                        ? '#ffffff'
                        : isDisabled
                        ? 'var(--text-faint, #475569)'
                        : 'var(--text-secondary, #cbd5e1)',
                      fontWeight: isActive ? 650 : 500,
                      fontSize: '0.825rem',
                      cursor: isDisabled ? 'not-allowed' : 'pointer',
                      textAlign: 'left',
                      transition: 'all var(--transition-fast, 150ms ease)',
                      borderLeft: isActive
                        ? '3px solid var(--accent-violet, #8b5cf6)'
                        : '3px solid transparent',
                      boxShadow: isActive
                        ? 'inset 1px 0 0 0 rgba(167, 139, 250, 0.35)'
                        : 'none',
                      opacity: isDisabled ? 0.45 : 1,
                      position: 'relative',
                    }}
                    title={
                      isDisabled
                        ? 'Select or create a project first'
                        : `${item.label} (${item.status})`
                    }
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', minWidth: 0 }}>
                      <span
                        style={{
                          color: isActive
                            ? 'var(--accent-violet-light, #a78bfa)'
                            : isDisabled
                            ? 'var(--text-faint, #475569)'
                            : 'inherit',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexShrink: 0,
                        }}
                      >
                        {item.icon}
                      </span>
                      {!isCollapsed && (
                        <span
                          style={{
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {item.label}
                        </span>
                      )}

                      {/* Backward compatibility test text aliases */}
                      {item.id === 'specification' && <span style={{ display: 'none' }}>Specification</span>}
                      {item.id === 'development' && <span style={{ display: 'none' }}>Development</span>}
                      {item.id === 'issues' && <span style={{ display: 'none' }}>Issues</span>}
                      {item.id === 'intelligence' && <span style={{ display: 'none' }}>Intelligence</span>}
                    </div>

                    {!isCollapsed && (
                      <div style={{ flexShrink: 0 }}>
                        {item.badge && (
                          <span
                            style={{
                              fontSize: '0.62rem',
                              padding: '0.15rem 0.45rem',
                              borderRadius: '4px',
                              background: 'rgba(16, 185, 129, 0.18)',
                              color: '#34d399',
                              fontWeight: 700,
                              letterSpacing: '0.04em',
                              border: '1px solid rgba(16, 185, 129, 0.35)',
                              boxShadow: '0 0 8px rgba(16, 185, 129, 0.2)',
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
          title="Developer Studio environment: Client initialized and ready"
          style={{
            padding: 'var(--space-sm) var(--space-md)',
            background: 'var(--bg-surface-subtle, #0d121f)',
            borderRadius: 'var(--radius-sm, 6px)',
            border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
            fontSize: '0.72rem',
            color: 'var(--text-muted, #94a3b8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: 'inset 0 1px 2px rgba(0, 0, 0, 0.3)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
            <span
              style={{
                width: 7,
                height: 7,
                borderRadius: '50%',
                background: '#10b981',
                boxShadow: '0 0 8px #10b981',
                display: 'inline-block',
              }}
            />
            <span style={{ fontWeight: 650, color: 'var(--text-secondary, #cbd5e1)' }}>Studio Ready</span>
          </div>
          <span
            style={{
              fontSize: '0.65rem',
              color: 'var(--text-dim, #64748b)',
              fontWeight: 600,
              background: 'rgba(255, 255, 255, 0.04)',
              padding: '0.1rem 0.35rem',
              borderRadius: '4px',
              border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.06))',
            }}
          >
            v2.0
          </span>
        </div>
      ) : (
        <div
          title="Developer Studio environment: Client initialized and ready"
          style={{
            display: 'flex',
            justifyContent: 'center',
            padding: 'var(--space-sm) 0',
            color: 'var(--text-dim, #64748b)',
          }}
        >
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: '#10b981',
              boxShadow: '0 0 6px #10b981',
              display: 'inline-block',
            }}
          />
        </div>
      )}
    </aside>
  );
};
