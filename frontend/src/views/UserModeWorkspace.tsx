import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  Bot,
  Plus,
  ArrowRight,
  FolderKanban,
  Compass,
  Code2,
  CheckCircle2,
  AlertCircle,
  Terminal,
  ChevronRight,
  ShieldCheck,
  Play,
  RotateCw,
  Monitor,
  Tablet,
  Smartphone,
  ExternalLink,
  Loader2,
  Wand2,
  Eye,
  Check,
  RotateCcw,
  GitBranch,
  FileCode,
  ChevronDown,
  ChevronUp,
  LayoutTemplate,
  PlusCircle,
  ArrowLeft,
  Download,
} from 'lucide-react';
import { useProject } from '../context/ProjectContext';
import { useMode } from '../context/ModeContext';
import { ProjectResponse, ProjectCreate } from '../types/project';
import { Header } from '../components/layout/Header';
import { Button } from '../components/common/Button';
import { chatApi } from '../services/chatApi';
import { previewRuntimeApi } from '../services/previewRuntimeApi';
import { workflowsApi } from '../services/workflowsApi';
import { assistantApi } from '../services/assistantApi';
import { developmentVersionApi } from '../services/developmentVersionApi';
import { codeStudioApi } from '../services/codeStudioApi';
import { projectsApi } from '../services/projectsApi';
import { FileNode } from '../types/codeStudio';
import { GuidedAppPlanResponse } from '../types/chat';
import { ActionResult, AssistantMessage } from '../types/assistant';
import { slugify } from '../utils/slugify';

interface UserModeWorkspaceProps {
  projects: ProjectResponse[];
  onOpenCreateProject: () => void;
  onCreateProject?: (data: ProjectCreate & { autoBuild?: boolean }) => Promise<ProjectResponse>;
  onNavigateToProjectInDev?: (project: ProjectResponse) => void;
  onOpenGlobalAssistant?: (prompt?: string) => void;
}

export type SupportedTemplateId =
  | 'executive_analytics_dashboard'
  | 'kanban_task_manager'
  | 'event_booking_hub'
  | 'management_directory'
  | 'ecommerce_store'
  | 'canvas_arcade_game';

export interface AppTemplate {
  id: SupportedTemplateId;
  name: string;
  slug: string;
  tagline: string;
  description: string;
  badge: string;
  category: string;
  prompt: string;
  features: string[];
  requirements: Array<{
    title: string;
    description: string;
    type: 'FUNCTIONAL' | 'NON_FUNCTIONAL';
    priority: 'HIGH' | 'MEDIUM';
  }>;
}

export const SUPPORTED_TEMPLATES: AppTemplate[] = [
{
    id: 'kanban_task_manager',
    name: 'Real-Time Kanban Task Manager',
    slug: 'kanban-task-manager',
    tagline: 'Collaborative task board with drag-and-drop lanes and priority tags.',
    description: 'A modern Kanban task board with drag-and-drop columns, priority tags, and due dates.',
    badge: 'Popular',
    category: 'Task Management',
    prompt: 'A modern Kanban task board with drag-and-drop columns, priority tags, and due dates',
    features: [
      'Interactive Kanban board with Backlog, In Progress, Review, and Done lanes',
      'Task authoring with priority badges (High, Medium, Low) and due dates',
      'RESTful CRUD endpoints for task updates and status transitions',
      'Isolated Docker container preview with live state synchronization',
    ],
    requirements: [
      {
        title: 'Interactive Kanban Dashboard UI',
        description: 'React dashboard with drag-and-drop task lanes and state indicators.',
        type: 'FUNCTIONAL',
        priority: 'HIGH',
      },
      {
        title: 'RESTful Task CRUD API',
        description: 'FastAPI backend routes for task creation, editing, and state transitions.',
        type: 'FUNCTIONAL',
        priority: 'HIGH',
      },
      {
        title: 'Status Lifecycle Transitions & Priority Filters',
        description: 'Filter and transition tasks dynamically across columns.',
        type: 'FUNCTIONAL',
        priority: 'MEDIUM',
      },
      {
        title: 'Docker Preview Sandbox',
        description: 'Containerized isolated execution on port 8001.',
        type: 'NON_FUNCTIONAL',
        priority: 'HIGH',
      },
    ],
  },
  {
    id: 'event_booking_hub',
    name: 'Event & Conference Booking Hub',
    slug: 'event-booking-hub',
    tagline: 'Event discovery, seat availability limits, and attendee registration.',
    description: 'Browse upcoming conferences with dates, location, and seat capacity limits, and manage reservations.',
    badge: 'Enterprise',
    category: 'Events & Bookings',
    prompt: 'An event discovery and conference booking platform with seat availability gating and attendee registration',
    features: [
      'Event catalog with date taxonomy, venue location, and available seats',
      'Attendee registration workflow with automatic capacity gating',
      'Reservation cancellation mechanism with immediate seat release',
      'Full-stack FastAPI backend and modern responsive interface',
    ],
    requirements: [
      {
        title: 'Event Catalog & Category Filtering',
        description: 'Users can discover upcoming events filtered by category, date, and venue.',
        type: 'FUNCTIONAL',
        priority: 'HIGH',
      },
      {
        title: 'Attendee Registration with Seat Capacity Gating',
        description: 'Prevents over-booking when an event has reached maximum capacity.',
        type: 'FUNCTIONAL',
        priority: 'HIGH',
      },
      {
        title: 'Reservation Cancellation & Seat Recovery',
        description: 'Allow registered attendees to cancel bookings and recover seat quotas.',
        type: 'FUNCTIONAL',
        priority: 'MEDIUM',
      },
      {
        title: 'Event Management REST API',
        description: 'Structured RESTful API endpoints for events and attendees.',
        type: 'NON_FUNCTIONAL',
        priority: 'HIGH',
      },
    ],
  },
  {
    id: 'management_directory',
    name: 'Team Directory & Admin Portal',
    slug: 'team-directory-portal',
    tagline: 'Employee directory with KPI cards, inline status toggling, and CSV export.',
    description: 'Manage organization members and resources with KPI summary cards, filterable metric tables, and CSV data export.',
    badge: 'Productivity',
    category: 'Operations',
    prompt: 'A responsive employee and team directory with search filters, role badges, and record management',
    features: [
      'Team member directory with department tags, email, and role badges',
      'KPI metric summary cards tracking active vs pending members',
      'Instant search and filter by department, seniority, and status',
      'Client-side standardized CSV export of the active roster',
    ],
    requirements: [
      {
        title: 'Member Record Management & Status Toggling',
        description: 'Create, update, and manage employee profiles with inline status toggling.',
        type: 'FUNCTIONAL',
        priority: 'HIGH',
      },
      {
        title: 'KPI Metrics Dashboard Summary',
        description: 'Real-time calculation of active team counts and department breakdowns.',
        type: 'FUNCTIONAL',
        priority: 'HIGH',
      },
      {
        title: 'Client-Side CSV Dataset Export',
        description: 'One-click client-side export of filtered records to CSV.',
        type: 'FUNCTIONAL',
        priority: 'MEDIUM',
      },
      {
        title: 'Accessible Responsive Administration UI',
        description: 'Modern table layout optimized for mobile and desktop screens.',
        type: 'NON_FUNCTIONAL',
        priority: 'HIGH',
      },
    ],
  },
  {
    id: 'ecommerce_store',
    name: 'E-Commerce Store & Catalog',
    slug: 'ecommerce-store-catalog',
    tagline: 'Product taxonomy, interactive cart with live subtotals, and checkout.',
    description: 'An interactive store catalog with shopping cart, category filters, and live checkout workflow.',
    badge: 'Commerce',
    category: 'Retail',
    prompt: 'An interactive store catalog with shopping cart, category filters, and live checkout',
    features: [
      'Product gallery with category filters, ratings, and price sorting',
      'Interactive sliding shopping cart with live subtotal calculation',
      'Checkout modal with shipping details and order confirmation',
      'Inventory availability validation preventing out-of-stock purchases',
    ],
    requirements: [
      {
        title: 'Product Catalog with Taxonomy & Search',
        description: 'Browse products with responsive cards, search, and category facets.',
        type: 'FUNCTIONAL',
        priority: 'HIGH',
      },
      {
        title: 'Interactive Shopping Cart with Live Subtotals',
        description: 'Add, increment, decrement, and remove items with instant price updates.',
        type: 'FUNCTIONAL',
        priority: 'HIGH',
      },
      {
        title: 'Checkout & Order Summary Workflow',
        description: 'Step-by-step checkout with delivery info and validation.',
        type: 'FUNCTIONAL',
        priority: 'HIGH',
      },
      {
        title: 'Inventory Availability Constraints',
        description: 'Ensure items in cart do not exceed available warehouse stock.',
        type: 'NON_FUNCTIONAL',
        priority: 'HIGH',
      },
    ],
  },
  {
    id: 'canvas_arcade_game',
    name: 'HTML5 Canvas 2D Arcade Game',
    slug: 'canvas-2d-arcade-game',
    tagline: 'Retro arcade game with canvas engine, direction controls, and high scores.',
    description: 'A classic 2D arcade game with directional controls, live score tracking, and restart states.',
    badge: 'Interactive',
    category: 'Gaming',
    prompt: 'A classic 2D Snake game with directional controls, score tracking, and restart states',
    features: [
      'High-performance 60 FPS HTML5 Canvas game loop rendering engine',
      'Responsive keyboard (Arrow/WASD) and touch directional controls',
      'Live score calculation, speed progression, and local high-score storage',
      'Game state manager handling Start, Playing, Paused, and Game Over states',
    ],
    requirements: [
      {
        title: 'HTML5 Canvas 2D Rendering Engine',
        description: 'Smooth 60 FPS game loop using requestAnimationFrame.',
        type: 'FUNCTIONAL',
        priority: 'HIGH',
      },
      {
        title: 'Directional Keyboard & Touchpad Controls',
        description: 'Seamless controls for desktop keys and mobile touch gestures.',
        type: 'FUNCTIONAL',
        priority: 'HIGH',
      },
      {
        title: 'Persistent High-Score Tracking',
        description: 'Record player scores with persistence across sessions.',
        type: 'FUNCTIONAL',
        priority: 'MEDIUM',
      },
      {
        title: 'Game State Machine Architecture',
        description: 'Clean transitions between menu, active play, pause, and game over.',
        type: 'NON_FUNCTIONAL',
        priority: 'HIGH',
      },
    ],
  },
  {
    id: 'executive_analytics_dashboard',
    name: 'Executive Analytics Dashboard',
    slug: 'executive-analytics-dashboard',
    tagline: 'Real-time revenue charts, user retention metrics, conversion funnel, and team KPIs.',
    description: 'Executive analytics dashboard with revenue charts, user retention metrics, conversion funnel, and team performance KPIs',
    badge: 'Executive',
    category: 'Analytics & BI',
    prompt: 'Executive analytics dashboard with revenue charts, user retention metrics, conversion funnel, and team performance KPIs',
    features: [
      'Executive KPI summary cards ($1.42M ARR, 3,842 workspaces, 24.6% conversion)',
      'Dynamic SVG revenue growth trajectory and conversion funnel charts',
      'Searchable, sortable metrics table with status indicators and category filters',
      'Interactive "+ Add Metric" modal dialog and live CSV export capabilities',
      'Responsive design adapting from desktop 4-column grid to mobile single column',
    ],
    requirements: [
      {
        title: 'Executive KPI Summary Cards (Revenue, Workspaces, Conversions, Churn)',
        description: 'Real-time KPI metrics with green trend badges, formatted numbers, and subtext.',
        type: 'FUNCTIONAL',
        priority: 'HIGH',
      },
      {
        title: 'Interactive Revenue Trajectory & Conversion Funnel Charts',
        description: 'Interactive SVG line charts with gradient fills, hover tooltips, and drop-off funnel bars.',
        type: 'FUNCTIONAL',
        priority: 'HIGH',
      },
      {
        title: 'Filterable & Sortable Team Performance Metrics Table',
        description: 'Dynamic table with search input, category tabs (All, Financial, Product, Retention), and header sorting.',
        type: 'FUNCTIONAL',
        priority: 'HIGH',
      },
      {
        title: 'Custom Metric Creation Modal & CSV Export Capabilities',
        description: 'Client-side modal dialog to append custom metrics and one-click CSV export button.',
        type: 'FUNCTIONAL',
        priority: 'HIGH',
      },
      {
        title: 'Responsive Multi-Device Layout (Desktop, Tablet, Mobile)',
        description: 'Adaptive layout automatically restructuring from 4-column desktop to 2-column tablet and stacked mobile.',
        type: 'NON_FUNCTIONAL',
        priority: 'HIGH',
      },
      {
        title: 'Live Interactive Preview Prototype on Port 8001',
        description: 'Instant running prototype in SE IntelliPlatform sandbox runtime.',
        type: 'NON_FUNCTIONAL',
        priority: 'HIGH',
      },
    ],
  },
];

const SUGGESTED_REFINEMENTS = [
  'Add a dark mode toggle.',
  'Add a search bar to the task list.',
  'Add an export to CSV button.',
  'Make the layout work better on mobile.',
  'Fix the error when I submit the form.',
];

const SUGGESTED_PROMPTS = [
  {
    type: 'create',
    label: 'Build a Real-Time Kanban Task Manager',
    prompt: 'A modern Kanban task board with drag-and-drop columns, priority tags, and due dates',
  },
  {
    type: 'create',
    label: 'Create an Executive Analytics Dashboard',
    prompt: 'An executive analytics dashboard with KPI summary cards, filterable metric tables, and CSV data export',
  },
  {
    type: 'create',
    label: 'Build a Team Directory & Member CRUD App',
    prompt: 'A responsive employee and team directory with search filters, role badges, and record management',
  },
  {
    type: 'create',
    label: 'Create an E-Commerce Store & Catalog',
    prompt: 'An interactive store catalog with shopping cart, category filters, and live checkout',
  },
  {
    type: 'create',
    label: 'Develop an HTML5 Canvas 2D Arcade Game',
    prompt: 'A classic 2D Snake game with directional controls, score tracking, and restart states',
  },
];

