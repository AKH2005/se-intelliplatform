import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ProjectProvider } from '../context/ProjectContext';
import { ProjectWorkspace } from '../views/ProjectWorkspace';
import { RequirementsWorkspace } from '../views/RequirementsWorkspace';
import { WorkflowStudio } from '../views/WorkflowStudio';
import { RunHistory } from '../views/RunHistory';
import { projectsApi } from '../services/projectsApi';
import { requirementsApi } from '../services/requirementsApi';
import { contextApi } from '../services/contextApi';
import { workflowsApi } from '../services/workflowsApi';
import { historyApi } from '../services/historyApi';
import { WorkflowResultResponse } from '../types/workflow';

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <ProjectProvider>{ui}</ProjectProvider>
    </QueryClientProvider>
  );
}

describe('Frontend Workspaces and Component Flows', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it('Project Workspace: renders empty state when no projects exist', async () => {
    vi.spyOn(projectsApi, 'list').mockResolvedValue([]);

    renderWithProviders(<ProjectWorkspace />);

    expect(await screen.findByText('Create your first project to begin')).toBeInTheDocument();
  });

  it('Project Workspace: renders project cards and context stats when project is present', async () => {
    const mockProjects = [
      {
        id: 'proj-1',
        name: 'Alpha Project',
        slug: 'alpha-project',
        description: 'First test project',
        status: 'IN_PROGRESS' as const,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ];

    const mockContext = {
      project: mockProjects[0],
      requirements: [],
      statistics: {
        total_requirements: 4,
        active_requirements: 3,
        functional_count: 2,
        non_functional_count: 1,
        constraint_count: 0,
        by_priority: {},
        by_status: {},
        completion_percentage: 66.7,
      },
      context_version: 1,
      generated_at: new Date().toISOString(),
    };

    localStorage.setItem('se_intelliplatform_active_project_id', 'proj-1');

    vi.spyOn(projectsApi, 'list').mockResolvedValue(mockProjects);
    vi.spyOn(contextApi, 'getContext').mockResolvedValue(mockContext);
    vi.spyOn(contextApi, 'listSnapshots').mockResolvedValue([]);

    renderWithProviders(<ProjectWorkspace />);

    expect(await screen.findByText('Alpha Project')).toBeInTheDocument();
    expect(await screen.findByText('66.7%')).toBeInTheDocument();
    expect(screen.getByText('Canonical Project Context')).toBeInTheDocument();
  });

  it('Requirements Workspace: renders requirements and handles empty state', async () => {
    localStorage.setItem('se_intelliplatform_active_project_id', 'proj-1');

    vi.spyOn(requirementsApi, 'list').mockResolvedValue([
      {
        id: 'req-1',
        project_id: 'proj-1',
        title: 'User Login with JWT',
        description: 'System must issue secure RS256 JWT tokens.',
        type: 'FUNCTIONAL',
        priority: 'HIGH',
        status: 'APPROVED',
        is_archived: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]);

    renderWithProviders(<RequirementsWorkspace />);

    expect(await screen.findByText('User Login with JWT')).toBeInTheDocument();
    expect(screen.getAllByText('FUNCTIONAL').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('HIGH')).toBeInTheDocument();
  });

  it('Workflow Studio: discovers workflows, displays runner, and synchronously shows execution results', async () => {
    localStorage.setItem('se_intelliplatform_active_project_id', 'proj-1');

    const mockWorkflows = [
      {
        workflow_id: 'software-design',
        version: '1.0.0',
        name: 'Software Design Workflow',
        description: 'Analyzes requirements, generates architecture, and models database schemas.',
        step_count: 3,
        steps: [
          { step_id: 'step-req-analysis', agent_id: 'requirement-analysis', required: true, depends_on: [] },
          { step_id: 'step-arch-rec', agent_id: 'architecture-recommendation', required: true, depends_on: ['step-req-analysis'] },
          { step_id: 'step-db-design', agent_id: 'database-design', required: true, depends_on: ['step-arch-rec'] },
        ],
        required_inputs: ['project_id'],
        optional_inputs: ['snapshot_id'],
      },
    ];

    const mockExecutionResult: WorkflowResultResponse = {
      workflow_execution_id: 'exec-1234-abcd',
      workflow_id: 'software-design',
      workflow_version: '1.0.0',
      status: 'COMPLETED',
      started_at: '2026-09-28T12:00:00Z',
      completed_at: '2026-09-28T12:00:05Z',
      step_results: [
        {
          step_id: 'step-req-analysis',
          agent_id: 'requirement-analysis',
          status: 'COMPLETED',
        },
      ],
      artifacts: {
        'step-req-analysis': {
          summary: 'Software design analysis completed successfully.',
          ambiguities: [],
          conflicts: [],
          missing_information: [],
          refinements: [],
          scope_clarifications: [],
          completeness_score: 100.0,
          active_requirements_count: 5,
          total_requirements_count: 5,
        },
      },
      errors: [],
      warnings: [],
      metadata: {},
    };

    vi.spyOn(workflowsApi, 'list').mockResolvedValue(mockWorkflows);
    vi.spyOn(contextApi, 'listSnapshots').mockResolvedValue([]);
    vi.spyOn(workflowsApi, 'execute').mockResolvedValue(mockExecutionResult);

    renderWithProviders(<WorkflowStudio />);

    expect(await screen.findByText('Software Design Workflow')).toBeInTheDocument();
    expect(screen.getByText('Execute Workflow')).toBeInTheDocument();

    // Trigger synchronous execution
    fireEvent.click(screen.getByText('Execute Workflow'));

    expect(await screen.findByText(/Execution Outcome: software-design/i)).toBeInTheDocument();
    expect(screen.getByText('exec-1234-abcd')).toBeInTheDocument();
  });

  it('Run History: renders executions and opens execution detail modal', async () => {
    localStorage.setItem('se_intelliplatform_active_project_id', 'proj-1');

    const mockHistory = {
      items: [
        {
          workflow_execution_id: 'run-9876',
          project_id: 'proj-1',
          workflow_id: 'software-design',
          workflow_version: '1.0.0',
          status: 'COMPLETED' as const,
          started_at: new Date().toISOString(),
          completed_at: new Date().toISOString(),
          context_snapshot_id: null,
          context_version: 1,
          step_count: 3,
          completed_steps: 3,
          failed_steps: 0,
          skipped_steps: 0,
          error_count: 0,
          warning_count: 0,
          artifact_keys: ['step-req-analysis'],
        },
      ],
      total: 1,
      limit: 50,
      offset: 0,
    };

    vi.spyOn(historyApi, 'listProjectHistory').mockResolvedValue(mockHistory);
    vi.spyOn(historyApi, 'getExecutionDetail').mockResolvedValue({
      workflow_execution_id: 'run-9876',
      project_id: 'proj-1',
      workflow_id: 'software-design',
      workflow_version: '1.0.0',
      status: 'COMPLETED',
      started_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
      context_snapshot_id: null,
      context_version: 1,
      step_count: 3,
      completed_steps: 3,
      failed_steps: 0,
      skipped_steps: 0,
      artifacts: {},
      errors: [],
      warnings: [],
      metadata: {},
    });

    renderWithProviders(<RunHistory />);

    expect(await screen.findByText('software-design')).toBeInTheDocument();
    expect(screen.getByText('Details')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Details'));

    expect(await screen.findByText('Workflow Execution Run Detail')).toBeInTheDocument();
    expect(await screen.findByText(/Run ID: run-9876/i)).toBeInTheDocument();
  });
});
