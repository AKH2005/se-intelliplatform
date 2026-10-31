import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../context/AuthContext';
import { ProjectProvider } from '../context/ProjectContext';
import { ModeProvider, MODE_STORAGE_KEY } from '../context/ModeContext';
import { App } from '../App';
import { ProjectResponse } from '../types/project';
import { authApi } from '../services/authApi';
import { projectsApi } from '../services/projectsApi';

const mockProjects: ProjectResponse[] = [
  {
    id: 'proj-omega-101',
    name: 'EventPulse Analytics',
    slug: 'eventpulse-analytics',
    description: 'Real-time telemetry and event monitoring platform.',
    status: 'IN_PROGRESS',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'proj-beta-202',
    name: 'CloudTask Scheduler',
    slug: 'cloudtask-scheduler',
    description: 'Distributed microservice task runner.',
    status: 'DRAFT',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const mockUser = {
  id: 'user-777',
  name: 'Dev Lead',
  email: 'lead@example.com',
  role: 'developer' as const,
  is_active: true,
  created_at: new Date().toISOString(),
};

function renderAppWithProviders(initialLocalStorage?: Record<string, string>) {
  localStorage.clear();
  localStorage.setItem('se_auth_token', 'test-jwt-token');
  if (initialLocalStorage) {
    Object.entries(initialLocalStorage).forEach(([k, v]) => {
      localStorage.setItem(k, v);
    });
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
          <ModeProvider>
            <App />
          </ModeProvider>
        </ProjectProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

describe('Phase 2: Mode Selection and Switching', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    window.history.replaceState({}, '', '/projects');

    vi.spyOn(authApi, 'getMe').mockResolvedValue(mockUser);
    vi.spyOn(projectsApi, 'list').mockResolvedValue(mockProjects);
  });

  it('1. Displays Mode Selection Screen on first use when no mode is in localStorage', async () => {
    renderAppWithProviders();

    // Mode selection screen appears
    expect(await screen.findByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Select Your Experience')).toBeInTheDocument();
    expect(screen.getByText('How would you like to work today?')).toBeInTheDocument();

    // User Mode card
    expect(screen.getByText(/“Your ideas. Your AI. Your possibilities.”/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /enter user mode/i })).toBeInTheDocument();

    // Developer Mode card
    expect(screen.getByText(/“Your workspace. Your code. Your control.”/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /enter developer mode/i })).toBeInTheDocument();
  });

  it('2. Selecting User Mode on first use updates localStorage and displays User Mode interface', async () => {
    renderAppWithProviders();

    const enterUserBtn = await screen.findByRole('button', { name: /enter user mode/i });
    fireEvent.click(enterUserBtn);

    // Mode is persisted in localStorage
    expect(localStorage.getItem(MODE_STORAGE_KEY)).toBe('user');

    // Welcoming User Mode workspace is displayed
    await waitFor(() => {
      expect(screen.getByText(/user mode active/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /create new project/i })).toBeInTheDocument();
      expect(screen.getByText(/your applications & projects/i)).toBeInTheDocument();
    });
  });

  it('3. Selecting Developer Mode on first use updates localStorage and displays Developer Mode workspace', async () => {
    renderAppWithProviders();

    const enterDevBtn = await screen.findByRole('button', { name: /enter developer mode/i });
    fireEvent.click(enterDevBtn);

    // Mode is persisted in localStorage
    expect(localStorage.getItem(MODE_STORAGE_KEY)).toBe('developer');

    // AppShell and SDLC tools are displayed
    await waitFor(() => {
      expect(screen.getByRole('banner')).toBeInTheDocument();
      expect(screen.getByRole('radio', { name: /switch to developer mode/i })).toHaveAttribute(
        'aria-checked',
        'true'
      );
    });
  });

  it('4. Restores Developer Mode automatically on later visits when stored in localStorage', async () => {
    window.history.replaceState({}, '', `/projects/${mockProjects[0].id}/workspace`);
    renderAppWithProviders({
      [MODE_STORAGE_KEY]: 'developer',
      se_intelliplatform_active_project_id: mockProjects[0].id,
    });

    // Should NOT show the first-time modal dialog
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    // Should directly render the Developer Mode workspace
    await waitFor(() => {
      expect(screen.getByRole('radio', { name: /switch to developer mode/i })).toHaveAttribute(
        'aria-checked',
        'true'
      );
      expect(screen.getByTitle(mockProjects[0].name)).toBeInTheDocument();
    });
  });

  it('5. Restores User Mode automatically on later visits when stored in localStorage', async () => {
    renderAppWithProviders({
      [MODE_STORAGE_KEY]: 'user',
    });

    // Should NOT show the first-time modal dialog
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    // Should directly render User Mode
    expect(screen.getByText(/user mode active/i)).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /switch to user mode/i })).toHaveAttribute(
      'aria-checked',
      'true'
    );
  });

  it('6. Allows switching modes via Header Mode Switcher without losing the selected project', async () => {
    window.history.replaceState({}, '', `/projects/${mockProjects[0].id}/workspace`);
    renderAppWithProviders({
      [MODE_STORAGE_KEY]: 'developer',
      se_intelliplatform_active_project_id: mockProjects[0].id,
    });

    // 1. Verify initially in Developer Mode with project active
    await waitFor(() => {
      expect(screen.getByTitle(mockProjects[0].name)).toBeInTheDocument();
      expect(screen.getByRole('radio', { name: /switch to developer mode/i })).toHaveAttribute(
        'aria-checked',
        'true'
      );
    });

    // 2. Switch to User Mode
    const userModeBtn = screen.getByRole('radio', { name: /switch to user mode/i });
    fireEvent.click(userModeBtn);

    // Verify User Mode is rendered and localStorage updated
    await waitFor(() => {
      expect(screen.getByText(/user mode active/i)).toBeInTheDocument();
      expect(localStorage.getItem(MODE_STORAGE_KEY)).toBe('user');
    });

    // Verify selected project is preserved in localStorage
    expect(localStorage.getItem('se_intelliplatform_active_project_id')).toBe(mockProjects[0].id);

    // 3. Switch back to Developer Mode
    const devModeBtn = screen.getByRole('radio', { name: /switch to developer mode/i });
    fireEvent.click(devModeBtn);

    // Verify back in Developer Mode with the same project still active
    await waitFor(() => {
      expect(screen.getByTitle(mockProjects[0].name)).toBeInTheDocument();
      expect(localStorage.getItem(MODE_STORAGE_KEY)).toBe('developer');
    });
  });

  it('7. Handles invalid or corrupted localStorage values safely by prompting mode selection', async () => {
    renderAppWithProviders({
      [MODE_STORAGE_KEY]: 'corrupted_random_json_{invalid}',
    });

    // Does not crash, purges invalid value, and displays the Mode Selection Screen
    expect(await screen.findByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Select Your Experience')).toBeInTheDocument();
    expect(localStorage.getItem(MODE_STORAGE_KEY)).toBeNull();
  });

  it('8. Supports re-opening Mode Selection overview from Header and dismissing if mode is already set', async () => {
    renderAppWithProviders({
      [MODE_STORAGE_KEY]: 'developer',
      se_intelliplatform_active_project_id: mockProjects[0].id,
    });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /open mode selection screen/i })).toBeInTheDocument();
    });

    // Click mode selection trigger in Header
    fireEvent.click(screen.getByRole('button', { name: /open mode selection screen/i }));

    // Modal opens with close button
    expect(await screen.findByRole('dialog')).toBeInTheDocument();
    const closeBtn = screen.getByRole('button', { name: /close mode selection/i });
    expect(closeBtn).toBeInTheDocument();

    // Click close
    fireEvent.click(closeBtn);

    // Modal closes
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });
});
