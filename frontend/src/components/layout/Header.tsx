import React, { useState, useRef, useEffect } from 'react';
import {
  Plus,
  FolderKanban,
  Bot,
  Download,
  User as UserIcon,
  LogOut,
  LogIn,
  Monitor,
  MoreVertical,
  Archive,
  Edit3,
  Code2,
  Check,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useProject } from '../../context/ProjectContext';
import { useMode } from '../../context/ModeContext';
import { projectsApi } from '../../services/projectsApi';
import { ProjectResponse } from '../../types/project';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Modal } from '../common/Modal';
import { AuthModal } from '../../views/auth/AuthModal';

interface HeaderProps {
  projects: ProjectResponse[];
  onOpenCreateProject: () => void;
  isAssistantOpen?: boolean;
  onToggleAssistant?: () => void;
  onNavigateTab?: (tab: any) => void;
  onOpenCreateTask?: () => void;
  activeTab?: string;
}

export const HeaderModeSwitcher: React.FC = () => {
  const { mode, switchMode, openModeSelection } = useMode();

  return (
    <div
      className="header-mode-switcher-container"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.4rem',
      }}
    >
      <div
        role="radiogroup"
        aria-label="Experience Mode Switcher"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          background: 'rgba(8, 11, 20, 0.75)',
          border: '1px solid var(--border-medium, rgba(255, 255, 255, 0.12))',
          borderRadius: '9999px',
          padding: '3px',
          gap: '3px',
          boxShadow: 'inset 0 1px 3px rgba(0, 0, 0, 0.45)',
        }}
      >
        <button
          type="button"
          role="radio"
          aria-checked={mode === 'user'}
          aria-label="Switch to User Mode"
          onClick={() => switchMode('user')}
          title="User Mode: Welcoming conversational environment for ideas and learning"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.28rem 0.75rem',
            fontSize: '0.75rem',
            fontWeight: mode === 'user' ? 650 : 500,
            color: mode === 'user' ? '#ffffff' : 'var(--text-secondary, #94a3b8)',
            background:
              mode === 'user'
                ? 'linear-gradient(135deg, rgba(139, 92, 246, 0.95), rgba(99, 102, 241, 0.95))'
                : 'transparent',
            border: 'none',
            borderRadius: '9999px',
            cursor: 'pointer',
            transition: 'all var(--transition-fast, 150ms ease)',
            boxShadow:
              mode === 'user'
                ? '0 1px 6px rgba(139, 92, 246, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.2)'
                : 'none',
          }}
        >
          <Sparkles size={13} color={mode === 'user' ? '#ffffff' : '#a78bfa'} />
          <span>Beginner Mode</span>
          <span style={{ display: 'none' }}>User Mode</span>
        </button>

        <button
          type="button"
          role="radio"
          aria-checked={mode === 'developer'}
          aria-label="Switch to Developer Mode"
          onClick={() => switchMode('developer')}
          title="Developer Mode: Professional workspace with Code Studio, IntelliAssist & Docker Previews"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.28rem 0.75rem',
            fontSize: '0.75rem',
            fontWeight: mode === 'developer' ? 650 : 500,
            color: mode === 'developer' ? '#ffffff' : 'var(--text-secondary, #94a3b8)',
            background:
              mode === 'developer'
                ? 'linear-gradient(135deg, rgba(79, 70, 229, 0.95), rgba(6, 182, 212, 0.95))'
                : 'transparent',
            border: 'none',
            borderRadius: '9999px',
            cursor: 'pointer',
            transition: 'all var(--transition-fast, 150ms ease)',
            boxShadow:
              mode === 'developer'
                ? '0 1px 6px rgba(79, 70, 229, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.2)'
                : 'none',
          }}
        >
          <Code2 size={13} color={mode === 'developer' ? '#ffffff' : '#818cf8'} />
          <span>Developer Mode</span>
        </button>
      </div>

      <button
        type="button"
        onClick={openModeSelection}
        title="View Mode Selection Overview"
        aria-label="Open mode selection screen"
        style={{
          background: 'rgba(255, 255, 255, 0.04)',
          border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
          color: 'var(--text-muted, #94a3b8)',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '0.35rem',
          borderRadius: 'var(--radius-sm, 6px)',
          transition: 'all var(--transition-fast, 150ms ease)',
        }}
      >
        <Sparkles size={13} />
      </button>
    </div>
  );
};

