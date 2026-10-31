import React, { useState } from 'react';
import { AlertTriangle, X } from 'lucide-react';
import { Sidebar, NavigationTab } from './Sidebar';
import { Header } from './Header';
import { AssistantDock } from '../assistant/AssistantDock';
import { ProjectResponse } from '../../types/project';
import { useProject } from '../../context/ProjectContext';

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

        <main className="app-content-scroll" role="main">
          {children}
        </main>
      </div>

      {/* 3. Persistent Intelli Assistant Dock */}
      <AssistantDock
        isOpen={isAssistantOpen}
        onClose={() => handleToggleAssistant()}
        activeProjectName={selectedProject?.name}
        projectId={selectedProjectId}
        onNavigate={onSelectTab}
        initialPrompt={initialAssistantPrompt}
        onClearInitialPrompt={onClearInitialAssistantPrompt}
      />
    </div>
  );
};
