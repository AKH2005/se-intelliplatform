import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ProjectProvider, useProject } from '../context/ProjectContext';
import { DevelopmentWorkspace } from '../views/DevelopmentWorkspace';
import { OverviewWorkspace } from '../views/OverviewWorkspace';
import { developmentVersionApi } from '../services/developmentVersionApi';
import { projectsApi } from '../services/projectsApi';
import { contextApi } from '../services/contextApi';
import { workflowsApi } from '../services/workflowsApi';
import { historyApi } from '../services/historyApi';
import { ProjectResponse } from '../types/project';
import { DevelopmentVersionResponse } from '../types/developmentVersion';

const mockProjectA: ProjectResponse = {
  id: 'proj-slow',
  name: 'Slow Legacy Project',
  slug: 'slow-legacy-project',
  description: 'Project with slow response latency',
  status: 'IN_PROGRESS',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const mockProjectB: ProjectResponse = {
  id: 'proj-fast',
  name: 'Fast Modern Project',
  slug: 'fast-modern-project',
  description: 'Project with instantaneous response latency',
  status: 'IN_PROGRESS',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const mockVersionSlow: DevelopmentVersionResponse = {
  version_id: 'ver-slow-99',
  project_id: 'proj-slow',
  version_number: 99,
  artifact_key: 'artifacts/v99.zip',
  status: 'ACTIVE',
  is_active: true,
  content_hash: 'hash-slow-99',
  manifest_hash: 'manifest-slow-99',
  file_count: 10,
  total_size_bytes: 45000,
  source_reason: 'Legacy Slow Architecture',
  created_by: 'system',
  requirement_ids: [],
  files_manifest: [
    { path: 'slow_legacy.py', size_bytes: 120, language: 'python', requirement_ids: [] },
  ],
  created_at: new Date().toISOString(),
};

const mockVersionFast: DevelopmentVersionResponse = {
  version_id: 'ver-fast-1',
  project_id: 'proj-fast',
  version_number: 1,
  artifact_key: 'artifacts/v1.zip',
  status: 'ACTIVE',
  is_active: true,
  content_hash: 'hash-fast-1',
  manifest_hash: 'manifest-fast-1',
  file_count: 3,
  total_size_bytes: 15000,
  source_reason: 'Modern Clean Architecture',
  created_by: 'developer',
  requirement_ids: [],
  files_manifest: [
    { path: 'fast_main.ts', size_bytes: 80, language: 'typescript', requirement_ids: [] },
  ],
  created_at: new Date().toISOString(),
};

describe('Milestone 3: Asynchronous Request Safety & Monotonic Generation Guards', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    vi.spyOn(projectsApi, 'list').mockResolvedValue([mockProjectA, mockProjectB]);
    vi.spyOn(workflowsApi, 'list').mockResolvedValue([]);
    vi.spyOn(historyApi, 'listProjectHistory').mockResolvedValue({
      items: [],
      total: 0,
      limit: 10,
      offset: 0,
    });
  });

  it('DevelopmentWorkspace discards out-of-order delayed responses when project switches rapidly', async () => {
    let resolveSlow: (val: any) => void;
    const slowPromise = new Promise((resolve) => {
      resolveSlow = resolve;
    });

    vi.spyOn(developmentVersionApi, 'listVersions').mockImplementation((projectId: string) => {
      if (projectId === 'proj-slow') {
        return slowPromise as Promise<any>;
      }
      if (projectId === 'proj-fast') {
        return Promise.resolve({
          items: [mockVersionFast],
          total: 1,
          limit: 50,
          offset: 0,
        });
      }
      return Promise.resolve({ items: [], total: 0, limit: 50, offset: 0 });
    });

    function TestDevSwitcher() {
      const { selectProject } = useProject();
      return (
        <div>
          <button onClick={() => selectProject(mockProjectA)}>Select Slow</button>
          <button onClick={() => selectProject(mockProjectB)}>Select Fast</button>
          <DevelopmentWorkspace />
        </div>
      );
    }

    render(
      <QueryClientProvider client={queryClient}>
        <ProjectProvider>
          <TestDevSwitcher />
        </ProjectProvider>
      </QueryClientProvider>
    );

    // 1. User starts on Slow Project (triggers inflight slowPromise)
    act(() => {
      screen.getByText('Select Slow').click();
    });

    // 2. User immediately switches to Fast Project before Slow finishes
    act(() => {
      screen.getByText('Select Fast').click();
    });

    // Fast project data resolves and should be displayed
    expect(await screen.findByText('Modern Clean Architecture')).toBeInTheDocument();
    expect(screen.getAllByText('fast_main.ts').length).toBeGreaterThan(0);

    // 3. Now the delayed slow response resolves late
    act(() => {
      resolveSlow({
        items: [mockVersionSlow],
        total: 1,
        limit: 50,
        offset: 0,
      });
    });

    // Wait a tick to ensure any unhandled promise callbacks would have executed
    await new Promise((r) => setTimeout(r, 50));

    // Stale slow project data must NOT contaminate the UI
    expect(screen.queryByText('Legacy Slow Architecture')).not.toBeInTheDocument();
    expect(screen.queryByText('slow_legacy.py')).not.toBeInTheDocument();

    // Fast project data remains firmly active
    expect(screen.getByText('Modern Clean Architecture')).toBeInTheDocument();
    expect(screen.getAllByText('fast_main.ts').length).toBeGreaterThan(0);
  });

  it('OverviewWorkspace filters out stale cross-project context when switching projects', async () => {
    vi.spyOn(contextApi, 'getContext').mockImplementation(async (projectId: string) => {
      if (projectId === 'proj-slow') {
        return {
          project: mockProjectA as any,
          requirements: [],
          schemas: [],
          endpoints: [],
          tasks: [],
          statistics: { total_requirements: 42, active_requirements: 40, completion_percentage: 95 },
        } as any;
      }
      if (projectId === 'proj-fast') {
        return {
          project: mockProjectB as any,
          requirements: [],
          schemas: [],
          endpoints: [],
          tasks: [],
          statistics: { total_requirements: 5, active_requirements: 5, completion_percentage: 100 },
        } as any;
      }
      throw new Error('Project not found');
    });

    function TestOverviewSwitcher() {
      const { selectProject } = useProject();
      return (
        <div>
          <button onClick={() => selectProject(mockProjectA)}>Select Slow</button>
          <button onClick={() => selectProject(mockProjectB)}>Select Fast</button>
          <OverviewWorkspace />
        </div>
      );
    }

    render(
      <QueryClientProvider client={queryClient}>
        <ProjectProvider>
          <TestOverviewSwitcher />
        </ProjectProvider>
      </QueryClientProvider>
    );

    // 1. Select Project A
    act(() => {
      screen.getByText('Select Slow').click();
    });

    expect(await screen.findByText('Slow Legacy Project')).toBeInTheDocument();
    expect(await screen.findByText('42')).toBeInTheDocument();

    // 2. Switch to Project B
    act(() => {
      screen.getByText('Select Fast').click();
    });

    expect(await screen.findByText('Fast Modern Project')).toBeInTheDocument();
    expect((await screen.findAllByText('5')).length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText('42')).not.toBeInTheDocument();
  });
});