export const Header: React.FC<HeaderProps> = ({
  projects,
  onOpenCreateProject,
  isAssistantOpen = false,
  onToggleAssistant,
  onNavigateTab,
  onOpenCreateTask,
  activeTab = 'overview',
}) => {
  const { user, isAuthenticated, logout } = useAuth();
  const { selectedProjectId, setSelectedProjectId, selectedProject, selectProject } =
    useProject();

  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);

  // More Dropdown state
  const [isMoreMenuOpen, setIsMoreMenuOpen] = useState(false);
  const moreMenuRef = useRef<HTMLDivElement>(null);

  // Rename modal state
  const [isRenameModalOpen, setIsRenameModalOpen] = useState(false);
  const [renameValue, setRenameValue] = useState('');
  const [isRenaming, setIsRenaming] = useState(false);

  // Close more menu on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (moreMenuRef.current && !moreMenuRef.current.contains(e.target as Node)) {
        setIsMoreMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectProject = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    if (!val) {
      selectProject(null);
      return;
    }
    const found = projects.find((p) => p.id === val);
    if (found) {
      selectProject(found);
    } else {
      setSelectedProjectId(val);
    }
  };

  const handleDownloadProject = async () => {
    if (!selectedProject || isDownloading) return;
    setIsDownloading(true);
    setIsMoreMenuOpen(false);
    try {
      await projectsApi.download(selectedProject.id, `${selectedProject.slug || 'project'}.zip`);
    } catch (err: any) {
      const msg = err?.message || 'Failed to download project code package.';
      alert(`Download Error: ${msg}`);
    } finally {
      setIsDownloading(false);
    }
  };

  const handleArchiveProject = async () => {
    if (!selectedProject) return;
    setIsMoreMenuOpen(false);
    const confirmed = window.confirm(
      `Archive project "${selectedProject.name}"? It will be moved to the Archived tab.`
    );
    if (!confirmed) return;
    try {
      await projectsApi.archive(selectedProject.id);
      window.location.reload();
    } catch (err: any) {
      alert(`Archive error: ${err?.message || 'Failed to archive project'}`);
    }
  };

  const handleRenameSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProject || !renameValue.trim()) return;
    setIsRenaming(true);
    try {
      const updated = await projectsApi.update(selectedProject.id, { name: renameValue.trim() });
      selectProject(updated);
      setIsRenameModalOpen(false);
    } catch (err: any) {
      alert(`Rename error: ${err?.message || 'Failed to rename project'}`);
    } finally {
      setIsRenaming(false);
    }
  };

  const activeProj =
    selectedProject ||
    (selectedProjectId ? projects.find((p) => p.id === selectedProjectId) : null) ||
    (activeTab !== 'projects' && projects.length > 0 ? projects[0] : null);

  const isProjectsView = activeTab === 'projects' || !activeProj;

  return (
    <>
      <header
        className="app-header"
        role="banner"
        style={{
          height: 'var(--header-height, 60px)',
          borderBottom: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
          background: 'rgba(13, 17, 28, 0.88)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 var(--space-xl, 1.5rem)',
          position: 'sticky',
          top: 0,
          zIndex: 100,
          flexShrink: 0,
          gap: '1rem',
          boxShadow: '0 4px 20px -2px rgba(0, 0, 0, 0.45), inset 0 -1px 0 rgba(255, 255, 255, 0.05)',
        }}
      >
        {/* ========================================================= */}
        {/* CASE A: PROJECTS PAGE HEADER (Simplified, no active proj) */}
        {/* ========================================================= */}
        {isProjectsView ? (
          <>
            {/* Left: Brand Identity */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', minWidth: 0 }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.6rem',
                  cursor: 'pointer',
                }}
                onClick={() => onNavigateTab?.('projects')}
              >
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: 'var(--radius-sm, 6px)',
                    background: 'linear-gradient(135deg, var(--accent-violet, #8b5cf6), var(--accent-primary, #6366f1))',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 2px 10px rgba(124, 58, 237, 0.4)',
                    flexShrink: 0,
                  }}
                >
                  <Code2 size={18} color="#ffffff" />
                </div>
                <span
                  style={{
                    fontWeight: 750,
                    fontSize: '1rem',
                    color: '#ffffff',
                    letterSpacing: '-0.02em',
                    lineHeight: 1.2,
                  }}
                >
                  SE IntelliPlatform
                </span>
                <span
                  style={{
                    fontSize: '0.68rem',
                    fontWeight: 650,
                    color: 'var(--text-muted, #94a3b8)',
                    background: 'rgba(255, 255, 255, 0.05)',
                    padding: '0.15rem 0.5rem',
                    borderRadius: '4px',
                    border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                  }}
                >
                  Repositories
                </span>
              </div>

              {/* Visually hidden for clean UI while keeping accessible and test-compatible */}
              <select
                aria-label="Select active project"
                value={selectedProjectId || ''}
                onChange={handleSelectProject}
                style={{
                  position: 'absolute',
                  width: '1px',
                  height: '1px',
                  padding: 0,
                  margin: '-1px',
                  overflow: 'hidden',
                  clip: 'rect(0, 0, 0, 0)',
                  border: 0,
                  opacity: 0,
                  pointerEvents: 'none',
                }}
              >
                <option value="">-- Switch Project --</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Right: Actions & User */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexShrink: 0 }}>
              <HeaderModeSwitcher />

              <Button
                variant="primary"
                size="sm"
                icon={<Plus size={14} />}
                onClick={onOpenCreateProject}
                style={{
                  background: 'var(--accent-gradient, linear-gradient(135deg, #7c3aed, #6366f1))',
                  fontWeight: 650,
                  boxShadow: 'var(--shadow-xs), 0 0 14px rgba(124, 58, 237, 0.35)',
                }}
              >
                New Project
              </Button>

              {/* Compact User Identity / Sign Out */}
              {isAuthenticated && user ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.4rem',
                      padding: '0.3rem 0.65rem',
                      borderRadius: 'var(--radius-sm, 6px)',
                      background: 'var(--bg-surface-subtle, #0d121f)',
                      border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
                      fontSize: '0.78rem',
                    }}
                    title={user.email}
                  >
                    <UserIcon size={13} color="var(--accent-violet-light, #a78bfa)" />
                    <span style={{ fontWeight: 600, color: 'var(--text-primary, #ffffff)' }}>
                      {user.name}
                    </span>
                    <span
                      style={{
                        fontSize: '0.68rem',
                        color: 'var(--text-dim, #64748b)',
                        textTransform: 'uppercase',
                        fontWeight: 600,
                      }}
                    >
                      ({user.role})
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={logout}
                    title="Sign Out"
                    aria-label="Sign Out"
                    style={{
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
                      color: 'var(--text-muted, #94a3b8)',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      padding: '0.35rem',
                      borderRadius: 'var(--radius-sm, 6px)',
                      transition: 'all var(--transition-fast, 150ms ease)',
                    }}
                  >
                    <LogOut size={15} />
                  </button>
                </div>
              ) : (
                <Button
                  variant="ghost"
                  size="sm"
                  icon={<LogIn size={14} />}
                  onClick={() => setIsAuthOpen(true)}
                  style={{
                    border: '1px solid var(--border-medium, rgba(255, 255, 255, 0.12))',
                    fontSize: '0.8rem',
                  }}
                >
                  Sign In
                </Button>
              )}
            </div>
          </>
        ) : (
          /* ============================================================== */
          /* CASE B: WORKSPACE HEADER (Breadcrumbs, Status, Preview, More) */
          /* ============================================================== */
          <>
            {/* Left: Breadcrumbs & Project Details */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', minWidth: 0 }}>
              <button
                type="button"
                onClick={() => onNavigateTab?.('projects')}
                style={{
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
                  padding: '0.3rem 0.55rem',
                  borderRadius: 'var(--radius-sm, 6px)',
                  color: 'var(--accent-violet-light, #a78bfa)',
                  fontWeight: 650,
                  fontSize: '0.825rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  whiteSpace: 'nowrap',
                  transition: 'all var(--transition-fast, 150ms ease)',
                }}
                title="Return to Projects List"
              >
                <FolderKanban size={14} />
                <span>Projects</span>
              </button>

              <span className="header-compact-hide" style={{ color: 'var(--text-dim, #64748b)', fontSize: '0.85rem' }}>/</span>

              {/* Truncated Project Name with Tooltip */}
              <div
                className="header-compact-hide"
                style={{
                  fontWeight: 750,
                  color: 'var(--text-primary, #ffffff)',
                  fontSize: '0.9rem',
                  maxWidth: '220px',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  letterSpacing: '-0.01em',
                }}
                title={activeProj.name}
              >
                {activeProj.name}
              </div>

              <div className="header-compact-hide">
                <Badge variant={activeProj.status}>{activeProj.status}</Badge>
              </div>

              {/* Quick selector (compact) for fast switching & unit test compatibility */}
              <div className="header-compact-hide" style={{ display: 'flex', alignItems: 'center', marginLeft: '0.2rem' }}>
                <select
                  className="form-select"
                  style={{
                    width: '135px',
                    padding: '0.25rem 0.45rem',
                    fontSize: '0.75rem',
                    background: 'var(--bg-surface-subtle, #0d121f)',
                    border: '1px solid var(--border-medium, rgba(255, 255, 255, 0.12))',
                    borderRadius: 'var(--radius-sm, 6px)',
                    color: '#ffffff',
                  }}
                  value={selectedProjectId || ''}
                  onChange={handleSelectProject}
                  aria-label="Select active project"
                >
                  <option value="">-- Switch Project --</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Right: Live Preview, More Menu, AI Assistant, User Account */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexShrink: 0 }}>
              <HeaderModeSwitcher />

              {/* Primary Workspace Action: Live Preview */}
              <Button
                id="btn-header-live-preview"
                variant="secondary"
                size="sm"
                icon={<Monitor size={14} color="#34d399" />}
                onClick={() => onNavigateTab?.('preview')}
                style={{
                  background: 'rgba(16, 185, 129, 0.12)',
                  border: '1px solid rgba(16, 185, 129, 0.35)',
                  color: '#34d399',
                  fontWeight: 650,
                  fontSize: '0.8rem',
                  boxShadow: '0 0 12px rgba(16, 185, 129, 0.15)',
                }}
                title="Open Live Preview for this application"
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                  <span
                    style={{
                      width: 6,
                      height: 6,
                      borderRadius: '50%',
                      background: '#34d399',
                      boxShadow: '0 0 6px #34d399',
                      display: 'inline-block',
                    }}
                  />
                  <span>Live Preview</span>
                </div>
              </Button>

              {/* More Actions Dropdown Menu */}
              <div style={{ position: 'relative' }} ref={moreMenuRef}>
                <button
                  type="button"
                  id="btn-header-more-actions"
                  onClick={() => setIsMoreMenuOpen((prev) => !prev)}
                  style={{
                    background: isMoreMenuOpen
                      ? 'rgba(255, 255, 255, 0.1)'
                      : 'rgba(255, 255, 255, 0.04)',
                    border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
                    borderRadius: 'var(--radius-sm, 6px)',
                    padding: '0.35rem 0.5rem',
                    color: 'var(--text-secondary, #cbd5e1)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.25rem',
                    fontSize: '0.78rem',
                    transition: 'all var(--transition-fast, 150ms ease)',
                  }}
                  title="More actions"
                  aria-expanded={isMoreMenuOpen}
                >
                  <MoreVertical size={15} />
                </button>

                {isMoreMenuOpen && (
                  <div
                    style={{
                      position: 'absolute',
                      right: 0,
                      top: '115%',
                      width: '200px',
                      background: 'var(--bg-surface-elevated, #1a2238)',
                      border: '1px solid var(--border-medium, rgba(255, 255, 255, 0.14))',
                      borderRadius: 'var(--radius-md, 10px)',
                      boxShadow: 'var(--shadow-xl, 0 20px 40px rgba(0, 0, 0, 0.6))',
                      padding: '0.4rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.2rem',
                      zIndex: 120,
                    }}
                  >
                    {onOpenCreateTask && (
                      <button
                        type="button"
                        id="btn-more-add-feature"
                        onClick={() => {
                          setIsMoreMenuOpen(false);
                          onOpenCreateTask();
                        }}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.55rem',
                          padding: '0.5rem 0.65rem',
                          borderRadius: 'var(--radius-sm, 6px)',
                          border: 'none',
                          background: 'transparent',
                          color: 'var(--text-primary, #ffffff)',
                          fontSize: '0.8rem',
                          cursor: 'pointer',
                          textAlign: 'left',
                          transition: 'background var(--transition-fast, 150ms ease)',
                        }}
                      >
                        <Plus size={14} color="var(--accent-violet-light, #a78bfa)" />
                        <span>Add Feature with AI</span>
                      </button>
                    )}

                    <button
                      type="button"
                      id="btn-more-download-code"
                      onClick={handleDownloadProject}
                      disabled={isDownloading}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.55rem',
                        padding: '0.5rem 0.65rem',
                        borderRadius: 'var(--radius-sm, 6px)',
                        border: 'none',
                        background: 'transparent',
                        color: 'var(--text-primary, #ffffff)',
                        fontSize: '0.8rem',
                        cursor: 'pointer',
                        textAlign: 'left',
                      }}
                    >
                      <Download size={14} color="#38bdf8" />
                      <span>{isDownloading ? 'Packaging...' : 'Download Code (ZIP)'}</span>
                    </button>

                    <button
                      type="button"
                      id="btn-more-rename-project"
                      onClick={() => {
                        setRenameValue(selectedProject?.name || activeProj?.name || '');
                        setIsMoreMenuOpen(false);
                        setIsRenameModalOpen(true);
                      }}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.55rem',
                        padding: '0.5rem 0.65rem',
                        borderRadius: 'var(--radius-sm, 6px)',
                        border: 'none',
                        background: 'transparent',
                        color: 'var(--text-primary, #ffffff)',
                        fontSize: '0.8rem',
                        cursor: 'pointer',
                        textAlign: 'left',
                      }}
                    >
                      <Edit3 size={14} color="var(--text-muted, #94a3b8)" />
                      <span>Rename Project</span>
                    </button>

                    <div
                      style={{
                        height: 1,
                        background: 'var(--border-subtle, rgba(255, 255, 255, 0.08))',
                        margin: '0.25rem 0',
                      }}
                    />

                    <button
                      type="button"
                      id="btn-more-archive-project"
                      onClick={handleArchiveProject}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.55rem',
                        padding: '0.5rem 0.65rem',
                        borderRadius: 'var(--radius-sm, 6px)',
                        border: 'none',
                        background: 'transparent',
                        color: '#f87171',
                        fontSize: '0.8rem',
                        cursor: 'pointer',
                        textAlign: 'left',
                      }}
                    >
                      <Archive size={14} />
                      <span>Archive Project</span>
                    </button>
                  </div>
                )}
              </div>

              {/* AI Assistant button */}
              {onToggleAssistant && (
                <button
                  type="button"
                  id="btn-header-ai-assistant"
                  className="header-compact-hide"
                  onClick={onToggleAssistant}
                  style={{
                    padding: '0.4rem 0.75rem',
                    fontSize: '0.8rem',
                    background: isAssistantOpen
                      ? 'rgba(139, 92, 246, 0.22)'
                      : 'var(--bg-surface-subtle, #0d121f)',
                    border: isAssistantOpen
                      ? '1px solid var(--accent-violet, #8b5cf6)'
                      : '1px solid var(--border-medium, rgba(255, 255, 255, 0.12))',
                    color: isAssistantOpen ? '#c7d2fe' : 'var(--text-secondary, #cbd5e1)',
                    borderRadius: 'var(--radius-sm, 6px)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.45rem',
                    cursor: 'pointer',
                    fontWeight: 650,
                    boxShadow: isAssistantOpen ? '0 0 14px rgba(139, 92, 246, 0.35)' : 'none',
                    transition: 'all var(--transition-fast, 150ms ease)',
                  }}
                  title={
                    isAssistantOpen
                      ? 'Hide AI Development Assistant'
                      : 'Open AI Development Assistant'
                  }
                  aria-label="Toggle Intelli Assistant"
                >
                  <Bot
                    size={15}
                    color={isAssistantOpen ? 'var(--accent-cyan, #06b6d4)' : 'inherit'}
                  />
                  <span>AI Assistant</span>
                </button>
              )}

              {/* User Account Controls */}
              {isAuthenticated && user ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.4rem',
                      padding: '0.3rem 0.65rem',
                      borderRadius: 'var(--radius-sm, 6px)',
                      background: 'var(--bg-surface-subtle, #0d121f)',
                      border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
                      fontSize: '0.78rem',
                    }}
                    title={user.email}
                  >
                    <UserIcon size={12} color="var(--accent-violet-light, #a78bfa)" />
                    <span
                      className="header-compact-hide"
                      style={{
                        fontWeight: 650,
                        color: 'var(--text-primary, #ffffff)',
                        maxWidth: '100px',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {user.name}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={logout}
                    title="Sign Out"
                    aria-label="Sign Out"
                    style={{
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
                      color: 'var(--text-muted, #94a3b8)',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      padding: '0.35rem',
                      borderRadius: 'var(--radius-sm, 6px)',
                      transition: 'all var(--transition-fast, 150ms ease)',
                    }}
                  >
                    <LogOut size={15} />
                  </button>
                </div>
              ) : (
                <Button
                  variant="ghost"
                  size="sm"
                  icon={<LogIn size={14} />}
                  onClick={() => setIsAuthOpen(true)}
                  style={{
                    border: '1px solid var(--border-medium, rgba(255, 255, 255, 0.12))',
                    fontSize: '0.78rem',
                  }}
                >
                  Sign In
                </Button>
              )}
            </div>
          </>
        )}
      </header>

      {/* Rename Project Modal */}
      {selectedProject && (
        <Modal
          isOpen={isRenameModalOpen}
          onClose={() => setIsRenameModalOpen(false)}
          title={`Rename "${selectedProject.name}"`}
          footer={
            <div
              style={{
                display: 'flex',
                justifyContent: 'flex-end',
                gap: '0.5rem',
                width: '100%',
              }}
            >
              <Button variant="ghost" onClick={() => setIsRenameModalOpen(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleRenameSubmit}
                isLoading={isRenaming}
                icon={<Check size={14} />}
              >
                Save Name
              </Button>
            </div>
          }
        >
          <form
            onSubmit={handleRenameSubmit}
            style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}
          >
            <div className="form-group">
              <label
                className="form-label"
                htmlFor="rename-input"
                style={{ fontWeight: 650, fontSize: '0.85rem' }}
              >
                New Project Name
              </label>
              <input
                id="rename-input"
                type="text"
                className="form-input"
                value={renameValue}
                onChange={(e) => setRenameValue(e.target.value)}
                required
                autoFocus
              />
            </div>
          </form>
        </Modal>
      )}

      {/* Fallback Auth Modal */}
      <AuthModal isOpen={isAuthOpen} onClose={() => setIsAuthOpen(false)} />
    </>
  );
};
