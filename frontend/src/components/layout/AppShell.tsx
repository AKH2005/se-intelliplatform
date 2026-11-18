import React, { useState, useEffect } from 'react';
import { Bot, AlertTriangle, X } from 'lucide-react';
import { Sidebar, NavigationTab } from './Sidebar';
import { Header } from './Header';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ChunkErrorBoundary } from '../common/ChunkErrorBoundary';
import { ProjectResponse } from '../../types/project';
import { useProject } from '../../context/ProjectContext';
const LazyAssistantDock = React.lazy(() =>
  import('../assistant/AssistantDock').then((m) => ({ default: m.AssistantDock }))
);

interface AppShellProps {
  activeTab: NavigationTab;
  onSelectTab: (tab: NavigationTab) => void;
  projects: ProjectResponse[];
  onOpenCreateProject: () => void;
  children: React.ReactNode;
  isAssistantOpen?: boolean;
  onToggleAssistant?: () => void;
  initialAssistantPrompt?: string | null;
  onClearInitialAssistantPrompt?: () => void;
  onOpenCreateTask?: () => void;
}

export const AppShell: React.FC<AppShellProps> = ({
  activeTab,
  onSelectTab,
  projects,
  onOpenCreateProject,
  children,
  isAssistantOpen: externalIsAssistantOpen,
  onToggleAssistant: externalOnToggleAssistant,
  initialAssistantPrompt,
  onClearInitialAssistantPrompt,
  onOpenCreateTask,
}) => {
  const { selectedProjectId, selectedProject, staleProjectNotice, clearStaleProjectNotice } =
    useProject();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [internalIsAssistantOpen, setInternalIsAssistantOpen] = useState(false);

  const isAssistantOpen =
    externalIsAssistantOpen !== undefined ? externalIsAssistantOpen : internalIsAssistantOpen;
  const handleToggleAssistant =
    externalOnToggleAssistant || (() => setInternalIsAssistantOpen((prev) => !prev));

  // Track whether assistant has been opened at least once in this session
  const [hasEverOpenedAssistant, setHasEverOpenedAssistant] = useState(isAssistantOpen);

  useEffect(() => {
    if (isAssistantOpen && !hasEverOpenedAssistant) {
      setHasEverOpenedAssistant(true);
    }
  }, [isAssistantOpen, hasEverOpenedAssistant]);

  return (
    <div className="app-shell">
      {/* 1. Left Navigation Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={onSelectTab}
        hasActiveProject={Boolean(selectedProjectId)}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
      />

      {/* 2. Main Workspace Viewport */}
      <div className="app-main-viewport">
        <Header
          activeTab={activeTab}
          projects={projects}
          onOpenCreateProject={onOpenCreateProject}
          isAssistantOpen={isAssistantOpen}
          onToggleAssistant={handleToggleAssistant}
          onNavigateTab={onSelectTab}
          onOpenCreateTask={onOpenCreateTask}
        />

        {staleProjectNotice && (
          <div
            role="status"
            style={{
              background:
                'linear-gradient(90deg, rgba(245, 158, 11, 0.14) 0%, rgba(217, 119, 6, 0.08) 100%)',
              borderBottom: '1px solid rgba(245, 158, 11, 0.28)',
              color: '#fef3c7',
              padding: '0.65rem 1.5rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontSize: '0.825rem',
              gap: '1rem',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.25)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <AlertTriangle size={16} color="#fbbf24" style={{ flexShrink: 0 }} />
              <span style={{ fontWeight: 550 }}>{staleProjectNotice}</span>
            </div>
            {clearStaleProjectNotice && (
              <button
                type="button"
                onClick={clearStaleProjectNotice}
                style={{
                  background: 'rgba(255, 255, 255, 0.06)',
                  border: 'none',
                  color: '#fbbf24',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  padding: '0.25rem',
                  borderRadius: '4px',
                  transition: 'all var(--transition-fast, 150ms ease)',
                }}
                aria-label="Dismiss notice"
              >
                <X size={14} />
              </button>
            )}
          </div>
        )}

        <main className="app-content-scroll" role="main" style={{ position: 'relative', zIndex: 1 }}>
          <ChunkErrorBoundary fallbackMessage="Unable to load workspace tab">
            <React.Suspense
              fallback={
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    minHeight: '60vh',
                    width: '100%',
                  }}
                >
                  <LoadingSpinner label="Loading workspace..." />
                </div>
              }
            >
              <div key={activeTab} className="workspace-view-enter" style={{ width: '100%', minHeight: '100%' }}>
                {children}
              </div>
            </React.Suspense>
          </ChunkErrorBoundary>
        </main>
      </div>

      {/* 3. Persistent Intelli Assistant Dock (Loaded on-demand, preserved once opened) */}
      {hasEverOpenedAssistant && (
        <ChunkErrorBoundary fallbackMessage="Unable to load Intelli Assistant">
          <React.Suspense
            fallback={
              isAssistantOpen ? (
                <aside className="assistant-dock open" aria-label="Intelli Assistant Dock">
                  <div className="assistant-dock-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <Bot size={18} color="var(--accent-primary)" />
                      <h3
                        style={{
                          margin: 0,
                          fontSize: '0.95rem',
                          fontWeight: 650,
                          color: 'var(--text-primary)',
                        }}
                      >
                        Intelli Assistant
                      </h3>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleToggleAssistant()}
                      aria-label="Close Intelli Assistant"
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-muted)',
                        cursor: 'pointer',
                        padding: '0.25rem',
                        display: 'flex',
                        alignItems: 'center',
                      }}
                    >
                      <X size={16} />
                    </button>
                  </div>
                  <div style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--border-subtle)' }}>
                    <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      Intelli Assistant connects conversational reasoning across requirements, architecture, code, tests, and preview containers.
                    </p>
                    <span style={{ fontSize: '0.75rem', color: 'var(--accent-primary)' }}>Assistant Ready</span>
                  </div>
                  <div style={{ padding: '3rem 1.5rem', display: 'flex', justifyContent: 'center' }}>
                    <LoadingSpinner label="Loading assistant engine..." size={28} />
                  </div>
                </aside>
              ) : null
            }
          >
            <LazyAssistantDock
              isOpen={isAssistantOpen}
              onClose={() => handleToggleAssistant()}
              activeProjectName={selectedProject?.name}
              projectId={selectedProjectId}
              onNavigate={onSelectTab}
              initialPrompt={initialAssistantPrompt}
              onClearInitialPrompt={onClearInitialAssistantPrompt}
            />
          </React.Suspense>
        </ChunkErrorBoundary>
      )}
    </div>
  );
};
