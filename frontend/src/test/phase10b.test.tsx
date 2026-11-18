import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ProjectProvider } from '../context/ProjectContext';
import { AppShell } from '../components/layout/AppShell';
import { Sidebar } from '../components/layout/Sidebar';
import { AssistantDock } from '../components/assistant/AssistantDock';
import { OverviewWorkspace } from '../views/OverviewWorkspace';
import { SpecificationWorkspace } from '../views/SpecificationWorkspace';
import { DevelopmentWorkspace } from '../views/DevelopmentWorkspace';
import { TestingWorkspace } from '../views/TestingWorkspace';
import { IssuesWorkspace } from '../views/IssuesWorkspace';
import { IntelligenceWorkspace } from '../views/IntelligenceWorkspace';
import { projectsApi } from '../services/projectsApi';
import { contextApi } from '../services/contextApi';
import { requirementsApi } from '../services/requirementsApi';
import { workflowsApi } from '../services/workflowsApi';
import { historyApi } from '../services/historyApi';

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

const mockProject = {
  id: 'proj-10b',
  name: 'Orion Gateway',
  slug: 'orion-gateway',
  description: 'Enterprise API gateway and intelligence platform',
  status: 'IN_PROGRESS' as const,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const mockContext = {
  project: mockProject,
  requirements: [],
  statistics: {
    total_requirements: 8,
    active_requirements: 7,
    functional_count: 5,
    non_functional_count: 2,
    constraint_count: 1,
    by_priority: {},
    by_status: {},
    completion_percentage: 87.5,
  },
  context_version: 2,
  generated_at: new Date().toISOString(),
};

describe('Phase 10B: SDLC Information Architecture & UX Foundation', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    localStorage.setItem('se_intelliplatform_active_project_id', 'proj-10b');
  });

  it('Sidebar renders 8 SDLC tabs categorized into PROJECT, DEVELOPMENT, INTELLIGENCE', () => {
    const handleSelect = vi.fn();
    render(
      <Sidebar
        activeTab="overview"
        onSelectTab={handleSelect}
        hasActiveProject={true}
      />
    );

    expect(screen.getByText('PROJECT')).toBeInTheDocument();
    expect(screen.getByText('DEVELOPMENT')).toBeInTheDocument();
    expect(screen.getByText('INTELLIGENCE')).toBeInTheDocument();

    // Verify all 8 primary navigation tabs exist
    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('Specification')).toBeInTheDocument();
    expect(screen.getByText('Development')).toBeInTheDocument();
    expect(screen.getByText('Testing & Quality')).toBeInTheDocument();
    expect(screen.getByText('Issues')).toBeInTheDocument();
    expect(screen.getByText('Intelligence')).toBeInTheDocument();
    expect(screen.getByText('Workflow Studio')).toBeInTheDocument();
    expect(screen.getByText('Run History')).toBeInTheDocument();

    // Clicking a tab triggers navigation callback
    fireEvent.click(screen.getByText('Development'));
    expect(handleSelect).toHaveBeenCalledWith('development');
  });

  it('AppShell toggles Assistant Dock and collapse states', () => {
    renderWithProviders(
      <AppShell
        activeTab="overview"
        onSelectTab={() => {}}
        projects={[mockProject]}
        onOpenCreateProject={() => {}}
      >
        <div>Main Content View</div>
      </AppShell>
    );

    expect(screen.getByText('Main Content View')).toBeInTheDocument();
    expect(screen.queryByText('Intelli Assistant')).not.toBeInTheDocument();

    // Open assistant dock
    const assistantBtn = screen.getByRole('button', { name: /Toggle Intelli Assistant/i });
    fireEvent.click(assistantBtn);

    expect(screen.getAllByText('Intelli Assistant').length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getByText(/Intelli Assistant connects conversational reasoning/i)
    ).toBeInTheDocument();

    // Close assistant dock
    const closeBtn = screen.getByRole('button', { name: /Close Intelli Assistant/i });
    fireEvent.click(closeBtn);
    expect(screen.queryByText('Assistant Ready')).not.toBeInTheDocument();
  });

  it('OverviewWorkspace displays project status, context stats, workflows, and capability matrix', async () => {
    vi.spyOn(projectsApi, 'list').mockResolvedValue([mockProject]);
    vi.spyOn(contextApi, 'getContext').mockResolvedValue(mockContext);
    vi.spyOn(workflowsApi, 'list').mockResolvedValue([
      {
        workflow_id: 'software-design',
        version: '1.0.0',
        name: 'Software Design',
        description: 'Design pipeline',
        step_count: 3,
        steps: [],
        required_inputs: [],
        optional_inputs: [],
      },
    ]);
    vi.spyOn(historyApi, 'listProjectHistory').mockResolvedValue({
      items: [],
      total: 0,
      limit: 10,
      offset: 0,
    });

    renderWithProviders(<OverviewWorkspace />);

    expect(await screen.findByText('Project Overview')).toBeInTheDocument();
    expect(await screen.findByText('Orion Gateway')).toBeInTheDocument();
    expect(await screen.findByText('87.5%')).toBeInTheDocument();
    expect(screen.getByText('SE IntelliPlatform Capability Matrix')).toBeInTheDocument();
    expect(screen.getByText('Requirements Management')).toBeInTheDocument();
    expect(screen.getByText('Code Generation Engine')).toBeInTheDocument();
  });

  it('SpecificationWorkspace renders unified Requirements, Context, Snapshots, and Blueprints', async () => {
    vi.spyOn(requirementsApi, 'list').mockResolvedValue([
      {
        id: 'req-spec-1',
        project_id: 'proj-10b',
        title: 'OAuth 2.0 PKCE Flow',
        description: 'Client authentication',
        type: 'FUNCTIONAL',
        priority: 'CRITICAL',
        status: 'APPROVED',
        is_archived: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]);
    vi.spyOn(contextApi, 'getContext').mockResolvedValue(mockContext);
    vi.spyOn(contextApi, 'listSnapshots').mockResolvedValue([
      {
        id: 'snap-1',
        project_id: 'proj-10b',
        version: 1,
        summary: 'Milestone Alpha',
        context_data: { project_id: 'proj-10b', project_name: 'Orion Gateway', requirements: [] },
        created_at: new Date().toISOString(),
      },
    ]);

    renderWithProviders(<SpecificationWorkspace />);

    expect(await screen.findByText('Specification & Context Workspace')).toBeInTheDocument();
    expect(await screen.findByText('OAuth 2.0 PKCE Flow')).toBeInTheDocument();

    // Switch to Snapshots tab
    fireEvent.click(screen.getByRole('tab', { name: /Versioned Snapshots/i }));
    expect(await screen.findByText('Milestone Alpha')).toBeInTheDocument();

    // Switch to Blueprints tab
    fireEvent.click(screen.getByRole('tab', { name: /Architecture & ERD Blueprints/i }));
    expect(screen.getByText('SE IntelliPlatform System Topology')).toBeInTheDocument();
    expect(screen.getByText('Core Domain Schema (Entity Relationship)')).toBeInTheDocument();
  });

  it('DevelopmentWorkspace displays BUILD, RUN, MODIFY, VERSION stages', () => {
    renderWithProviders(<DevelopmentWorkspace />);

    expect(screen.getByText('Development Workspace')).toBeInTheDocument();
    expect(screen.getByText('BUILD')).toBeInTheDocument();
    expect(screen.getByText('RUN')).toBeInTheDocument();
    expect(screen.getByText('MODIFY')).toBeInTheDocument();
    expect(screen.getByText('VERSION')).toBeInTheDocument();
    expect(
      screen.getByText(/Continuous Engineering Pipeline Active/i)
    ).toBeInTheDocument();
    expect(screen.queryByText('Development Workspace Layout Preview')).not.toBeInTheDocument();
  });

  it('TestingWorkspace clearly distinguishes Analysis from Execution', () => {
    vi.spyOn(historyApi, 'listProjectHistory').mockResolvedValue({
      items: [],
      total: 0,
      limit: 10,
      offset: 0,
    });

    renderWithProviders(<TestingWorkspace />);

    expect(screen.getByText('Testing & Quality Workspace')).toBeInTheDocument();
    expect(screen.getByText('Architectural Distinction: Analysis vs Execution')).toBeInTheDocument();

    // Implemented analysis agents are visible
    expect(screen.getByText('Test Case Generation Agent')).toBeInTheDocument();
    expect(screen.getByText('Bug Prediction Agent')).toBeInTheDocument();
    expect(screen.getByText('Code Review Agent')).toBeInTheDocument();

    // Switch to execution tab
    fireEvent.click(screen.getByRole('tab', { name: /Test Execution Engine/i }));
    expect(screen.getByText('Automated Pytest & Jest Sandbox Runner')).toBeInTheDocument();
    expect(screen.getByText('End-to-End Application Testing')).toBeInTheDocument();
  });

  it('IssuesWorkspace renders closed-loop defect lifecycle and honest empty state', () => {
    renderWithProviders(<IssuesWorkspace />);

    expect(screen.getByText('Issues & Debugging Workspace')).toBeInTheDocument();
    expect(screen.getByText('Closed-Loop Defect Remediation Lifecycle')).toBeInTheDocument();
    expect(screen.getByText('No issues have been reported.')).toBeInTheDocument();
    expect(
      screen.getByText(/Issue tracking, evidence collection, AI-assisted debugging/i)
    ).toBeInTheDocument();
  });

  it('IntelligenceWorkspace renders user-centric narrative pillars and artifact viewer', async () => {
    const mockExecution = {
      workflow_execution_id: 'exec-intel-1',
      project_id: 'proj-10b',
      workflow_id: 'software-design',
      workflow_version: '1.0.0',
      status: 'COMPLETED' as const,
      started_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
      step_count: 3,
      completed_steps: 3,
      failed_steps: 0,
      skipped_steps: 0,
      error_count: 0,
      warning_count: 0,
      artifact_keys: ['step-req-analysis'],
    };

    const mockDetail = {
      ...mockExecution,
      context_snapshot_id: null,
      context_version: 1,
      artifacts: {
        'step-req-analysis': {
          summary: 'Requirements are complete and ready for architecture generation.',
          ambiguities: [],
          conflicts: [],
          missing_information: [],
          refinements: [],
          scope_clarifications: [],
          completeness_score: 95.0,
          active_requirements_count: 8,
          total_requirements_count: 8,
        },
      },
      errors: [],
      warnings: [],
      metadata: {},
    };

    vi.spyOn(historyApi, 'listProjectHistory').mockResolvedValue({
      items: [mockExecution],
      total: 1,
      limit: 10,
      offset: 0,
    });
    vi.spyOn(historyApi, 'getExecutionDetail').mockResolvedValue(mockDetail);

    renderWithProviders(<IntelligenceWorkspace />);

    expect(await screen.findByText('Artifacts & Intelligence')).toBeInTheDocument();
    expect(await screen.findByText('1. What Was Analyzed')).toBeInTheDocument();
    expect(screen.getByText('2. What Was Found')).toBeInTheDocument();
    expect(screen.getByText('3. Why It Matters')).toBeInTheDocument();
    expect(screen.getByText('4. What To Do Next')).toBeInTheDocument();

    // Verify artifact viewer rendered the requirement analysis summary
    expect(
      await screen.findByText('Requirements are complete and ready for architecture generation.')
    ).toBeInTheDocument();
  });

  it('IntelliAssistant UI records prompt chips and informs user of future integration without LLM execution', () => {
    render(
      <AssistantDock
        isOpen={true}
        onClose={() => {}}
        activeProjectName="Orion Gateway"
      />
    );

    expect(screen.getByText('Intelli Assistant')).toBeInTheDocument();
    expect(screen.getByText('Assistant Ready for Orion Gateway')).toBeInTheDocument();

    const chipBtn = screen.getByText('Which workflows are available to run?');
    fireEvent.click(chipBtn);

    expect(
      screen.getByText(/Select an active project to enable contextual reasoning/i)
    ).toBeInTheDocument();
  });
});
