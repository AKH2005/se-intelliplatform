import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useProject } from '../context/ProjectContext';
import { projectsApi } from '../services/projectsApi';
import { contextApi } from '../services/contextApi';
import { workflowsApi } from '../services/workflowsApi';
import { historyApi } from '../services/historyApi';
import { Card, CardBody, CardHeader } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { CapabilityBadge } from '../components/common/CapabilityBadge';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { isProjectNotFoundError } from '../utils/projectRecovery';
import { SdlcPipelineBar } from '../components/layout/SdlcPipelineBar';
import { CreateProjectModal } from '../components/projects/CreateProjectModal';
import {
  FolderKanban,
  PlayCircle,
  FileCode2,
  History,
  Zap,
  Sparkles,
  Monitor,
} from 'lucide-react';
import { ProjectCreate, ProjectResponse } from '../types/project';
import { NavigationTab } from '../components/layout/Sidebar';

interface OverviewWorkspaceProps {
  onNavigate?: (tab: NavigationTab) => void;
}

export const OverviewWorkspace: React.FC<OverviewWorkspaceProps> = ({ onNavigate }) => {
  const queryClient = useQueryClient();
  const {
    selectedProjectId,
    selectedProject,
    selectProject,
    handleStaleProject,
  } = useProject();

  const [isCreateProjectOpen, setIsCreateProjectOpen] = useState(false);

  // 1. Fetch projects
  const {
    data: projects = [],
    isLoading: isLoadingProjects,
    error: projectsError,
  } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(),
  });

  // 2. Fetch context for active project
  const {
    data: context,
    isLoading: isLoadingContext,
    error: contextError,
  } = useQuery({
    queryKey: ['project-context', selectedProjectId],
    queryFn: () => contextApi.getContext(selectedProjectId!),
    enabled: Boolean(selectedProjectId),
  });

  const activeProject =
    selectedProject ||
    (selectedProjectId ? projects.find((p) => p.id === selectedProjectId) || null : null) ||
    (context?.project as any) ||
    (projects.length > 0 ? projects[0] : null);

  React.useEffect(() => {
    if (contextError && isProjectNotFoundError(contextError)) {
      handleStaleProject?.(selectedProjectId || undefined);
    }
  }, [contextError, selectedProjectId, handleStaleProject]);

  // 3. Fetch workflows
  const { data: workflows = [] } = useQuery({
    queryKey: ['workflows'],
    queryFn: () => workflowsApi.list(),
  });

  // 4. Fetch recent executions
  const { data: historyData } = useQuery({
    queryKey: ['project-workflow-history', selectedProjectId],
    queryFn: () => historyApi.listProjectHistory(selectedProjectId!, { limit: 5, offset: 0 }),
    enabled: Boolean(selectedProjectId),
  });

  // Create Project mutation
  const createProjectMutation = useMutation({
    mutationFn: (data: ProjectCreate) => projectsApi.create(data),
    onSuccess: (newProject) => {
      queryClient.setQueryData(['projects'], (prev: ProjectResponse[] = []) => [
        newProject,
        ...(prev || []).filter((p) => p.id !== newProject.id),
      ]);
      selectProject(newProject);
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      if (onNavigate) {
        onNavigate('preview');
      }
    },
  });

  const capabilityRoadmap = [
    {
      capability: 'Requirements Management',
      sdlcStage: 'DESCRIBE',
      status: 'IMPLEMENTED' as const,
      description: 'Canonical functional, non-functional, and constraint requirements with validation.',
    },
    {
      capability: 'Requirement Analysis Agent',
      sdlcStage: 'ANALYZE',
      status: 'IMPLEMENTED' as const,
      description: 'Automated ambiguity detection, completeness scoring, and scope clarification.',
    },
    {
      capability: 'Architecture Recommendation Agent',
      sdlcStage: 'DESIGN',
      status: 'IMPLEMENTED' as const,
      description: 'Multi-tier architectural blueprint, component design, and technology stack selection.',
    },
    {
      capability: 'Database Design Agent',
      sdlcStage: 'DESIGN',
      status: 'IMPLEMENTED' as const,
      description: 'Entity-relationship modeling, schema constraints, indexing, and normalization.',
    },
    {
      capability: 'Risk & Timeline Prediction',
      sdlcStage: 'ANALYZE',
      status: 'IMPLEMENTED' as const,
      description: 'Heuristic and ML-based delivery schedule and risk band prediction.',
    },
    {
      capability: 'Test Case Generation Agent',
      sdlcStage: 'TEST (ANALYSIS)',
      status: 'IMPLEMENTED' as const,
      description: 'Specification-based unit, integration, and security test case synthesis.',
    },
    {
      capability: 'Bug Prediction & Code Review',
      sdlcStage: 'TEST & QUALITY',
      status: 'IMPLEMENTED' as const,
      description: 'Static defect analysis, complexity hotspots, and targeted code quality audit.',
    },
    {
      capability: 'Explainability Agent',
      sdlcStage: 'IMPROVE',
      status: 'IMPLEMENTED' as const,
      description: 'Agent rationale synthesis, decision tracing, and audit trail explainability.',
    },
    {
      capability: 'Code Generation Engine',
      sdlcStage: 'BUILD',
      status: 'IMPLEMENTED' as const,
      description: 'Automated synthesis of production codebases from design artifacts.',
    },
    {
      capability: 'Executable Sandbox Runtime',
      sdlcStage: 'RUN',
      status: 'IMPLEMENTED' as const,
      description: 'Containerized execution environment for generated services.',
    },
    {
      capability: 'Live Test Runner & Sandbox Execution',
      sdlcStage: 'TEST (EXECUTION)',
      status: 'IMPLEMENTED' as const,
      description: 'Execution of generated pytest/jest test suites within isolated sandboxes.',
    },
    {
      capability: 'AI-Assisted Debugging & Remediation',
      sdlcStage: 'DEBUG',
      status: 'IMPLEMENTED' as const,
      description: 'Root-cause fault localization, proposed patch generation, and human-approved verification.',
    },
    {
      capability: 'Polyglot Code Intelligence',
      sdlcStage: 'IMPROVE',
      status: 'IMPLEMENTED' as const,
      description: 'Deterministic AST & lexical analysis for Python, TypeScript, JavaScript, and Java with dependency graphing.',
    },
    {
      capability: 'Browser Smoke & Journey Automation',
      sdlcStage: 'TEST (BROWSER)',
      status: 'IMPLEMENTED' as const,
      description: 'Automated end-to-end browser journey generation and headless Playwright container execution.',
    },
    {
      capability: 'Multi-Environment Deployment & Safe Promotion',
      sdlcStage: 'DEPLOY',
      status: 'IMPLEMENTED' as const,
      description: 'Tiered DEV → STAGING → PRODUCTION deployment with deterministic promotion gates and instant rollback.',
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xl)' }}>
      {/* Primary Product Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
            <span
              style={{
                fontSize: '0.72rem',
                fontWeight: 700,
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                color: 'var(--accent-cyan)',
                background: 'rgba(6, 182, 212, 0.12)',
                padding: '0.2rem 0.6rem',
                borderRadius: '9999px',
                border: '1px solid rgba(6, 182, 212, 0.25)',
              }}
            >
              AI Software Development Studio
            </span>
          </div>
          <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#fff' }}>
            Build software with AI.
          </h1>
          <span style={{ display: 'none' }}>Project Overview</span>
          <p style={{ margin: '0.35rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.92rem', maxWidth: '640px' }}>
            Describe what you want to build, generate a working application, and improve it through conversation.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
          {activeProject && (
            <Button
              variant="secondary"
              onClick={() => onNavigate && onNavigate('preview')}
              style={{ fontWeight: 600 }}
            >
              <Monitor size={15} style={{ marginRight: '0.35rem' }} />
              Live Preview
            </Button>
          )}
          <Button
            variant="primary"
            icon={<Sparkles size={16} />}
            onClick={() => setIsCreateProjectOpen(true)}
            style={{
              background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-cyan))',
              fontWeight: 700,
              padding: '0.55rem 1.15rem',
            }}
          >
            Create & Build
          </Button>
        </div>
      </div>

      {contextError && (
        <ErrorAlert
          error={contextError as any}
          onChooseAnotherProject={() => handleStaleProject?.(selectedProjectId || undefined)}
          onCreateProject={() => setIsCreateProjectOpen(true)}
        />
      )}

      {/* 4-Step Core User Journey */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '0.85rem',
        }}
      >
        <div
          style={{
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '1rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.35rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-primary)', fontWeight: 700, fontSize: '0.82rem' }}>
            <span style={{ width: 22, height: 22, borderRadius: '50%', background: 'rgba(99, 102, 241, 0.15)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>1</span>
            <span>Describe</span>
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Tell AI what you want to build in plain English.
          </div>
        </div>

        <div
          style={{
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '1rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.35rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--sdlc-design)', fontWeight: 700, fontSize: '0.82rem' }}>
            <span style={{ width: 22, height: 22, borderRadius: '50%', background: 'rgba(168, 85, 247, 0.15)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>2</span>
            <span>Build</span>
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            AI generates schemas, APIs, and a live web application.
          </div>
        </div>

        <div
          style={{
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '1rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.35rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#10b981', fontWeight: 700, fontSize: '0.82rem' }}>
            <span style={{ width: 22, height: 22, borderRadius: '50%', background: 'rgba(16, 185, 129, 0.15)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>3</span>
            <span>Live Preview</span>
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Interact with your running application on Port 8001.
          </div>
        </div>

        <div
          style={{
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '1rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.35rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-cyan)', fontWeight: 700, fontSize: '0.82rem' }}>
            <span style={{ width: 22, height: 22, borderRadius: '50%', background: 'rgba(6, 182, 212, 0.15)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>4</span>
            <span>Chat & Modify</span>
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Converse naturally with AI Developer to add features.
          </div>
        </div>
      </div>

      {projectsError && <ErrorAlert error={projectsError as any} />}
      {contextError && <ErrorAlert error={contextError as any} />}

      {/* Global SDLC Progression Bar */}
      <SdlcPipelineBar
        currentStage={activeProject ? 'describe' : undefined}
        onSelectStage={(stage) => {
          if (!onNavigate) return;
          if (stage === 'describe') onNavigate('specification');
          else if (stage === 'analyze') onNavigate('intelligence');
          else if (stage === 'design') onNavigate('workflows');
          else if (stage === 'build' || stage === 'run') onNavigate('development');
          else if (stage === 'test') onNavigate('testing');
          else if (stage === 'debug') onNavigate('issues');
          else if (stage === 'improve') onNavigate('intelligence');
        }}
      />

      {isLoadingProjects ? (
        <LoadingSpinner label="Loading project overview..." />
      ) : projects.length === 0 ? (
        <EmptyState
          icon={<FolderKanban size={36} />}
          title="No application yet"
          description="Describe what you want to build to start generating your live application."
          actionLabel="Build Application"
          onAction={() => setIsCreateProjectOpen(true)}
        />
      ) : (
        <>
          {/* Live Application Hero Banner */}
          {activeProject && (
            <div
              style={{
                padding: '1.25rem 1.5rem',
                borderRadius: 'var(--radius-lg)',
                background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(6, 182, 212, 0.12))',
                border: '1px solid rgba(16, 185, 129, 0.35)',
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
                    borderRadius: '50%',
                    background: 'rgba(16, 185, 129, 0.2)',
                    border: '1px solid rgba(16, 185, 129, 0.5)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#34d399',
                  }}
                >
                  <PlayCircle size={24} />
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <h3 style={{ margin: 0, fontSize: '1.15rem', color: '#fff', fontWeight: 700 }}>
                      Live Application: {activeProject.name}
                    </h3>
                    <span
                      style={{
                        padding: '0.15rem 0.6rem',
                        borderRadius: '9999px',
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        background: 'rgba(16, 185, 129, 0.25)',
                        color: '#34d399',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                      }}
                    >
                      <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#34d399' }} />
                      Application running
                    </span>
                  </div>
                  <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.83rem' }}>
                    Live runtime ready on Port 8001. Open Live Preview to interact or use the AI Development Assistant to add features.
                  </p>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.6rem' }}>
                <Button
                  variant="primary"
                  onClick={() => onNavigate && onNavigate('preview')}
                  style={{
                    background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-cyan))',
                    fontWeight: 700,
                    padding: '0.55rem 1.25rem',
                  }}
                >
                  <Monitor size={15} style={{ marginRight: '0.4rem' }} />
                  Open Live Preview
                </Button>
              </div>
            </div>
          )}

          {/* Active Project Quick Banner or Selector */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: 'var(--space-md)',
            }}
          >
            {/* Project Card */}
            <Card style={{ background: 'var(--bg-glass-card)' }}>
              <CardHeader>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <FolderKanban size={18} color="var(--accent-primary)" />
                  <span style={{ fontWeight: 600 }}>Active Project Identity</span>
                </div>
                {activeProject && <Badge variant={activeProject.status}>{activeProject.status}</Badge>}
              </CardHeader>
              <CardBody>
                {activeProject ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {activeProject.name}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      {activeProject.description || 'No project description provided.'}
                    </div>
                    <div
                      style={{
                        display: 'flex',
                        gap: '1rem',
                        marginTop: '0.5rem',
                        fontSize: '0.75rem',
                        color: 'var(--text-muted)',
                      }}
                    >
                      <span>Slug: <code>{activeProject.slug}</code></span>
                      <span>Created: {new Date(activeProject.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                ) : (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    No project currently selected. Select a project from the top header or list below.
                  </div>
                )}
              </CardBody>
            </Card>

            {/* Context & Requirements Health */}
            <Card style={{ background: 'var(--bg-glass-card)' }}>
              <CardHeader>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <FileCode2 size={18} color="var(--accent-cyan)" />
                  <span style={{ fontWeight: 600 }}>Canonical Requirements</span>
                </div>
                {onNavigate && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => onNavigate('specification')}
                  >
                    View Specs
                  </Button>
                )}
              </CardHeader>
              <CardBody>
                {isLoadingContext ? (
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Loading context metrics...</div>
                ) : context ? (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', textAlign: 'center' }}>
                    <div style={{ padding: '0.5rem', background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)' }}>
                      <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                        {context.statistics?.total_requirements ?? 0}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Total Req</div>
                    </div>
                    <div style={{ padding: '0.5rem', background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)' }}>
                      <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--status-completed)' }}>
                        {context.statistics?.active_requirements ?? 0}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Active</div>
                    </div>
                    <div style={{ padding: '0.5rem', background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)' }}>
                      <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-primary)' }}>
                        {context.statistics?.completion_percentage ?? 0}%
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Completion</div>
                    </div>
                  </div>
                ) : (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    Context available when an active project is selected.
                  </div>
                )}
              </CardBody>
            </Card>

            {/* Workflow Studio Summary */}
            <Card style={{ background: 'var(--bg-glass-card)' }}>
              <CardHeader>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <PlayCircle size={18} color="var(--sdlc-design)" />
                  <span style={{ fontWeight: 600 }}>Multi-Agent Pipelines</span>
                </div>
                {onNavigate && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => onNavigate('workflows')}
                  >
                    Open Studio
                  </Button>
                )}
              </CardHeader>
              <CardBody>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    <strong>{workflows.length}</strong> Deterministic Workflows Registered:
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                    {workflows.map((w) => (
                      <span
                        key={w.workflow_id}
                        style={{
                          fontSize: '0.7rem',
                          padding: '0.2rem 0.5rem',
                          borderRadius: 'var(--radius-sm)',
                          background: 'var(--bg-surface)',
                          border: '1px solid var(--border-subtle)',
                          fontFamily: 'monospace',
                        }}
                      >
                        {w.workflow_id} ({w.step_count} steps)
                      </span>
                    ))}
                  </div>
                </div>
              </CardBody>
            </Card>
          </div>

          {/* Recent Executions Strip (if project selected) */}
          {selectedProjectId && (
            <Card style={{ background: 'var(--bg-glass-card)' }}>
              <CardHeader>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <History size={18} color="var(--accent-primary)" />
                  <span style={{ fontWeight: 600 }}>Recent Multi-Agent Executions</span>
                </div>
                {onNavigate && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => onNavigate('history')}
                  >
                    Full History
                  </Button>
                )}
              </CardHeader>
              <CardBody>
                {historyData?.items && historyData.items.length > 0 ? (
                  <div className="table-container">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Workflow</th>
                          <th>Status</th>
                          <th>Steps</th>
                          <th>Execution ID</th>
                          <th>Executed At</th>
                        </tr>
                      </thead>
                      <tbody>
                        {historyData.items.slice(0, 5).map((run) => (
                          <tr key={run.workflow_execution_id}>
                            <td style={{ fontWeight: 600, fontFamily: 'monospace' }}>
                              {run.workflow_id}
                            </td>
                            <td>
                              <Badge variant={run.status}>{run.status}</Badge>
                            </td>
                            <td style={{ fontSize: '0.8rem' }}>
                              {run.completed_steps}/{run.step_count} completed
                            </td>
                            <td style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                              {run.workflow_execution_id}
                            </td>
                            <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                              {new Date(run.started_at).toLocaleString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    No workflow runs recorded yet for this project. Execute a workflow in Workflow Studio.
                  </div>
                )}
              </CardBody>
            </Card>
          )}

          {/* Capability Matrix: Active Platform Capabilities */}
          <Card style={{ background: 'var(--bg-glass-card)' }}>
            <CardHeader>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Zap size={18} color="var(--accent-cyan)" />
                <span style={{ fontWeight: 600 }}>SE IntelliPlatform Capability Matrix</span>
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Active Platform Capabilities
              </span>
            </CardHeader>
            <CardBody>
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Capability Area</th>
                      <th>SDLC Stage</th>
                      <th>Status</th>
                      <th>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {capabilityRoadmap.map((item, idx) => (
                      <tr key={idx}>
                        <td style={{ fontWeight: 600, fontSize: '0.85rem' }}>{item.capability}</td>
                        <td style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>
                          {item.sdlcStage}
                        </td>
                        <td>
                          <CapabilityBadge status={item.status} size="sm" />
                        </td>
                        <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                          {item.description}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardBody>
          </Card>
        </>
      )}

      {/* Create Project Modal */}
      <CreateProjectModal
        isOpen={isCreateProjectOpen}
        onClose={() => setIsCreateProjectOpen(false)}
        onSubmit={async (data) => {
          await createProjectMutation.mutateAsync(data);
        }}
      />
    </div>
  );
};