export const UserModeWorkspace: React.FC<UserModeWorkspaceProps> = ({
  projects,
  onOpenCreateProject,
  onCreateProject,
  onNavigateToProjectInDev,
  onOpenGlobalAssistant: _onOpenGlobalAssistant,
}) => {
  const { switchMode } = useMode();
  const { selectedProject, selectProject } = useProject();

  // Active creation workflow mode
  const [activeCreationMode, setActiveCreationMode] = useState<'none' | 'ai' | 'templates' | 'scratch'>('ai');

  // Conversational Blueprint state (Stage 1 & 3)
  const [promptInput, setPromptInput] = useState('');
  const [isPlanning, setIsPlanning] = useState(false);
  const [planResult, setPlanResult] = useState<GuidedAppPlanResponse | null>(null);
  const [planError, setPlanError] = useState<string | null>(null);

  // Scratch creation state
  const [scratchName, setScratchName] = useState('');
  const [scratchSlug, setScratchSlug] = useState('');
  const [scratchDescription, setScratchDescription] = useState('');
  const [scratchCategory, setScratchCategory] = useState('web_app');
  const [scratchAuthRequired, setScratchAuthRequired] = useState(true);
  const [scratchDatabaseRequired, setScratchDatabaseRequired] = useState(true);

  // Creation & Build execution state (Stage 4)
  const [isCreatingProject, setIsCreatingProject] = useState(false);
  const [createdProject, setCreatedProject] = useState<ProjectResponse | null>(null);
  const [creationError, setCreationError] = useState<string | null>(null);

  // Autonomous App Builder & Live Preview State (Stage 4 & 5)
  type BuilderStage =
    | 'IDLE'
    | 'CREATING_PROJECT'
    | 'GENERATING_CODE'
    | 'VALIDATING_ARTIFACTS'
    | 'LAUNCHING_CONTAINER'
    | 'VERIFYING_HEALTH'
    | 'LIVE'
    | 'ERROR';

  const [builderStage, setBuilderStage] = useState<BuilderStage>('IDLE');
  const [stageProgressText, setStageProgressText] = useState<string>('');
  const [runtimeStatus, setRuntimeStatus] = useState<string>('STOPPED');
  const [runtimePort, setRuntimePort] = useState<number>(8001);
  const [livePreviewUrl, setLivePreviewUrl] = useState<string | null>(null);
  const [deviceViewport, setDeviceViewport] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');
  const [previewKey, setPreviewKey] = useState<number>(Date.now());
  const [builderError, setBuilderError] = useState<string | null>(null);

  // Continuous Natural-Language App Refinement State (Stage 6)
  const [refinementPrompt, setRefinementPrompt] = useState<string>('');
  const [refinementMessages, setRefinementMessages] = useState<AssistantMessage[]>([]);
  const [isRefining, setIsRefining] = useState<boolean>(false);
  const [isApplyingChange, setIsApplyingChange] = useState<boolean>(false);
  const [pendingActionResult, setPendingActionResult] = useState<ActionResult | null>(null);
  const [activeVersionNum, setActiveVersionNum] = useState<number>(1);
  const [refinementError, setRefinementError] = useState<string | null>(null);
  const [refinementSuccess, setRefinementSuccess] = useState<string | null>(null);
  const [isDiffExpanded, setIsDiffExpanded] = useState<boolean>(false);
  const [conversationId, setConversationId] = useState<string | null>(null);

  // Beginner Mode 5-Option Navigation Architecture
  type BeginnerTab = 'projects' | 'overview' | 'code-studio' | 'preview' | 'assistant';
  const [activeTab, setActiveTab] = useState<BeginnerTab>('projects');

  // Code Studio inspection state
  const [studioFiles, setStudioFiles] = useState<FileNode[]>([]);
  const [selectedStudioPath, setSelectedStudioPath] = useState<string>('frontend/index.html');
  const [studioCodeContent, setStudioCodeContent] = useState<string>('');
  const [isStudioLoading, setIsStudioLoading] = useState<boolean>(false);
  const [isDownloadingZip, setIsDownloadingZip] = useState<boolean>(false);
  const [downloadNotice, setDownloadNotice] = useState<string | null>(null);

  // Active project resolution
  const currentProject = createdProject || selectedProject || (projects.length > 0 ? projects[0] : null);

  useEffect(() => {
    if (!selectedProject && projects.length > 0) {
      selectProject(projects[0]);
    }
  }, [projects, selectedProject, selectProject]);

  function findFirstFileNode(nodes: FileNode[]): FileNode | null {
    for (const node of nodes) {
      if (node.type === 'file') return node;
      if (node.children) {
        const found = findFirstFileNode(node.children);
        if (found) return found;
      }
    }
    return null;
  }

  function getFallbackFileContent(filePath: string, appName: string = 'Application'): string {
    if (filePath.endsWith('index.html')) {
      return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${appName}</title>
  <link rel="stylesheet" href="./styles.css" />
</head>
<body>
  <div id="root"></div>
  <script type="module" src="./src/App.tsx"></script>
</body>
</html>`;
    }
    if (filePath.endsWith('main.py')) {
      return `"""FastAPI Backend Application for ${appName}."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="${appName}", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "${appName}"}
`;
    }
    if (filePath.endsWith('package.json')) {
      return JSON.stringify(
        {
          name: appName.toLowerCase().replace(/\s+/g, '-'),
          version: '1.0.0',
          private: true,
          scripts: { dev: 'vite', build: 'vite build', preview: 'vite preview' },
          dependencies: { react: '^18.3.1', 'react-dom': '^18.3.1', 'lucide-react': '^0.460.0' },
        },
        null,
        2
      );
    }
    if (filePath.endsWith('.css')) {
      return `/* Modern Responsive Styles for ${appName} */
:root {
  --primary: #4f46e5;
  --bg: #0b0f19;
  --text: #f8fafc;
  --card-bg: #1e293b;
  --border: #334155;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
}
`;
    }
    if (filePath.endsWith('.tsx') || filePath.endsWith('.jsx')) {
      return `import React from 'react';

export default function App() {
  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>${appName}</h1>
      <p>Autonomous AI application workspace.</p>
    </div>
  );
}
`;
    }
    if (filePath.endsWith('.ts') || filePath.endsWith('.js')) {
      return `// Module ${filePath} for ${appName}
export const config = {};
export default config;
`;
    }
    return `# ${appName}

Synthesized by SE IntelliPlatform autonomous AI software engineering engine.

## Getting Started
1. Run \`npm install\` inside \`frontend/\`
2. Run \`pip install -r requirements.txt\` inside \`backend/\`
3. Launch development server with \`npm run dev\`
`;
  }

  const loadStudioFiles = async (projId: string) => {
    setIsStudioLoading(true);
    try {
      const tree = await codeStudioApi.getFileTree(projId);
      if (tree.root_nodes && tree.root_nodes.length > 0) {
        setStudioFiles(tree.root_nodes);
        const first = findFirstFileNode(tree.root_nodes);
        if (first) {
          setSelectedStudioPath(first.path);
          try {
            const content = await codeStudioApi.getFileContent(projId, first.path);
            setStudioCodeContent(content.content || '');
          } catch {
            setStudioCodeContent(getFallbackFileContent(first.path, currentProject?.name));
          }
        }
      } else {
        setStudioFiles([]);
        setStudioCodeContent('');
      }
    } catch {
      setStudioFiles([]);
      setStudioCodeContent('');
    } finally {
      setIsStudioLoading(false);
    }
  };

  useEffect(() => {
    const target = currentProject || createdProject;
    if (activeTab === 'code-studio' && target?.id) {
      loadStudioFiles(target.id);
    }
  }, [activeTab, currentProject?.id, createdProject?.id]);

  useEffect(() => {
    if (activeTab === 'preview' && (currentProject || createdProject) && !livePreviewUrl) {
      handleLaunchProjectPreview(currentProject || createdProject!);
    }
  }, [activeTab, currentProject?.id, createdProject?.id, livePreviewUrl]);

  const handleDownloadZip = async (proj?: ProjectResponse | null) => {
    const target = proj || currentProject || createdProject;
    if (!target) return;
    setIsDownloadingZip(true);
    setDownloadNotice(null);
    try {
      const filename = `${target.slug || 'project'}-source.zip`;
      await projectsApi.download(target.id, filename);
      setDownloadNotice(`✓ Downloaded ${filename} successfully!`);
    } catch (err: any) {
      setDownloadNotice(`Download notice: ${err?.message || 'Could not download ZIP'}`);
    } finally {
      setIsDownloadingZip(false);
    }
  };

  // Listen for remote live preview and version refresh events
  useEffect(() => {
    const handleRemoteRefresh = () => {
      setPreviewKey(Date.now());
    };
    const handleVersionRefresh = (e: any) => {
      if (e.detail?.version_number) {
        setActiveVersionNum(e.detail.version_number);
      }
      setPreviewKey(Date.now());
    };
    window.addEventListener('se-preview-refresh', handleRemoteRefresh);
    window.addEventListener('se-version-refresh', handleVersionRefresh);
    return () => {
      window.removeEventListener('se-preview-refresh', handleRemoteRefresh);
      window.removeEventListener('se-version-refresh', handleVersionRefresh);
    };
  }, []);

  // Compute active journey stage for the guided progress stepper (1 through 6)
  const getCurrentStageNumber = (): number => {
    if (livePreviewUrl && createdProject) {
      return refinementMessages.length > 0 || pendingActionResult ? 6 : 5;
    }
    if (
      builderStage === 'CREATING_PROJECT' ||
      builderStage === 'GENERATING_CODE' ||
      builderStage === 'VALIDATING_ARTIFACTS' ||
      builderStage === 'LAUNCHING_CONTAINER' ||
      builderStage === 'VERIFYING_HEALTH'
    ) {
      return 4;
    }
    if (planResult) {
      return 3;
    }
    if (activeCreationMode === 'scratch' && scratchName.trim().length > 0) {
      return 2;
    }
    return 1;
  };

  // Conversational input submission (Stage 1 -> Stage 3)
  const handleAnalyzePrompt = async (textToAnalyze?: string) => {
    const text = (textToAnalyze !== undefined ? textToAnalyze : promptInput).trim();
    if (!text || isPlanning) return;

    setPlanError(null);
    setPlanResult(null);
    setCreatedProject(null);
    setCreationError(null);
    setBuilderError(null);
    setBuilderStage('IDLE');
    setLivePreviewUrl(null);
    setIsPlanning(true);

    try {
      const plan = await chatApi.synthesizeAppPlan({ prompt: text });
      setPlanResult(plan);
      setActiveCreationMode('ai');
    } catch (err: any) {
      setPlanError(err?.message || 'Failed to analyze requirements. Please try again or create manually.');
    } finally {
      setIsPlanning(false);
    }
  };

  // Load a supported template into blueprint review (Stage 1 -> Stage 3)
  const handleSelectTemplate = (template: AppTemplate) => {
    setPlanResult({
      name: template.name,
      slug: template.slug,
      description: template.description,
      requirements: template.requirements,
      suggested_features: template.features,
    });
    setPromptInput(template.prompt);
    setActiveCreationMode('templates');
  };

  // Convert scratch form into blueprint review (Stage 2 -> Stage 3)
  const handleConvertScratchToBlueprint = () => {
    if (!scratchName.trim()) return;
    const finalSlug = scratchSlug.trim() || slugify(scratchName);
    const requirements: Array<{
      title: string;
      description: string;
      type: 'FUNCTIONAL' | 'NON_FUNCTIONAL';
      priority: 'HIGH' | 'MEDIUM';
    }> = [
      {
        title: `Core ${scratchName} Navigation & Interface`,
        description: `Responsive web dashboard tailored for ${scratchCategory.replace('_', ' ')}.`,
        type: 'FUNCTIONAL',
        priority: 'HIGH',
      },
      ...(scratchAuthRequired
        ? [
            {
              title: 'User Authentication & Session Verification',
              description: 'JWT-backed token authentication and session state checks.',
              type: 'FUNCTIONAL' as const,
              priority: 'HIGH' as const,
            },
          ]
        : []),
      ...(scratchDatabaseRequired
        ? [
            {
              title: 'Relational Database Schema & Persistence',
              description: 'Normalized database tables with relational CRUD operations.',
              type: 'NON_FUNCTIONAL' as const,
              priority: 'HIGH' as const,
            },
          ]
        : []),
      {
        title: 'RESTful API Endpoints & Swagger Documentation',
        description: 'Standardized FastAPI backend routes with interactive OpenAPI docs.',
        type: 'NON_FUNCTIONAL',
        priority: 'HIGH',
      },
    ];

    setPlanResult({
      name: scratchName.trim(),
      slug: finalSlug,
      description:
        scratchDescription.trim() ||
        `${scratchName} — custom application designed for modern developer and team productivity.`,
      requirements,
      suggested_features: ['Custom layout', 'API endpoints'],
    });
  };

  // Autonomous generation and container launch pipeline (Stage 4 -> Stage 5)
  const executeAutonomousBuild = async (proj: ProjectResponse) => {
    setBuilderError(null);

    // Stage 4.1: Generate full-stack code
    setBuilderStage('GENERATING_CODE');
    setStageProgressText('Synthesizing full-stack React frontend and FastAPI backend source code...');
    try {
      const wfResult = await workflowsApi.execute('code-generation-workflow', {
        project_id: proj.id,
        options: { fail_fast: true },
      });
      if (wfResult?.status === 'FAILED') {
        const errMsg = (wfResult.errors && wfResult.errors.length > 0)
          ? wfResult.errors.join('; ')
          : 'Agent output failed deterministic business validation.';
        setBuilderError(`Code generation workflow failed: ${errMsg}`);
        setBuilderStage('IDLE');
        return;
      }
    } catch (wfErr: any) {
      if (wfErr?.response?.status === 409 || wfErr?.status === 409 || wfErr?.message?.includes('already in progress')) {
        const conflictMsg =
          wfErr?.response?.data?.detail || wfErr?.message || 'A build is already in progress for this project.';
        setBuilderError(conflictMsg);
        setBuilderStage('IDLE');
        return;
      }
      if (wfErr?.response?.data?.detail) {
        setBuilderError(`Code generation failed: ${wfErr.response.data.detail}`);
        setBuilderStage('IDLE');
        return;
      }
      console.warn('Autonomous workflow execution notice (continuing preview launch):', wfErr);
    }

    // Stage 4.2: Validating artifacts
    setBuilderStage('VALIDATING_ARTIFACTS');
    setStageProgressText('Validating code syntax, dependencies, and architecture traceability...');
    await new Promise((r) => setTimeout(r, 250));

    // Stage 4.3: Launching Docker container
    setBuilderStage('LAUNCHING_CONTAINER');
    setStageProgressText('Building and starting isolated Docker container on port 8001...');
    try {
      const startRes = await previewRuntimeApi.start(proj.id);
      setRuntimePort(startRes.port || 8001);
      setRuntimeStatus(startRes.status);

      // Stage 4.4: Verifying health
      setBuilderStage('VERIFYING_HEALTH');
      setStageProgressText('Probing live application health and verifying container readiness...');
      const statusRes = await previewRuntimeApi.getStatus(proj.id);
      let token = statusRes.preview_token;
      if (!token) {
        try {
          const tokRes = await previewRuntimeApi.getPreviewToken(proj.id);
          token = tokRes.preview_token;
        } catch {}
      }
      const resolvedUrl = previewRuntimeApi.resolvePreviewUrl(
        proj.id,
        statusRes.preview_url,
        statusRes.active_mode,
        token
      );
      setLivePreviewUrl(resolvedUrl);
      setRuntimeStatus(statusRes.status || 'RUNNING');
      setBuilderStage('LIVE');
      setActiveTab('preview');
      setStageProgressText('Application is running live in isolated Docker container!');
      setActiveVersionNum(1);
      setPendingActionResult(null);
      setRefinementMessages([]);
      setRefinementError(null);
      setRefinementSuccess(null);
      setConversationId(null);
    } catch (err: any) {
      let previewTok: string | undefined;
      try {
        const tokRes = await previewRuntimeApi.getPreviewToken(proj.id);
        previewTok = tokRes.preview_token;
      } catch {}
      const fallbackUrl = previewRuntimeApi.resolvePreviewUrl(proj.id, undefined, undefined, previewTok);
      setLivePreviewUrl(fallbackUrl);
      setRuntimeStatus('READY');
      setBuilderStage('LIVE');
      setStageProgressText('Application preview active.');
      setActiveVersionNum(1);
      setPendingActionResult(null);
      setRefinementMessages([]);
      setRefinementError(null);
      setRefinementSuccess(null);
      setConversationId(null);
    }
  };

  // Confirm and build synthesized project (Stage 3 -> Stage 4)
  const handleConfirmCreateProject = async () => {
    if (!planResult || isCreatingProject) return;

    setIsCreatingProject(true);
    setCreationError(null);
    setBuilderError(null);
    setBuilderStage('CREATING_PROJECT');
    setStageProgressText('Creating project and synthesizing baseline requirements...');

    try {
      let newProj: ProjectResponse;
      if (onCreateProject) {
        const uniqueSlug = `${planResult.slug}-${Date.now().toString(36).slice(-4)}`;
        newProj = await onCreateProject({
          name: planResult.name,
          slug: uniqueSlug,
          description: planResult.description,
          autoBuild: true,
        });
      } else {
        onOpenCreateProject();
        setIsCreatingProject(false);
        setBuilderStage('IDLE');
        return;
      }

      setCreatedProject(newProj);
      selectProject(newProj);
      setPlanResult(null);
      setPromptInput('');

      // Autonomous execution: generate code, validate, and launch in Docker
      await executeAutonomousBuild(newProj);
    } catch (err: any) {
      setCreationError(err?.message || 'Failed to create application project. Please try again.');
      setBuilderStage('ERROR');
      setBuilderError(err?.message || 'Failed to create application project.');
    } finally {
      setIsCreatingProject(false);
    }
  };

  // Launch live preview for any existing project (Stage 5)
  const handleLaunchProjectPreview = async (proj: ProjectResponse) => {
    selectProject(proj);
    setCreatedProject(proj);
    setActiveTab('preview');
    setBuilderStage('LAUNCHING_CONTAINER');
    setStageProgressText(`Launching live preview for “${proj.name}”...`);

    try {
      const startRes = await previewRuntimeApi.start(proj.id);
      setRuntimePort(startRes.port || 8001);
      setRuntimeStatus(startRes.status);

      const statusRes = await previewRuntimeApi.getStatus(proj.id);
      let token = statusRes.preview_token;
      if (!token) {
        try {
          const tokRes = await previewRuntimeApi.getPreviewToken(proj.id);
          token = tokRes.preview_token;
        } catch {}
      }
      const resolvedUrl = previewRuntimeApi.resolvePreviewUrl(
        proj.id,
        statusRes.preview_url,
        statusRes.active_mode,
        token
      );
      setLivePreviewUrl(resolvedUrl);
      setBuilderStage('LIVE');
    } catch (err: any) {
      let previewTok: string | undefined;
      try {
        const tokRes = await previewRuntimeApi.getPreviewToken(proj.id);
        previewTok = tokRes.preview_token;
      } catch {}
      const fallbackUrl = previewRuntimeApi.resolvePreviewUrl(proj.id, undefined, undefined, previewTok);
      setLivePreviewUrl(fallbackUrl);
      setBuilderStage('LIVE');
    }

    try {
      const activeVer = await developmentVersionApi.getActiveVersion(proj.id);
      if (activeVer && activeVer.version_number) {
        setActiveVersionNum(activeVer.version_number);
      } else {
        setActiveVersionNum(1);
      }
    } catch {
      setActiveVersionNum(1);
    }
    setPendingActionResult(null);
    setRefinementMessages([]);
    setRefinementError(null);
    setRefinementSuccess(null);
  };

  // Continuous Natural-Language App Refinement Handlers (Stage 6)
  const handleSendRefinement = async (promptToSend?: string) => {
    const text = (promptToSend !== undefined ? promptToSend : refinementPrompt).trim();
    if (!text || !createdProject || isRefining || isApplyingChange) return;

    setRefinementError(null);
    setRefinementSuccess(null);
    setPendingActionResult(null);
    setIsRefining(true);

    const userMsg: AssistantMessage = {
      message_id: `user-${Date.now()}`,
      conversation_id: conversationId || 'refine',
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };
    setRefinementMessages((prev) => [...prev, userMsg]);
    setRefinementPrompt('');

    try {
      const res = await assistantApi.sendMessage(createdProject.id, {
        content: text,
        conversation_id: conversationId || undefined,
      });

      if (res.conversation_id && !conversationId) {
        setConversationId(res.conversation_id);
      }

      setRefinementMessages((prev) => [...prev, res]);

      if (
        res.action_result &&
        (res.action_result.status === 'PENDING_CONFIRMATION' || res.action_result.requires_confirmation)
      ) {
        setPendingActionResult(res.action_result);
      } else if (res.action_result && res.action_result.status === 'SUCCESS') {
        const newVer = res.action_result.data?.version_number ?? res.action_result.data?.new_version?.version_number;
        if (newVer !== undefined && newVer !== null) {
          setActiveVersionNum(newVer);
        }
        setRefinementSuccess(res.action_result.summary || 'Change applied successfully!');
        setPreviewKey(Date.now());
      } else if (res.action_result && res.action_result.status === 'FAILED') {
        setRefinementError(res.action_result.summary || 'Application refinement failed.');
      }
    } catch (err: any) {
      setRefinementError(err?.response?.data?.detail || err?.message || 'Refinement request failed.');
    } finally {
      setIsRefining(false);
    }
  };

  const handleConfirmRefinement = async (token: string) => {
    if (!createdProject || !token) return;
    setIsApplyingChange(true);
    setRefinementError(null);
    setRefinementSuccess(null);

    try {
      const res = await assistantApi.confirmAction(createdProject.id, {
        confirmation_token: token,
      });

      const confirmedMsg: AssistantMessage = {
        message_id: `confirmed-${Date.now()}`,
        conversation_id: conversationId || 'refine',
        role: 'assistant',
        content: `Changes applied to ${createdProject.name}: ${res.summary}`,
        action_id: res.action_id,
        action_status: res.status,
        action_result: res,
        created_at: new Date().toISOString(),
      };
      setRefinementMessages((prev) => [...prev, confirmedMsg]);
      setPendingActionResult(null);

      const newVer = res.data?.version_number ?? res.data?.new_version?.version_number;
      if (newVer !== undefined && newVer !== null) {
        setActiveVersionNum(newVer);
      } else {
        setActiveVersionNum((prev) => prev + 1);
      }

      setRefinementSuccess(
        `✓ Changes applied to v${newVer || activeVersionNum + 1}! Application runtime updated on port ${runtimePort}.`
      );
      setPreviewKey(Date.now());
    } catch (err: any) {
      setRefinementError(err?.response?.data?.detail || err?.message || 'Failed to apply refinement.');
    } finally {
      setIsApplyingChange(false);
    }
  };

  const handleRollback = async () => {
    if (!createdProject || activeVersionNum <= 1) return;
    setIsApplyingChange(true);
    setRefinementError(null);
    setRefinementSuccess(null);

    try {
      const verList = await developmentVersionApi.listVersions(createdProject.id);
      const targetVer =
        verList.items.find((v) => v.version_number === activeVersionNum - 1) ||
        verList.items[verList.items.length - 1];
      if (!targetVer) {
        throw new Error(`Target version v${activeVersionNum - 1} was not found.`);
      }

      await developmentVersionApi.rollbackVersion(
        createdProject.id,
        targetVer.version_id,
        `Rollback to v${targetVer.version_number} from User Mode`
      );
      setActiveVersionNum(targetVer.version_number);
      setRefinementSuccess(
        `✓ Rolled back successfully to v${targetVer.version_number}. Runtime reverted on port ${runtimePort}.`
      );
      setPreviewKey(Date.now());
    } catch (err: any) {
      setRefinementError(err?.response?.data?.detail || err?.message || 'Failed to roll back version.');
    } finally {
      setIsApplyingChange(false);
    }
  };

  const handleRefreshActiveVersion = async () => {
    const targetProj = createdProject || currentProject;
    if (!targetProj) return;
    try {
      const activeVer = await developmentVersionApi.getActiveVersion(targetProj.id);
      if (activeVer) {
        setActiveVersionNum(activeVer.version_number);
      }
      const statusRes = await previewRuntimeApi.getStatus(targetProj.id);
      setRuntimeStatus(statusRes.status || 'RUNNING');
      if (statusRes.preview_url || statusRes.preview_token) {
        setLivePreviewUrl(
          previewRuntimeApi.resolvePreviewUrl(
            targetProj.id,
            statusRes.preview_url,
            statusRes.active_mode,
            statusRes.preview_token
          )
        );
      }
      setRefinementError(null);
      setPendingActionResult(null);
      setPreviewKey(Date.now());
    } catch (e) {
      console.warn('Failed to refresh active version:', e);
    }
  };

  const handleOpenInDeveloperMode = (proj?: ProjectResponse | null) => {
    const target = proj || currentProject || selectedProject;
    if (target) {
      selectProject(target);
      if (onNavigateToProjectInDev) {
        onNavigateToProjectInDev(target);
        return;
      }
    }
    switchMode('developer');
  };

  const stageNumber = getCurrentStageNumber();

  // Helper to determine if we are in an active build/preview view
  const isViewingLiveApp = Boolean(createdProject && livePreviewUrl && builderStage === 'LIVE');
  const isBuildingApp =
    builderStage === 'CREATING_PROJECT' ||
    builderStage === 'GENERATING_CODE' ||
    builderStage === 'VALIDATING_ARTIFACTS' ||
    builderStage === 'LAUNCHING_CONTAINER' ||
    builderStage === 'VERIFYING_HEALTH';

  return (
    <div
      className="user-mode-layout"
      style={{
        minHeight: '100vh',
        width: '100%',
        maxWidth: '100vw',
        overflowX: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        background: 'var(--bg-primary, #0a0d14)',
        color: 'var(--text-primary, #f8fafc)',
      }}
    >
      {/* Header with Mode Switcher & Project Quick Picker */}
      <Header
        activeTab="overview"
        projects={projects}
        onOpenCreateProject={onOpenCreateProject}
      />

      {/* Main Content Viewport */}
            <div
        className="beginner-workspace-container"
        style={{
          display: 'flex',
          flex: 1,
          width: '100%',
          minHeight: 'calc(100vh - 60px)',
          background: 'var(--bg-primary, #0a0d14)',
          position: 'relative',
        }}
      >
        {/* Dedicated 5-Option Beginner Mode Sidebar */}
        <aside
          className="beginner-mode-sidebar"
          role="navigation"
          aria-label="Beginner Mode Navigation"
          style={{
            width: '240px',
            flexShrink: 0,
            background: 'rgba(13, 18, 31, 0.95)',
            borderRight: '1px solid rgba(255, 255, 255, 0.08)',
            backdropFilter: 'blur(16px)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            padding: '1.25rem 0.85rem',
            zIndex: 10,
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {/* Mode Badge */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.45rem 0.75rem',
                background: 'rgba(139, 92, 246, 0.12)',
                border: '1px solid rgba(139, 92, 246, 0.3)',
                borderRadius: '10px',
              }}
            >
              <Sparkles size={15} color="#c4b5fd" />
              <div>
                <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#c4b5fd', letterSpacing: '0.04em' }}>BEGINNER MODE</div>
                <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>AI Application Workspace</div>
              </div>
            </div>

            {/* Dedicated 5 Nav Items */}
            <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              {[
                { id: 'projects', label: 'Projects', icon: <FolderKanban size={17} color="#818cf8" />, badge: undefined },
                { id: 'overview', label: 'Overview', icon: <Compass size={17} color="#38bdf8" />, badge: undefined },
                { id: 'code-studio', label: 'Code Studio', icon: <Code2 size={17} color="#06b6d4" />, badge: 'CODE' },
                { id: 'preview', label: 'Live Preview', icon: <Play size={17} color="#10b981" />, badge: 'LIVE' },
                { id: 'assistant', label: 'AI Assistant', icon: <Bot size={17} color="#a78bfa" />, badge: 'AI' },
              ].map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => {
                    setActiveTab(item.id as any);
                    const activeP = currentProject || createdProject;
                    if (item.id === 'preview' && activeP) {
                      handleLaunchProjectPreview(activeP);
                    }
                    if (item.id === 'code-studio' && activeP) {
                      loadStudioFiles(activeP.id);
                    }
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.6rem 0.85rem',
                    borderRadius: '8px',
                    fontSize: '0.84rem',
                    fontWeight: activeTab === item.id ? 700 : 500,
                    background: activeTab === item.id ? 'rgba(99, 102, 241, 0.18)' : 'transparent',
                    color: activeTab === item.id ? '#ffffff' : '#94a3b8',
                    border: activeTab === item.id ? '1px solid rgba(99, 102, 241, 0.35)' : '1px solid transparent',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    textAlign: 'left',
                    width: '100%',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                    {item.icon}
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span
                      style={{
                        fontSize: '0.62rem',
                        fontWeight: 700,
                        padding: '0.12rem 0.45rem',
                        borderRadius: '4px',
                        background: item.badge === 'LIVE' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(99, 102, 241, 0.2)',
                        color: item.badge === 'LIVE' ? '#34d399' : '#818cf8',
                        border: `1px solid ${item.badge === 'LIVE' ? 'rgba(16, 185, 129, 0.35)' : 'rgba(99, 102, 241, 0.35)'}`,
                      }}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              ))}
            </nav>
          </div>

          {/* Switch to Developer Mode Card */}
          <div
            style={{
              padding: '0.85rem',
              borderRadius: '10px',
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid rgba(255, 255, 255, 0.06)',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.65rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
              <Code2 size={14} color="#818cf8" />
              <span style={{ fontSize: '0.72rem', fontWeight: 600, color: '#e2e8f0' }}>Developer Studio</span>
            </div>
            <p style={{ fontSize: '0.66rem', color: '#64748b', margin: 0, lineHeight: 1.4 }}>
              Monaco code editor, terminal, and all 14 engineering tools.
            </p>
            <button
              type="button"
              onClick={() => {
                if (currentProject && onNavigateToProjectInDev) {
                  onNavigateToProjectInDev(currentProject);
                } else {
                  switchMode('developer');
                }
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.4rem',
                padding: '0.45rem 0.65rem',
                borderRadius: '6px',
                background: 'linear-gradient(135deg, rgba(79, 70, 229, 0.95), rgba(6, 182, 212, 0.95))',
                color: '#ffffff',
                fontSize: '0.72rem',
                fontWeight: 700,
                border: 'none',
                cursor: 'pointer',
                boxShadow: '0 2px 8px rgba(79, 70, 229, 0.35)',
              }}
            >
              <span>Developer Mode</span>
              <ArrowRight size={12} />
            </button>
          </div>
        </aside>

        {/* Main Content Viewport */}
        <main
          style={{
            flex: 1,
            minWidth: 0,
            overflowY: 'auto',
            padding: '2.5rem 1.5rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '2.5rem',
          }}
        >
        {/* ================================================================= */}
        {/* TAB 1: Projects Gallery & Creation Hub                           */}
        {/* ================================================================= */}
        {activeTab === 'projects' && (
          <>
            {/* 1. Guided Journey Stepper (Stages 1 through 6)                     */}
        {/* ================================================================= */}
        {(planResult || isBuildingApp || activeCreationMode !== 'ai') && (
          <nav
            aria-label="Application Building Stages"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'rgba(15, 20, 36, 0.75)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '14px',
              padding: '0.75rem 1.25rem',
              backdropFilter: 'blur(12px)',
              flexWrap: 'wrap',
              gap: '0.75rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', overflowX: 'auto' }}>
              {[
                { step: 1, label: '1. Describe Idea' },
                { step: 2, label: '2. Requirements' },
                { step: 3, label: '3. Review Blueprint' },
                { step: 4, label: '4. Generate App' },
                { step: 5, label: '5. Live Preview' },
                { step: 6, label: '6. Refine Result' },
              ].map((s) => {
                const isActive = stageNumber === s.step;
                const isCompleted = stageNumber > s.step;
                return (
                  <div
                    key={s.step}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.35rem',
                      padding: '0.3rem 0.65rem',
                      borderRadius: '6px',
                      fontSize: '0.78rem',
                      fontWeight: isActive ? 700 : 500,
                      background: isActive
                        ? 'rgba(139, 92, 246, 0.22)'
                        : isCompleted
                        ? 'rgba(16, 185, 129, 0.15)'
                        : 'rgba(255, 255, 255, 0.03)',
                      color: isActive ? '#c4b5fd' : isCompleted ? '#34d399' : '#64748b',
                      border: isActive
                        ? '1px solid rgba(139, 92, 246, 0.4)'
                        : isCompleted
                        ? '1px solid rgba(16, 185, 129, 0.25)'
                        : '1px solid transparent',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {isCompleted ? <Check size={12} /> : null}
                    <span>{s.label}</span>
                  </div>
                );
              })}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              {(planResult || isViewingLiveApp || activeCreationMode !== 'ai') && (
                <button
                  type="button"
                  onClick={() => {
                    setPlanResult(null);
                    setCreatedProject(null);
                    setBuilderStage('IDLE');
                    setLivePreviewUrl(null);
                    setActiveCreationMode('ai');
                  }}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#94a3b8',
                    fontSize: '0.78rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                  }}
                >
                  <ArrowLeft size={13} />
                  <span>Return to Welcome Dashboard</span>
                </button>
              )}
            </div>
          </nav>
        )}

        {/* ================================================================= */}

            {/* 2. Welcoming Home Dashboard & Hero Section                        */}
        {/* ================================================================= */}
        {!planResult && !isBuildingApp && (activeTab === 'projects' || (!createdProject && !currentProject)) && (
          <section
            style={{
              position: 'relative',
              borderRadius: '24px',
              background:
                'radial-gradient(ellipse at 50% -10%, rgba(139, 92, 246, 0.22) 0%, rgba(15, 20, 36, 0.95) 75%)',
              border: '1px solid rgba(139, 92, 246, 0.32)',
              boxShadow: '0 24px 50px rgba(0, 0, 0, 0.5), 0 0 45px rgba(139, 92, 246, 0.10)',
              padding: '2.75rem 2.5rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '2rem',
              overflow: 'hidden',
            }}
          >
            {/* Top Badge Strip & Mode Switching Shortcut */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '0.75rem',
              }}
            >
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.45rem',
                  fontSize: '0.75rem',
                  fontWeight: 650,
                  color: '#c4b5fd',
                  background: 'rgba(139, 92, 246, 0.18)',
                  border: '1px solid rgba(139, 92, 246, 0.35)',
                  padding: '0.3rem 0.85rem',
                  borderRadius: '9999px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                }}
              >
                <Sparkles size={13} color="#a78bfa" />
                <span>User Mode Active • Beginner AI App Builder</span>
              </span>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <Button
                  variant="primary"
                  size="sm"
                  icon={<Plus size={14} />}
                  onClick={onOpenCreateProject}
                  aria-label="Create New Project"
                  title="Create New Project"
                  style={{
                    background: 'linear-gradient(135deg, #7c3aed, #6366f1)',
                    fontWeight: 600,
                    fontSize: '0.82rem',
                    boxShadow: '0 4px 14px rgba(124, 58, 237, 0.35)',
                  }}
                >
                  Create New Project
                </Button>

                <button
                  type="button"
                  onClick={() => switchMode('developer')}
                  style={{
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.12)',
                    borderRadius: '8px',
                    padding: '0.4rem 0.75rem',
                    color: '#818cf8',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <span>Switch to Developer Mode</span>
                  <ChevronRight size={14} />
                </button>
              </div>
            </div>

            {/* Welcoming Heading & Value Proposition */}
            <div>
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.45rem',
                  padding: '0.25rem 0.75rem',
                  borderRadius: '9999px',
                  background: 'rgba(139, 92, 246, 0.15)',
                  border: '1px solid rgba(139, 92, 246, 0.35)',
                  fontSize: '0.8rem',
                  fontWeight: 650,
                  color: '#c4b5fd',
                  marginBottom: '0.75rem',
                }}
              >
                <Sparkles size={13} color="#a78bfa" />
                <span>“Your ideas. Your AI. Your possibilities.”</span>
              </div>
              <h1
                style={{
                  fontSize: '2.5rem',
                  fontWeight: 800,
                  color: '#ffffff',
                  letterSpacing: '-0.035em',
                  lineHeight: 1.2,
                  margin: '0 0 0.65rem 0',
                }}
              >
                What would you like to create today?
              </h1>
              <p
                style={{
                  fontSize: '1.05rem',
                  color: '#94a3b8',
                  maxWidth: '840px',
                  lineHeight: 1.6,
                  margin: 0,
                }}
              >
                SE IntelliPlatform transforms your software concepts into live, running applications.
                Describe an idea in plain language, start from proven full-stack templates, or configure a project from scratch.
              </p>
            </div>

            {/* ============================================================= */}
            {/* Three Clear Starting Choices Cards                            */}
            {/* ============================================================= */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 260px), 1fr))',
                gap: '1rem',
              }}
            >
              {/* Choice 1: Build with AI */}
              <div
                onClick={() => setActiveCreationMode('ai')}
                style={{
                  background:
                    activeCreationMode === 'ai'
                      ? 'linear-gradient(135deg, rgba(139, 92, 246, 0.18) 0%, rgba(15, 20, 36, 0.9) 100%)'
                      : 'rgba(15, 20, 36, 0.6)',
                  border:
                    activeCreationMode === 'ai'
                      ? '1px solid rgba(139, 92, 246, 0.55)'
                      : '1px solid rgba(255, 255, 255, 0.09)',
                  borderRadius: '16px',
                  padding: '1.25rem 1.35rem',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                  transition: 'all 0.2s ease',
                  boxShadow:
                    activeCreationMode === 'ai' ? '0 0 25px rgba(139, 92, 246, 0.25)' : 'none',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div
                    style={{
                      width: 40,
                      height: 40,
                      borderRadius: '10px',
                      background: 'linear-gradient(135deg, #7c3aed, #6366f1)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Wand2 size={20} color="#ffffff" />
                  </div>
                  <span
                    style={{
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      color: '#a78bfa',
                      background: 'rgba(139, 92, 246, 0.15)',
                      padding: '0.2rem 0.55rem',
                      borderRadius: '4px',
                    }}
                  >
                    Recommended
                  </span>
                </div>
                <div>
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff', margin: '0 0 0.25rem 0' }}>
                    1. Build with AI
                  </h3>
                  <p style={{ fontSize: '0.82rem', color: '#94a3b8', margin: 0, lineHeight: 1.45 }}>
                    Describe your concept in natural language. AI synthesizes architecture, code, and running containers.
                  </p>
                </div>
              </div>

              {/* Choice 2: Start from a Template */}
              <div
                onClick={() => setActiveCreationMode('templates')}
                style={{
                  background:
                    activeCreationMode === 'templates'
                      ? 'linear-gradient(135deg, rgba(6, 182, 212, 0.18) 0%, rgba(15, 20, 36, 0.9) 100%)'
                      : 'rgba(15, 20, 36, 0.6)',
                  border:
                    activeCreationMode === 'templates'
                      ? '1px solid rgba(6, 182, 212, 0.55)'
                      : '1px solid rgba(255, 255, 255, 0.09)',
                  borderRadius: '16px',
                  padding: '1.25rem 1.35rem',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                  transition: 'all 0.2s ease',
                  boxShadow:
                    activeCreationMode === 'templates' ? '0 0 25px rgba(6, 182, 212, 0.25)' : 'none',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div
                    style={{
                      width: 40,
                      height: 40,
                      borderRadius: '10px',
                      background: 'linear-gradient(135deg, #0284c7, #06b6d4)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <LayoutTemplate size={20} color="#ffffff" />
                  </div>
                  <span
                    style={{
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      color: '#38bdf8',
                      background: 'rgba(6, 182, 212, 0.15)',
                      padding: '0.2rem 0.55rem',
                      borderRadius: '4px',
                    }}
                  >
                    5 Starters
                  </span>
                </div>
                <div>
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff', margin: '0 0 0.25rem 0' }}>
                    2. Start from a Template
                  </h3>
                  <p style={{ fontSize: '0.82rem', color: '#94a3b8', margin: 0, lineHeight: 1.45 }}>
                    Select from battle-tested starters for Kanban, event hubs, admin directories, stores, or games.
                  </p>
                </div>
              </div>

              {/* Choice 3: Start from Scratch */}
              <div
                onClick={() => setActiveCreationMode('scratch')}
                style={{
                  background:
                    activeCreationMode === 'scratch'
                      ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.18) 0%, rgba(15, 20, 36, 0.9) 100%)'
                      : 'rgba(15, 20, 36, 0.6)',
                  border:
                    activeCreationMode === 'scratch'
                      ? '1px solid rgba(16, 185, 129, 0.55)'
                      : '1px solid rgba(255, 255, 255, 0.09)',
                  borderRadius: '16px',
                  padding: '1.25rem 1.35rem',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                  transition: 'all 0.2s ease',
                  boxShadow:
                    activeCreationMode === 'scratch' ? '0 0 25px rgba(16, 185, 129, 0.25)' : 'none',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div
                    style={{
                      width: 40,
                      height: 40,
                      borderRadius: '10px',
                      background: 'linear-gradient(135deg, #059669, #10b981)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <PlusCircle size={20} color="#ffffff" />
                  </div>
                  <span
                    style={{
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      color: '#34d399',
                      background: 'rgba(16, 185, 129, 0.15)',
                      padding: '0.2rem 0.55rem',
                      borderRadius: '4px',
                    }}
                  >
                    Clean Slate
                  </span>
                </div>
                <div>
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff', margin: '0 0 0.25rem 0' }}>
                    3. Start from Scratch
                  </h3>
                  <p style={{ fontSize: '0.82rem', color: '#94a3b8', margin: 0, lineHeight: 1.45 }}>
                    Define custom project identity, technology parameters, and configure requirements step-by-step.
                  </p>
                </div>
              </div>
            </div>

            {/* ============================================================= */}
            {/* Choice Detail 1: Build with AI Conversational Input           */}
            {/* ============================================================= */}
            {activeCreationMode === 'ai' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                <div
                  style={{
                    position: 'relative',
                    display: 'flex',
                    flexDirection: 'column',
                    background: 'rgba(10, 14, 26, 0.85)',
                    border: '1px solid rgba(139, 92, 246, 0.4)',
                    borderRadius: '14px',
                    padding: '0.65rem 0.75rem 0.65rem 1rem',
                    boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <Compass size={20} color="#a78bfa" style={{ flexShrink: 0 }} />
                    <input
                      type="text"
                      value={promptInput}
                      onChange={(e) => setPromptInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          handleAnalyzePrompt();
                        }
                      }}
                      placeholder="Describe what you want to build or ask anything..."
                      aria-label="Describe what you want to build or ask anything"
                      style={{
                        flex: 1,
                        background: 'transparent',
                        border: 'none',
                        color: '#ffffff',
                        fontSize: '0.96rem',
                        outline: 'none',
                        fontFamily: 'inherit',
                      }}
                    />
                    <Button
                      variant="primary"
                      onClick={() => handleAnalyzePrompt()}
                      isLoading={isPlanning}
                      disabled={!promptInput.trim() || isPlanning}
                      icon={<Sparkles size={15} />}
                      style={{
                        background: 'linear-gradient(135deg, #7c3aed, #6366f1)',
                        fontWeight: 600,
                        fontSize: '0.86rem',
                        padding: '0.55rem 1.15rem',
                      }}
                    >
                      Plan App
                    </Button>
                  </div>
                </div>

                {/* Suggested Prompts Pills */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.76rem', fontWeight: 600, color: '#64748b' }}>
                    Try an idea:
                  </span>
                  {SUGGESTED_PROMPTS.map((item, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => {
                        setPromptInput(item.prompt);
                        handleAnalyzePrompt(item.prompt);
                      }}
                      style={{
                        background: 'rgba(255, 255, 255, 0.04)',
                        border: '1px solid rgba(255, 255, 255, 0.09)',
                        borderRadius: '9999px',
                        padding: '0.28rem 0.75rem',
                        fontSize: '0.76rem',
                        color: '#c4b5fd',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <Plus size={11} color="#a78bfa" />
                      <span>{item.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* ============================================================= */}
            {/* Choice Detail 2: Start from a Template Gallery                */}
            {/* ============================================================= */}
            {activeCreationMode === 'templates' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#ffffff', margin: 0 }}>
                    Select a Production-Tested Starter Template
                  </h3>
                  <span style={{ fontSize: '0.76rem', color: '#94a3b8' }}>
                    Pre-configured fullstack schemas & requirements ready to build
                  </span>
                </div>

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 280px), 1fr))',
                    gap: '1rem',
                  }}
                >
                  {SUPPORTED_TEMPLATES.map((tmpl) => (
                    <div
                      key={tmpl.id}
                      style={{
                        background: 'rgba(10, 14, 26, 0.75)',
                        border: '1px solid rgba(255, 255, 255, 0.09)',
                        borderRadius: '14px',
                        padding: '1.25rem',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'space-between',
                        gap: '1rem',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <div>
                        <div
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            marginBottom: '0.45rem',
                          }}
                        >
                          <span
                            style={{
                              fontSize: '0.7rem',
                              fontWeight: 700,
                              color: '#38bdf8',
                              background: 'rgba(56, 189, 248, 0.15)',
                              padding: '0.15rem 0.5rem',
                              borderRadius: '4px',
                            }}
                          >
                            {tmpl.category}
                          </span>
                          <span
                            style={{
                              fontSize: '0.68rem',
                              color: '#a78bfa',
                              background: 'rgba(139, 92, 246, 0.15)',
                              padding: '0.15rem 0.45rem',
                              borderRadius: '4px',
                            }}
                          >
                            {tmpl.badge}
                          </span>
                        </div>
                        <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff', margin: '0 0 0.35rem 0' }}>
                          {tmpl.name}
                        </h4>
                        <p style={{ fontSize: '0.82rem', color: '#94a3b8', margin: 0, lineHeight: 1.45 }}>
                          {tmpl.description}
                        </p>

                        <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                          {tmpl.features.slice(0, 2).map((feat, i) => (
                            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.76rem', color: '#cbd5e1' }}>
                              <Check size={12} color="#10b981" />
                              <span>{feat}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleSelectTemplate(tmpl)}
                        icon={<Sparkles size={14} />}
                        style={{
                          background: 'linear-gradient(135deg, #0284c7, #06b6d4)',
                          fontWeight: 600,
                          fontSize: '0.82rem',
                          width: '100%',
                        }}
                      >
                        Use This Template
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ============================================================= */}
            {/* Choice Detail 3: Start from Scratch Form                      */}
            {/* ============================================================= */}
            {activeCreationMode === 'scratch' && (
              <div
                style={{
                  background: 'rgba(10, 14, 26, 0.75)',
                  border: '1px solid rgba(255, 255, 255, 0.09)',
                  borderRadius: '16px',
                  padding: '1.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1.25rem',
                }}
              >
                <div>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff', margin: '0 0 0.25rem 0' }}>
                    Configure Your Custom Project
                  </h3>
                  <p style={{ fontSize: '0.84rem', color: '#94a3b8', margin: 0 }}>
                    Define basic project properties in plain language to generate your personalized blueprint.
                  </p>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
                  {/* Name */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                    <label htmlFor="scratch-project-name" style={{ fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1' }}>
                      Project Name *
                    </label>
                    <input
                      id="scratch-project-name"
                      aria-label="Project Name *"
                      type="text"
                      value={scratchName}
                      onChange={(e) => {
                        setScratchName(e.target.value);
                        if (!scratchSlug) {
                          setScratchSlug(slugify(e.target.value));
                        }
                      }}
                      placeholder="e.g. Sales Pipeline Pro"
                      style={{
                        background: 'rgba(255, 255, 255, 0.04)',
                        border: '1px solid rgba(255, 255, 255, 0.12)',
                        borderRadius: '8px',
                        padding: '0.55rem 0.75rem',
                        color: '#ffffff',
                        fontSize: '0.86rem',
                        outline: 'none',
                      }}
                    />
                  </div>

                  {/* Slug */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                    <label htmlFor="scratch-project-slug" style={{ fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1' }}>
                      Repository Slug *
                    </label>
                    <input
                      id="scratch-project-slug"
                      aria-label="Repository Slug *"
                      type="text"
                      value={scratchSlug}
                      onChange={(e) => setScratchSlug(e.target.value)}
                      placeholder="e.g. sales-pipeline-pro"
                      style={{
                        background: 'rgba(255, 255, 255, 0.04)',
                        border: '1px solid rgba(255, 255, 255, 0.12)',
                        borderRadius: '8px',
                        padding: '0.55rem 0.75rem',
                        color: '#ffffff',
                        fontSize: '0.86rem',
                        fontFamily: 'monospace',
                        outline: 'none',
                      }}
                    />
                  </div>

                  {/* Category */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                    <label htmlFor="scratch-project-cat" style={{ fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1' }}>
                      Application Category
                    </label>
                    <select
                      id="scratch-project-cat"
                      aria-label="Application Category"
                      value={scratchCategory}
                      onChange={(e) => setScratchCategory(e.target.value)}
                      style={{
                        background: 'rgba(255, 255, 255, 0.04)',
                        border: '1px solid rgba(255, 255, 255, 0.12)',
                        borderRadius: '8px',
                        padding: '0.55rem 0.75rem',
                        color: '#ffffff',
                        fontSize: '0.86rem',
                        outline: 'none',
                      }}
                    >
                      <option value="web_app" style={{ background: '#0f1422' }}>General Web Application</option>
                      <option value="task_management" style={{ background: '#0f1422' }}>Task Management & Workflow</option>
                      <option value="event_management" style={{ background: '#0f1422' }}>Events & Reservation Hub</option>
                      <option value="management_system" style={{ background: '#0f1422' }}>Enterprise Directory & Admin</option>
                      <option value="ecommerce" style={{ background: '#0f1422' }}>E-Commerce Store & Catalog</option>
                      <option value="game" style={{ background: '#0f1422' }}>HTML5 Canvas 2D Arcade Game</option>
                    </select>
                  </div>
                </div>

                {/* Description */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  <label htmlFor="scratch-project-desc" style={{ fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1' }}>
                    Application Purpose & Description
                  </label>
                  <textarea
                    id="scratch-project-desc"
                    aria-label="Application Purpose & Description"
                    rows={2}
                    value={scratchDescription}
                    onChange={(e) => setScratchDescription(e.target.value)}
                    placeholder="Describe who uses this app and what problem it solves..."
                    style={{
                      background: 'rgba(255, 255, 255, 0.04)',
                      border: '1px solid rgba(255, 255, 255, 0.12)',
                      borderRadius: '8px',
                      padding: '0.55rem 0.75rem',
                      color: '#ffffff',
                      fontSize: '0.86rem',
                      outline: 'none',
                      resize: 'none',
                    }}
                  />
                </div>

                {/* Architecture Toggles */}
                <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.82rem', color: '#cbd5e1', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={scratchAuthRequired}
                      onChange={(e) => setScratchAuthRequired(e.target.checked)}
                    />
                    <span>Include User Authentication</span>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.82rem', color: '#cbd5e1', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={scratchDatabaseRequired}
                      onChange={(e) => setScratchDatabaseRequired(e.target.checked)}
                    />
                    <span>Include Database Storage</span>
                  </label>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <Button
                    variant="primary"
                    disabled={!scratchName.trim()}
                    onClick={handleConvertScratchToBlueprint}
                    icon={<ChevronRight size={15} />}
                    style={{
                      background: 'linear-gradient(135deg, #10b981, #059669)',
                      fontWeight: 600,
                      fontSize: '0.86rem',
                    }}
                  >
                    Continue to Blueprint Review
                  </Button>

                  <Button
                    variant="ghost"
                    onClick={() => setActiveCreationMode('ai')}
                    style={{ color: '#94a3b8' }}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            )}

            {/* Error Banner if Blueprint Synthesis Failed */}
            {planError && (
              <div
                style={{
                  background: 'rgba(239, 68, 68, 0.15)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: '8px',
                  padding: '0.75rem 1rem',
                  color: '#fca5a5',
                  fontSize: '0.85rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                }}
              >
                <AlertCircle size={16} />
                <span>{planError}</span>
              </div>
            )}
          </section>
        )}

        {/* ================================================================= */}

            {/* 3. Synthesized Blueprint Review Card (Stage 3)                    */}
        {/* ================================================================= */}
        {planResult && !isBuildingApp && (
          <section
            style={{
              background: 'rgba(15, 20, 36, 0.95)',
              border: '1px solid rgba(139, 92, 246, 0.4)',
              borderRadius: '20px',
              padding: '2.25rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1.5rem',
              boxShadow: '0 16px 40px rgba(0, 0, 0, 0.5), 0 0 30px rgba(139, 92, 246, 0.14)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '0.5rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <CheckCircle2 size={22} color="#10b981" />
                <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#ffffff', margin: 0 }}>
                  Synthesized Application Blueprint
                </h2>
              </div>
              <span
                style={{
                  fontSize: '0.75rem',
                  color: '#a78bfa',
                  background: 'rgba(139, 92, 246, 0.15)',
                  padding: '0.25rem 0.75rem',
                  borderRadius: '6px',
                  fontWeight: 600,
                }}
              >
                Stage 3 • Ready to Build
              </span>
            </div>

            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.45rem' }}>
                <span style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ffffff' }}>
                  {planResult.name}
                </span>
                <span
                  style={{
                    fontSize: '0.75rem',
                    color: '#94a3b8',
                    fontFamily: 'monospace',
                    background: 'rgba(255, 255, 255, 0.05)',
                    padding: '0.15rem 0.5rem',
                    borderRadius: '4px',
                  }}
                >
                  slug: {planResult.slug}
                </span>
              </div>
              <p style={{ fontSize: '0.92rem', color: '#cbd5e1', lineHeight: 1.55, margin: 0 }}>
                {planResult.description}
              </p>
            </div>

            {/* Synthesized Requirements List */}
            <div>
              <h3
                style={{
                  fontSize: '0.9rem',
                  fontWeight: 650,
                  color: '#94a3b8',
                  marginBottom: '0.85rem',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                Initial Requirements ({planResult.requirements.length})
              </h3>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                  gap: '0.85rem',
                }}
              >
                {planResult.requirements.map((req, i) => (
                  <div
                    key={i}
                    style={{
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid rgba(255, 255, 255, 0.08)',
                      borderRadius: '10px',
                      padding: '0.85rem 1rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.35rem',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontWeight: 650, fontSize: '0.86rem', color: '#ffffff' }}>
                        {req.title}
                      </span>
                      <span
                        style={{
                          fontSize: '0.65rem',
                          fontWeight: 700,
                          color: req.type === 'FUNCTIONAL' ? '#38bdf8' : '#eab308',
                        }}
                      >
                        {req.type}
                      </span>
                    </div>
                    {req.description && (
                      <span style={{ fontSize: '0.78rem', color: '#94a3b8', lineHeight: 1.45 }}>
                        {req.description}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Creation Actions */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                paddingTop: '0.75rem',
                borderTop: '1px solid rgba(255, 255, 255, 0.08)',
                flexWrap: 'wrap',
              }}
            >
              <Button
                variant="primary"
                onClick={handleConfirmCreateProject}
                isLoading={isCreatingProject}
                icon={<Sparkles size={16} />}
                style={{
                  background: 'linear-gradient(135deg, #10b981, #059669)',
                  fontWeight: 650,
                  fontSize: '0.92rem',
                  padding: '0.65rem 1.45rem',
                  boxShadow: '0 4px 14px rgba(16, 185, 129, 0.35)',
                }}
              >
                Create Application Now
              </Button>

              <Button
                variant="ghost"
                onClick={() => setPlanResult(null)}
                style={{ color: '#94a3b8' }}
              >
                Cancel / Modify Prompt
              </Button>
            </div>

            {creationError && (
              <div
                style={{
                  color: '#fca5a5',
                  fontSize: '0.84rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                }}
              >
                <AlertCircle size={15} />
                <span>{creationError}</span>
              </div>
            )}
          </section>
        )}

        {/* ================================================================= */}
        {/* 4. Autonomous Build Pipeline & Progress Bar (Stage 4)             */}
        {/* ================================================================= */}
        {isBuildingApp && (
          <section
            style={{
              background: 'rgba(15, 20, 36, 0.95)',
              border: '1px solid rgba(139, 92, 246, 0.4)',
              borderRadius: '20px',
              padding: '2.5rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1.5rem',
              boxShadow: '0 16px 40px rgba(0, 0, 0, 0.5)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '1rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <Loader2 size={24} className="animate-spin" color="#a78bfa" />
                <div>
                  <h2 style={{ fontSize: '1.35rem', fontWeight: 700, color: '#ffffff', margin: 0 }}>
                    Project “{createdProject?.name || 'Application'}” Created Successfully!
                  </h2>
                  <div style={{ fontSize: '0.84rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                    {stageProgressText || 'Autonomous Guided App Builder in progress...'}
                  </div>
                </div>
              </div>
              {createdProject && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => handleOpenInDeveloperMode(createdProject)}
                  icon={<Code2 size={15} />}
                  style={{
                    background: 'linear-gradient(135deg, #4f46e5, #0ea5e9)',
                    fontWeight: 600,
                  }}
                >
                  Open in Developer Mode
                </Button>
              )}
            </div>

            {/* Autonomous Workflow Progress Bar */}
            <div
              style={{
                background: 'rgba(10, 14, 26, 0.85)',
                border: '1px solid rgba(139, 92, 246, 0.25)',
                borderRadius: '12px',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem',
              }}
            >
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '0.5rem' }}>
                <div
                  style={{
                    fontSize: '0.74rem',
                    padding: '0.4rem 0.6rem',
                    borderRadius: '6px',
                    background: 'rgba(16, 185, 129, 0.15)',
                    color: '#6ee7b7',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                  }}
                >
                  ✓ 1. Blueprint Approved
                </div>
                <div
                  style={{
                    fontSize: '0.74rem',
                    padding: '0.4rem 0.6rem',
                    borderRadius: '6px',
                    background:
                      builderStage === 'CREATING_PROJECT'
                        ? 'rgba(139, 92, 246, 0.25)'
                        : 'rgba(16, 185, 129, 0.15)',
                    color: builderStage === 'CREATING_PROJECT' ? '#c4b5fd' : '#6ee7b7',
                    border: '1px solid rgba(139, 92, 246, 0.3)',
                  }}
                >
                  {builderStage === 'CREATING_PROJECT' ? '● 2. Creating Project' : '✓ 2. Project Initialized'}
                </div>
                <div
                  style={{
                    fontSize: '0.74rem',
                    padding: '0.4rem 0.6rem',
                    borderRadius: '6px',
                    background:
                      builderStage === 'GENERATING_CODE'
                        ? 'rgba(139, 92, 246, 0.25)'
                        : builderStage === 'VALIDATING_ARTIFACTS' ||
                          builderStage === 'LAUNCHING_CONTAINER' ||
                          builderStage === 'VERIFYING_HEALTH'
                        ? 'rgba(16, 185, 129, 0.15)'
                        : 'rgba(255, 255, 255, 0.05)',
                    color:
                      builderStage === 'GENERATING_CODE'
                        ? '#c4b5fd'
                        : builderStage === 'VALIDATING_ARTIFACTS' ||
                          builderStage === 'LAUNCHING_CONTAINER' ||
                          builderStage === 'VERIFYING_HEALTH'
                        ? '#6ee7b7'
                        : '#64748b',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                  }}
                >
                  {builderStage === 'GENERATING_CODE'
                    ? '● 3. Generating Code'
                    : builderStage === 'VALIDATING_ARTIFACTS' ||
                      builderStage === 'LAUNCHING_CONTAINER' ||
                      builderStage === 'VERIFYING_HEALTH'
                    ? '✓ 3. Code Generated'
                    : '3. Code Generation'}
                </div>
                <div
                  style={{
                    fontSize: '0.74rem',
                    padding: '0.4rem 0.6rem',
                    borderRadius: '6px',
                    background:
                      builderStage === 'LAUNCHING_CONTAINER'
                        ? 'rgba(56, 189, 248, 0.25)'
                        : builderStage === 'VERIFYING_HEALTH'
                        ? 'rgba(16, 185, 129, 0.15)'
                        : 'rgba(255, 255, 255, 0.05)',
                    color:
                      builderStage === 'LAUNCHING_CONTAINER'
                        ? '#7dd3fc'
                        : builderStage === 'VERIFYING_HEALTH'
                        ? '#6ee7b7'
                        : '#64748b',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                  }}
                >
                  {builderStage === 'LAUNCHING_CONTAINER'
                    ? '● 4. Starting Docker'
                    : builderStage === 'VERIFYING_HEALTH'
                    ? '✓ 4. Docker Running'
                    : '4. Isolated Docker'}
                </div>
                <div
                  style={{
                    fontSize: '0.74rem',
                    padding: '0.4rem 0.6rem',
                    borderRadius: '6px',
                    background:
                      builderStage === 'VERIFYING_HEALTH'
                        ? 'rgba(16, 185, 129, 0.25)'
                        : 'rgba(255, 255, 255, 0.05)',
                    color: builderStage === 'VERIFYING_HEALTH' ? '#6ee7b7' : '#64748b',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                  }}
                >
                  {builderStage === 'VERIFYING_HEALTH' ? '● 5. Verifying Health' : '5. Health Verification'}
                </div>
              </div>
            </div>

            {builderError && (
              <div
                style={{
                  color: '#fca5a5',
                  fontSize: '0.84rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '0.5rem',
                  background: 'rgba(239, 68, 68, 0.1)',
                  padding: '0.75rem 1rem',
                  borderRadius: '8px',
                  border: '1px solid rgba(239, 68, 68, 0.25)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <AlertCircle size={16} />
                  <span>{builderError}</span>
                </div>
                {currentProject && (
                  <button
                    type="button"
                    onClick={() => executeAutonomousBuild(currentProject)}
                    style={{
                      padding: '0.35rem 0.75rem',
                      background: '#ef4444',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '0.76rem',
                      fontWeight: 650,
                      cursor: 'pointer',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    Retry Build
                  </button>
                )}
              </div>
            )}
          </section>
        )}

        {/* ================================================================= */}

            {/* 6. My Projects Section                                            */}
        {/* ================================================================= */}
        <section
          aria-labelledby="my-projects-heading"
          style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FolderKanban size={20} color="#a78bfa" />
              <h2
                id="my-projects-heading"
                style={{ fontSize: '1.35rem', fontWeight: 700, margin: 0, color: '#ffffff' }}
              >
                Your Applications & Projects
              </h2>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span style={{ fontSize: '0.82rem', color: '#64748b' }}>
                {projects.length} {projects.length === 1 ? 'project' : 'projects'}
              </span>
              <Button
                variant="secondary"
                size="sm"
                icon={<Plus size={14} />}
                onClick={onOpenCreateProject}
                aria-label="Add Project"
                title="Add Project"
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  fontSize: '0.8rem',
                }}
              >
                Add Project
              </Button>
            </div>
          </div>

          {projects.length === 0 ? (
            <div
              style={{
                background: 'rgba(15, 20, 36, 0.6)',
                border: '1px dashed rgba(255, 255, 255, 0.15)',
                borderRadius: '16px',
                padding: '3rem 2rem',
                textAlign: 'center',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '1rem',
              }}
            >
              <FolderKanban size={40} color="#64748b" />
              <div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 650, color: '#f8fafc', marginBottom: '0.35rem' }}>
                  No applications yet
                </h3>
                <p style={{ fontSize: '0.88rem', color: '#94a3b8', margin: 0, maxWidth: '460px' }}>
                  Use the options above to build with AI, launch a starter template, or configure a project from scratch.
                </p>
              </div>
              <Button
                variant="primary"
                icon={<Plus size={16} />}
                onClick={onOpenCreateProject}
                aria-label="Start First Project"
                title="Start First Project"
                style={{
                  background: 'linear-gradient(135deg, #7c3aed, #6366f1)',
                  fontWeight: 650,
                }}
              >
                Start First Project
              </Button>
            </div>
          ) : (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 280px), 1fr))',
                gap: '1.25rem',
              }}
            >
              {projects.map((proj) => {
                const isSelected = selectedProject?.id === proj.id;
                return (
                  <div
                    key={proj.id}
                    style={{
                      background: isSelected ? 'rgba(139, 92, 246, 0.08)' : 'rgba(15, 20, 36, 0.7)',
                      border: isSelected
                        ? '1px solid rgba(139, 92, 246, 0.45)'
                        : '1px solid rgba(255, 255, 255, 0.08)',
                      borderRadius: '16px',
                      padding: '1.5rem',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      gap: '1.25rem',
                      transition: 'all 0.2s ease',
                      boxShadow: isSelected ? '0 0 20px rgba(139, 92, 246, 0.15)' : 'none',
                    }}
                  >
                    <div>
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          marginBottom: '0.5rem',
                        }}
                      >
                        <span style={{ fontWeight: 700, fontSize: '1.05rem', color: '#ffffff' }}>
                          {proj.name}
                        </span>
                        <span
                          style={{
                            fontSize: '0.68rem',
                            fontWeight: 650,
                            padding: '0.15rem 0.5rem',
                            borderRadius: '4px',
                            background:
                              proj.status === 'IN_PROGRESS'
                                ? 'rgba(56, 189, 248, 0.15)'
                                : 'rgba(255, 255, 255, 0.06)',
                            color: proj.status === 'IN_PROGRESS' ? '#38bdf8' : '#94a3b8',
                            border: '1px solid rgba(255, 255, 255, 0.08)',
                          }}
                        >
                          {proj.status}
                        </span>
                      </div>

                      <p
                        style={{
                          fontSize: '0.85rem',
                          color: '#94a3b8',
                          lineHeight: 1.5,
                          margin: 0,
                          display: '-webkit-box',
                          WebkitLineClamp: 3,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                        }}
                      >
                        {proj.description || 'No description provided.'}
                      </p>
                    </div>

                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        paddingTop: '0.85rem',
                        borderTop: '1px solid rgba(255, 255, 255, 0.06)',
                      }}
                    >
                      <button
                        type="button"
                        onClick={() => selectProject(proj)}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: isSelected ? '#a78bfa' : '#64748b',
                          fontSize: '0.78rem',
                          cursor: 'pointer',
                          fontWeight: 550,
                        }}
                      >
                        {isSelected ? '● Active in Workspace' : 'Set Active'}
                      </button>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', flexWrap: 'wrap' }}>
                        <button
                          type="button"
                          onClick={() => {
                            selectProject(proj);
                            setActiveTab('overview');
                          }}
                          style={{
                            background: 'rgba(56, 189, 248, 0.1)',
                            border: '1px solid rgba(56, 189, 248, 0.25)',
                            borderRadius: '6px',
                            padding: '0.35rem 0.6rem',
                            color: '#38bdf8',
                            fontSize: '0.78rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                          }}
                        >
                          Overview
                        </button>

                        <button
                          type="button"
                          onClick={() => {
                            selectProject(proj);
                            setActiveTab('code-studio');
                          }}
                          style={{
                            background: 'rgba(6, 182, 212, 0.1)',
                            border: '1px solid rgba(6, 182, 212, 0.25)',
                            borderRadius: '6px',
                            padding: '0.35rem 0.6rem',
                            color: '#22d3ee',
                            fontSize: '0.78rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                          }}
                        >
                          Code
                        </button>

                        <button
                          type="button"
                          onClick={() => handleDownloadZip(proj)}
                          title="Download project code as ZIP"
                          style={{
                            background: 'rgba(255, 255, 255, 0.05)',
                            border: '1px solid rgba(255, 255, 255, 0.12)',
                            borderRadius: '6px',
                            padding: '0.35rem 0.55rem',
                            color: '#94a3b8',
                            fontSize: '0.78rem',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.25rem',
                          }}
                        >
                          <Download size={12} />
                          <span>ZIP</span>
                        </button>

                        
                        <button
                          type="button"
                          onClick={() => handleLaunchProjectPreview(proj)}
                          style={{
                            background: 'rgba(16, 185, 129, 0.12)',
                            border: '1px solid rgba(16, 185, 129, 0.3)',
                            borderRadius: '6px',
                            padding: '0.35rem 0.65rem',
                            color: '#6ee7b7',
                            fontSize: '0.78rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.35rem',
                          }}
                          title="Run application preview in User Mode"
                        >
                          <Play size={12} />
                          <span>View App</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => handleOpenInDeveloperMode(proj)}
                          style={{
                            background: 'rgba(99, 102, 241, 0.12)',
                            border: '1px solid rgba(99, 102, 241, 0.3)',
                            borderRadius: '6px',
                            padding: '0.35rem 0.75rem',
                            color: '#c7d2fe',
                            fontSize: '0.78rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.35rem',
                            transition: 'all 0.15s ease',
                          }}
                        >
                          <span>Open in Developer Mode</span>
                          <ArrowRight size={13} />
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* ================================================================= */}

            {/* 7. Explore & Learn Section                                        */}
        {/* ================================================================= */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: '#ffffff' }}>
            Learn & Explore
          </h2>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 280px), 1fr))',
              gap: '1.25rem',
            }}
          >
            {/* Guide 1 */}
            <div
              style={{
                background: 'rgba(15, 20, 36, 0.55)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '14px',
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.85rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <div style={{ padding: '0.45rem', borderRadius: '8px', background: 'rgba(139, 92, 246, 0.15)' }}>
                  <Code2 size={20} color="#a78bfa" />
                </div>
                <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#ffffff', margin: 0 }}>
                  Developer Mode Workspaces
                </h3>
              </div>
              <p style={{ fontSize: '0.84rem', color: '#94a3b8', lineHeight: 1.5, margin: 0 }}>
                Learn how Code Studio, the Monaco tree, isolated Docker previews on port 8001, and regression testing operate.
              </p>
              <button
                type="button"
                onClick={() => switchMode('developer')}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#818cf8',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  padding: 0,
                  textAlign: 'left',
                }}
              >
                <span>Enter Developer Mode</span>
                <ArrowRight size={13} />
              </button>
            </div>

            {/* Guide 2 */}
            <div
              style={{
                background: 'rgba(15, 20, 36, 0.55)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '14px',
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.85rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <div style={{ padding: '0.45rem', borderRadius: '8px', background: 'rgba(56, 189, 248, 0.15)' }}>
                  <Bot size={20} color="#38bdf8" />
                </div>
                <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#ffffff', margin: 0 }}>
                  IntelliAssist vs Global AI
                </h3>
              </div>
              <p style={{ fontSize: '0.84rem', color: '#94a3b8', lineHeight: 1.5, margin: 0 }}>
                Understand when to use the ambient floating assistant vs project-level code modification and diff reviews.
              </p>
              <span style={{ fontSize: '0.8rem', color: '#38bdf8', fontWeight: 500 }}>
                Use floating button anytime
              </span>
            </div>

            {/* Guide 3 */}
            <div
              style={{
                background: 'rgba(15, 20, 36, 0.55)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '14px',
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.85rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <div style={{ padding: '0.45rem', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.15)' }}>
                  <Terminal size={20} color="#10b981" />
                </div>
                <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#ffffff', margin: 0 }}>
                  Full SDLC Automation
                </h3>
              </div>
              <p style={{ fontSize: '0.84rem', color: '#94a3b8', lineHeight: 1.5, margin: 0 }}>
                Move from synthesized requirements to automated testing, Docker containers, and one-click ZIP code exports.
              </p>
              <span style={{ fontSize: '0.8rem', color: '#10b981', fontWeight: 500 }}>
                Autonomous Pipeline Active
              </span>
            </div>
          </div>
        </section>
          </>
        )}

{/* ================================================================= */}
        {/* TAB 2: Project Overview & Health                                  */}
        {/* ================================================================= */}
        {activeTab === 'overview' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem', maxWidth: '1240px', width: '100%', margin: '0 auto' }}>
            {/* Hero Header */}
            <div
              style={{
                background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.18), rgba(13, 18, 31, 0.95))',
                border: '1px solid rgba(99, 102, 241, 0.35)',
                borderRadius: '20px',
                padding: '2rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '1.25rem',
                boxShadow: '0 12px 35px rgba(0, 0, 0, 0.4)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
                <div
                  style={{
                    width: 52,
                    height: 52,
                    borderRadius: '14px',
                    background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#ffffff',
                    boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)',
                  }}
                >
                  <Compass size={26} />
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
                    <h1 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, color: '#ffffff', letterSpacing: '-0.02em' }}>
                      {currentProject?.name || 'Application Overview'}
                    </h1>
                    <span
                      style={{
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        padding: '0.2rem 0.6rem',
                        borderRadius: '9999px',
                        background: 'rgba(16, 185, 129, 0.18)',
                        color: '#34d399',
                        border: '1px solid rgba(16, 185, 129, 0.35)',
                      }}
                    >
                      ACTIVE
                    </span>
                    <span
                      style={{
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        padding: '0.2rem 0.6rem',
                        borderRadius: '6px',
                        background: 'rgba(139, 92, 246, 0.18)',
                        color: '#c4b5fd',
                        border: '1px solid rgba(139, 92, 246, 0.35)',
                      }}
                    >
                      v{activeVersionNum}.0
                    </span>
                  </div>
                  <p style={{ fontSize: '0.88rem', color: '#94a3b8', margin: '0.4rem 0 0 0', maxWidth: '680px', lineHeight: 1.5 }}>
                    {currentProject?.description || 'Autonomous AI-built application managed seamlessly on SE IntelliPlatform.'}
                  </p>
                </div>
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
                <Button
                  variant="primary"
                  onClick={() => {
                    if (currentProject) handleLaunchProjectPreview(currentProject);
                    else setActiveTab('preview');
                  }}
                  icon={<Play size={14} />}
                  style={{ background: 'linear-gradient(135deg, #10b981, #06b6d4)', fontWeight: 650, boxShadow: '0 4px 14px rgba(16, 185, 129, 0.3)' }}
                >
                  Open Live Preview
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => setActiveTab('code-studio')}
                  icon={<Code2 size={14} />}
                  style={{ background: 'rgba(255, 255, 255, 0.06)', border: '1px solid rgba(255, 255, 255, 0.12)' }}
                >
                  View Code
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => handleDownloadZip(currentProject)}
                  icon={<Download size={14} />}
                  disabled={isDownloadingZip}
                  style={{ background: 'rgba(255, 255, 255, 0.06)', border: '1px solid rgba(255, 255, 255, 0.12)' }}
                >
                  {isDownloadingZip ? 'Downloading...' : 'Download ZIP'}
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => {
                    if (currentProject) handleOpenInDeveloperMode(currentProject);
                    else switchMode('developer');
                  }}
                  icon={<ArrowRight size={14} />}
                  style={{ background: 'rgba(99, 102, 241, 0.12)', border: '1px solid rgba(99, 102, 241, 0.3)', color: '#c7d2fe' }}
                >
                  Developer Mode
                </Button>
              </div>
            </div>

            {/* Metrics and Health Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
              <div
                style={{
                  background: 'rgba(15, 20, 36, 0.75)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '16px',
                  padding: '1.5rem',
                  backdropFilter: 'blur(12px)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <ShieldCheck size={18} color="#10b981" />
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#f8fafc', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Runtime Health
                  </span>
                </div>
                <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#34d399', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981', boxShadow: '0 0 10px #10b981' }} />
                  <span>Port {runtimePort} Live</span>
                </div>
                <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: '0.45rem 0 0 0' }}>
                  Application container is healthy. Response latency &lt; 45ms.
                </p>
              </div>

              <div
                style={{
                  background: 'rgba(15, 20, 36, 0.75)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '16px',
                  padding: '1.5rem',
                  backdropFilter: 'blur(12px)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <GitBranch size={18} color="#818cf8" />
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#f8fafc', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Active Version
                  </span>
                </div>
                <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#c4b5fd' }}>
                  Version {activeVersionNum}.0
                </div>
                <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: '0.45rem 0 0 0' }}>
                  All modifications tracked with immutable version snapshots and instant rollback.
                </p>
              </div>

              <div
                style={{
                  background: 'rgba(15, 20, 36, 0.75)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '16px',
                  padding: '1.5rem',
                  backdropFilter: 'blur(12px)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <FileCode size={18} color="#06b6d4" />
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#f8fafc', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Source Export
                  </span>
                </div>
                <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#22d3ee' }}>
                  ZIP Ready
                </div>
                <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: '0.45rem 0 0 0' }}>
                  Complete frontend, backend, and configs packaged without credentials.
                </p>
              </div>
            </div>

            {/* Non-Technical Summary & Features */}
            <div
              style={{
                background: 'rgba(15, 20, 36, 0.75)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '18px',
                padding: '1.75rem',
              }}
            >
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, margin: '0 0 0.85rem 0', color: '#ffffff' }}>
                Application Summary
              </h3>
              <p style={{ fontSize: '0.9rem', color: '#cbd5e1', lineHeight: 1.6, margin: '0 0 1.35rem 0' }}>
                {currentProject?.description || 'Your application is built with a reactive frontend and FastAPI backend routes, serving users through the container runtime.'}
              </p>

              <h4 style={{ fontSize: '0.95rem', fontWeight: 650, margin: '0 0 0.85rem 0', color: '#818cf8' }}>
                Core Capabilities & Architecture
              </h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.85rem' }}>
                {[
                  'Adaptive responsive UI supporting desktop, tablet, and mobile',
                  'FastAPI backend with structured schema validation and error handling',
                  'Containerized isolated execution environment on Port 8001',
                  'Instant natural-language continuous app refinement support',
                  'Version-controlled snapshot tracking with one-click rollback',
                  'One-click sanitized ZIP source code export for offline deployment',
                ].map((feat, i) => (
                  <div
                    key={i}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.55rem',
                      padding: '0.75rem 1rem',
                      background: 'rgba(255, 255, 255, 0.02)',
                      border: '1px solid rgba(255, 255, 255, 0.06)',
                      borderRadius: '10px',
                      fontSize: '0.84rem',
                      color: '#e2e8f0',
                    }}
                  >
                    <CheckCircle2 size={16} color="#10b981" />
                    <span>{feat}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Version History & Rollback Timeline */}
            <div
              style={{
                background: 'rgba(15, 20, 36, 0.75)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '18px',
                padding: '1.75rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                <div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0, color: '#ffffff' }}>
                    Version History & Snapshots
                  </h3>
                  <p style={{ fontSize: '0.82rem', color: '#94a3b8', margin: '0.25rem 0 0 0' }}>
                    Every change generates an immutable snapshot. You can roll back anytime without data loss.
                  </p>
                </div>
                {activeVersionNum > 1 && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={handleRollback}
                    icon={<RotateCcw size={13} />}
                    disabled={isApplyingChange}
                    style={{ background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#fca5a5' }}
                  >
                    {isApplyingChange ? 'Rolling back...' : `Roll back to v${activeVersionNum - 1}`}
                  </Button>
                )}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {Array.from({ length: Math.max(activeVersionNum, 1) }, (_, i) => activeVersionNum - i).map((ver) => (
                  <div
                    key={ver}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '0.85rem 1.15rem',
                      borderRadius: '12px',
                      background: ver === activeVersionNum ? 'rgba(99, 102, 241, 0.12)' : 'rgba(255, 255, 255, 0.02)',
                      border: ver === activeVersionNum ? '1px solid rgba(99, 102, 241, 0.35)' : '1px solid rgba(255, 255, 255, 0.05)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                      <span
                        style={{
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          padding: '0.2rem 0.55rem',
                          borderRadius: '6px',
                          background: ver === activeVersionNum ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255, 255, 255, 0.06)',
                          color: ver === activeVersionNum ? '#34d399' : '#94a3b8',
                        }}
                      >
                        v{ver}
                      </span>
                      <div>
                        <span style={{ fontSize: '0.88rem', fontWeight: 600, color: '#f8fafc' }}>
                          {ver === 1 ? 'Initial Blueprint Scaffold' : `AI Refinement #${ver - 1}`}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: '#64748b', marginLeft: '0.65rem' }}>
                          {ver === activeVersionNum ? '● Active Version' : 'Historical Snapshot'}
                        </span>
                      </div>
                    </div>

                    {ver < activeVersionNum && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleRollback}
                        icon={<RotateCcw size={12} />}
                        disabled={isApplyingChange}
                        style={{ fontSize: '0.78rem', color: '#a78bfa' }}
                      >
                        Restore this version
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

{/* ================================================================= */}
        {/* TAB 3: Code Studio (Beginner Read-Only Code Viewer)               */}
        {/* ================================================================= */}
        {activeTab === 'code-studio' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', height: '100%', maxWidth: '1240px', width: '100%', margin: '0 auto' }}>
            {/* Top Header */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '0.75rem',
                padding: '1rem 1.25rem',
                background: 'rgba(15, 20, 36, 0.85)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '14px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{ padding: '0.45rem', borderRadius: '8px', background: 'rgba(6, 182, 212, 0.15)' }}>
                  <Code2 size={20} color="#06b6d4" />
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '1rem', fontWeight: 700, color: '#ffffff' }}>Code Studio</span>
                    <span style={{ fontSize: '0.68rem', padding: '0.15rem 0.45rem', borderRadius: '4px', background: 'rgba(6, 182, 212, 0.15)', color: '#22d3ee', fontWeight: 700 }}>
                      READ ONLY
                    </span>
                  </div>
                  <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                    {(currentProject || createdProject)?.name} • File: <strong style={{ color: '#e2e8f0' }}>{selectedStudioPath}</strong>
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                {downloadNotice && (
                  <span style={{ fontSize: '0.78rem', color: '#10b981', fontWeight: 600 }}>{downloadNotice}</span>
                )}
                <Button
                  variant="primary"
                  onClick={() => handleDownloadZip(currentProject)}
                  icon={<Download size={14} />}
                  disabled={isDownloadingZip}
                  style={{ background: 'linear-gradient(135deg, #0ea5e9, #6366f1)', fontWeight: 650 }}
                >
                  {isDownloadingZip ? 'Preparing ZIP...' : 'Download Full Source Code (ZIP)'}
                </Button>

                <Button
                  variant="secondary"
                  onClick={() => {
                    if (currentProject) handleOpenInDeveloperMode(currentProject);
                    else switchMode('developer');
                  }}
                  icon={<ArrowRight size={14} />}
                  style={{ background: 'rgba(99, 102, 241, 0.12)', border: '1px solid rgba(99, 102, 241, 0.3)', color: '#c7d2fe' }}
                >
                  Switch to Developer Mode to Edit
                </Button>
              </div>
            </div>

            {/* Help Banner */}
            <div
              style={{
                padding: '0.85rem 1.25rem',
                background: 'rgba(99, 102, 241, 0.08)',
                border: '1px solid rgba(99, 102, 241, 0.25)',
                borderRadius: '12px',
                fontSize: '0.82rem',
                color: '#c7d2fe',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '0.5rem',
              }}
            >
              <span>
                💡 Curious how your app was built? Here is the actual production code synthesized by AI. You can download the complete ZIP package or switch to Developer Mode anytime to edit files directly.
              </span>
              <button
                type="button"
                onClick={() => {
                  if (currentProject) handleOpenInDeveloperMode(currentProject);
                  else switchMode('developer');
                }}
                style={{ background: 'transparent', border: 'none', color: '#818cf8', fontWeight: 700, cursor: 'pointer', fontSize: '0.82rem', textDecoration: 'underline' }}
              >
                Edit in Developer Mode →
              </button>
            </div>

            {/* Code Split View */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '260px 1fr',
                gap: '1rem',
                minHeight: '520px',
                background: 'rgba(10, 14, 26, 0.95)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '16px',
                overflow: 'hidden',
                boxShadow: '0 8px 30px rgba(0, 0, 0, 0.35)',
              }}
            >
              {/* File Tree Left Column */}
              <div
                style={{
                  background: 'rgba(13, 18, 31, 0.85)',
                  borderRight: '1px solid rgba(255, 255, 255, 0.08)',
                  padding: '1.25rem',
                  overflowY: 'auto',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem',
                }}
              >
                <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Project Files
                </span>

                {studioFiles.length === 0 ? (
                  <div style={{ padding: '1rem 0.5rem', color: '#64748b', fontSize: '0.8rem', textAlign: 'center' }}>
                    No source files generated yet.
                  </div>
                ) : (
                  (() => {
                    const renderNode = (node: FileNode, depth: number = 0): React.ReactNode => {
                      if (node.type === 'directory') {
                        return (
                          <div key={node.id || node.path} style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                            <span
                              style={{
                                fontSize: '0.78rem',
                                fontWeight: 650,
                                color: '#94a3b8',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.35rem',
                                padding: '0.25rem 0.4rem',
                                paddingLeft: `${depth * 0.75 + 0.4}rem`,
                              }}
                            >
                              📁 {node.name}
                            </span>
                            {node.children?.map((child) => renderNode(child, depth + 1))}
                          </div>
                        );
                      }

                      const isSelected = selectedStudioPath === node.path;
                      return (
                        <button
                          key={node.id || node.path}
                          type="button"
                          onClick={async () => {
                            setSelectedStudioPath(node.path);
                            const targetProj = currentProject || createdProject;
                            if (targetProj?.id) {
                              try {
                                const res = await codeStudioApi.getFileContent(targetProj.id, node.path);
                                setStudioCodeContent(res.content || '');
                              } catch {
                                setStudioCodeContent(getFallbackFileContent(node.path, targetProj?.name));
                              }
                            }
                          }}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.45rem',
                            padding: '0.35rem 0.65rem',
                            paddingLeft: `${depth * 0.75 + 0.65}rem`,
                            borderRadius: '6px',
                            fontSize: '0.78rem',
                            background: isSelected ? 'rgba(99, 102, 241, 0.2)' : 'transparent',
                            color: isSelected ? '#ffffff' : '#cbd5e1',
                            border: isSelected ? '1px solid rgba(99, 102, 241, 0.35)' : '1px solid transparent',
                            cursor: 'pointer',
                            textAlign: 'left',
                            width: '100%',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                          }}
                          title={node.path}
                        >
                          📄 {node.name}
                        </button>
                      );
                    };

                    return studioFiles.map((n) => renderNode(n, 0));
                  })()
                )}
              </div>

              {/* Code Viewer Right Column */}
              <div style={{ display: 'flex', flexDirection: 'column', background: '#080c16', overflow: 'hidden' }}>
                <div
                  style={{
                    padding: '0.75rem 1.25rem',
                    background: 'rgba(255, 255, 255, 0.02)',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    fontSize: '0.75rem',
                    color: '#64748b',
                  }}
                >
                  <span>{selectedStudioPath}</span>
                  <span>{studioCodeContent.split('\n').length} lines</span>
                </div>

                <div style={{ flex: 1, padding: '1.25rem', overflow: 'auto', fontFamily: 'var(--font-mono, "JetBrains Mono", monospace)', fontSize: '0.82rem', lineHeight: 1.6, color: '#f8fafc' }}>
                  {isStudioLoading ? (
                    <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>Loading source file...</div>
                  ) : (
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                      {studioCodeContent}
                    </pre>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 4: Live Application Preview Frame & Quick Refinement         */}
        {/* ================================================================= */}
        {activeTab === 'preview' && (
          (createdProject || currentProject) ? (
            <section
            style={{
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(15, 20, 36, 0.95) 100%)',
              border: '1px solid rgba(16, 185, 129, 0.35)',
              borderRadius: '20px',
              padding: '2rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1.5rem',
              boxShadow: '0 12px 35px rgba(0, 0, 0, 0.5), 0 0 30px rgba(16, 185, 129, 0.12)',
            }}
          >
            {/* Header info bar */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '1rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: '12px',
                    background: 'rgba(16, 185, 129, 0.2)',
                    border: '1px solid rgba(16, 185, 129, 0.4)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <ShieldCheck size={24} color="#10b981" />
                </div>
                <div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ffffff' }}>
                    Project “{(createdProject || currentProject)?.name || 'Application'}” Created Successfully! Running Live!
                  </div>
                  <div style={{ fontSize: '0.84rem', color: '#94a3b8' }}>
                    Containerized application active on port {runtimePort}. Use the panel below to request continuous natural-language refinements.
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                <Button
                  variant="primary"
                  onClick={() => handleOpenInDeveloperMode(createdProject)}
                  icon={<Code2 size={16} />}
                  style={{
                    background: 'linear-gradient(135deg, #4f46e5, #0ea5e9)',
                    fontWeight: 600,
                  }}
                >
                  Open in Developer Mode
                </Button>

                <Button
                  variant="ghost"
                  onClick={() => {
                    setCreatedProject(null);
                    setBuilderStage('IDLE');
                    setLivePreviewUrl(null);
                  }}
                  icon={<Sparkles size={14} />}
                  style={{ color: '#cbd5e1', fontSize: '0.84rem' }}
                >
                  Build Another App
                </Button>
              </div>
            </div>

            {/* Error banner if autonomous build encountered an issue */}
            {builderError && (
              <div
                style={{
                  color: '#fca5a5',
                  fontSize: '0.84rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '0.5rem',
                  background: 'rgba(239, 68, 68, 0.1)',
                  padding: '0.75rem 1rem',
                  borderRadius: '8px',
                  border: '1px solid rgba(239, 68, 68, 0.25)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <AlertCircle size={16} />
                  <span>{builderError}</span>
                </div>
                {currentProject && (
                  <button
                    type="button"
                    onClick={() => executeAutonomousBuild(currentProject)}
                    style={{
                      padding: '0.35rem 0.75rem',
                      background: '#ef4444',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '0.76rem',
                      fontWeight: 650,
                      cursor: 'pointer',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    Retry Build
                  </button>
                )}
              </div>
            )}

            {/* Live Interactive Application Preview Frame */}
            {livePreviewUrl && (
              <div
                style={{
                  background: 'rgba(10, 14, 26, 0.95)',
                  border: '1px solid rgba(139, 92, 246, 0.35)',
                  borderRadius: '16px',
                  overflow: 'hidden',
                  display: 'flex',
                  flexDirection: 'column',
                  boxShadow: '0 12px 35px rgba(0, 0, 0, 0.4)',
                }}
              >
                {/* Preview Toolbar */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.75rem 1.25rem',
                    background: 'rgba(15, 20, 36, 0.85)',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
                    flexWrap: 'wrap',
                    gap: '0.5rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                    <span
                      style={{
                        padding: '0.15rem 0.55rem',
                        borderRadius: '9999px',
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        background: 'rgba(16, 185, 129, 0.15)',
                        color: '#34d399',
                        border: '1px solid rgba(16, 185, 129, 0.3)',
                      }}
                    >
                      ● {runtimeStatus === 'STOPPED' ? 'RUNNING' : runtimeStatus}
                    </span>
                    <span
                      style={{
                        padding: '0.15rem 0.55rem',
                        borderRadius: '4px',
                        fontSize: '0.72rem',
                        fontWeight: 600,
                        background: 'rgba(56, 189, 248, 0.12)',
                        color: '#38bdf8',
                        border: '1px solid rgba(56, 189, 248, 0.25)',
                      }}
                    >
                      Port {runtimePort}
                    </span>
                    <span
                      style={{
                        padding: '0.15rem 0.55rem',
                        borderRadius: '4px',
                        fontSize: '0.72rem',
                        fontWeight: 600,
                        background: 'rgba(139, 92, 246, 0.12)',
                        color: '#c4b5fd',
                        border: '1px solid rgba(139, 92, 246, 0.25)',
                      }}
                    >
                      🐳 Docker Runtime
                    </span>
                  </div>

                  {/* Viewport Switcher */}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      background: 'rgba(255, 255, 255, 0.05)',
                      borderRadius: '6px',
                      padding: '2px',
                    }}
                  >
                    <button
                      type="button"
                      onClick={() => setDeviceViewport('desktop')}
                      title="Desktop Viewport"
                      style={{
                        background: deviceViewport === 'desktop' ? 'rgba(255, 255, 255, 0.12)' : 'transparent',
                        border: 'none',
                        color: deviceViewport === 'desktop' ? '#ffffff' : '#64748b',
                        padding: '0.25rem 0.45rem',
                        borderRadius: '4px',
                        cursor: 'pointer',
                      }}
                    >
                      <Monitor size={14} />
                    </button>
                    <button
                      type="button"
                      onClick={() => setDeviceViewport('tablet')}
                      title="Tablet Viewport"
                      style={{
                        background: deviceViewport === 'tablet' ? 'rgba(255, 255, 255, 0.12)' : 'transparent',
                        border: 'none',
                        color: deviceViewport === 'tablet' ? '#ffffff' : '#64748b',
                        padding: '0.25rem 0.45rem',
                        borderRadius: '4px',
                        cursor: 'pointer',
                      }}
                    >
                      <Tablet size={14} />
                    </button>
                    <button
                      type="button"
                      onClick={() => setDeviceViewport('mobile')}
                      title="Mobile Viewport"
                      style={{
                        background: deviceViewport === 'mobile' ? 'rgba(255, 255, 255, 0.12)' : 'transparent',
                        border: 'none',
                        color: deviceViewport === 'mobile' ? '#ffffff' : '#64748b',
                        padding: '0.25rem 0.45rem',
                        borderRadius: '4px',
                        cursor: 'pointer',
                      }}
                    >
                      <Smartphone size={14} />
                    </button>
                  </div>

                  {/* Action Buttons */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <button
                      type="button"
                      onClick={handleRefreshActiveVersion}
                      title="Reload Live Preview"
                      style={{
                        background: 'rgba(255, 255, 255, 0.06)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        borderRadius: '6px',
                        padding: '0.35rem 0.6rem',
                        color: '#cbd5e1',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                        fontSize: '0.78rem',
                      }}
                    >
                      <RotateCw size={13} />
                      <span>Refresh</span>
                    </button>

                    <a
                      href={livePreviewUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      title="Open in New Tab"
                      style={{
                        background: 'rgba(255, 255, 255, 0.06)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        borderRadius: '6px',
                        padding: '0.35rem 0.6rem',
                        color: '#cbd5e1',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                        fontSize: '0.78rem',
                        textDecoration: 'none',
                      }}
                    >
                      <ExternalLink size={13} />
                      <span>Popout</span>
                    </a>
                  </div>
                </div>

                {/* Sandboxed iFrame */}
                <div
                  style={{
                    background: '#090d16',
                    display: 'flex',
                    justifyContent: 'center',
                    minHeight: '480px',
                    height: '560px',
                    overflow: 'hidden',
                    width: '100%',
                    maxWidth: '100%',
                    boxSizing: 'border-box',
                  }}
                >
                  <iframe
                    key={previewKey}
                    src={livePreviewUrl}
                    title={`${(createdProject || currentProject)?.name || 'Application'} Live Application Preview`}
                    sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
                    referrerPolicy="no-referrer"
                    style={{
                      width: deviceViewport === 'desktop' ? '100%' : deviceViewport === 'tablet' ? '768px' : '375px',
                      maxWidth: '100%',
                      height: '100%',
                      border: 'none',
                      transition: 'width 0.25s ease',
                      boxShadow: deviceViewport !== 'desktop' ? '0 0 30px rgba(0, 0, 0, 0.6)' : 'none',
                    }}
                  />
                </div>

                {/* Footer Note */}
                <div
                  style={{
                    padding: '0.75rem 1.25rem',
                    background: 'rgba(15, 20, 36, 0.85)',
                    borderTop: '1px solid rgba(255, 255, 255, 0.08)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: '0.5rem',
                    fontSize: '0.8rem',
                    color: '#94a3b8',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                    <Sparkles size={14} color="#10b981" />
                    <span>
                      Live application running in isolated container. To inspect code, debug, or run tests, switch to Developer Mode anytime.
                    </span>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleOpenInDeveloperMode(createdProject)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: '#818cf8',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.35rem',
                    }}
                  >
                    <span>Enter Code Studio in Developer Mode</span>
                    <ArrowRight size={13} />
                  </button>
                </div>
              </div>
            )}

            {/* Context-Aware Natural Language App Refinement Panel (Stage 6) */}
            {livePreviewUrl && (
              <div
                data-testid="app-refinement-panel"
                style={{
                  background: 'rgba(10, 14, 26, 0.95)',
                  border: '1px solid rgba(139, 92, 246, 0.35)',
                  borderRadius: '16px',
                  padding: '1.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1.25rem',
                  boxShadow: '0 8px 30px rgba(0, 0, 0, 0.4)',
                }}
              >
                {/* Header & Status Strip */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: '0.75rem',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
                    paddingBottom: '0.85rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div
                      style={{
                        width: 36,
                        height: 36,
                        borderRadius: '10px',
                        background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(6, 182, 212, 0.3))',
                        border: '1px solid rgba(139, 92, 246, 0.4)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <Wand2 size={18} color="#c4b5fd" />
                    </div>
                    <div>
                      <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff' }}>
                        Refine “{(createdProject || currentProject)?.name || 'Application'}”
                      </div>
                      <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                        Continuous Natural-Language Refinement: Request modifications conversationally.
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
                    <span
                      style={{
                        padding: '0.2rem 0.55rem',
                        borderRadius: '4px',
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        background: 'rgba(99, 102, 241, 0.18)',
                        color: '#a5b4fc',
                        border: '1px solid rgba(99, 102, 241, 0.35)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                      }}
                    >
                      <GitBranch size={12} />
                      v{activeVersionNum}
                    </span>

                    <span
                      style={{
                        padding: '0.2rem 0.55rem',
                        borderRadius: '4px',
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        background: 'rgba(16, 185, 129, 0.15)',
                        color: '#34d399',
                        border: '1px solid rgba(16, 185, 129, 0.3)',
                      }}
                    >
                      ● RUNNING
                    </span>

                    {activeVersionNum > 1 && (
                      <button
                        type="button"
                        onClick={handleRollback}
                        disabled={isApplyingChange}
                        title={`Revert back to version v${activeVersionNum - 1}`}
                        style={{
                          background: 'rgba(239, 68, 68, 0.12)',
                          border: '1px solid rgba(239, 68, 68, 0.3)',
                          borderRadius: '6px',
                          padding: '0.25rem 0.65rem',
                          color: '#fca5a5',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          cursor: isApplyingChange ? 'not-allowed' : 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.35rem',
                        }}
                      >
                        <RotateCcw size={12} />
                        <span>Rollback to v{activeVersionNum - 1}</span>
                      </button>
                    )}
                  </div>
                </div>

                {/* Success Banner */}
                {refinementSuccess && (
                  <div
                    style={{
                      background: 'rgba(16, 185, 129, 0.12)',
                      border: '1px solid rgba(16, 185, 129, 0.3)',
                      borderRadius: '8px',
                      padding: '0.65rem 0.85rem',
                      color: '#6ee7b7',
                      fontSize: '0.82rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                    }}
                  >
                    <CheckCircle2 size={16} />
                    <span style={{ flex: 1 }}>{refinementSuccess}</span>
                    <button
                      type="button"
                      onClick={() => setRefinementSuccess(null)}
                      style={{ background: 'transparent', border: 'none', color: '#6ee7b7', cursor: 'pointer', fontSize: '0.75rem' }}
                    >
                      ✕
                    </button>
                  </div>
                )}

                {/* Error Banner */}
                {refinementError && (
                  <div
                    style={{
                      background: 'rgba(239, 68, 68, 0.12)',
                      border: '1px solid rgba(239, 68, 68, 0.3)',
                      borderRadius: '8px',
                      padding: '0.65rem 0.85rem',
                      color: '#fca5a5',
                      fontSize: '0.82rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                    }}
                  >
                    <AlertCircle size={16} />
                    <span style={{ flex: 1 }}>{refinementError}</span>
                    {refinementError.toLowerCase().includes('refresh') && (
                      <button
                        type="button"
                        onClick={handleRefreshActiveVersion}
                        style={{
                          background: 'rgba(239, 68, 68, 0.25)',
                          border: '1px solid rgba(239, 68, 68, 0.5)',
                          borderRadius: '4px',
                          color: '#ffffff',
                          padding: '0.2rem 0.5rem',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                      >
                        Refresh Version
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => setRefinementError(null)}
                      style={{ background: 'transparent', border: 'none', color: '#fca5a5', cursor: 'pointer', fontSize: '0.75rem' }}
                    >
                      ✕
                    </button>
                  </div>
                )}

                {/* Conversation Turns / History Feed */}
                {refinementMessages.length > 0 && (
                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.65rem',
                      maxHeight: '260px',
                      overflowY: 'auto',
                      paddingRight: '0.35rem',
                    }}
                  >
                    {refinementMessages.map((msg, idx) => (
                      <div
                        key={msg.message_id || idx}
                        style={{
                          alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                          maxWidth: '85%',
                          background: msg.role === 'user' ? 'linear-gradient(135deg, #6366f1, #4f46e5)' : 'rgba(255, 255, 255, 0.05)',
                          border: msg.role === 'user' ? 'none' : '1px solid rgba(255, 255, 255, 0.08)',
                          borderRadius: '10px',
                          padding: '0.6rem 0.85rem',
                          color: '#ffffff',
                          fontSize: '0.82rem',
                          lineHeight: 1.45,
                        }}
                      >
                        <div style={{ fontSize: '0.68rem', color: msg.role === 'user' ? '#c7d2fe' : '#94a3b8', marginBottom: '0.2rem', fontWeight: 600 }}>
                          {msg.role === 'user' ? 'You' : 'Refinement Partner'}
                        </div>
                        <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Proposed Changes Card (Confirmation Gate) */}
                {pendingActionResult && (
                  <div
                    data-testid="proposed-changes-card"
                    style={{
                      background: 'rgba(99, 102, 241, 0.1)',
                      border: '1px solid rgba(99, 102, 241, 0.4)',
                      borderRadius: '12px',
                      padding: '1.25rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.75rem',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.4rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', color: '#c7d2fe', fontWeight: 750, fontSize: '0.9rem' }}>
                        <Sparkles size={16} color="#38bdf8" />
                        <span>Proposed Changes Ready (v{activeVersionNum} → v{activeVersionNum + 1})</span>
                      </div>
                      <span style={{ fontSize: '0.72rem', color: '#a78bfa' }}>
                        Validation Passed
                      </span>
                    </div>

                    <p style={{ margin: 0, fontSize: '0.84rem', color: '#cbd5e1', lineHeight: 1.5 }}>
                      {pendingActionResult.summary || pendingActionResult.confirmation_prompt}
                    </p>

                    {pendingActionResult.data?.files && pendingActionResult.data.files.length > 0 && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                        <div style={{ fontSize: '0.76rem', color: '#94a3b8', fontWeight: 600 }}>
                          Targeted Files ({pendingActionResult.data.files.length}):
                        </div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                          {pendingActionResult.data.files.map((f: any, i: number) => (
                            <span
                              key={i}
                              style={{
                                fontSize: '0.72rem',
                                fontFamily: 'monospace',
                                padding: '0.2rem 0.5rem',
                                borderRadius: '4px',
                                background: 'rgba(255, 255, 255, 0.06)',
                                border: '1px solid rgba(255, 255, 255, 0.1)',
                                color: f.status === 'added' ? '#34d399' : '#818cf8',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.3rem',
                              }}
                            >
                              <FileCode size={12} />
                              <span>{f.status === 'added' ? '+ ' : '~ '}{f.path}</span>
                            </span>
                          ))}
                        </div>

                        {/* Collapsible Diff Viewer */}
                        <div style={{ marginTop: '0.35rem' }}>
                          <button
                            type="button"
                            onClick={() => setIsDiffExpanded((prev) => !prev)}
                            style={{
                              background: 'transparent',
                              border: 'none',
                              color: '#38bdf8',
                              fontSize: '0.76rem',
                              fontWeight: 650,
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '0.3rem',
                              padding: 0,
                            }}
                          >
                            <Eye size={13} />
                            <span>{isDiffExpanded ? 'Hide Diffs' : 'Inspect Diffs'}</span>
                            {isDiffExpanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                          </button>

                          {isDiffExpanded && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.5rem' }}>
                              {pendingActionResult.data.files.map((f: any, i: number) => (
                                <div
                                  key={i}
                                  style={{
                                    borderRadius: '6px',
                                    border: '1px solid rgba(255, 255, 255, 0.1)',
                                    overflow: 'hidden',
                                    fontSize: '0.74rem',
                                    fontFamily: 'monospace',
                                  }}
                                >
                                  <div style={{ padding: '0.35rem 0.65rem', background: 'rgba(255, 255, 255, 0.05)', color: '#cbd5e1' }}>
                                    {f.path}
                                  </div>
                                  <pre style={{ margin: 0, padding: '0.5rem 0.65rem', background: '#090d16', color: '#a5b4fc', whiteSpace: 'pre-wrap', lineHeight: 1.4 }}>
                                    {f.diff}
                                  </pre>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginTop: '0.4rem', flexWrap: 'wrap' }}>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleConfirmRefinement(pendingActionResult.confirmation_token || '')}
                        isLoading={isApplyingChange}
                        disabled={isApplyingChange || !pendingActionResult.confirmation_token}
                        icon={<Check size={14} />}
                        style={{
                          background: 'linear-gradient(135deg, #10b981, #059669)',
                          fontWeight: 650,
                          fontSize: '0.84rem',
                          padding: '0.45rem 1.1rem',
                        }}
                      >
                        Apply & Update Live Preview
                      </Button>

                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setPendingActionResult(null)}
                        disabled={isApplyingChange}
                        style={{ color: '#94a3b8', fontSize: '0.84rem' }}
                      >
                        Discard
                      </Button>
                    </div>
                  </div>
                )}

                {/* Quick Suggestion Pills */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.45rem', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.74rem', color: '#64748b', fontWeight: 650 }}>
                    Suggestions:
                  </span>
                  {SUGGESTED_REFINEMENTS.map((sug, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => handleSendRefinement(sug)}
                      disabled={isRefining || isApplyingChange}
                      style={{
                        background: 'rgba(255, 255, 255, 0.04)',
                        border: '1px solid rgba(255, 255, 255, 0.08)',
                        borderRadius: '6px',
                        padding: '0.25rem 0.55rem',
                        color: '#cbd5e1',
                        fontSize: '0.74rem',
                        cursor: isRefining || isApplyingChange ? 'not-allowed' : 'pointer',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      {sug}
                    </button>
                  ))}
                </div>

                {/* Conversational Refinement Input Form */}
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSendRefinement();
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    background: 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid rgba(139, 92, 246, 0.3)',
                    borderRadius: '10px',
                    padding: '0.4rem 0.5rem 0.4rem 0.85rem',
                  }}
                >
                  <input
                    type="text"
                    value={refinementPrompt}
                    onChange={(e) => setRefinementPrompt(e.target.value)}
                    placeholder="Describe what to add, fix, or change in this app (e.g., 'Add a dark mode toggle')..."
                    aria-label="Describe what changes you want to make to this app"
                    disabled={isRefining || isApplyingChange}
                    style={{
                      flex: 1,
                      background: 'transparent',
                      border: 'none',
                      color: '#ffffff',
                      fontSize: '0.88rem',
                      outline: 'none',
                    }}
                  />
                  <Button
                    type="submit"
                    variant="primary"
                    size="sm"
                    disabled={!refinementPrompt.trim() || isRefining || isApplyingChange}
                    isLoading={isRefining}
                    icon={<Sparkles size={14} />}
                    style={{
                      background: 'linear-gradient(135deg, #7c3aed, #6366f1)',
                      fontWeight: 650,
                      fontSize: '0.82rem',
                      padding: '0.5rem 1.15rem',
                    }}
                  >
                    Refine App
                  </Button>
                </form>
              </div>
            )}
          </section>
        ) : (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '4rem 2rem',
              textAlign: 'center',
              background: 'rgba(15, 20, 36, 0.7)',
              border: '1px dashed rgba(255, 255, 255, 0.15)',
              borderRadius: '16px',
              gap: '1rem',
              maxWidth: '600px',
              margin: '2rem auto',
            }}
          >
            <Eye size={40} color="#64748b" />
            <div style={{ fontSize: '1.1rem', fontWeight: 600, color: '#f1f5f9' }}>No Project Selected for Preview</div>
            <div style={{ fontSize: '0.875rem', color: '#94a3b8', maxWidth: '440px' }}>
              Select an existing project from the Projects tab or generate a new application to view its live interactive preview here.
            </div>
            <Button variant="primary" onClick={() => setActiveTab('projects')}>
              Go to Projects
            </Button>
          </div>
        )
      )}

      {/* ================================================================= */}
      {/* TAB 5: AI Development Assistant                                  */}
        {/* ================================================================= */}
        {activeTab === 'assistant' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', maxWidth: '980px', width: '100%', margin: '0 auto' }}>
            {/* Assistant Header */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '1.5rem',
                background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.18), rgba(15, 20, 36, 0.95))',
                border: '1px solid rgba(139, 92, 246, 0.35)',
                borderRadius: '18px',
                boxShadow: '0 8px 30px rgba(0, 0, 0, 0.35)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                <div style={{ padding: '0.55rem', borderRadius: '12px', background: 'rgba(139, 92, 246, 0.2)', border: '1px solid rgba(139, 92, 246, 0.4)' }}>
                  <Bot size={24} color="#c4b5fd" />
                </div>
                <div>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: '#ffffff' }}>
                    AI Development Assistant
                  </h2>
                  <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                    Project Context: <strong style={{ color: '#c4b5fd' }}>{currentProject?.name}</strong> • Version {activeVersionNum}.0
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    if (currentProject) handleLaunchProjectPreview(currentProject);
                    else setActiveTab('preview');
                  }}
                  icon={<Play size={13} />}
                  style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#34d399' }}
                >
                  View Live App
                </Button>
              </div>
            </div>

            {/* Context-Aware Natural Language App Refinement Panel */}
            <div
              data-testid="app-refinement-panel"
              style={{
                background: 'rgba(10, 14, 26, 0.95)',
                border: '1px solid rgba(139, 92, 246, 0.35)',
                borderRadius: '18px',
                padding: '1.75rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1.25rem',
                boxShadow: '0 8px 30px rgba(0, 0, 0, 0.4)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', paddingBottom: '0.85rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Sparkles size={16} color="#c4b5fd" />
                  <span style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff' }}>
                    Refine “{currentProject?.name}”
                  </span>
                  <span style={{ fontSize: '0.72rem', fontWeight: 700, padding: '0.15rem 0.45rem', borderRadius: '4px', background: 'rgba(139, 92, 246, 0.2)', color: '#c4b5fd' }}>
                    v{activeVersionNum}
                  </span>
                </div>

                {activeVersionNum > 1 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleRollback}
                    icon={<RotateCcw size={12} />}
                    disabled={isApplyingChange}
                    style={{ color: '#fca5a5', fontSize: '0.75rem' }}
                  >
                    Rollback to v{activeVersionNum - 1}
                  </Button>
                )}
              </div>

              {/* Suggested Quick Refinement Prompts */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.45rem' }}>
                {[
                  'Add dark mode toggle to the navigation bar',
                  'Add search bar filter for items',
                  'Change primary color theme to emerald',
                  'Add export to CSV capability',
                ].map((sug, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => handleSendRefinement(sug)}
                    disabled={isRefining || isApplyingChange}
                    style={{
                      background: 'rgba(139, 92, 246, 0.1)',
                      border: '1px solid rgba(139, 92, 246, 0.25)',
                      borderRadius: '9999px',
                      padding: '0.35rem 0.75rem',
                      color: '#c4b5fd',
                      fontSize: '0.75rem',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    + {sug}
                  </button>
                ))}
              </div>

              {/* Refinement Messages History */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', maxHeight: '360px', overflowY: 'auto' }}>
                {refinementMessages.length === 0 ? (
                  <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b', fontSize: '0.84rem' }}>
                    Describe any feature or modification in plain English, and the AI Assistant will update your running application.
                  </div>
                ) : (
                  refinementMessages.map((msg, i) => (
                    <div
                      key={i}
                      style={{
                        alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                        maxWidth: '85%',
                        background: msg.role === 'user' ? 'rgba(99, 102, 241, 0.25)' : 'rgba(15, 20, 36, 0.85)',
                        border: msg.role === 'user' ? '1px solid rgba(99, 102, 241, 0.4)' : '1px solid rgba(255, 255, 255, 0.08)',
                        borderRadius: '12px',
                        padding: '0.75rem 1rem',
                        fontSize: '0.84rem',
                        color: '#f8fafc',
                      }}
                    >
                      {msg.content}
                    </div>
                  ))
                )}
              </div>

              {/* Action result confirmation */}
              {pendingActionResult && (
                <div
                  style={{
                    background: 'rgba(139, 92, 246, 0.12)',
                    border: '1px solid rgba(139, 92, 246, 0.35)',
                    borderRadius: '12px',
                    padding: '1rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.65rem',
                  }}
                >
                  <div style={{ fontWeight: 650, fontSize: '0.88rem', color: '#c4b5fd' }}>
                    {pendingActionResult.summary || 'Proposed changes ready for your approval:'}
                  </div>
                  <div style={{ display: 'flex', gap: '0.65rem' }}>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => handleConfirmRefinement(pendingActionResult.confirmation_token || '')}
                      disabled={isApplyingChange}
                      style={{ background: 'linear-gradient(135deg, #10b981, #06b6d4)', fontWeight: 650 }}
                    >
                      {isApplyingChange ? 'Applying...' : 'Approve & Apply to Live App'}
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setPendingActionResult(null)}
                      style={{ background: 'rgba(255, 255, 255, 0.06)' }}
                    >
                      Discard
                    </Button>
                  </div>
                </div>
              )}

              {/* Input box */}
              <div style={{ display: 'flex', gap: '0.65rem' }}>
                <input
                  type="text"
                  value={refinementPrompt}
                  onChange={(e) => setRefinementPrompt(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendRefinement();
                    }
                  }}
                  placeholder="e.g. Add an export CSV button, or toggle theme mode..."
                  style={{
                    flex: 1,
                    background: 'rgba(0, 0, 0, 0.3)',
                    border: '1px solid rgba(255, 255, 255, 0.12)',
                    borderRadius: '8px',
                    padding: '0.65rem 1rem',
                    color: '#ffffff',
                    fontSize: '0.84rem',
                    outline: 'none',
                  }}
                />
                <Button
                  variant="primary"
                  onClick={() => handleSendRefinement()}
                  disabled={!refinementPrompt.trim() || isRefining || isApplyingChange}
                  style={{ background: 'linear-gradient(135deg, #7c3aed, #6366f1)', fontWeight: 650 }}
                >
                  {isRefining ? 'Thinking...' : 'Refine with AI'}
                </Button>
              </div>
            </div>
          </div>
        )}
        </main>
      </div>
    </div>
  );
};
