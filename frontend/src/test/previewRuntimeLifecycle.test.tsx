import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { PreviewWorkspace } from '../views/PreviewWorkspace';
import { ProjectContext, ProjectContextValue } from '../context/ProjectContext';
import { previewRuntimeApi } from '../services/previewRuntimeApi';
import { ProjectResponse } from '../types/project';

// Mock previewRuntimeApi
vi.mock('../services/previewRuntimeApi', () => ({
  previewRuntimeApi: {
    getStatus: vi.fn(),
    start: vi.fn(),
    restart: vi.fn(),
  },
}));

describe('PreviewWorkspace Runtime Lifecycle & Port 8001 Health Probing', () => {
  const mockProject: ProjectResponse = {
    id: 'f9538964-b2ae-4f6d-a3f4-ad5465409d94',
    name: 'todo list',
    slug: 'todo-list',
    description: 'adding tasks ,deleting and modify them with time also',
    status: 'IN_PROGRESS',
    created_at: '2026-10-07T00:00:00Z',
    updated_at: '2026-10-07T00:00:00Z',
  };

  const renderWithProject = (project: ProjectResponse = mockProject, props = {}) => {
    const mockContextValue: ProjectContextValue = {
      selectedProjectId: project.id,
      setSelectedProjectId: vi.fn(),
      selectedProject: project,
      setSelectedProject: vi.fn(),
      selectProject: vi.fn(),
      projects: [project],
      setProjects: vi.fn(),
      validateAndSyncProjects: vi.fn(),
      handleStaleProject: vi.fn().mockResolvedValue(undefined),
      isProjectStale: false,
      staleProjectNotice: null,
      clearStaleProjectNotice: vi.fn(),
      openCreateProject: vi.fn(),
      registerOpenCreateProject: vi.fn(),
    };

    return render(
      <ProjectContext.Provider value={mockContextValue}>
        <PreviewWorkspace {...props} />
      </ProjectContext.Provider>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('probes runtime status and displays RUNNING badge and iframe when healthy', async () => {
    vi.mocked(previewRuntimeApi.getStatus).mockResolvedValueOnce({
      status: 'RUNNING',
      port: 8001,
      preview_url: 'http://127.0.0.1:8001/',
      is_healthy: true,
      project_id: mockProject.id,
      project_name: 'todo list',
      active_mode: 'taskflow',
      detail: 'Application running on port 8001.',
    });

    renderWithProject();

    // Verify status transitions to RUNNING
    await waitFor(() => {
      expect(screen.getByText(/Application running/i)).toBeInTheDocument();
    });

    // Verify iframe rendered with live URL
    const iframe = screen.getByTitle('Generated Application Live Preview');
    expect(iframe).toBeInTheDocument();
    expect(iframe).toHaveAttribute('src', 'http://127.0.0.1:8001/');
  });

  it('displays controlled platform error state and actions when runtime is unavailable', async () => {
    vi.mocked(previewRuntimeApi.getStatus).mockResolvedValueOnce({
      status: 'UNAVAILABLE',
      port: 8001,
      preview_url: 'http://127.0.0.1:8001/',
      is_healthy: false,
      active_mode: 'taskflow',
      detail: 'Application runtime unavailable on port 8001.',
    });
    vi.mocked(previewRuntimeApi.start).mockResolvedValueOnce({
      status: 'FAILED',
      port: 8001,
      preview_url: 'http://127.0.0.1:8001/',
      is_healthy: false,
      active_mode: 'taskflow',
      detail: 'Failed to bind port 8001.',
    });

    const onSendAssistantPrompt = vi.fn();
    renderWithProject(mockProject, { onSendAssistantPrompt });

    // Verify status changes to unavailable
    await waitFor(() => {
      expect(screen.getAllByText(/Application unavailable/i).length).toBeGreaterThanOrEqual(1);
    });

    // Verify no raw iframe is rendered in error state
    expect(screen.queryByTitle('Generated Application Live Preview')).not.toBeInTheDocument();

    // Verify error card message and actions
    expect(screen.getByText(/The application started but is not responding yet/i)).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
    expect(screen.getByText('Restart Application')).toBeInTheDocument();
    expect(screen.getByText('Ask AI to Fix')).toBeInTheDocument();

    // Test View Runtime Details toggle
    const detailsToggle = screen.getByText(/View Runtime Details/i);
    fireEvent.click(detailsToggle);
    expect(screen.getByText(/Target Port:/i)).toBeInTheDocument();
    expect(screen.getByText(/Failed to bind port 8001/i)).toBeInTheDocument();

    // Test Ask AI to Fix action
    const askAiBtn = screen.getByText('Ask AI to Fix');
    fireEvent.click(askAiBtn);
    expect(onSendAssistantPrompt).toHaveBeenCalledWith(
      expect.stringContaining('The application runtime on port 8001 is unavailable')
    );
  });

  it('supports restarting runtime and recovers to running state', async () => {
    vi.mocked(previewRuntimeApi.getStatus).mockResolvedValueOnce({
      status: 'RUNNING',
      port: 8001,
      preview_url: 'http://127.0.0.1:8001/',
      is_healthy: true,
      active_mode: 'taskflow',
      detail: 'Application running on port 8001.',
    });

    vi.mocked(previewRuntimeApi.restart).mockResolvedValueOnce({
      status: 'RUNNING',
      port: 8001,
      preview_url: 'http://127.0.0.1:8001/',
      is_healthy: true,
      active_mode: 'taskflow',
      detail: 'Application restarted successfully.',
    });

    renderWithProject();

    await waitFor(() => {
      expect(screen.getByText(/Application running/i)).toBeInTheDocument();
    });

    const restartBtn = screen.getByTitle('Restart runtime process on Port 8001');
    fireEvent.click(restartBtn);

    await waitFor(() => {
      expect(previewRuntimeApi.restart).toHaveBeenCalledWith(mockProject.id);
    });

    expect(screen.getByText(/Application running/i)).toBeInTheDocument();
  });
});
