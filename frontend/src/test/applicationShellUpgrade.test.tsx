import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../context/AuthContext';
import { ProjectProvider } from '../context/ProjectContext';
import { ModeProvider } from '../context/ModeContext';
import { AppShell } from '../components/layout/AppShell';
import { Sidebar } from '../components/layout/Sidebar';
import { Header, HeaderModeSwitcher } from '../components/layout/Header';
import { ProjectResponse } from '../types/project';
import { authApi } from '../services/authApi';
import { projectsApi } from '../services/projectsApi';

const mockProjects: ProjectResponse[] = [
  {
    id: 'proj-shell-1',
    name: 'Apollo Telemetry Engine',
    slug: 'apollo-telemetry-engine',
    description: 'High-throughput telemetry ingestion pipeline.',
    status: 'IN_PROGRESS',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'proj-shell-2',
    name: 'Helios Microservice',
    slug: 'helios-microservice',
    description: 'Distributed microservice cluster.',
    status: 'DRAFT',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const mockUser = {
  id: 'user-shell-dev',
  name: 'Senior Architect',
  email: 'architect@example.com',
  role: 'developer' as const,
  is_active: true,
  created_at: new Date().toISOString(),
};

function renderWithShellProviders(ui: React.ReactElement, initialProjectId?: string) {
  localStorage.clear();
  localStorage.setItem('se_auth_token', 'test-token');
  if (initialProjectId) {
    localStorage.setItem('se_intelliplatform_active_project_id', initialProjectId);
  }

  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ProjectProvider>
          <ModeProvider>{ui}</ModeProvider>
        </ProjectProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

describe('S-Tier Upgrade: Application Shell (Header, Sidebar, AppShell)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    vi.spyOn(authApi, 'getMe').mockResolvedValue(mockUser);
    vi.spyOn(projectsApi, 'list').mockResolvedValue(mockProjects);
  });

  it('1. AppShell renders Header, Sidebar, main viewport, and toggles Assistant Dock', async () => {
    const handleSelectTab = vi.fn();
    const handleOpenCreateProject = vi.fn();

    renderWithShellProviders(
      <AppShell
        activeTab="overview"
        onSelectTab={handleSelectTab}
        projects={mockProjects}
        onOpenCreateProject={handleOpenCreateProject}
      >
        <div data-testid="test-main-content">Engineering Workspace View</div>
      </AppShell>,
      mockProjects[0].id
    );

    // Verify main content rendered
    expect(screen.getByTestId('test-main-content')).toBeInTheDocument();
    expect(screen.getByText('Engineering Workspace View')).toBeInTheDocument();

    // Verify Header is rendered with banner role
    expect(screen.getByRole('banner')).toBeInTheDocument();

    // Verify Sidebar is rendered with navigation role
    expect(screen.getByRole('navigation', { name: /main navigation/i })).toBeInTheDocument();

    // Toggle assistant dock
    const assistantBtn = screen.getByRole('button', { name: /Toggle Intelli Assistant/i });
    expect(assistantBtn).toBeInTheDocument();
    fireEvent.click(assistantBtn);

    // Verify dock opens
    expect(screen.getAllByText('Intelli Assistant').length).toBeGreaterThanOrEqual(1);

    // Close dock
    const closeBtn = screen.getByRole('button', { name: /Close Intelli Assistant/i });
    fireEvent.click(closeBtn);
    expect(screen.queryByText('Assistant Ready')).not.toBeInTheDocument();
  });

  it('2. Sidebar organizes all 14 tools into PROJECT, DEVELOPMENT, and INTELLIGENCE groups with capability badges', () => {
    const handleSelect = vi.fn();

    renderWithShellProviders(
      <Sidebar
        activeTab="overview"
        onSelectTab={handleSelect}
        hasActiveProject={true}
        isCollapsed={false}
      />
    );

    // Verify 3 distinct group headings
    expect(screen.getByText('PROJECT')).toBeInTheDocument();
    expect(screen.getByText('DEVELOPMENT')).toBeInTheDocument();
    expect(screen.getByText('INTELLIGENCE')).toBeInTheDocument();

    // Verify tools under PROJECT
    expect(screen.getByText('Projects')).toBeInTheDocument();
    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('Code Studio')).toBeInTheDocument();
    expect(screen.getByText('IDE')).toBeInTheDocument();
    expect(screen.getByText('Live Preview')).toBeInTheDocument();
    expect(screen.getByText('LIVE')).toBeInTheDocument();
    expect(screen.getByText('AI Development Assistant')).toBeInTheDocument();

    // Verify tools under DEVELOPMENT
    expect(screen.getByText('Code & Versions')).toBeInTheDocument();
    expect(screen.getByText('Requirements & Specs')).toBeInTheDocument();
    expect(screen.getByText('Testing & Quality')).toBeInTheDocument();
    expect(screen.getByText('Code Intelligence')).toBeInTheDocument();

    // Verify tools under INTELLIGENCE
    expect(screen.getByText('Artifacts & Intelligence')).toBeInTheDocument();
    expect(screen.getByText('Issues & Triage')).toBeInTheDocument();
    expect(screen.getByText('Workflow Studio')).toBeInTheDocument();
    expect(screen.getByText('Environments & Deploy')).toBeInTheDocument();
    expect(screen.getByText('Run History')).toBeInTheDocument();

    // Verify footer status
    expect(screen.getByText('Studio Ready')).toBeInTheDocument();
    expect(screen.getByText('v2.0')).toBeInTheDocument();

    // Click a navigation tab
    fireEvent.click(screen.getByText('Code Studio'));
    expect(handleSelect).toHaveBeenCalledWith('code-studio');
  });

  it('3. Sidebar supports collapse and expansion with accessible aria labels', () => {
    const handleToggleCollapse = vi.fn();

    const { rerender } = renderWithShellProviders(
      <Sidebar
        activeTab="overview"
        onSelectTab={() => {}}
        hasActiveProject={true}
        isCollapsed={false}
        onToggleCollapse={handleToggleCollapse}
      />
    );

    // Initial state: expanded
    const collapseBtn = screen.getByRole('button', { name: /Collapse sidebar/i });
    expect(collapseBtn).toBeInTheDocument();
    fireEvent.click(collapseBtn);
    expect(handleToggleCollapse).toHaveBeenCalledTimes(1);

    // Rerender as collapsed
    rerender(
      <QueryClientProvider client={new QueryClient()}>
        <AuthProvider>
          <ProjectProvider>
            <ModeProvider>
              <Sidebar
                activeTab="overview"
                onSelectTab={() => {}}
                hasActiveProject={true}
                isCollapsed={true}
                onToggleCollapse={handleToggleCollapse}
              />
            </ModeProvider>
          </ProjectProvider>
        </AuthProvider>
      </QueryClientProvider>
    );

    // Now has expand button
    expect(screen.getByRole('button', { name: /Expand sidebar/i })).toBeInTheDocument();
    // Labels are collapsed
    expect(screen.queryByText('Studio Ready')).not.toBeInTheDocument();
  });

  it('4. Header Mode Switcher enables toggling between User Mode and Developer Mode with keyboard roles', () => {
    renderWithShellProviders(<HeaderModeSwitcher />);

    const radiogroup = screen.getByRole('radiogroup', { name: /Experience Mode Switcher/i });
    expect(radiogroup).toBeInTheDocument();

    const userRadio = screen.getByRole('radio', { name: /Switch to User Mode/i });
    const devRadio = screen.getByRole('radio', { name: /Switch to Developer Mode/i });

    expect(userRadio).toBeInTheDocument();
    expect(devRadio).toBeInTheDocument();

    // Mode overview modal trigger
    expect(screen.getByTitle('View Mode Selection Overview')).toBeInTheDocument();

    // Switch mode
    fireEvent.click(userRadio);
    expect(userRadio).toHaveAttribute('aria-checked', 'true');

    fireEvent.click(devRadio);
    expect(devRadio).toHaveAttribute('aria-checked', 'true');
  });

  it('5. Workspace Header provides Breadcrumbs, status badge, Live Preview, and More menu', async () => {
    const handleNavigate = vi.fn();
    const handleCreateTask = vi.fn();

    renderWithShellProviders(
      <Header
        activeTab="overview"
        projects={mockProjects}
        onOpenCreateProject={() => {}}
        onNavigateTab={handleNavigate}
        onOpenCreateTask={handleCreateTask}
      />,
      mockProjects[0].id
    );

    // Breadcrumbs
    expect(screen.getByTitle('Return to Projects List')).toBeInTheDocument();
    expect(screen.getByTitle(mockProjects[0].name)).toBeInTheDocument();

    // Status badge
    expect(screen.getByText('IN_PROGRESS')).toBeInTheDocument();

    // Live Preview button
    const previewBtn = screen.getByRole('button', { name: /live preview/i });
    expect(previewBtn).toBeInTheDocument();
    fireEvent.click(previewBtn);
    expect(handleNavigate).toHaveBeenCalledWith('preview');

    // More Actions menu
    const moreBtn = screen.getByTitle('More actions');
    expect(moreBtn).toBeInTheDocument();
    fireEvent.click(moreBtn);

    // More menu dropdown items
    expect(screen.getByText('Add Feature with AI')).toBeInTheDocument();
    expect(screen.getByText('Download Code (ZIP)')).toBeInTheDocument();
    expect(screen.getByText('Rename Project')).toBeInTheDocument();
    expect(screen.getByText('Archive Project')).toBeInTheDocument();

    // Click Add Feature with AI
    fireEvent.click(screen.getByText('Add Feature with AI'));
    expect(handleCreateTask).toHaveBeenCalledTimes(1);
  });
});

