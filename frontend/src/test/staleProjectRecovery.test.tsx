import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { isProjectNotFoundError, extractUuidFromMessage } from '../utils/projectRecovery';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { ProjectProvider, useProject, LOCAL_STORAGE_KEY } from '../context/ProjectContext';
import { ApiError } from '../types/api';
import { ProjectResponse } from '../types/project';
import { projectsApi } from '../services/projectsApi';

const STALE_PROJECT_ID = 'e0240625-33a7-468f-abfc-543abdad153f';

const mockValidProject1: ProjectResponse = {
  id: '5ec6a638-4520-4c14-ad8b-b9d1aaa0df6c',
  name: 'EventHub 6769',
  slug: 'eventhub-6769',
  description: 'Event management platform',
  status: 'DRAFT',
  settings: {},
  created_at: '2026-10-07T09:52:53.839361',
  updated_at: '2026-10-07T09:52:53.839364',
};

const mockValidProject2: ProjectResponse = {
  id: '99999999-4520-4c14-ad8b-b9d1aaa0df6c',
  name: 'TaskMaster Pro',
  slug: 'taskmaster-pro',
  description: 'Task management platform',
  status: 'IN_PROGRESS',
  settings: {},
  created_at: '2026-10-07T10:00:00.000000',
  updated_at: '2026-10-07T10:00:00.000000',
};

describe('Stale Project Detection & Error Normalization', () => {
  it('1. correctly identifies HTTP 404 project-not-found error', () => {
    const apiError = new ApiError(
      404,
      `Project with identifier '${STALE_PROJECT_ID}' was not found.`,
      {
        title: 'Resource Not Found',
        status: 404,
        detail: `Project with identifier '${STALE_PROJECT_ID}' was not found.`,
        resource: 'Project',
      } as any
    );

    expect(isProjectNotFoundError(apiError)).toBe(true);
  });

  it('2. distinguishes project 404 from other resource 404s and server errors', () => {
    const workflow404 = new ApiError(
      404,
      'WorkflowExecution with identifier 123 was not found.',
      {
        title: 'Resource Not Found',
        status: 404,
        detail: 'WorkflowExecution not found.',
        resource: 'WorkflowExecution',
      } as any
    );

    const server500 = new ApiError(500, 'Internal Server Error');

    expect(isProjectNotFoundError(workflow404)).toBe(false);
    expect(isProjectNotFoundError(server500)).toBe(false);
    expect(isProjectNotFoundError(null)).toBe(false);
  });

  it('3. extractUuidFromMessage extracts the target UUID correctly', () => {
    const msg = `Project with identifier '${STALE_PROJECT_ID}' was not found.`;
    expect(extractUuidFromMessage(msg)).toBe(STALE_PROJECT_ID);
    expect(extractUuidFromMessage('No UUID here')).toBeNull();
  });
});

describe('ErrorAlert UX: Friendly Project Not Found Presentation', () => {
  it('4. shows "That project is no longer available." and hides raw UUID by default', () => {
    const error = new ApiError(
      404,
      `Project with identifier '${STALE_PROJECT_ID}' was not found.`
    );

    render(<ErrorAlert error={error} />);

    // Primary friendly message
    expect(screen.getByText('Project Not Available')).toBeInTheDocument();
    expect(screen.getByText('That project is no longer available.')).toBeInTheDocument();

    // Raw UUID is NOT displayed in normal view
    expect(screen.queryByText(new RegExp(STALE_PROJECT_ID, 'i'))).not.toBeInTheDocument();

    // Button to expand technical details exists
    const toggleBtn = screen.getByText('Technical error details');
    expect(toggleBtn).toBeInTheDocument();

    // Expanding reveals technical details and UUID
    fireEvent.click(toggleBtn);
    expect(screen.getByText(new RegExp(STALE_PROJECT_ID, 'i'))).toBeInTheDocument();
    expect(screen.getByText(/HTTP 404 \(Not Found\)/i)).toBeInTheDocument();
  });

  it('5. provides actionable buttons for choosing another project or creating new', () => {
    const error = new ApiError(
      404,
      `Project with identifier '${STALE_PROJECT_ID}' was not found.`
    );
    const mockChooseAnother = vi.fn();
    const mockCreateNew = vi.fn();

    render(
      <ErrorAlert
        error={error}
        onChooseAnotherProject={mockChooseAnother}
        onCreateProject={mockCreateNew}
      />
    );

    const chooseBtn = screen.getByText('Choose Another Project');
    const createBtn = screen.getByText('Create New Project');

    expect(chooseBtn).toBeInTheDocument();
    expect(createBtn).toBeInTheDocument();

    fireEvent.click(chooseBtn);
    expect(mockChooseAnother).toHaveBeenCalledTimes(1);

    fireEvent.click(createBtn);
    expect(mockCreateNew).toHaveBeenCalledTimes(1);
  });
});

