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
import { CodeStudioWorkspace } from './views/CodeStudioWorkspace';
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
import { useMode } from './context/ModeContext';
import { ModeSelectionView } from './views/ModeSelectionView';
import { UserModeWorkspace } from './views/UserModeWorkspace';
import { FloatingAssistant } from './components/assistant/FloatingAssistant';
import { ProjectCreate, ProjectResponse } from './types/project';

// Helper to parse pathname into project ID, workspace tab, and active view mode
const parseCurrentUrl = () => {
  if (typeof window === 'undefined') {
    return { isProjectsList: false, urlProjectId: null, urlTab: null, isSelectMode: false, isUserMode: false };
  }
  const path = window.location.pathname;
  if (path === '/select-mode' || path === '/select-mode/') {
    return { isProjectsList: false, urlProjectId: null, urlTab: null, isSelectMode: true, isUserMode: false };
  }
  if (path === '/user' || path === '/user/') {
    return { isProjectsList: false, urlProjectId: null, urlTab: null, isSelectMode: false, isUserMode: true };
  }
  if (path === '/projects' || path === '/projects/') {
    return { isProjectsList: true, urlProjectId: null, urlTab: null, isSelectMode: false, isUserMode: false };
  }
  const match = path.match(/^\/projects\/([^/]+)(?:\/workspace)?(?:\/([a-z-]+))?/i);
  if (match) {
    return {
      isProjectsList: false,
      urlProjectId: match[1],
      urlTab: (match[2] as NavigationTab) || null,
      isSelectMode: false,
      isUserMode: false,
    };
  }
  return { isProjectsList: false, urlProjectId: null, urlTab: null, isSelectMode: false, isUserMode: false };
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
  const { mode, isModeSelected, isModeSelectionOpen, setMode, switchMode, closeModeSelection } = useMode();

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

  // Auto-redirect authenticated user from /login, /register, or / to mode destination
  React.useEffect(() => {
    if (isAuthenticated && typeof window !== 'undefined') {
      const path = window.location.pathname;
      if (path === '/' || path === '/login' || path === '/register') {
        if (!isModeSelected) {
          window.history.replaceState({}, '', '/select-mode');
        } else if (mode === 'user') {
          window.history.replaceState({}, '', '/user');
        } else {
          window.history.replaceState({}, '', '/projects');
          setActiveTab('projects');
        }
      }
    }
  }, [isAuthenticated, isModeSelected, mode]);

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
    enabled: isAuthenticated,
  });

  // Authoritatively sync projects and auto-heal stale projects
  React.useEffect(() => {
    if (isAuthenticated && projects.length > 0 && validateAndSyncProjects) {
      validateAndSyncProjects(projects);
    }
  }, [projects, validateAndSyncProjects, isAuthenticated]);

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
      const { isProjectsList, urlProjectId, urlTab, isSelectMode, isUserMode } = parseCurrentUrl();
      if (isSelectMode) {
        return;
      }
      if (isUserMode) {
        if (mode !== 'user') switchMode('user');
        return;
      }
      if (isProjectsList) {
        if (mode !== 'developer') switchMode('developer');
        setActiveTab('projects');
      } else if (urlProjectId && projects.length > 0) {
        if (mode !== 'developer') switchMode('developer');
        const match = projects.find((p) => p.id === urlProjectId || p.slug === urlProjectId);
        if (match) {
          selectProject(match);
          setActiveTab(urlTab || 'overview');
        }
      }
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [projects, selectProject, mode, switchMode]);

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
    const hasWord = (w: string) => new RegExp(`\\b${w}\\b`, 'i').test(text);

    const isShadowMasterApp = text.includes('shadow') || text.includes('ninja') || text.includes('stealth') || text.includes('skill builder');
    const isCarromApp = text.includes('carrom') || text.includes('striker');
    const isChessApp = text.includes('chess') || text.includes('checkmate') || text.includes('chessboard');
    const isPlatformerApp = text.includes('platformer') || text.includes('side-scroller') || (text.includes('jump') && text.includes('run'));
    const isRacingApp = text.includes('racing') || text.includes('racer') || text.includes('circuit') || text.includes('speedway') || text.includes('nitro');
    const isPuzzleApp = text.includes('puzzle') || text.includes('sliding tile') || text.includes('15-puzzle') || text.includes('sudoku');
    const isEducationalApp = text.includes('flashcard') || text.includes('studydeck') || text.includes('quiz') || text.includes('trivia') || text.includes('vocab');
    const isAnalyticsApp = text.includes('analytics') || text.includes('dashboard') || text.includes('kpi') || text.includes('metric') || text.includes('revenue') || text.includes('bi ');
    const isSnakeGameApp = text.includes('snake') || text.includes('slither') || text.includes('nibbles');
    const isGameApp = text.includes('arcade') || text.includes('game');
    const isEventApp = text.includes('event') || text.includes('conference') || text.includes('summit');
    const isTaskApp = text.includes('kanban') || text.includes('taskflow') || text.includes('todo') || text.includes('backlog') || (text.includes('task') && !text.includes('management'));
    const isShopApp = text.includes('shop') || text.includes('store') || text.includes('ecommerce') || text.includes('cart') || hasWord('merchandise') || hasWord('catalog');
    const isManageApp = text.includes('student') || text.includes('employee') || text.includes('directory') || text.includes('roster') || text.includes('management') || text.includes('admin') || text.includes('record');

    if (isShadowMasterApp) {
      return [
        { title: 'HTML5 Canvas 2D Shadow Master combat arena.', description: 'Smooth 60fps rendering with player shadow physics, directional movement (WASD/Arrow keys), and mouse aim.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Full combat ability suite with active hotbar.', description: 'Katana Slash (Q), Shadow Dash (W), Shuriken Volley (E), Shadow Cloak (R), and Shadow Decoy (Space).', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Dynamic enemy training dummies and patrolling shadow guards.', description: 'Real-time collision detection, enemy health bars, floating combat text, and XP rewards.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Real-time Skill Builder and Parameter Customizer.', description: 'Live tuning panel for skill damage, energy cost, cooldown, radius, element type, and preset loader.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Player combat HUD with stats, combo multiplier, and score.', description: 'Dynamic Health bar, Shadow Energy meter, level progression, combo multiplier, and total score.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Skill Tree JSON export and backend synchronization.', description: 'One-click validated JSON export for game engine consumption and REST API combat score persistence.', type: 'NON_FUNCTIONAL' as const, priority: 'HIGH' as const },
      ];
    } else if (isCarromApp) {
      return [
        { title: 'HTML5 Canvas 2D Carrom board physics engine.', description: 'Smooth 60fps simulation of striker and carrom pieces with realistic 2D circular collision, rebound restitution, and surface friction.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Interactive striker placement and aiming controls.', description: 'Baseline position slider and intuitive pull-back drag aiming with dynamic power gauge and trajectory guidance.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Full 19-piece carrom set and pocket detection.', description: 'Nine white pieces, nine black pieces, and one red Queen with corner pocket hole detection and automated piece collection.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Live match scoreboard and turn tracking.', description: 'Player 1 (White) and Player 2 (Black) score tally, active turn indicator, Queen cover state, and remaining coin count.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Solo practice mode and match reset.', description: 'Toggle between two-player turn-based match and solo practice drill with board reset.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Interactive Live Preview prototype.', description: 'Direct browser carrom game prototype on SE IntelliPlatform preview runtime.', type: 'NON_FUNCTIONAL' as const, priority: 'HIGH' as const },
      ];
    } else if (isChessApp) {
      return [
        { title: 'Interactive 8x8 Chessboard with standard rules.', description: 'Turn-based move evaluation, legal move indicators, and piece selection.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Live move history algebraic notation logger.', description: 'Records standard algebraic moves and turn sequencing dynamically.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Captured pieces tray and material advantage score.', description: 'Visual tray tallying captured pawns, knights, bishops, rooks, and queens.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Match timer, restart, and side-switch controls.', description: 'Full match lifecycle control with turn timers and clean reset.', type: 'FUNCTIONAL' as const, priority: 'MEDIUM' as const },
        { title: 'Interactive Live Preview prototype.', description: 'Direct browser strategic chess prototype on SE IntelliPlatform preview runtime.', type: 'NON_FUNCTIONAL' as const, priority: 'HIGH' as const },
      ];
    } else if (isPlatformerApp) {
      return [
        { title: '60 FPS 2D physics engine with gravity and momentum.', description: 'Smooth player velocity, jumping mechanics, platform collisions, and inertia.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Multi-tiered floating platforms and collectible coins.', description: 'Level terrain with collectible gold coins and scoring incentives.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Dynamic hazard obstacles and life loss penalties.', description: 'Spikes and boundary fall hazards with health/lives management.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Live game HUD with score, coins, and lives counter.', description: 'Real-time performance indicators and game-over state restart.', type: 'FUNCTIONAL' as const, priority: 'MEDIUM' as const },
      ];
    } else if (isRacingApp) {
      return [
        { title: 'Top-down 2D racing circuit with continuous asphalt track.', description: 'Smooth 60fps canvas rendering of circuit curves and track barriers.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Realistic vehicle steering physics with drift and brake.', description: 'Acceleration curves, friction braking, steering angles, and drift smoke.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Telemetry HUD displaying speedometer, tachometer, and lap timer.', description: 'Real-time vehicle telemetry with current, best, and total lap times.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Interactive Live Preview prototype.', description: 'Direct browser circuit racing prototype on SE IntelliPlatform preview runtime.', type: 'NON_FUNCTIONAL' as const, priority: 'HIGH' as const },
      ];
    } else if (isPuzzleApp) {
      return [
        { title: 'Interactive sliding tile puzzle grid with smooth animation.', description: 'Dynamic grid layout with empty slot swapping mechanics.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Solvable shuffle algorithm and move counter.', description: 'Mathematically guaranteed solvable permutations with move counter.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Live timer, victory detection banner, and difficulty presets.', description: 'Elapsed time tracker and instant win state verification.', type: 'FUNCTIONAL' as const, priority: 'MEDIUM' as const },
      ];
    } else if (isEducationalApp) {
      return [
        { title: 'Interactive 3D flip study flashcards with mastery marking.', description: 'Smooth CSS 3D card flips between question and answer with Know/Need Review buttons.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Timed multiple-choice quiz engine with instant score tally.', description: 'Randomized questions, immediate feedback, and score calculation.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Deck category switcher and performance analytics summary.', description: 'Study subject switching and completion percentage tracking.', type: 'FUNCTIONAL' as const, priority: 'MEDIUM' as const },
      ];
    } else if (isAnalyticsApp) {
      return [
        { title: 'Executive KPI summary cards for revenue, retention, and conversion.', description: 'Real-time performance cards with formatted currency and trend indicators.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Interactive revenue trajectory chart and multi-stage funnel visualization.', description: 'Dynamic SVG trend line with hoverable data points and funnel drop-off metrics.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Searchable, filterable, and sortable team metrics data table.', description: 'Interactive table with category tabs, search input, and column sorting.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Custom metric creation modal and client-side CSV export.', description: 'Dialog to record new metrics and one-click CSV download capability.', type: 'FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Responsive grid adapting seamlessly from desktop to tablet and mobile.', description: 'Fluid layout adjusting from 4-column KPI cards to 2-column tablet and stacked mobile.', type: 'NON_FUNCTIONAL' as const, priority: 'HIGH' as const },
        { title: 'Interactive Live Preview prototype.', description: 'Direct browser executive analytics prototype on SE IntelliPlatform preview runtime.', type: 'NON_FUNCTIONAL' as const, priority: 'HIGH' as const },
      ];
    } else if (isSnakeGameApp || isGameApp) {
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
    const intendedPath = typeof window !== 'undefined' ? window.location.pathname : '/select-mode';
    const isRegisterRoute = intendedPath === '/register';
    return (
      <LoginView
        initialMode={isRegisterRoute ? 'register' : 'login'}
        redirectPath={
          intendedPath === '/login' || intendedPath === '/register' || intendedPath === '/'
            ? '/select-mode'
            : intendedPath
        }
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['projects'] });
        }}
      />
    );
  }

  // 3. First-time or Explicit Mode Selection Gate
  const isSelectModePath = typeof window !== 'undefined' && window.location.pathname.startsWith('/select-mode');
  if (!isModeSelected || isSelectModePath) {
    return (
      <ModeSelectionView
        onSelectMode={(selectedMode, remember) => {
          setMode(selectedMode, remember);
          if (selectedMode === 'user') {
            window.history.pushState({}, '', '/user');
          } else {
            const target = selectedProjectId ? `/projects/${selectedProjectId}/workspace` : '/projects';
            window.history.pushState({}, '', target);
            if (!selectedProjectId) {
              setActiveTab('projects');
            }
          }
        }}
        canClose={isModeSelected}
        onClose={closeModeSelection}
        currentMode={mode}
      />
    );
  }

  // 4. User Mode Experience
  if (mode === 'user') {
    return (
      <>
        <UserModeWorkspace
          projects={projects}
          onOpenCreateProject={() => setIsCreateProjectOpen(true)}
          onCreateProject={async (data) => {
            return await createProjectMutation.mutateAsync(data);
          }}
          onNavigateToProjectInDev={(proj) => {
            selectProject(proj);
            setActiveTab('overview');
            window.history.pushState({}, '', `/projects/${proj.id}/workspace`);
            switchMode('developer');
          }}
        />

        {/* Global Floating AI Assistant (ambient, general Q&A) */}
        <FloatingAssistant
          currentMode="user"
          activeProjectName={selectedProject?.name}
          onNavigateTab={handleSelectTab}
        />

        {isModeSelectionOpen && (
          <ModeSelectionView
            onSelectMode={(selectedMode, remember) => {
              setMode(selectedMode, remember);
              if (selectedMode === 'user') {
                window.history.pushState({}, '', '/user');
              } else {
                const target = selectedProjectId ? `/projects/${selectedProjectId}/workspace` : '/projects';
                window.history.pushState({}, '', target);
                if (!selectedProjectId) {
                  setActiveTab('projects');
                }
              }
            }}
            canClose={true}
            onClose={closeModeSelection}
            currentMode={mode}
          />
        )}

        <CreateProjectModal
          isOpen={isCreateProjectOpen}
          onClose={() => setIsCreateProjectOpen(false)}
          onSubmit={async (data) => {
            await createProjectMutation.mutateAsync(data);
          }}
        />
      </>
    );
  }

  // 5. Developer Mode Experience (Existing AppShell)
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
        {activeTab === 'code-studio' && (
          <CodeStudioWorkspace onNavigate={handleSelectTab} />
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

      {/* Global Floating AI Assistant (ambient across Developer Mode) */}
      <FloatingAssistant
        currentMode="developer"
        activeProjectName={selectedProject?.name}
        onNavigateTab={handleSelectTab}
      />

      {/* Mode selection modal overlay if re-opened from Header */}
      {isModeSelectionOpen && (
        <ModeSelectionView
          onSelectMode={(selectedMode, remember) => {
            setMode(selectedMode, remember);
            if (selectedMode === 'user') {
              window.history.pushState({}, '', '/user');
            } else {
              const target = selectedProjectId ? `/projects/${selectedProjectId}/workspace` : '/projects';
              window.history.pushState({}, '', target);
              if (!selectedProjectId) {
                setActiveTab('projects');
              }
            }
          }}
          canClose={true}
          onClose={closeModeSelection}
          currentMode={mode}
        />
      )}

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
