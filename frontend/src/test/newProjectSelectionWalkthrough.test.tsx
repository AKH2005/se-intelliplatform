import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ProjectProvider, LOCAL_STORAGE_KEY } from '../context/ProjectContext';
import { App } from '../App';
import { projectsApi } from '../services/projectsApi';
import { requirementsApi } from '../services/requirementsApi';
import { contextApi } from '../services/contextApi';
import { ProjectResponse } from '../types/project';

const existingProject: ProjectResponse = {
  id: '5ec6a638-4520-4c14-ad8b-b9d1aaa0df6c',
  name: 'EventHub 6769',
  slug: 'eventhub-6769',
  description: 'Build an event management platform',
  status: 'DRAFT',
  settings: {},
  created_at: '2026-10-07T09:52:53.839361',
  updated_at: '2026-10-07T09:52:53.839364',
};

const newCanonicalProject: ProjectResponse = {
  id: 'd2948b81-7f9a-4e2b-a012-3456789abcde',
  name: 'EventHub Verification 2026',
  slug: 'eventhub-verification-2026',
  description:
    'A modern event management application where users can discover events, search and filter events, view event details, register for events, cancel registrations, and manage their registrations.',
  status: 'DRAFT',
  settings: {},
  created_at: '2026-10-07T12:00:00.000000',
  updated_at: '2026-10-07T12:00:00.000000',
};

describe('Human User Walkthrough: New Project Creation, Selection, & Refresh', () => {
  let queryClient: QueryClient;
  let projectList: ProjectResponse[];

  beforeEach(() => {
    localStorage.clear();
    projectList = [existingProject];

    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

    vi.spyOn(projectsApi, 'list').mockImplementation(async () => [...projectList]);
    vi.spyOn(projectsApi, 'create').mockImplementation(async (data) => {
      const created: ProjectResponse = {
        ...newCanonicalProject,
        name: data.name,
        slug: data.slug,
        description: data.description || '',
      };
      projectList = [created, ...projectList];
      return created;
    });
    vi.spyOn(requirementsApi, 'create').mockResolvedValue({} as any);
    vi.spyOn(requirementsApi, 'list').mockResolvedValue([]);
    vi.spyOn(contextApi, 'createSnapshot').mockResolvedValue({} as any);
    vi.spyOn(contextApi, 'getContext').mockResolvedValue({} as any);
    vi.spyOn(contextApi, 'listSnapshots').mockResolvedValue([]);
  });

  it('performs full user walkthrough: create EventHub Verification 2026, activates it, updates localStorage and Header, preserves across refresh', async () => {
    // 1. Open the platform
    const { unmount } = render(
      <QueryClientProvider client={queryClient}>
        <ProjectProvider>
          <App />
        </ProjectProvider>
      </QueryClientProvider>
    );

    // Initial project loads
    await waitFor(() => {
      expect(screen.getByRole('combobox', { name: /select active project/i })).toHaveValue(
        existingProject.id
      );
    });

    // 2. Open Create Project Modal
    const createProjectButtons = screen.getAllByRole('button', { name: /new project/i });
    fireEvent.click(createProjectButtons[0]);

    // Modal is open
    expect(screen.getByText('Create New Project')).toBeInTheDocument();

    // 3. Enter Name & Description
    const nameInput = screen.getByLabelText(/project name/i);
    fireEvent.change(nameInput, { target: { value: 'EventHub Verification 2026' } });

    const descInput = screen.getByLabelText(/^Description/i);
    fireEvent.change(descInput, {
      target: {
        value:
          'A modern event management application where users can discover events, search and filter events, view event details, register for events, cancel registrations, and manage their registrations.',
      },
    });

    // 4. Click "Build Application"
    const buildBtn = screen.getByRole('button', { name: /build application/i });
    fireEvent.click(buildBtn);

    // 5. Verification: The newly created project MUST become active immediately!
    await waitFor(() => {
      const selector = screen.getByRole('combobox', { name: /select active project/i }) as HTMLSelectElement;
      expect(selector.value).toBe(newCanonicalProject.id);
    });

    // Verify localStorage has the new project's ID
    expect(localStorage.getItem(LOCAL_STORAGE_KEY)).toBe(newCanonicalProject.id);

    // Header selector shows the new project name in selected option
    const selector = screen.getByRole('combobox', { name: /select active project/i }) as HTMLSelectElement;
    const selectedOption = selector.options[selector.selectedIndex];
    expect(selectedOption.textContent).toContain('EventHub Verification 2026');

    // 6. Navigate to Overview
    const overviewTabBtn = screen.getByRole('button', { name: /overview/i });
    fireEvent.click(overviewTabBtn);

    // Overview displays new project name
    await waitFor(() => {
      expect(screen.getAllByText(/EventHub Verification 2026/i).length).toBeGreaterThan(0);
    });

    // 7. Navigate to Intelligence
    const intellTabBtn = screen.getByRole('button', { name: /intelligence/i });
    fireEvent.click(intellTabBtn);

    // Intelligence workspace loads without 404
    await waitFor(() => {
      expect(screen.queryByText(/404/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/Project with identifier.*not found/i)).not.toBeInTheDocument();
    });

    // 8. Refresh Edge simulation (unmount and remount with localStorage populated)
    unmount();

    const refreshQueryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    render(
      <QueryClientProvider client={refreshQueryClient}>
        <ProjectProvider>
          <App />
        </ProjectProvider>
      </QueryClientProvider>
    );

    // 9. Confirm EventHub Verification 2026 is STILL the active project after refresh
    await waitFor(() => {
      const refreshedSelector = screen.getByRole('combobox', {
        name: /select active project/i,
      }) as HTMLSelectElement;
      expect(refreshedSelector.value).toBe(newCanonicalProject.id);
    });

    expect(localStorage.getItem(LOCAL_STORAGE_KEY)).toBe(newCanonicalProject.id);
  }, 15000);

  it('stale project test: recovers gracefully when invalid project ID is in localStorage, removes stale ID, selects valid project, shows friendly notice without raw UUID', async () => {
    const STALE_UUID = 'e0240625-33a7-468f-abfc-543abdad153f';
    localStorage.setItem(LOCAL_STORAGE_KEY, STALE_UUID);

    render(
      <QueryClientProvider client={queryClient}>
        <ProjectProvider>
          <App />
        </ProjectProvider>
      </QueryClientProvider>
    );

    // Stale project detected & auto-healed to existing valid project
    await waitFor(() => {
      const selector = screen.getByRole('combobox', { name: /select active project/i }) as HTMLSelectElement;
      expect(selector.value).toBe(existingProject.id);
    });

    // Friendly recovery notice is shown
    expect(screen.getByText(/That project is no longer available/i)).toBeInTheDocument();

    // No raw UUID exposed in message
    expect(screen.queryByText(STALE_UUID)).not.toBeInTheDocument();

    // LocalStorage is cleaned and updated with valid project ID
    expect(localStorage.getItem(LOCAL_STORAGE_KEY)).toBe(existingProject.id);
  });
});
