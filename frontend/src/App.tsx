import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi } from './services/projectsApi';
import { requirementsApi } from './services/requirementsApi';
import { contextApi } from './services/contextApi';
import { useProject } from './context/ProjectContext';
import { AppShell } from './components/layout/AppShell';
import { NavigationTab } from './components/layout/Sidebar';
import { OverviewWorkspace } from './views/OverviewWorkspace';
import { PreviewWorkspace } from './views/PreviewWorkspace';
import { SpecificationWorkspace } from './views/SpecificationWorkspace';
import { DevelopmentWorkspace } from './views/DevelopmentWorkspace';
import { TestingWorkspace } from './views/TestingWorkspace';
import { IssuesWorkspace } from './views/IssuesWorkspace';
import { IntelligenceWorkspace } from './views/IntelligenceWorkspace';
import { EnvironmentWorkspace } from './views/EnvironmentWorkspace';
import { CodeIntelligenceWorkspace } from './views/CodeIntelligenceWorkspace';
import { WorkflowStudio } from './views/WorkflowStudio';
import { RunHistory } from './views/RunHistory';
import { ProjectsView } from './views/ProjectsView';
import { CreateProjectModal } from './components/projects/CreateProjectModal';
import { CreateTaskModal } from './components/requirements/CreateTaskModal';
import { LoginView } from './views/auth/LoginView';
import { LoadingSpinner } from './components/common/LoadingSpinner';
import { useAuth } from './context/AuthContext';
import { ProjectCreate, ProjectResponse } from './types/project';

// Helper to parse pathname into project ID and workspace tab
const parseCurrentUrl = () => {
  if (typeof window === 'undefined') return { isProjectsList: false, urlProjectId: null, urlTab: null };
  const path = window.location.pathname;
  if (path === '/projects' || path === '/projects/') {
    return { isProjectsList: true, urlProjectId: null, urlTab: null };
  }
  const match = path.match(/^\/projects\/([^/]+)(?:\/workspace)?(?:\/([a-z-]+))?/i);
  if (match) {
    return {
      isProjectsList: false,
      urlProjectId: match[1],
      urlTab: (match[2] as NavigationTab) || null,
    };
  }
  return { isProjectsList: false, urlProjectId: null, urlTab: null };
};

