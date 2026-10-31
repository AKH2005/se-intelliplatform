import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../context/AuthContext';
import { ProjectProvider } from '../context/ProjectContext';
import { ModeProvider, MODE_STORAGE_KEY, MODE_REMEMBER_KEY } from '../context/ModeContext';
import { App } from '../App';
import { authApi } from '../services/authApi';
import { projectsApi } from '../services/projectsApi';
import { ProjectResponse } from '../types/project';

const mockProjects: ProjectResponse[] = [
  {
    id: 'proj-select-1',
    name: 'RealTime Analytics Dashboard',
    slug: 'realtime-analytics-dashboard',
    description: 'High performance metrics aggregation and streaming UI.',
    status: 'IN_PROGRESS',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const mockUser = {
  id: 'user-select-test',
  name: 'Alex Engineer',
  email: 'alex@example.com',
  role: 'developer' as const,
  is_active: true,
  created_at: new Date().toISOString(),
};

function renderAppWithRoute(route: string = '/select-mode') {
  window.history.replaceState({}, '', route);

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

describe('Mode Selection & Routing Specification', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    localStorage.setItem('se_auth_token', 'test-valid-jwt');

    vi.spyOn(authApi, 'getMe').mockResolvedValue(mockUser);
    vi.spyOn(projectsApi, 'list').mockResolvedValue(mockProjects);
  });

  it('1. Displays dedicated Mode Selection screen when navigating to /select-mode without auto-forcing Developer Mode', async () => {
    renderAppWithRoute('/select-mode');

    // Title and Dialog present
    expect(await screen.findByRole('dialog', { name: /how would you like to work today|choose your engineering experience/i })).toBeInTheDocument();
    expect(screen.getByText(/Choose Your Engineering Experience/i)).toBeInTheDocument();

    // Both modes explicitly presented with descriptions
    expect(screen.getByRole('heading', { name: /Beginner Mode/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Developer Mode/i })).toBeInTheDocument();

    // Verify prominent action buttons
    expect(screen.getByTestId('enter-beginner-mode')).toBeInTheDocument();
    expect(screen.getByTestId('enter-developer-mode')).toBeInTheDocument();
  });

  it('2. Selecting Beginner Mode activates user mode and transitions route to /user', async () => {
    renderAppWithRoute('/select-mode');

    const enterBeginnerBtn = await screen.findByTestId('enter-beginner-mode');
    fireEvent.click(enterBeginnerBtn);

    // Verifies route updated to /user
    await waitFor(() => {
      expect(window.location.pathname).toBe('/user');
      expect(localStorage.getItem(MODE_STORAGE_KEY)).toBe('user');
    });

    // Verifies Beginner Mode workspace is rendered
    expect(await screen.findByText(/What would you like to create today\?/i)).toBeInTheDocument();
  });

  it('3. Selecting Developer Mode activates developer mode and transitions route to /projects', async () => {
    renderAppWithRoute('/select-mode');

    const enterDevBtn = await screen.findByTestId('enter-developer-mode');
    fireEvent.click(enterDevBtn);

    // Verifies route updated to /projects
    await waitFor(() => {
      expect(window.location.pathname).toBe('/projects');
      expect(localStorage.getItem(MODE_STORAGE_KEY)).toBe('developer');
    });

    // Verifies Developer Mode AppShell / ProjectsView is rendered
    const matchedElements = await screen.findAllByText(/RealTime Analytics Dashboard/i);
    expect(matchedElements.length).toBeGreaterThanOrEqual(1);
  });

  it('4. Handles "Remember my preference" checkbox correctly', async () => {
    renderAppWithRoute('/select-mode');

    const checkbox = (await screen.findByLabelText(/Remember my mode preference on this device/i)) as HTMLInputElement;
    expect(checkbox.checked).toBe(true);

    // Uncheck remember preference
    fireEvent.click(checkbox);
    expect(checkbox.checked).toBe(false);

    // Select Beginner Mode without remember preference
    const enterBeginnerBtn = screen.getByTestId('enter-beginner-mode');
    fireEvent.click(enterBeginnerBtn);

    await waitFor(() => {
      expect(localStorage.getItem(MODE_STORAGE_KEY)).toBe('user');
      // When remember is unchecked, MODE_REMEMBER_KEY should not be set
      expect(localStorage.getItem(MODE_REMEMBER_KEY)).toBeNull();
    });
  });

  it('5. Switching modes preserves active project context seamlessly', async () => {
    // Start in developer mode with stored preference
    localStorage.setItem(MODE_STORAGE_KEY, 'developer');
    localStorage.setItem(MODE_REMEMBER_KEY, 'true');
    renderAppWithRoute('/projects');

    // Wait for project list to load
    const matched = await screen.findAllByText(/RealTime Analytics Dashboard/i);
    expect(matched.length).toBeGreaterThanOrEqual(1);

    // Switch to User Mode via Header Mode Switcher
    const switchUserBtn = screen.getByRole('radio', { name: /switch to user mode/i });
    fireEvent.click(switchUserBtn);

    // Confirm Beginner Mode opens and retains project context
    await waitFor(() => {
      expect(screen.getByText(/What would you like to create today\?/i)).toBeInTheDocument();
      const userMatched = screen.getAllByText(/RealTime Analytics Dashboard/i);
      expect(userMatched.length).toBeGreaterThanOrEqual(1);
    });
  });
});
