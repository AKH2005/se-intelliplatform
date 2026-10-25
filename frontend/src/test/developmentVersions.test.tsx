import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ProjectProvider } from '../context/ProjectContext';
import { DevelopmentWorkspace } from '../views/DevelopmentWorkspace';
import { developmentVersionApi } from '../services/developmentVersionApi';
import {
  DevelopmentVersionListResponse,
  DevelopmentVersionResponse,
  VerificationSnapshot,
} from '../types/developmentVersion';

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <ProjectProvider>{ui}</ProjectProvider>
    </QueryClientProvider>
  );
}

describe('Phase 11H: Continuous Engineering Loop & Development Workspace UI', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.setItem('se_intelliplatform_active_project_id', 'proj-test-11h');
  });

  const mockSnapshot: VerificationSnapshot = {
    verification_status: 'PASSED',
    is_verified: true,
    summary: 'All required verification stages passed cleanly',
    static_analysis: {
      stage: 'static_analysis',
      requirement_level: 'REQUIRED',
      status: 'PASSED',
      details: 'Ruff passed with 0 errors',
      error_count: 0,
      warning_count: 0,
      blocking_issues: [],
    },
    sandbox_execution: {
      stage: 'sandbox_execution',
      requirement_level: 'REQUIRED',
      status: 'PASSED',
      details: 'Tests passed in Docker sandbox (1 passed)',
      error_count: 0,
      warning_count: 0,
      blocking_issues: [],
    },
    ai_tests: {
      stage: 'ai_tests',
      requirement_level: 'OPTIONAL',
      status: 'NOT_RUN',
      details: 'No AI tests generated for version',
      error_count: 0,
      warning_count: 0,
      blocking_issues: [],
    },
    failure_analysis: {
      stage: 'failure_analysis',
      requirement_level: 'OPTIONAL',
      status: 'NOT_RUN',
      details: 'No failures diagnosed',
      error_count: 0,
      warning_count: 0,
      blocking_issues: [],
    },
    verified_at: new Date().toISOString(),
  };

  const mockVersions: DevelopmentVersionResponse[] = [
    {
      version_id: 'ver-uuid-1',
      project_id: 'proj-test-11h',
      version_number: 1,
      artifact_key: 'code-generation',
      status: 'SUPERSEDED',
      is_active: false,
      content_hash: '1111111111111111222222222222222233333333333333334444444444444444',
      manifest_hash: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
      file_count: 2,
      total_size_bytes: 2048,
      source_reason: 'INITIAL_CREATION',
      created_by: 'system',
      requirement_ids: ['REQ-1'],
      files_manifest: [
        {
          path: 'app/main.py',
          size_bytes: 1024,
          language: 'python',
          requirement_ids: ['REQ-1'],
        },
        {
          path: 'tests/test_main.py',
          size_bytes: 1024,
          language: 'python',
          requirement_ids: ['REQ-1'],
        },
      ],
      verification_summary: mockSnapshot,
      created_at: new Date().toISOString(),
    },
    {
      version_id: 'ver-uuid-2',
      project_id: 'proj-test-11h',
      version_number: 2,
      parent_version_id: 'ver-uuid-1',
      artifact_key: 'code-generation',
      status: 'ACTIVE',
      is_active: true,
      content_hash: '5555555555555555666666666666666677777777777777778888888888888888',
      manifest_hash: 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
      file_count: 2,
      total_size_bytes: 2100,
      source_reason: 'REMEDIATION_PATCH',
      created_by: 'remediation_service',
      requirement_ids: ['REQ-1'],
      files_manifest: [
        {
          path: 'app/main.py',
          size_bytes: 1050,
          language: 'python',
          requirement_ids: ['REQ-1'],
        },
        {
          path: 'tests/test_main.py',
          size_bytes: 1050,
          language: 'python',
          requirement_ids: ['REQ-1'],
        },
      ],
      verification_summary: mockSnapshot,
      created_at: new Date().toISOString(),
    },
  ];

  const mockListResponse: DevelopmentVersionListResponse = {
    items: mockVersions,
    total: 2,
    active_version_id: 'ver-uuid-2',
  };

  it('renders Active Version banner and timeline with v1 and v2', async () => {
    vi.spyOn(developmentVersionApi, 'listVersions').mockResolvedValue(mockListResponse);
    vi.spyOn(developmentVersionApi, 'getVersionFileContent').mockResolvedValue('def main(): return 42\n');

    renderWithProviders(<DevelopmentWorkspace />);

    expect(await screen.findByText('Active Release: v2')).toBeInTheDocument();
    expect(screen.getByText('Version Timeline')).toBeInTheDocument();
    expect(screen.getByText('v1')).toBeInTheDocument();
    expect(screen.getByText('v2')).toBeInTheDocument();
    expect(screen.getByText('LIVE LOOP')).toBeInTheDocument();
  });

  it('renders Deterministic Verification Gate stage cards on tab click', async () => {
    vi.spyOn(developmentVersionApi, 'listVersions').mockResolvedValue(mockListResponse);
    vi.spyOn(developmentVersionApi, 'getVersionFileContent').mockResolvedValue('def main(): return 42\n');

    renderWithProviders(<DevelopmentWorkspace />);

    expect(await screen.findByText('Active Release: v2')).toBeInTheDocument();

    const verGateTab = screen.getByRole('button', { name: /Verification Gate/i });
    fireEvent.click(verGateTab);

    expect(await screen.findByText('Deterministic Verification Snapshot')).toBeInTheDocument();
    expect(screen.getByText('Static Analysis')).toBeInTheDocument();
    expect(screen.getByText('Docker Sandbox')).toBeInTheDocument();
    expect(screen.getByText('AI Test Suite')).toBeInTheDocument();
    expect(screen.getByText('Failure Analysis')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Recompute Verification Gate/i })).toBeInTheDocument();
  });

  it('allows user to roll back active version pointer to v1', async () => {
    vi.spyOn(developmentVersionApi, 'listVersions').mockResolvedValue(mockListResponse);
    vi.spyOn(developmentVersionApi, 'getVersionFileContent').mockResolvedValue('def main(): return 1\n');
    const rollbackSpy = vi.spyOn(developmentVersionApi, 'rollbackVersion').mockResolvedValue({
      ...mockVersions[0],
      is_active: true,
      status: 'ACTIVE',
    });

    renderWithProviders(<DevelopmentWorkspace />);

    expect(await screen.findByText('Active Release: v2')).toBeInTheDocument();

    // Select v1 from timeline
    const v1Node = screen.getByText('v1');
    fireEvent.click(v1Node);

    // Rollback button should appear for v1
    const rollbackBtn = await screen.findByRole('button', { name: /Rollback to v1/i });
    fireEvent.click(rollbackBtn);

    // Modal opens
    expect(await screen.findByText('Rollback to Version v1')).toBeInTheDocument();
    const confirmBtn = screen.getByRole('button', { name: /Confirm Rollback/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(rollbackSpy).toHaveBeenCalledWith('proj-test-11h', 'ver-uuid-1', undefined);
    });
  });
});
