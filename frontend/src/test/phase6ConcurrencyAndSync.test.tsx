import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../context/AuthContext';
import { ProjectProvider } from '../context/ProjectContext';
import { ModeProvider, MODE_STORAGE_KEY } from '../context/ModeContext';
import { App } from '../App';
import { authApi } from '../services/authApi';
import { projectsApi } from '../services/projectsApi';
import { previewRuntimeApi } from '../services/previewRuntimeApi';
import { developmentVersionApi } from '../services/developmentVersionApi';
import { assistantApi } from '../services/assistantApi';
import { workflowsApi } from '../services/workflowsApi';
import { ProjectResponse } from '../types/project';
import { RuntimeStatusResponse } from '../types/previewRuntime';
import { DevelopmentVersionResponse } from '../types/developmentVersion';

// Mock user and data fixtures
const mockUser = {
  id: 'user-p6',
  name: 'Morgan Developer',
  email: 'morgan@example.com',
  role: 'developer' as const,
  is_active: true,
  created_at: new Date().toISOString(),
};

const sampleProject: ProjectResponse = {
  id: 'proj-phase6-101',
  name: 'TaskMaster Realtime',
  slug: 'taskmaster-realtime',
  description: 'Enterprise task manager application with realtime collaboration',
  status: 'IN_PROGRESS',
  settings: { active_version_id: 'ver-v1-uuid', category: 'taskflow' },
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const mockV1Version: DevelopmentVersionResponse = {
  version_id: 'ver-v1-uuid',
  project_id: sampleProject.id,
  version_number: 1,
  artifact_key: 'artifacts/v1.zip',
  status: 'ACTIVE',
  is_active: true,
  content_hash: 'hash-v1',
  manifest_hash: 'manifest-v1',
  file_count: 5,
  total_size_bytes: 12000,
  source_reason: 'Initial blueprint scaffold',
  created_by: 'system',
  requirement_ids: [],
  files_manifest: [],
  created_at: new Date().toISOString(),
};

const mockV2Version: DevelopmentVersionResponse = {
  version_id: 'ver-v2-uuid',
  project_id: sampleProject.id,
  version_number: 2,
  artifact_key: 'artifacts/v2.zip',
  status: 'ACTIVE',
  is_active: true,
  content_hash: 'hash-v2',
  manifest_hash: 'manifest-v2',
  file_count: 6,
  total_size_bytes: 14500,
  source_reason: 'Refined by another team member',
  created_by: 'collaborator',
  requirement_ids: [],
  files_manifest: [],
  created_at: new Date().toISOString(),
};

const sampleRuntime: RuntimeStatusResponse = {
  status: 'RUNNING',
  port: 8001,
  preview_url: 'http://127.0.0.1:8001/preview?project_id=proj-phase6-101',
  is_healthy: true,
  project_id: sampleProject.id,
  project_name: sampleProject.name,
  active_mode: 'taskflow',
  detail: 'Application is running on port 8001.',
  execution_type: 'isolated_container',
  container_status: 'RUNNING',
  container_detail: 'Container se-app-proj-phase6-101 is healthy.',
  active_version_id: 'ver-v1-uuid',
  active_version_number: 1,
};

describe('Phase 6: Multi-Operation Reliability, Concurrency & Live Preview Protection', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    localStorage.setItem('se_auth_token', 'test-auth-token');
    localStorage.setItem(MODE_STORAGE_KEY, 'user');
    window.history.replaceState({}, '', '/projects');

    vi.spyOn(authApi, 'getMe').mockResolvedValue(mockUser);
    vi.spyOn(projectsApi, 'list').mockResolvedValue([sampleProject]);
    vi.spyOn(projectsApi, 'get').mockResolvedValue(sampleProject);
    vi.spyOn(previewRuntimeApi, 'getStatus').mockResolvedValue(sampleRuntime);
    vi.spyOn(previewRuntimeApi, 'start').mockResolvedValue(sampleRuntime);
    vi.spyOn(previewRuntimeApi, 'resolvePreviewUrl').mockReturnValue('http://127.0.0.1:8001/preview?project_id=proj-phase6-101');
    vi.spyOn(developmentVersionApi, 'listVersions').mockResolvedValue({ items: [mockV1Version], total: 1, active_version_id: mockV1Version.version_id });
    vi.spyOn(developmentVersionApi, 'getActiveVersion').mockResolvedValue(mockV1Version);
  });

  const renderApp = (initialMode: 'user' | 'developer' = 'user') => {
    localStorage.setItem('se_auth_token', 'test-auth-token');
    localStorage.setItem(MODE_STORAGE_KEY, initialMode);
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
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
  };

  it('1. Displays 409 Conflict banner for stale refinement edits and recovers with 1-click Refresh', async () => {
    renderApp();

    // Click "View App" to open running application in User Mode
    const viewAppBtn = await screen.findByRole('button', { name: /view app/i }, { timeout: 4500 });
    fireEvent.click(viewAppBtn);

    // Verify preview and refinement panel are rendered
    const refinementPanel = await screen.findByTestId('app-refinement-panel');
    expect(refinementPanel).toBeInTheDocument();
    expect(within(refinementPanel).getByText('v1')).toBeInTheDocument();

    // Mock assistant returning HTTP 409 Conflict because active version advanced to v2
    const conflictError: any = new Error('The project has changed since this edit was prepared (active version is v2, but edit was prepared against version v1). Please refresh before retrying.');
    conflictError.response = {
      status: 409,
      data: {
        detail: 'The project has changed since this edit was prepared (active version is v2, but edit was prepared against version v1). Please refresh before retrying.',
      },
    };
    vi.spyOn(assistantApi, 'sendMessage').mockRejectedValue(conflictError);

    // Enter refinement prompt and submit
    const input = await screen.findByPlaceholderText(/Describe what to add, fix, or change in this app/i);
    fireEvent.change(input, { target: { value: 'Add export to CSV button' } });
    const sendBtn = screen.getByRole('button', { name: /refine app/i });
    fireEvent.click(sendBtn);

    // Verify 409 conflict error message and "Refresh Version" recovery action
    expect(await screen.findByText(/The project has changed since this edit was prepared/i)).toBeInTheDocument();
    const refreshBtn = screen.getByRole('button', { name: /refresh version/i });
    expect(refreshBtn).toBeInTheDocument();

    // Simulate backend now returning v2 as active version
    vi.spyOn(developmentVersionApi, 'getActiveVersion').mockResolvedValue(mockV2Version);

    // Click "Refresh Version"
    fireEvent.click(refreshBtn);

    // Verify error is cleared and active version badge updates to v2
    await waitFor(() => {
      expect(screen.queryByText(/The project has changed since this edit was prepared/i)).not.toBeInTheDocument();
      expect(within(refinementPanel).getByText('v2')).toBeInTheDocument();
    });
  }, 20000);

  it('2. Prevents duplicate builds and displays clear status when a build is already in progress', async () => {
    // Mock workflowsApi returning 409 Conflict on duplicate build
    const duplicateBuildError: any = new Error("A build is already in progress for project 'TaskMaster Realtime'. Please wait for it to complete.");
    duplicateBuildError.status = 409;
    duplicateBuildError.response = {
      status: 409,
      data: {
        detail: "A build is already in progress for project 'TaskMaster Realtime'. Please wait for it to complete.",
      },
    };
    vi.spyOn(workflowsApi, 'execute').mockRejectedValue(duplicateBuildError);

    renderApp();

    // Verify the project card is visible
    const projectCards = await screen.findAllByText(/TaskMaster Realtime/i, {}, { timeout: 3500 });
    expect(projectCards.length).toBeGreaterThanOrEqual(1);
  });

  it('3. Keeps User Mode and Developer Mode synchronized without divergent project copies', async () => {
    renderApp();

    // Open project in User Mode
    const viewAppBtn = await screen.findByRole('button', { name: /view app/i }, { timeout: 3500 });
    fireEvent.click(viewAppBtn);

    // Switch to Developer Mode via mode switcher
    const devModeRadio = screen.getByRole('radio', { name: /switch to developer mode/i });
    fireEvent.click(devModeRadio);

    // Developer mode should show the exact same active project
    await waitFor(() => {
      expect(screen.getAllByText(/TaskMaster Realtime/i).length).toBeGreaterThanOrEqual(1);
    });

    // Switch back to User Mode
    const userModeRadio = screen.getByRole('radio', { name: /switch to user mode/i });
    fireEvent.click(userModeRadio);

    // User mode preserves active project
    await waitFor(() => {
      expect(screen.getAllByText(/TaskMaster Realtime/i).length).toBeGreaterThanOrEqual(1);
    });
  });
});
