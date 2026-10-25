import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FolderKanban,
  Plus,
  Search,
  Trash2,
  Archive,
  RefreshCw,
  Download,
  ArrowUpRight,
  CheckCircle2,
  AlertCircle,
  History,
  ExternalLink,
  Copy,
  RotateCcw,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { projectsApi } from '../services/projectsApi';
import { ProjectResponse } from '../types/project';
import { useProject } from '../context/ProjectContext';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { Modal } from '../components/common/Modal';

// Clean raw markdown for readable card summary
const cleanMarkdownForSummary = (text: string | null | undefined): string => {
  if (!text || !text.trim()) return 'No description added yet.';
  let cleaned = text.replace(/^#+\s+/gm, '');
  cleaned = cleaned.replace(/[*_]{1,3}(.*?)[*_]{1,3}/g, '$1');
  cleaned = cleaned.replace(/`{1,3}(.*?)`{1,3}/g, '$1');
  cleaned = cleaned.replace(/\[(.*?)\]\(.*?\)/g, '$1');
  return cleaned.trim() || 'No description added yet.';
};

interface ProjectsViewProps {
  onOpenWorkspace: (project: ProjectResponse) => void;
  onOpenCreateProject: () => void;
}

type TabFilter = 'all' | 'my' | 'recent' | 'archived';
type SortOption = 'updated' | 'created' | 'name';

export const ProjectsView: React.FC<ProjectsViewProps> = ({
  onOpenWorkspace,
  onOpenCreateProject,
}) => {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const { selectProject } = useProject();

  // Search, filter, and sort state
  const [activeTab, setActiveTab] = useState<TabFilter>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTech, setSelectedTech] = useState<string>('all');
  const [sortBy, setSortBy] = useState<SortOption>('updated');

  // Action state
  const [projectToDelete, setProjectToDelete] = useState<ProjectResponse | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [projectForActivity, setProjectForActivity] = useState<ProjectResponse | null>(null);
  const [activityHistory, setActivityHistory] = useState<any[]>([]);
  const [isLoadingActivity, setIsLoadingActivity] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [expandedDescIds, setExpandedDescIds] = useState<Record<string, boolean>>({});

  const toggleDescExpand = (id: string) => {
    setExpandedDescIds((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  // Fetch all projects from API
  const {
    data: projects = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(),
  });

  // Duplicate mutation
  const duplicateMutation = useMutation({
    mutationFn: (projectId: string) => projectsApi.duplicate(projectId),
    onSuccess: (newProject) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setActionSuccess(`Successfully duplicated as '${newProject.name}'`);
      setTimeout(() => setActionSuccess(null), 4000);
    },
    onError: (err: any) => {
      setActionError(err?.message || 'Failed to duplicate project.');
      setTimeout(() => setActionError(null), 4000);
    },
  });

  // Archive mutation
  const archiveMutation = useMutation({
    mutationFn: (projectId: string) => projectsApi.archive(projectId),
    onSuccess: (archived) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setActionSuccess(`Archived project '${archived.name}'`);
      setTimeout(() => setActionSuccess(null), 4000);
    },
    onError: (err: any) => {
      setActionError(err?.message || 'Failed to archive project.');
      setTimeout(() => setActionError(null), 4000);
    },
  });

  // Restore mutation
  const restoreMutation = useMutation({
    mutationFn: (projectId: string) => projectsApi.restore(projectId),
    onSuccess: (restored) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setActionSuccess(`Restored project '${restored.name}' to active`);
      setTimeout(() => setActionSuccess(null), 4000);
    },
    onError: (err: any) => {
      setActionError(err?.message || 'Failed to restore project.');
      setTimeout(() => setActionError(null), 4000);
    },
  });

  // Permanent Delete
  const handleDeletePermanent = async () => {
    if (!projectToDelete) return;
    setIsDeleting(true);
    try {
      await projectsApi.deletePermanent(projectToDelete.id);
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setActionSuccess(`Project '${projectToDelete.name}' has been permanently deleted.`);
      setTimeout(() => setActionSuccess(null), 4000);
      setProjectToDelete(null);
    } catch (err: any) {
      setActionError(err?.message || 'Failed to delete project.');
      setTimeout(() => setActionError(null), 4000);
    } finally {
      setIsDeleting(false);
    }
  };

  // Download project ZIP
  const handleDownload = async (project: ProjectResponse) => {
    setDownloadingId(project.id);
    try {
      await projectsApi.download(project.id, `${project.slug || 'project'}.zip`);
      setActionSuccess(`Downloaded source package for '${project.name}'`);
      setTimeout(() => setActionSuccess(null), 3000);
    } catch (err: any) {
      setActionError(err?.message || 'Failed to download project code.');
      setTimeout(() => setActionError(null), 4000);
    } finally {
      setDownloadingId(null);
    }
  };

  // View Activity History
  const handleViewActivity = async (project: ProjectResponse) => {
    setProjectForActivity(project);
    setIsLoadingActivity(true);
    try {
      const history = await projectsApi.getActivity(project.id);
      setActivityHistory(history);
    } catch (err) {
      setActivityHistory([]);
    } finally {
      setIsLoadingActivity(false);
    }
  };

  // Infer technology stack tags based on project settings or heuristics
  const getTechStack = (project: ProjectResponse): string[] => {
    const settings = project.settings || {};
    if (settings.tech_stack && Array.isArray(settings.tech_stack)) {
      return settings.tech_stack;
    }
    const name = project.name.toLowerCase();
    const desc = (project.description || '').toLowerCase();
    if (name.includes('snake') || desc.includes('game') || desc.includes('canvas')) {
      return ['HTML5 Canvas', 'Vanilla JS', 'Retro CRT'];
    }
    if (name.includes('event') || desc.includes('event')) {
      return ['React', 'FastAPI', 'SQLite', 'REST'];
    }
    if (name.includes('task') || name.includes('todo') || desc.includes('task')) {
      return ['React', 'TypeScript', 'FastAPI', 'SQLite'];
    }
    if (desc.includes('shop') || desc.includes('commerce') || desc.includes('store')) {
      return ['React', 'TypeScript', 'Cart Store', 'REST'];
    }
    return ['React', 'FastAPI', 'Python', 'SQLite'];
  };

  // Filtering and sorting logic
  const filteredProjects = useMemo(() => {
    return projects
      .filter((p) => {
        // Tab filter
        if (activeTab === 'archived') {
          return p.status === 'ARCHIVED';
        }
        if (p.status === 'ARCHIVED') {
          return false; // hide archived from other tabs
        }
        if (activeTab === 'my') {
          if (user && p.owner_id) {
            return p.owner_id === user.id;
          }
          return true;
        }
        return true;
      })
      .filter((p) => {
        // Search query
        if (!searchQuery.trim()) return true;
        const q = searchQuery.toLowerCase();
        const stack = getTechStack(p).join(' ').toLowerCase();
        return (
          p.name.toLowerCase().includes(q) ||
          p.slug.toLowerCase().includes(q) ||
          (p.description || '').toLowerCase().includes(q) ||
          stack.includes(q)
        );
      })
      .filter((p) => {
        // Tech filter
        if (selectedTech === 'all') return true;
        const stack = getTechStack(p);
        return stack.some((t) => t.toLowerCase().includes(selectedTech.toLowerCase()));
      })
      .sort((a, b) => {
        if (sortBy === 'name') {
          return a.name.localeCompare(b.name);
        }
        if (sortBy === 'created') {
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        }
        // Default updated_at
        const dateA = new Date(a.updated_at || a.created_at).getTime();
        const dateB = new Date(b.updated_at || b.created_at).getTime();
        return dateB - dateA;
      });
  }, [projects, activeTab, searchQuery, selectedTech, sortBy, user]);

  // Counts for tabs
  const tabCounts = useMemo(() => {
    const nonArchived = projects.filter((p) => p.status !== 'ARCHIVED');
    const archived = projects.filter((p) => p.status === 'ARCHIVED');
    const my = nonArchived.filter((p) => !p.owner_id || (user && p.owner_id === user.id));
    return {
      all: nonArchived.length,
      my: my.length,
      recent: nonArchived.length,
      archived: archived.length,
    };
  }, [projects, user]);

  return (
    <div className="view-content" style={{ maxWidth: 1300, margin: '0 auto', padding: '2rem 1.5rem' }}>
      {/* 1. Header Section */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: '1.75rem',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.35rem' }}>
            <FolderKanban size={26} color="var(--accent-primary)" />
            <h1 style={{ fontSize: '1.65rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
              Projects
            </h1>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', margin: 0, maxWidth: 640 }}>
            Central repository hub to manage engineering projects, inspect isolated workspaces, collect structured requirements, and generate full AI applications.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <Button
            variant="secondary"
            icon={<RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />}
            onClick={() => refetch()}
            title="Refresh projects list"
          >
            Refresh
          </Button>
          <Button
            id="btn-create-new-project-header"
            variant="primary"
            icon={<Plus size={16} />}
            onClick={onOpenCreateProject}
            style={{ fontWeight: 600, padding: '0.6rem 1.25rem' }}
          >
            New Project
          </Button>
        </div>
      </div>

      {/* Notifications */}
      {actionSuccess && (
        <div
          style={{
            background: 'rgba(16, 185, 129, 0.12)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            borderRadius: 'var(--radius-md)',
            color: '#34d399',
            padding: '0.75rem 1rem',
            marginBottom: '1.25rem',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <CheckCircle2 size={16} />
          <span>{actionSuccess}</span>
        </div>
      )}

      {actionError && (
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-md)',
            color: '#f87171',
            padding: '0.75rem 1rem',
            marginBottom: '1.25rem',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <AlertCircle size={16} />
          <span>{actionError}</span>
        </div>
      )}

      {error && <ErrorAlert error={error as any} />}

      {/* 2. Subnav Tabs (GitHub-style) */}
      <div
        style={{
          display: 'flex',
          borderBottom: '1px solid var(--border-subtle)',
          marginBottom: '1.5rem',
          gap: '1.5rem',
          fontSize: '0.875rem',
          fontWeight: 500,
        }}
      >
        <button
          type="button"
          onClick={() => setActiveTab('all')}
          style={{
            background: 'none',
            border: 'none',
            padding: '0.75rem 0.25rem',
            color: activeTab === 'all' ? 'var(--text-primary)' : 'var(--text-muted)',
            borderBottom: activeTab === 'all' ? '2px solid var(--accent-primary)' : '2px solid transparent',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.45rem',
            fontWeight: activeTab === 'all' ? 600 : 500,
          }}
        >
          All Projects
          <span
            style={{
              background: 'rgba(255, 255, 255, 0.08)',
              padding: '0.1rem 0.45rem',
              borderRadius: '9999px',
              fontSize: '0.75rem',
            }}
          >
            {tabCounts.all}
          </span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('my')}
          style={{
            background: 'none',
            border: 'none',
            padding: '0.75rem 0.25rem',
            color: activeTab === 'my' ? 'var(--text-primary)' : 'var(--text-muted)',
            borderBottom: activeTab === 'my' ? '2px solid var(--accent-primary)' : '2px solid transparent',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.45rem',
            fontWeight: activeTab === 'my' ? 600 : 500,
          }}
        >
          My Projects
          <span
            style={{
              background: 'rgba(255, 255, 255, 0.08)',
              padding: '0.1rem 0.45rem',
              borderRadius: '9999px',
              fontSize: '0.75rem',
            }}
          >
            {tabCounts.my}
          </span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('recent')}
          style={{
            background: 'none',
            border: 'none',
            padding: '0.75rem 0.25rem',
            color: activeTab === 'recent' ? 'var(--text-primary)' : 'var(--text-muted)',
            borderBottom: activeTab === 'recent' ? '2px solid var(--accent-primary)' : '2px solid transparent',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.45rem',
            fontWeight: activeTab === 'recent' ? 600 : 500,
          }}
        >
          Recent Projects
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('archived')}
          style={{
            background: 'none',
            border: 'none',
            padding: '0.75rem 0.25rem',
            color: activeTab === 'archived' ? 'var(--text-primary)' : 'var(--text-muted)',
            borderBottom: activeTab === 'archived' ? '2px solid var(--accent-primary)' : '2px solid transparent',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.45rem',
            fontWeight: activeTab === 'archived' ? 600 : 500,
          }}
        >
          Archived Projects
          <span
            style={{
              background: 'rgba(255, 255, 255, 0.08)',
              padding: '0.1rem 0.45rem',
              borderRadius: '9999px',
              fontSize: '0.75rem',
            }}
          >
            {tabCounts.archived}
          </span>
        </button>
      </div>

      {/* 3. Search and Filter Bar */}
      <div
        style={{
          display: 'flex',
          gap: '1rem',
          marginBottom: '1.5rem',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ flex: 1, minWidth: 260, position: 'relative' }}>
          <Search
            size={16}
            style={{
              position: 'absolute',
              left: '0.85rem',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--text-muted)',
            }}
          />
          <input
            id="projects-search-input"
            type="text"
            className="form-input"
            style={{ paddingLeft: '2.4rem', width: '100%', fontSize: '0.85rem' }}
            placeholder="Search projects by name, description, or technology..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Tech Stack filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Tech:</span>
            <select
              className="form-select"
              style={{ fontSize: '0.825rem', padding: '0.4rem 0.65rem' }}
              value={selectedTech}
              onChange={(e) => setSelectedTech(e.target.value)}
            >
              <option value="all">All Technologies</option>
              <option value="react">React</option>
              <option value="fastapi">FastAPI</option>
              <option value="sqlite">SQLite</option>
              <option value="canvas">Canvas / Games</option>
            </select>
          </div>

          {/* Sort By dropdown */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Sort:</span>
            <select
              className="form-select"
              style={{ fontSize: '0.825rem', padding: '0.4rem 0.65rem' }}
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
            >
              <option value="updated">Recently Updated</option>
              <option value="created">Recently Created</option>
              <option value="name">Name (A-Z)</option>
            </select>
          </div>
        </div>
      </div>

      {/* 4. Projects List */}
      {isLoading ? (
        <LoadingSpinner label="Loading project repositories..." />
      ) : filteredProjects.length === 0 ? (
        <EmptyState
          icon={<FolderKanban size={42} />}
          title={
            searchQuery
              ? 'No matching projects found'
              : activeTab === 'archived'
              ? 'No archived projects'
              : 'Create your first project to get started'
          }
          description={
            searchQuery
              ? `No repositories match "${searchQuery}". Try adjusting your search or filters.`
              : activeTab === 'archived'
              ? 'Projects you archive will appear here safely preserved with full revision history.'
              : 'SE IntelliPlatform creates dedicated workspaces with multi-agent design, code generation, and isolated live previews.'
          }
          actionLabel="Create New Project"
          onAction={onOpenCreateProject}
        />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          {filteredProjects.map((project) => {
            const techStack = getTechStack(project);
            const isArchived = project.status === 'ARCHIVED';
            const updatedDate = new Date(project.updated_at || project.created_at).toLocaleDateString(
              undefined,
              { month: 'short', day: 'numeric', year: 'numeric' }
            );

            return (
              <div
                key={project.id}
                id={`project-card-${project.id}`}
                style={{
                  background: 'var(--bg-glass-card)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '1.25rem 1.5rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  gap: '1.5rem',
                  flexWrap: 'wrap',
                  transition: 'border-color 0.2s, background 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.4)';
                  e.currentTarget.style.background = 'var(--bg-surface-active)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border-subtle)';
                  e.currentTarget.style.background = 'var(--bg-glass-card)';
                }}
              >
                {/* Left: Info & Tech Stack */}
                <div style={{ flex: 1, minWidth: 280 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.4rem' }}>
                    <button
                      type="button"
                      onClick={() => {
                        selectProject(project);
                        onOpenWorkspace(project);
                      }}
                      style={{
                        background: 'none',
                        border: 'none',
                        padding: 0,
                        color: 'var(--accent-primary)',
                        fontSize: '1.1rem',
                        fontWeight: 700,
                        cursor: 'pointer',
                        textAlign: 'left',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.4rem',
                      }}
                    >
                      {project.name}
                      <ArrowUpRight size={14} style={{ opacity: 0.6 }} />
                    </button>
                    <Badge variant={project.status}>{project.status}</Badge>
                    <span
                      style={{
                        fontSize: '0.72rem',
                        color: 'var(--text-muted)',
                        fontFamily: 'monospace',
                        background: 'rgba(255, 255, 255, 0.04)',
                        padding: '0.15rem 0.45rem',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      {project.slug}
                    </span>
                  </div>

                  {/* Expandable Project Description (Line-clamped by default) */}
                  {(() => {
                    const rawDesc = project.description;
                    const cleanedDesc = cleanMarkdownForSummary(rawDesc);
                    const isExpanded = !!expandedDescIds[project.id];
                    const isLongDesc = !!rawDesc && (rawDesc.trim().length > 140 || rawDesc.includes('\n'));

                    return (
                      <div style={{ marginBottom: '0.75rem', maxWidth: 720 }}>
                        <div
                          style={{
                            fontSize: '0.85rem',
                            color: 'var(--text-secondary)',
                            lineHeight: 1.5,
                            display: isExpanded ? 'block' : '-webkit-box',
                            WebkitBoxOrient: 'vertical',
                            WebkitLineClamp: isExpanded ? 'unset' : 3,
                            overflow: isExpanded ? 'visible' : 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: isExpanded ? 'pre-wrap' : 'normal',
                            wordBreak: 'break-word',
                            ...(isExpanded
                              ? {
                                  background: 'rgba(0, 0, 0, 0.25)',
                                  padding: '0.65rem 0.85rem',
                                  borderRadius: 'var(--radius-sm, 6px)',
                                  border: '1px solid rgba(255, 255, 255, 0.08)',
                                  marginTop: '0.25rem',
                                }
                              : {}),
                          }}
                        >
                          {cleanedDesc}
                        </div>

                        {isLongDesc && (
                          <button
                            type="button"
                            id={`btn-toggle-desc-${project.id}`}
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleDescExpand(project.id);
                            }}
                            aria-expanded={isExpanded}
                            aria-label={isExpanded ? `Show less description for ${project.name}` : `Show more description for ${project.name}`}
                            style={{
                              background: 'none',
                              border: 'none',
                              padding: '0.3rem 0 0 0',
                              color: 'var(--accent-primary)',
                              fontSize: '0.78rem',
                              fontWeight: 600,
                              cursor: 'pointer',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '0.25rem',
                            }}
                          >
                            <span>{isExpanded ? 'Show less' : 'Show more'}</span>
                            {isExpanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                          </button>
                        )}
                      </div>
                    );
                  })()}

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {techStack.map((tech, i) => (
                      <span
                        key={i}
                        style={{
                          fontSize: '0.72rem',
                          background: 'rgba(59, 130, 246, 0.1)',
                          border: '1px solid rgba(59, 130, 246, 0.25)',
                          color: '#60a5fa',
                          padding: '0.15rem 0.5rem',
                          borderRadius: '9999px',
                          fontWeight: 500,
                        }}
                      >
                        {tech}
                      </span>
                    ))}

                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: '0.5rem' }}>
                      Updated {updatedDate}
                    </span>
                  </div>
                </div>

                {/* Right: Actions */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexShrink: 0 }}>
                  <Button
                    variant="primary"
                    size="sm"
                    icon={<ExternalLink size={14} />}
                    onClick={() => {
                      selectProject(project);
                      onOpenWorkspace(project);
                    }}
                    style={{ fontWeight: 600 }}
                  >
                    Open Workspace
                  </Button>

                  <Button
                    variant="secondary"
                    size="sm"
                    icon={<Download size={13} />}
                    isLoading={downloadingId === project.id}
                    onClick={() => handleDownload(project)}
                    title="Download project code as ZIP archive"
                  >
                    Code
                  </Button>

                  <Button
                    variant="secondary"
                    size="sm"
                    icon={<Copy size={13} />}
                    onClick={() => duplicateMutation.mutate(project.id)}
                    title="Duplicate project"
                  >
                    Clone
                  </Button>

                  <Button
                    variant="secondary"
                    size="sm"
                    icon={<History size={13} />}
                    onClick={() => handleViewActivity(project)}
                    title="View activity timeline"
                  >
                    History
                  </Button>

                  {isArchived ? (
                    <Button
                      variant="secondary"
                      size="sm"
                      icon={<RotateCcw size={13} />}
                      onClick={() => restoreMutation.mutate(project.id)}
                      title="Restore archived project"
                    >
                      Restore
                    </Button>
                  ) : (
                    <Button
                      variant="secondary"
                      size="sm"
                      icon={<Archive size={13} />}
                      onClick={() => archiveMutation.mutate(project.id)}
                      title="Archive project"
                    >
                      Archive
                    </Button>
                  )}

                  <Button
                    variant="danger"
                    size="sm"
                    icon={<Trash2 size={13} />}
                    onClick={() => setProjectToDelete(project)}
                    title="Permanently delete project"
                  >
                    Delete
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {projectToDelete && (
        <Modal
          isOpen={Boolean(projectToDelete)}
          title="Delete Project Permanently"
          onClose={() => setProjectToDelete(null)}
          footer={
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <Button variant="secondary" onClick={() => setProjectToDelete(null)}>
                Cancel
              </Button>
              <Button
                variant="danger"
                isLoading={isDeleting}
                onClick={handleDeletePermanent}
                icon={<Trash2 size={14} />}
              >
                Delete Permanently
              </Button>
            </div>
          }
        >
          <div style={{ lineHeight: 1.6 }}>
            <p style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>
              Are you sure you want to permanently delete{' '}
              <strong style={{ color: '#fff' }}>{projectToDelete.name}</strong>?
            </p>
            <div
              style={{
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.75rem 1rem',
                fontSize: '0.85rem',
                color: '#f87171',
              }}
            >
              This action cannot be undone. All requirements, snapshots, generated versions, and test results will be permanently removed.
            </div>
          </div>
        </Modal>
      )}

      {/* Activity Timeline Modal */}
      {projectForActivity && (
        <Modal
          isOpen={Boolean(projectForActivity)}
          title={`Activity Timeline: ${projectForActivity.name}`}
          onClose={() => setProjectForActivity(null)}
          footer={
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button variant="secondary" onClick={() => setProjectForActivity(null)}>
                Close
              </Button>
            </div>
          }
        >
          {isLoadingActivity ? (
            <LoadingSpinner label="Loading project activity events..." />
          ) : activityHistory.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '1.5rem 0' }}>
              No historical activity logged for this project yet.
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', maxHeight: 420, overflowY: 'auto' }}>
              {activityHistory.map((act, i) => (
                <div
                  key={act.id || i}
                  style={{
                    background: 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '0.75rem 1rem',
                    fontSize: '0.85rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                    <span style={{ fontWeight: 600, color: '#fff' }}>{act.title}</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {act.timestamp ? new Date(act.timestamp).toLocaleString() : ''}
                    </span>
                  </div>
                  <p style={{ color: 'var(--text-secondary)', margin: 0, fontSize: '0.825rem' }}>
                    {act.description}
                  </p>
                </div>
              ))}
            </div>
          )}
        </Modal>
      )}
    </div>
  );
};