describe('ProjectContext Resilience & Auto-Healing', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    localStorage.clear();
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    vi.restoreAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('6. detects stale project ID from localStorage, heals to valid project, and updates storage', async () => {
    localStorage.setItem(LOCAL_STORAGE_KEY, STALE_PROJECT_ID);

    const Consumer = () => {
      const { selectedProjectId, selectedProject, staleProjectNotice, validateAndSyncProjects } =
        useProject();

      useEffect(() => {
        validateAndSyncProjects([mockValidProject1, mockValidProject2]);
      }, [validateAndSyncProjects]);

      return (
        <div>
          <div data-testid="selected-id">{selectedProjectId}</div>
          <div data-testid="selected-name">{selectedProject?.name}</div>
          <div data-testid="stale-notice">{staleProjectNotice}</div>
        </div>
      );
    };

    render(
      <QueryClientProvider client={queryClient}>
        <ProjectProvider>
          <Consumer />
        </ProjectProvider>
      </QueryClientProvider>
    );

    // Should heal to mockValidProject1
    await waitFor(() => {
      expect(screen.getByTestId('selected-id').textContent).toBe(mockValidProject1.id);
    });

    expect(screen.getByTestId('selected-name').textContent).toBe(mockValidProject1.name);
    expect(screen.getByTestId('stale-notice').textContent).toContain('That project is no longer available');

    // Local storage should now store the valid project, not the stale one!
    expect(localStorage.getItem(LOCAL_STORAGE_KEY)).toBe(mockValidProject1.id);
  });

  it('7. clears stale ID when backend returns empty projects list', async () => {
    localStorage.setItem(LOCAL_STORAGE_KEY, STALE_PROJECT_ID);

    const Consumer = () => {
      const { selectedProjectId, selectedProject, staleProjectNotice, validateAndSyncProjects } =
        useProject();

      useEffect(() => {
        validateAndSyncProjects([]);
      }, [validateAndSyncProjects]);

      return (
        <div>
          <div data-testid="selected-id">{selectedProjectId || 'none'}</div>
          <div data-testid="selected-name">{selectedProject?.name || 'none'}</div>
          <div data-testid="stale-notice">{staleProjectNotice || 'none'}</div>
        </div>
      );
    };

    render(
      <QueryClientProvider client={queryClient}>
        <ProjectProvider>
          <Consumer />
        </ProjectProvider>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('selected-id').textContent).toBe('none');
    });

    expect(localStorage.getItem(LOCAL_STORAGE_KEY)).toBeNull();
    expect(screen.getByTestId('stale-notice').textContent).toContain('That project is no longer available');
  });

  it('8. preserves valid project ID in localStorage across loads', async () => {
    localStorage.setItem(LOCAL_STORAGE_KEY, mockValidProject2.id);

    const Consumer = () => {
      const { selectedProjectId, selectedProject, staleProjectNotice, validateAndSyncProjects } =
        useProject();

      useEffect(() => {
        validateAndSyncProjects([mockValidProject1, mockValidProject2]);
      }, [validateAndSyncProjects]);

      return (
        <div>
          <div data-testid="selected-id">{selectedProjectId}</div>
          <div data-testid="selected-name">{selectedProject?.name}</div>
          <div data-testid="stale-notice">{staleProjectNotice || 'none'}</div>
        </div>
      );
    };

    render(
      <QueryClientProvider client={queryClient}>
        <ProjectProvider>
          <Consumer />
        </ProjectProvider>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('selected-name').textContent).toBe(mockValidProject2.name);
    });

    expect(screen.getByTestId('selected-id').textContent).toBe(mockValidProject2.id);
    expect(screen.getByTestId('stale-notice').textContent).toBe('none');
    expect(localStorage.getItem(LOCAL_STORAGE_KEY)).toBe(mockValidProject2.id);
  });

  it('9. handleStaleProject refetches projects and auto-recovers', async () => {
    localStorage.setItem(LOCAL_STORAGE_KEY, STALE_PROJECT_ID);
    vi.spyOn(projectsApi, 'list').mockResolvedValue([mockValidProject1]);

    const Consumer = () => {
      const { selectedProjectId, selectedProject, handleStaleProject } = useProject();
      return (
        <div>
          <button onClick={() => handleStaleProject(STALE_PROJECT_ID)}>Trigger Recovery</button>
          <div data-testid="selected-id">{selectedProjectId}</div>
          <div data-testid="selected-name">{selectedProject?.name || 'none'}</div>
        </div>
      );
    };

    render(
      <QueryClientProvider client={queryClient}>
        <ProjectProvider>
          <Consumer />
        </ProjectProvider>
      </QueryClientProvider>
    );

    fireEvent.click(screen.getByText('Trigger Recovery'));

    await waitFor(() => {
      expect(screen.getByTestId('selected-id').textContent).toBe(mockValidProject1.id);
    });

    expect(screen.getByTestId('selected-name').textContent).toBe(mockValidProject1.name);
    expect(localStorage.getItem(LOCAL_STORAGE_KEY)).toBe(mockValidProject1.id);
  });

  it('10. newly created project becomes active immediately and is not reverted by background sync', async () => {
    const mockNewProject: ProjectResponse = {
      id: 'aabbccdd-4520-4c14-ad8b-b9d1aaa0df6c',
      name: 'EventHub Verification 2026',
      slug: 'eventhub-verification-2026',
      description: 'A modern event management application',
      status: 'DRAFT',
      settings: {},
      created_at: '2026-10-07T11:00:00.000000',
      updated_at: '2026-10-07T11:00:00.000000',
    };

    let triggerSync: (list: ProjectResponse[]) => void = () => {};
    let triggerSelect: (p: ProjectResponse) => void = () => {};

    const Consumer = () => {
      const { selectedProjectId, selectedProject, selectProject, validateAndSyncProjects } =
        useProject();

      triggerSync = validateAndSyncProjects;
      triggerSelect = selectProject;

      return (
        <div>
          <div data-testid="selected-id">{selectedProjectId || 'none'}</div>
          <div data-testid="selected-name">{selectedProject?.name || 'none'}</div>
        </div>
      );
    };

    render(
      <QueryClientProvider client={queryClient}>
        <ProjectProvider>
          <Consumer />
        </ProjectProvider>
      </QueryClientProvider>
    );

    // Initial sync with project 1
    triggerSync([mockValidProject1]);
    await waitFor(() => {
      expect(screen.getByTestId('selected-id').textContent).toBe(mockValidProject1.id);
    });

    // New project created -> selectProject is called
    triggerSelect(mockNewProject);
    await waitFor(() => {
      expect(screen.getByTestId('selected-id').textContent).toBe(mockNewProject.id);
      expect(screen.getByTestId('selected-name').textContent).toBe('EventHub Verification 2026');
    });
    expect(localStorage.getItem(LOCAL_STORAGE_KEY)).toBe(mockNewProject.id);

    // Simulate background query sync firing with OLD cache (only mockValidProject1)
    // This MUST NOT revert selectedProject to mockValidProject1!
    triggerSync([mockValidProject1]);
    expect(screen.getByTestId('selected-id').textContent).toBe(mockNewProject.id);
    expect(screen.getByTestId('selected-name').textContent).toBe('EventHub Verification 2026');
    expect(localStorage.getItem(LOCAL_STORAGE_KEY)).toBe(mockNewProject.id);

    // When background query finishes with updated list including mockNewProject
    triggerSync([mockNewProject, mockValidProject1]);
    expect(screen.getByTestId('selected-id').textContent).toBe(mockNewProject.id);
    expect(screen.getByTestId('selected-name').textContent).toBe('EventHub Verification 2026');
  });
});
