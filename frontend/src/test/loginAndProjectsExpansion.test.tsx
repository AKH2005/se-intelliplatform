import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../context/AuthContext';
import { ProjectProvider } from '../context/ProjectContext';
import { App } from '../App';
import { Header } from '../components/layout/Header';
import { ProjectsView } from '../views/ProjectsView';
import { LoginView } from '../views/auth/LoginView';
import { authApi } from '../services/authApi';
import { projectsApi } from '../services/projectsApi';
import { ProjectResponse } from '../types/project';

const mockProjects: ProjectResponse[] = [
  {
    id: 'proj-1-short',
    name: 'EventHub Starter',
    slug: 'eventhub-starter',
    description: 'A compact event discovery platform.',
    status: 'IN_PROGRESS',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'proj-2-long',
    name: 'TaskFlow Enterprise',
    slug: 'taskflow-enterprise',
    description: `### Comprehensive Project Specification
TaskFlow Enterprise is an end-to-end task and engineering workflow system.
It features hierarchical project breakdowns, sprint capacity planning, automated GitHub branch synchronization,
interactive kanban boards, real-time web socket notifications, audit logs, and customizable dashboard widgets.`,
    status: 'DRAFT',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const mockUser = {
  id: 'user-123',
  name: 'Alex Morgan',
  email: 'alex@example.com',
  role: 'developer' as const,
  is_active: true,
  created_at: new Date().toISOString(),
};

function renderWithAuthAndQuery(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ProjectProvider>{ui}</ProjectProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

describe('Phase 2, 3, & 4: Login, Header Simplification, & Expandable Descriptions', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    window.history.replaceState({}, '', '/');
  });

  it('1. Displays LoginView as the default entry point when unauthenticated on "/"', async () => {
    vi.spyOn(authApi, 'getMe').mockRejectedValue(new Error('Unauthenticated'));

    renderWithAuthAndQuery(<App />);

    // Should render LoginView
    expect(await screen.findByRole('heading', { name: /welcome back/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in to workspace/i })).toBeInTheDocument();
  });

  it('2. LoginView supports password visibility toggle and switching to Register mode', async () => {
    render(<LoginView initialMode="login" />);

    const passwordInput = screen.getByLabelText(/password/i);
    expect(passwordInput).toHaveAttribute('type', 'password');

    // Toggle password visibility
    const toggleBtn = screen.getByTitle(/show password/i);
    fireEvent.click(toggleBtn);
    expect(passwordInput).toHaveAttribute('type', 'text');

    // Switch to Register mode
    const registerTab = screen.getByRole('button', { name: /register/i });
    fireEvent.click(registerTab);

    expect(screen.getByRole('heading', { name: /create your account/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create account & continue/i })).toBeInTheDocument();
  });

  it('3. Successful login persists token and resolves session', async () => {
    vi.spyOn(authApi, 'login').mockResolvedValue({
      access_token: 'valid-test-jwt-token',
      token_type: 'bearer',
      user: mockUser,
    });
    vi.spyOn(projectsApi, 'list').mockResolvedValue(mockProjects);

    const handleSuccess = vi.fn();
    renderWithAuthAndQuery(<LoginView onSuccess={handleSuccess} />);

    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'alex@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'Secret123!' },
    });

    fireEvent.click(screen.getByRole('button', { name: /sign in to workspace/i }));

    await waitFor(() => {
      expect(handleSuccess).toHaveBeenCalled();
      expect(localStorage.getItem('se_auth_token')).toBe('valid-test-jwt-token');
    });
  });

  it('4. Projects page header displays simplified layout without project-specific actions', () => {
    renderWithAuthAndQuery(
      <Header
        activeTab="projects"
        projects={mockProjects}
        onOpenCreateProject={() => {}}
      />
    );

    // Displays brand and New Project button
    expect(screen.getByText('SE IntelliPlatform')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /new project/i })).toBeInTheDocument();

    // Does NOT display workspace actions like Live Preview or More Actions in the Projects header
    expect(screen.queryByRole('button', { name: /live preview/i })).not.toBeInTheDocument();
  });

  it('5. Workspace header displays Breadcrumbs, compact status, Live Preview, and More menu', () => {
    const handleNavigate = vi.fn();
    const handleCreateTask = vi.fn();

    // Simulate active project in localStorage
    localStorage.setItem('se_intelliplatform_active_project_id', mockProjects[0].id);

    renderWithAuthAndQuery(
      <Header
        activeTab="overview"
        projects={mockProjects}
        onOpenCreateProject={() => {}}
        onNavigateTab={handleNavigate}
        onOpenCreateTask={handleCreateTask}
      />
    );

    // Breadcrumbs
    expect(screen.getByTitle('Return to Projects List')).toBeInTheDocument();
    expect(screen.getByTitle(mockProjects[0].name)).toBeInTheDocument();

    // Live Preview Action
    const previewBtn = screen.getByRole('button', { name: /live preview/i });
    expect(previewBtn).toBeInTheDocument();
    fireEvent.click(previewBtn);
    expect(handleNavigate).toHaveBeenCalledWith('preview');

    // More Actions Menu
    const moreBtn = screen.getByTitle('More actions');
    expect(moreBtn).toBeInTheDocument();
    fireEvent.click(moreBtn);

    // Dropdown contains secondary items
    expect(screen.getByText(/add feature with ai/i)).toBeInTheDocument();
    expect(screen.getByText(/download code \(zip\)/i)).toBeInTheDocument();
    expect(screen.getByText(/rename project/i)).toBeInTheDocument();
    expect(screen.getByText(/archive project/i)).toBeInTheDocument();
  });

  it('6. Project cards truncate long descriptions and support per-card expand / collapse', async () => {
    vi.spyOn(projectsApi, 'list').mockResolvedValue(mockProjects);

    renderWithAuthAndQuery(
      <ProjectsView onOpenWorkspace={() => {}} onOpenCreateProject={() => {}} />
    );

    // Short project description is rendered directly without an expand button
    expect(await screen.findByText('EventHub Starter')).toBeInTheDocument();
    expect(screen.getByText('A compact event discovery platform.')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /show more description for EventHub Starter/i })).not.toBeInTheDocument();

    // Long project description has "Show more" button and stripped raw markdown headings
    expect(screen.getByText('TaskFlow Enterprise')).toBeInTheDocument();
    const showMoreBtn = screen.getByRole('button', { name: /show more description for TaskFlow Enterprise/i });
    expect(showMoreBtn).toBeInTheDocument();
    expect(showMoreBtn).toHaveTextContent('Show more');

    // Click "Show more" to expand description
    fireEvent.click(showMoreBtn);

    // Should now show "Show less"
    expect(screen.getByRole('button', { name: /show less description for TaskFlow Enterprise/i })).toHaveTextContent('Show less');

    // Click "Show less" to collapse back
    const showLessBtn = screen.getByRole('button', { name: /show less description for TaskFlow Enterprise/i });
    fireEvent.click(showLessBtn);
    expect(screen.getByRole('button', { name: /show more description for TaskFlow Enterprise/i })).toHaveTextContent('Show more');
  });
});