export const App: React.FC = () => {
  const queryClient = useQueryClient();
  const { user: _user, isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const {
    selectedProjectId,
    selectedProject,
    selectProject,
    validateAndSyncProjects,
    registerOpenCreateProject,
  } = useProject();

  const initialUrl = parseCurrentUrl();
  const [activeTab, setActiveTab] = useState<NavigationTab>(() => {
    if (initialUrl.isProjectsList) return 'projects';
    if (initialUrl.urlTab) return initialUrl.urlTab;
    return 'overview';
  });
  const [isCreateProjectOpen, setIsCreateProjectOpen] = useState(false);
  const [isCreateTaskOpen, setIsCreateTaskOpen] = useState(false);
  const [isAssistantExplicitOpen, setIsAssistantExplicitOpen] = useState(false);
  const [assistantInitialPrompt, setAssistantInitialPrompt] = useState<string | null>(null);

  // Auto-redirect authenticated user from /login, /register, or / to /projects
  React.useEffect(() => {
    if (isAuthenticated && typeof window !== 'undefined') {
      const path = window.location.pathname;
      if (path === '/' || path === '/login' || path === '/register') {
        window.history.replaceState({}, '', '/projects');
        setActiveTab('projects');
      }
    }
  }, [isAuthenticated]);

  // Register open create project handler with context
  React.useEffect(() => {
    if (registerOpenCreateProject) {
      registerOpenCreateProject(() => setIsCreateProjectOpen(true));
    }
  }, [registerOpenCreateProject]);

  // Fetch all projects for the global header selector
  const { data: projects = [], isLoading: isLoadingProjects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(),
  });

  // Authoritatively sync projects and auto-heal stale projects
  React.useEffect(() => {
    if (projects.length > 0 && validateAndSyncProjects) {
      validateAndSyncProjects(projects);
    }
  }, [projects, validateAndSyncProjects]);

  // Sync with URL when projects are loaded
  React.useEffect(() => {
    const { isProjectsList, urlProjectId, urlTab } = parseCurrentUrl();
    if (isProjectsList) {
      setActiveTab('projects');
      return;
    }
    if (urlProjectId && projects.length > 0) {
      const match = projects.find((p) => p.id === urlProjectId || p.slug === urlProjectId);
      if (match) {
        selectProject(match);
        if (urlTab) {
          setActiveTab(urlTab);
        } else if (activeTab === 'projects') {
          setActiveTab('overview');
        }
      }
    }
  }, [projects]);

  // Listen to popstate (browser back/forward)
  React.useEffect(() => {
    const handlePopState = () => {
      const { isProjectsList, urlProjectId, urlTab } = parseCurrentUrl();
      if (isProjectsList) {
        setActiveTab('projects');
      } else if (urlProjectId && projects.length > 0) {
        const match = projects.find((p) => p.id === urlProjectId || p.slug === urlProjectId);
        if (match) {
          selectProject(match);
          setActiveTab(urlTab || 'overview');
        }
      }
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [projects, selectProject]);

  // Tab navigation handler with URL pushState
  const handleSelectTab = (tab: NavigationTab) => {
    if (tab === 'assistant') {
      setIsAssistantExplicitOpen(true);
      return;
    }
    setActiveTab(tab);
    if (tab === 'projects') {
      if (window.location.pathname !== '/projects') {
        window.history.pushState({}, '', '/projects');
      }
    } else if (selectedProjectId) {
      const targetUrl = `/projects/${selectedProjectId}/workspace`;
      if (window.location.pathname !== targetUrl) {
        window.history.pushState({}, '', targetUrl);
      }
    }
  };

  // Validate active project context when project list updates
  React.useEffect(() => {
    if (!isLoadingProjects) {
      validateAndSyncProjects(projects);
    }
  }, [projects, isLoadingProjects, validateAndSyncProjects]);

  // Helper to extract realistic starter requirements from natural language description
  const extractStarterRequirements = (desc: string) => {
    const text = desc.toLowerCase();
    const isGameApp = text.includes('game') || text.includes('snake') || text.includes('arcade');
    const isEventApp = text.includes('event');
    const isTaskApp = text.includes('task');
    const isShopApp = text.includes('shop') || text.includes('store') || text.includes('commerce') || text.includes('product') || text.includes('cart');
    const isManageApp = text.includes('student') || text.includes('employee') || text.includes('manage') || text.includes('admin') || text.includes('record');

    if (isGameApp) {
      return [
        { title: 'HTML5 Canvas 2D game rendering engine.', description: 'Smooth 60fps rendering with coordinate grid calculation.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Responsive directional controls (Keyboard Arrow/WASD & Touch D-Pad).', description: 'Real-time steering with prevent-reverse safeguards.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Real-time score calculation and persistent high-score tracking.', description: 'Score accumulation and localStorage persistent high scores.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Dynamic food generation, speed ramping, and self-collision boundaries.', description: 'Automated food placement avoiding snake body and boundary death triggers.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Modular game lifecycle (Start, Pause, Reset, Difficulty Speed select).', description: 'Game state machine controlling active, paused, and game-over states.', type: 'FUNCTIONAL' as const, priority: 'MEDIUM' as const },
        { title: 'Interactive Live Preview prototype.', description: 'Direct browser game prototype on SE IntelliPlatform preview runtime.', type: 'NON_FUNCTIONAL' as const, priority: 'HIGH' as const },
      ];
    } else if (isShopApp) {
      return [
        { title: 'Product catalog browsing with category filters and search.', description: 'Browse and filter available catalog products dynamically.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Interactive shopping cart with live subtotal calculation.', description: 'Add/remove items and calculate line item totals in real time.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Streamlined checkout modal with customer order summary.', description: 'Checkout form with shipping details and order confirmation.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Stock availability validation before order completion.', description: 'Validates inventory count before order placement.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Production-ready REST APIs for products and orders.', description: 'Endpoints for catalog query and order checkout processing.', type: 'NON_FUNCTIONAL' as const, priority: 'HIGH' as const },
      ];
    } else if (isManageApp) {
      return [
        { title: 'Entity record directory with status indicators and search.', description: 'Filter and inspect member/employee/student records dynamically.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'KPI metrics dashboard summarizing active vs pending records.', description: 'Key performance indicators aggregating system records.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Inline status toggling and record creation workflow.', description: 'Create and update member records with validation.', type: 'FUNCTIONAL' as const, priority: 'MEDIUM' as const },
        { title: 'Export records to standardized CSV dataset.', description: 'One-click client-side CSV export of active directory.', type: 'FUNCTIONAL' as const, priority: 'MEDIUM' as const },
      ];
    } else if (isEventApp) {
      return [
        { title: 'Users can browse available events.', description: 'Users can browse available events with details and scheduling.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Users can search and filter events by category and date.', description: 'Filter events by taxonomy, tags, and date range.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Users can view complete event details including location, date, time and available seats.', description: 'Detailed view for single event including seat capacity.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Users can register for an available event.', description: 'Users can submit registration with attendee information.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Users can cancel their event registration.', description: 'Users can withdraw from registered events and free up seats.', type: 'FUNCTIONAL' as const, priority: 'MEDIUM' as const },
        { title: 'The system must prevent registration when an event has no available seats.', description: 'Registration gate rejects bookings when capacity is reached.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'The application provides REST APIs for event and registration management.', description: 'RESTful API interface for event lifecycle and attendee management.', type: 'NON_FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'The application provides a responsive web frontend.', description: 'Adaptive web interface compatible with modern browsers.', type: 'NON_FUNCTIONAL' as const, priority: 'HIGH' as const },
      ];
    } else if (isTaskApp) {
      return [
        { title: 'Users can create tasks with title, description, priority and due date.', description: 'Task authoring with priority and due date metadata.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Users can view all tasks in a responsive dashboard.', description: 'Dashboard view displaying tasks categorized by status.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Users can update task status and priority.', description: 'Inline editing and status transition for tasks.', type: 'FUNCTIONAL' as const, priority: 'MEDIUM' as const },
        { title: 'Users can delete tasks with confirmation.', description: 'Removal of tasks with safeguard confirmation modal.', type: 'FUNCTIONAL' as const, priority: 'MEDIUM' as const },
        { title: 'The application provides REST APIs for task management.', description: 'Comprehensive endpoints for task CRUD operations.', type: 'NON_FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'The application provides a modern web interface.', description: 'Polished web UI for productivity.', type: 'NON_FUNCTIONAL' as const, priority: 'HIGH' as const },
      ];
    }

    // Generic modern application starter requirements
    return [
      { title: 'Users can discover and browse core resources.', description: 'Directory view for exploring core system resources.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
      { title: 'Users can create, view, update and manage records.', description: 'Full lifecycle management for domain resources.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
      { title: 'Users can search and filter records dynamically.', description: 'Real-time query filters for record search.', type: 'FUNCTIONAL' as const, priority: 'MEDIUM' as const },
      { title: 'Application provides production-ready REST endpoints.', description: 'Standardized REST API contract with OpenAPI docs.', type: 'NON_FUNCTIONAL' as const, priority: 'HIGH' as const },
      { title: 'Application provides a responsive web client.', description: 'Accessible client supporting all form factors.', type: 'NON_FUNCTIONAL' as const, priority: 'HIGH' as const },
    ];
  };

  // Global Project creation & fast-track build mutation
  const createProjectMutation = useMutation({
    mutationFn: async (data: ProjectCreate & { autoBuild?: boolean }) => {
      const newProj = await projectsApi.create(data);

      // Fast Build Path: Automatically populate initial canonical requirements if description provided
      if (data.description && data.autoBuild !== false) {
        const starterReqs = extractStarterRequirements(data.description);
        for (const req of starterReqs) {
          try {
            await requirementsApi.create(newProj.id, {
              title: req.title,
              description: `Automated requirement synthesized from user project description: ${data.description.slice(0, 100)}...`,
              type: req.type,
              priority: req.priority,
            });
          } catch (e) {
            // Ignore single req error
          }
        }

        // Create baseline Context Snapshot v1
        try {
          await contextApi.createSnapshot(newProj.id, {
            summary: `${newProj.name} Baseline v1 — Initial requirements synthesized from project prompt.`,
          });
        } catch (e) {
          // Continue gracefully
        }
      }

      return newProj;
    },
    onSuccess: (newProject) => {
      queryClient.setQueryData(['projects'], (prev: ProjectResponse[] = []) => [
        newProject,
        ...prev.filter((p) => p.id !== newProject.id),
      ]);
      selectProject(newProject);
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      window.history.pushState({}, '', `/projects/${newProject.id}/workspace`);
      // Immediately land on central Live Preview!
      setActiveTab('preview');
    },
  });

  // 1. Session resolution loading state
  if (isAuthLoading) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'var(--bg-base, #0a0e1a)',
        }}
      >
        <LoadingSpinner label="Authenticating session..." />
      </div>
    );
  }

  // 2. Unauthenticated Gate -> Render Professional LoginView
  if (!isAuthenticated) {
    const intendedPath = typeof window !== 'undefined' ? window.location.pathname : '/projects';
    const isRegisterRoute = intendedPath === '/register';
    return (
      <LoginView
        initialMode={isRegisterRoute ? 'register' : 'login'}
        redirectPath={
          intendedPath === '/login' || intendedPath === '/register' || intendedPath === '/'
            ? '/projects'
            : intendedPath
        }
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['projects'] });
        }}
      />
    );
  }

  return (
    <>
      <AppShell
        activeTab={activeTab}
        onSelectTab={handleSelectTab}
        projects={projects}
        onOpenCreateProject={() => setIsCreateProjectOpen(true)}
        onOpenCreateTask={() => setIsCreateTaskOpen(true)}
        isAssistantOpen={isAssistantExplicitOpen}
        onToggleAssistant={() => setIsAssistantExplicitOpen((prev) => !prev)}
        initialAssistantPrompt={assistantInitialPrompt}
        onClearInitialAssistantPrompt={() => setAssistantInitialPrompt(null)}
      >
        {activeTab === 'projects' && (
          <ProjectsView
            onOpenWorkspace={(proj) => {
              selectProject(proj);
              setActiveTab('overview');
              window.history.pushState({}, '', `/projects/${proj.id}/workspace`);
            }}
            onOpenCreateProject={() => setIsCreateProjectOpen(true)}
          />
        )}
        {activeTab === 'preview' && (
          <PreviewWorkspace
            onNavigate={handleSelectTab}
            onOpenAssistant={() => setIsAssistantExplicitOpen(true)}
            onSendAssistantPrompt={(prompt) => {
              setAssistantInitialPrompt(prompt);
              setIsAssistantExplicitOpen(true);
            }}
            onOpenCreateProject={() => setIsCreateProjectOpen(true)}
          />
        )}
        {activeTab === 'overview' && (
          <OverviewWorkspace onNavigate={handleSelectTab} />
        )}
        {(activeTab === 'specification' || activeTab === 'requirements') && (
          <SpecificationWorkspace />
        )}
        {activeTab === 'development' && (
          <DevelopmentWorkspace onNavigate={handleSelectTab} />
        )}
        {activeTab === 'testing' && (
          <TestingWorkspace onNavigate={handleSelectTab} />
        )}
        {activeTab === 'environments' && (
          <EnvironmentWorkspace onNavigate={handleSelectTab} />
        )}
        {activeTab === 'issues' && <IssuesWorkspace />}
        {(activeTab === 'intelligence' || activeTab === 'data') && (
          <IntelligenceWorkspace onNavigate={handleSelectTab} />
        )}
        {activeTab === 'code-intelligence' && (
          <CodeIntelligenceWorkspace onNavigate={handleSelectTab} />
        )}
        {activeTab === 'workflows' && <WorkflowStudio />}
        {activeTab === 'history' && <RunHistory />}
      </AppShell>

      <CreateProjectModal
        isOpen={isCreateProjectOpen}
        onClose={() => setIsCreateProjectOpen(false)}
        onSubmit={async (data) => {
          await createProjectMutation.mutateAsync(data);
        }}
      />

      {selectedProjectId && (
        <CreateTaskModal
          isOpen={isCreateTaskOpen}
          onClose={() => setIsCreateTaskOpen(false)}
          projectId={selectedProjectId}
          projectName={selectedProject?.name}
          onNavigateTab={handleSelectTab}
        />
      )}
    </>
  );
};
