import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../context/AuthContext';
import { ProjectProvider } from '../context/ProjectContext';
import { ModeProvider, MODE_STORAGE_KEY } from '../context/ModeContext';
import { App } from '../App';
import { chatApi } from '../services/chatApi';
import { authApi } from '../services/authApi';
import { projectsApi } from '../services/projectsApi';
import { previewRuntimeApi } from '../services/previewRuntimeApi';
import { workflowsApi } from '../services/workflowsApi';
import { ProjectResponse } from '../types/project';

const mockProjects: ProjectResponse[] = [
  {
    id: 'proj-p4-kanban',
    name: 'Real-Time Kanban Task Manager',
    slug: 'kanban-task-manager',
    description: 'A modern Kanban task board with drag-and-drop columns, priority tags, and due dates.',
    status: 'IN_PROGRESS',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const mockUser = {
  id: 'user-p4',
  name: 'Taylor Builder',
  email: 'taylor@example.com',
  role: 'developer' as const,
  is_active: true,
  created_at: new Date().toISOString(),
};

function renderApp(initialMode: 'user' | 'developer' = 'user', initialProjectId?: string) {
  localStorage.clear();
  localStorage.setItem('se_auth_token', 'test-auth-token');
  localStorage.setItem(MODE_STORAGE_KEY, initialMode);
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
          <ModeProvider>
            <App />
          </ModeProvider>
        </ProjectProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

describe('Phase 4: Autonomous Guided App Builder & Template Accelerator', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    window.history.replaceState({}, '', '/projects');

    vi.spyOn(authApi, 'getMe').mockResolvedValue(mockUser);
    vi.spyOn(projectsApi, 'list').mockResolvedValue(mockProjects);
  });

  it('1. Approves a generated application blueprint with synthesized fullstack requirements', async () => {
    vi.spyOn(chatApi, 'synthesizeAppPlan').mockResolvedValue({
      name: 'TaskFlow Pro Kanban',
      slug: 'taskflow-pro-kanban',
      description: 'A full-stack collaborative Kanban board with React and FastAPI.',
      requirements: [
        { title: 'Interactive Kanban Dashboard UI', description: 'React dashboard with drag-and-drop task lanes.', type: 'FUNCTIONAL', priority: 'HIGH' },
        { title: 'RESTful Task CRUD API', description: 'FastAPI backend routes for task state transitions.', type: 'FUNCTIONAL', priority: 'HIGH' },
        { title: 'Docker Preview Sandbox', description: 'Containerized isolated execution on port 8001.', type: 'NON_FUNCTIONAL', priority: 'HIGH' },
      ],
      suggested_features: ['Drag and drop columns', 'Due date alerts'],
    });

    renderApp('user');

    const input = await screen.findByPlaceholderText(/describe what you want to build or ask anything/i);
    fireEvent.change(input, { target: { value: 'Build a fullstack Kanban task manager' } });

    const planBtn = screen.getByRole('button', { name: /plan app/i });
    fireEvent.click(planBtn);

    expect(await screen.findByText('Synthesized Application Blueprint')).toBeInTheDocument();
    expect(screen.getByText('TaskFlow Pro Kanban')).toBeInTheDocument();
    expect(screen.getByText('Interactive Kanban Dashboard UI')).toBeInTheDocument();
    expect(screen.getByText('RESTful Task CRUD API')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create application now/i })).toBeInTheDocument();
  });

  it('2. End-to-end: Creates project, generates code, starts Docker container, verifies health, and displays live preview in User Mode', async () => {
    const createdProject: ProjectResponse = {
      id: 'proj-p4-live-run',
      name: 'TaskFlow Pro Kanban',
      slug: 'taskflow-pro-kanban',
      description: 'A full-stack collaborative Kanban board with React and FastAPI.',
      status: 'IN_PROGRESS',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    vi.spyOn(chatApi, 'synthesizeAppPlan').mockResolvedValue({
      name: 'TaskFlow Pro Kanban',
      slug: 'taskflow-pro-kanban',
      description: 'A full-stack collaborative Kanban board with React and FastAPI.',
      requirements: [
        { title: 'Interactive React Task Dashboard', description: 'React client', type: 'FUNCTIONAL', priority: 'HIGH' },
      ],
      suggested_features: ['Drag and drop'],
    });

    const createSpy = vi.spyOn(projectsApi, 'create').mockResolvedValue(createdProject);
    const workflowSpy = vi.spyOn(workflowsApi, 'execute').mockResolvedValue({
      workflow_execution_id: 'wf-exec-p4',
      workflow_id: 'code-generation-workflow',
      workflow_version: '1.0.0',
      status: 'COMPLETED' as any,
      started_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
      step_results: [],
      artifacts: {
        'code-generation': {
          total_files: 15,
          generated_files: [
            { path: 'frontend/src/App.tsx', size_bytes: 2048, language: 'typescript' },
            { path: 'backend/app/main.py', size_bytes: 1024, language: 'python' },
          ],
        },
      },
      errors: [],
      warnings: [],
      metadata: {},
    });

    const startSpy = vi.spyOn(previewRuntimeApi, 'start').mockResolvedValue({
      status: 'RUNNING',
      port: 8001,
      preview_url: 'http://127.0.0.1:8001/',
      is_healthy: true,
      project_id: createdProject.id,
      project_name: createdProject.name,
      active_mode: 'taskflow',
      detail: 'Application container verified healthy on port 8001.',
      execution_type: 'isolated_container',
      container_status: 'RUNNING',
    });

    const statusSpy = vi.spyOn(previewRuntimeApi, 'getStatus').mockResolvedValue({
      status: 'RUNNING',
      port: 8001,
      preview_url: 'http://127.0.0.1:8001/',
      is_healthy: true,
      project_id: createdProject.id,
      project_name: createdProject.name,
      active_mode: 'taskflow',
      detail: 'Container healthy.',
      execution_type: 'isolated_container',
      container_status: 'RUNNING',
    });

    renderApp('user');

    // 1. Submit prompt & plan app
    const input = await screen.findByPlaceholderText(/describe what you want to build or ask anything/i);
    fireEvent.change(input, { target: { value: 'TaskFlow Pro' } });
    fireEvent.click(screen.getByRole('button', { name: /plan app/i }));

    // 2. Click "Create Application Now"
    const createBtn = await screen.findByRole('button', { name: /create application now/i });
    fireEvent.click(createBtn);

    // 3. Verifies project creation, workflow execution, container start, and status probe
    await waitFor(() => {
      expect(createSpy).toHaveBeenCalled();
      expect(workflowSpy).toHaveBeenCalledWith('code-generation-workflow', expect.objectContaining({
        project_id: createdProject.id,
      }));
      expect(startSpy).toHaveBeenCalledWith(createdProject.id);
      expect(statusSpy).toHaveBeenCalledWith(createdProject.id);
    });

    // 4. Verifies Live Interactive Application Preview is rendered in User Mode!
    expect(await screen.findByTitle('TaskFlow Pro Kanban Live Application Preview')).toBeInTheDocument();
    expect(screen.getAllByText('● RUNNING').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Port 8001')).toBeInTheDocument();
    expect(screen.getByText('🐳 Docker Runtime')).toBeInTheDocument();

    // 5. Verifies actions to transition to Developer Mode
    const openDevBtns = screen.getAllByRole('button', { name: /open in developer mode/i });
    expect(openDevBtns.length).toBeGreaterThanOrEqual(1);

    fireEvent.click(openDevBtns[0]);
    await waitFor(() => {
      expect(localStorage.getItem(MODE_STORAGE_KEY)).toBe('developer');
    });
  });

  it('3. Existing projects in User Mode support one-click live preview launch', async () => {
    const startSpy = vi.spyOn(previewRuntimeApi, 'start').mockResolvedValue({
      status: 'RUNNING',
      port: 8001,
      preview_url: 'http://127.0.0.1:8001/',
      is_healthy: true,
      project_id: mockProjects[0].id,
      project_name: mockProjects[0].name,
      active_mode: 'taskflow',
      detail: 'Running.',
      execution_type: 'isolated_container',
      container_status: 'RUNNING',
    });

    vi.spyOn(previewRuntimeApi, 'getStatus').mockResolvedValue({
      status: 'RUNNING',
      port: 8001,
      preview_url: 'http://127.0.0.1:8001/',
      is_healthy: true,
      project_id: mockProjects[0].id,
      project_name: mockProjects[0].name,
      active_mode: 'taskflow',
      detail: 'Running.',
      execution_type: 'isolated_container',
      container_status: 'RUNNING',
    });

    renderApp('user');

    // Click "View App" on the Kanban card
    const viewAppBtn = await screen.findByRole('button', { name: /view app/i });
    fireEvent.click(viewAppBtn);

    await waitFor(() => {
      expect(startSpy).toHaveBeenCalledWith(mockProjects[0].id);
      expect(screen.getByTitle('Real-Time Kanban Task Manager Live Application Preview')).toBeInTheDocument();
    });
  });

  it('4. Developer Mode PreviewWorkspace includes action to return to User Mode', async () => {
    vi.spyOn(previewRuntimeApi, 'getStatus').mockResolvedValue({
      status: 'RUNNING',
      port: 8001,
      preview_url: 'http://127.0.0.1:8001/',
      is_healthy: true,
      project_id: mockProjects[0].id,
      active_mode: 'taskflow',
      detail: 'Healthy',
      execution_type: 'isolated_container',
      container_status: 'RUNNING',
    });

    window.history.replaceState({}, '', `/projects/${mockProjects[0].id}/workspace/preview`);
    renderApp('developer', mockProjects[0].id);

    // Verifies "User Mode" return button is present in PreviewWorkspace
    const userModeBtn = await screen.findByRole('button', { name: /user mode/i });
    expect(userModeBtn).toBeInTheDocument();

    fireEvent.click(userModeBtn);

    await waitFor(() => {
      expect(localStorage.getItem(MODE_STORAGE_KEY)).toBe('user');
    });
  });
});
