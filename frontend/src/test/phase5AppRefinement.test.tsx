import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../context/AuthContext';
import { ProjectProvider } from '../context/ProjectContext';
import { ModeProvider, MODE_STORAGE_KEY } from '../context/ModeContext';
import { App } from '../App';
import { authApi } from '../services/authApi';
import { projectsApi } from '../services/projectsApi';
import { previewRuntimeApi } from '../services/previewRuntimeApi';
import { assistantApi } from '../services/assistantApi';
import { developmentVersionApi } from '../services/developmentVersionApi';
import { ProjectResponse } from '../types/project';
import { AssistantMessage, ActionResult } from '../types/assistant';
import { DevelopmentVersionListResponse } from '../types/developmentVersion';

const mockProject: ProjectResponse = {
  id: 'proj-p5-refine',
  name: 'Team Task Dashboard',
  slug: 'team-task-dashboard',
  description: 'A collaborative task board with fullstack React and FastAPI.',
  status: 'IN_PROGRESS',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const mockUser = {
  id: 'user-p5',
  name: 'Morgan Developer',
  email: 'morgan@example.com',
  role: 'developer' as const,
  is_active: true,
  created_at: new Date().toISOString(),
};

function renderApp(initialMode: 'user' | 'developer' = 'user') {
  localStorage.clear();
  localStorage.setItem('se_auth_token', 'test-auth-token');
  localStorage.setItem(MODE_STORAGE_KEY, initialMode);

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

describe('Phase 5: Continuous Natural-Language App Refinement', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    window.history.replaceState({}, '', '/projects');

    vi.spyOn(authApi, 'getMe').mockResolvedValue(mockUser);
    vi.spyOn(projectsApi, 'list').mockResolvedValue([mockProject]);
    vi.spyOn(previewRuntimeApi, 'getStatus').mockResolvedValue({
      project_id: mockProject.id,
      status: 'RUNNING',
      port: 8001,
      preview_url: 'http://localhost:8001',
      is_healthy: true,
      detail: 'Running',
      active_mode: 'taskflow',
    });
    vi.spyOn(previewRuntimeApi, 'start').mockResolvedValue({
      project_id: mockProject.id,
      status: 'RUNNING',
      port: 8001,
      preview_url: 'http://localhost:8001',
      is_healthy: true,
      detail: 'Running',
      active_mode: 'taskflow',
    });
    vi.spyOn(developmentVersionApi, 'getActiveVersion').mockResolvedValue({
      version_id: 'ver-1',
      project_id: mockProject.id,
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
    });
  });

  it('1. Displays the running application preview and the context-aware refinement panel in User Mode', async () => {
    renderApp('user');

    // Click "View App" on the application card
    const viewAppBtn = await screen.findByRole('button', { name: /view app/i }, { timeout: 3500 });
    fireEvent.click(viewAppBtn);

    // Verify preview frame and header badges
    expect(await screen.findByTitle(/Team Task Dashboard Live Application Preview/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Port 8001/i).length).toBeGreaterThanOrEqual(1);

    // Verify Refinement Panel
    const refinementPanel = screen.getByTestId('app-refinement-panel');
    expect(refinementPanel).toBeInTheDocument();
    expect(within(refinementPanel).getByText('Refine “Team Task Dashboard”')).toBeInTheDocument();
    expect(within(refinementPanel).getByText('v1')).toBeInTheDocument();
    expect(within(refinementPanel).getByText('● RUNNING')).toBeInTheDocument();

    // Verify quick suggestion chips
    expect(screen.getByText('Add a dark mode toggle.')).toBeInTheDocument();
    expect(screen.getByText('Add a search bar to the task list.')).toBeInTheDocument();
    expect(screen.getByText('Add an export to CSV button.')).toBeInTheDocument();
  });

  it('2. Translates a natural language refinement request into targeted multi-file diffs with confirmation token', async () => {
    const mockProposedAction: ActionResult = {
      action_id: 'action-101',
      status: 'PENDING_CONFIRMATION',
      summary: 'Add dark mode toggle to navigation bar and update theme state.',
      requires_confirmation: true,
      confirmation_prompt: 'Approve applying dark mode styles and state toggle.',
      confirmation_token: 'token-dark-mode-101',
      warnings: [],
      errors: [],
      data: {
        files: [
          {
            path: 'frontend/src/components/Navbar.tsx',
            status: 'modified',
            diff: '@@ -10,3 +10,6 @@\n+ <ThemeToggle />',
          },
          {
            path: 'frontend/src/context/ThemeContext.tsx',
            status: 'added',
            diff: '@@ -0,0 +1,15 @@\n+ export const ThemeProvider = ...',
          },
        ],
      },
    };

    const mockAssistantResponse: AssistantMessage = {
      message_id: 'msg-resp-1',
      conversation_id: 'conv-refine-p5',
      role: 'assistant',
      content: 'I prepared the dark mode toggle implementation. Please review the targeted changes below.',
      action_id: 'action-101',
      action_status: 'PENDING_CONFIRMATION',
      action_result: mockProposedAction,
      created_at: new Date().toISOString(),
    };

    const sendSpy = vi.spyOn(assistantApi, 'sendMessage').mockResolvedValue(mockAssistantResponse);

    renderApp('user');

    const viewAppBtn = await screen.findByRole('button', { name: /view app/i });
    fireEvent.click(viewAppBtn);

    const input = await screen.findByPlaceholderText(/Describe what to add, fix, or change in this app/i);
    fireEvent.change(input, { target: { value: 'Add a dark mode toggle' } });

    const refineBtn = screen.getByRole('button', { name: /refine app/i });
    fireEvent.click(refineBtn);

    await waitFor(() => {
      expect(sendSpy).toHaveBeenCalledWith(
        mockProject.id,
        expect.objectContaining({
          content: 'Add a dark mode toggle',
        })
      );
    });

    // Proposed changes card is shown
    expect(await screen.findByTestId('proposed-changes-card')).toBeInTheDocument();
    expect(screen.getByText(/Proposed Changes Ready \(v1 → v2\)/i)).toBeInTheDocument();
    expect(screen.getByText('~ frontend/src/components/Navbar.tsx')).toBeInTheDocument();
    expect(screen.getByText('+ frontend/src/context/ThemeContext.tsx')).toBeInTheDocument();

    // Inspect Diffs
    const inspectDiffsBtn = screen.getByRole('button', { name: /inspect diffs/i });
    fireEvent.click(inspectDiffsBtn);
    expect(screen.getByText(/ThemeToggle/i)).toBeInTheDocument();
    expect(screen.getByText(/ThemeProvider/i)).toBeInTheDocument();

    // Check action buttons
    expect(screen.getByRole('button', { name: /apply & update live preview/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /discard/i })).toBeInTheDocument();
  });

  it('3. Applies confirmed refinement, creates immutable v2, updates live container preview, and verifies success', async () => {
    const mockProposedAction: ActionResult = {
      action_id: 'action-102',
      status: 'PENDING_CONFIRMATION',
      summary: 'Add export to CSV button in tasks table.',
      requires_confirmation: true,
      confirmation_token: 'token-csv-export-102',
      warnings: [],
      errors: [],
      data: {
        files: [{ path: 'frontend/src/components/TasksTable.tsx', status: 'modified', diff: '+ <ExportCsvBtn />' }],
      },
    };

    vi.spyOn(assistantApi, 'sendMessage').mockResolvedValue({
      message_id: 'msg-resp-2',
      conversation_id: 'conv-refine-p5',
      role: 'assistant',
      content: 'Here is the CSV export change.',
      action_result: mockProposedAction,
      created_at: new Date().toISOString(),
    });

    const confirmSpy = vi.spyOn(assistantApi, 'confirmAction').mockResolvedValue({
      action_id: 'action-102',
      status: 'SUCCESS',
      summary: 'Export to CSV button implemented and container updated.',
      requires_confirmation: false,
      warnings: [],
      errors: [],
      data: {
        version_number: 2,
        new_version: { version_number: 2, version_id: 'ver-2' },
      },
    });

    renderApp('user');

    const viewAppBtn = await screen.findByRole('button', { name: /view app/i });
    fireEvent.click(viewAppBtn);

    // Click suggestion chip for CSV button
    const csvChip = await screen.findByRole('button', { name: /add an export to csv button\./i });
    fireEvent.click(csvChip);

    const applyBtn = await screen.findByRole('button', { name: /apply & update live preview/i });
    fireEvent.click(applyBtn);

    await waitFor(() => {
      expect(confirmSpy).toHaveBeenCalledWith(mockProject.id, {
        confirmation_token: 'token-csv-export-102',
      });
    });

    // Version badge advances to v2
    expect(await screen.findByText('v2')).toBeInTheDocument();
    expect(screen.getByText(/✓ Changes applied to v2! Application runtime updated on port 8001\./i)).toBeInTheDocument();

    // Rollback button is now available
    expect(screen.getByRole('button', { name: /rollback to v1/i })).toBeInTheDocument();
  });

  it('4. Reverts to previous version v1 via 1-click rollback, updating the live runtime', async () => {
    // Initial state at v2
    vi.spyOn(developmentVersionApi, 'getActiveVersion').mockResolvedValue({
      version_id: 'ver-2',
      project_id: mockProject.id,
      version_number: 2,
      artifact_key: 'artifacts/v2.zip',
      status: 'ACTIVE',
      is_active: true,
      content_hash: 'hash-v2',
      manifest_hash: 'manifest-v2',
      file_count: 6,
      total_size_bytes: 14000,
      source_reason: 'Added dark mode toggle',
      created_by: 'assistant',
      requirement_ids: [],
      files_manifest: [],
      created_at: new Date().toISOString(),
    });

    const mockVersionsList: DevelopmentVersionListResponse = {
      items: [
        {
          version_id: 'ver-1',
          project_id: mockProject.id,
          version_number: 1,
          artifact_key: 'artifacts/v1.zip',
          status: 'SUPERSEDED',
          is_active: false,
          content_hash: 'hash-v1',
          manifest_hash: 'manifest-v1',
          file_count: 5,
          total_size_bytes: 12000,
          source_reason: 'Scaffold',
          created_by: 'system',
          requirement_ids: [],
          files_manifest: [],
          created_at: new Date().toISOString(),
        },
        {
          version_id: 'ver-2',
          project_id: mockProject.id,
          version_number: 2,
          artifact_key: 'artifacts/v2.zip',
          status: 'ACTIVE',
          is_active: true,
          content_hash: 'hash-v2',
          manifest_hash: 'manifest-v2',
          file_count: 6,
          total_size_bytes: 14000,
          source_reason: 'Dark mode',
          created_by: 'assistant',
          requirement_ids: [],
          files_manifest: [],
          created_at: new Date().toISOString(),
        },
      ],
      total: 2,
      active_version_id: 'ver-2',
    };

    vi.spyOn(developmentVersionApi, 'listVersions').mockResolvedValue(mockVersionsList);
    const rollbackSpy = vi.spyOn(developmentVersionApi, 'rollbackVersion').mockResolvedValue(mockVersionsList.items[0]);

    renderApp('user');

    const viewAppBtn = await screen.findByRole('button', { name: /view app/i });
    fireEvent.click(viewAppBtn);

    // Rollback button to v1
    const rollbackBtn = await screen.findByRole('button', { name: /rollback to v1/i });
    fireEvent.click(rollbackBtn);

    await waitFor(() => {
      expect(rollbackSpy).toHaveBeenCalledWith(
        mockProject.id,
        'ver-1',
        'Rollback to v1 from User Mode'
      );
    });

    // Version badge returns to v1
    expect(await screen.findByText('v1')).toBeInTheDocument();
    expect(screen.getByText(/✓ Rolled back successfully to v1\. Runtime reverted on port 8001\./i)).toBeInTheDocument();
  });

  it('5. Discards proposed changes safely without mutating application or runtime version', async () => {
    const mockProposedAction: ActionResult = {
      action_id: 'action-discard',
      status: 'PENDING_CONFIRMATION',
      summary: 'Change layout colors to monochrome.',
      requires_confirmation: true,
      confirmation_token: 'token-discard',
      warnings: [],
      errors: [],
      data: {
        files: [{ path: 'frontend/src/index.css', status: 'modified', diff: '- #fff\n+ #000' }],
      },
    };

    vi.spyOn(assistantApi, 'sendMessage').mockResolvedValue({
      message_id: 'msg-resp-discard',
      conversation_id: 'conv-refine-p5',
      role: 'assistant',
      content: 'Proposed layout color changes.',
      action_result: mockProposedAction,
      created_at: new Date().toISOString(),
    });

    renderApp('user');

    const viewAppBtn = await screen.findByRole('button', { name: /view app/i });
    fireEvent.click(viewAppBtn);

    const input = await screen.findByPlaceholderText(/Describe what to add, fix, or change in this app/i);
    fireEvent.change(input, { target: { value: 'Make layout monochrome' } });
    fireEvent.click(screen.getByRole('button', { name: /refine app/i }));

    expect(await screen.findByTestId('proposed-changes-card')).toBeInTheDocument();

    const discardBtn = screen.getByRole('button', { name: /discard/i });
    fireEvent.click(discardBtn);

    // Card is dismissed and version remains v1
    expect(screen.queryByTestId('proposed-changes-card')).not.toBeInTheDocument();
    expect(screen.getByText('v1')).toBeInTheDocument();
  });

  it('6. Handles refinement errors gracefully while preserving the running preview', async () => {
    vi.spyOn(assistantApi, 'sendMessage').mockRejectedValue(new Error('Syntax validation failed in generated patch.'));

    renderApp('user');

    const viewAppBtn = await screen.findByRole('button', { name: /view app/i });
    fireEvent.click(viewAppBtn);

    const input = await screen.findByPlaceholderText(/Describe what to add, fix, or change in this app/i);
    fireEvent.change(input, { target: { value: 'Break the syntax' } });
    fireEvent.click(screen.getByRole('button', { name: /refine app/i }));

    // Error banner is displayed
    expect(await screen.findByText('Syntax validation failed in generated patch.')).toBeInTheDocument();

    // Live preview frame remains intact and running
    expect(screen.getByTitle(/Team Task Dashboard Live Application Preview/i)).toBeInTheDocument();
    expect(screen.getAllByText('● RUNNING').length).toBeGreaterThanOrEqual(1);
  });
});
