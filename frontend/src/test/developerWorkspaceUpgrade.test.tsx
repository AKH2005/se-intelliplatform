import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ProjectProvider } from '../context/ProjectContext';
import { CodeStudioWorkspace } from '../views/CodeStudioWorkspace';
import { codeStudioApi } from '../services/codeStudioApi';
import { developmentVersionApi } from '../services/developmentVersionApi';
import { previewRuntimeApi } from '../services/previewRuntimeApi';
import { FileTreeResponse, FileContentResponse, SaveFileResponse } from '../types/codeStudio';
import { DevelopmentVersionListResponse } from '../types/developmentVersion';

function renderWithProviders(ui: React.ReactElement, initialProjectId: string = 'proj-dev-test') {
  localStorage.clear();
  localStorage.setItem('se_intelliplatform_active_project_id', initialProjectId);

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

describe('S-Tier Upgrade: Developer Mode & Code Studio Workspace', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    localStorage.setItem('se_intelliplatform_active_project_id', 'proj-dev-test');
  });

  const mockFileTree: FileTreeResponse = {
    project_id: 'proj-dev-test',
    version_id: 'ver-alpha-1',
    version_number: 1,
    has_generated_code: true,
    total_files: 3,
    root_nodes: [
      {
        id: 'app',
        name: 'app',
        path: 'app',
        type: 'directory',
        children: [
          {
            id: 'app/main.py',
            name: 'main.py',
            path: 'app/main.py',
            type: 'file',
            size_bytes: 240,
            language: 'python',
          },
          {
            id: 'app/routes.py',
            name: 'routes.py',
            path: 'app/routes.py',
            type: 'file',
            size_bytes: 180,
            language: 'python',
          },
        ],
      },
      {
        id: 'README.md',
        name: 'README.md',
        path: 'README.md',
        type: 'file',
        size_bytes: 90,
        language: 'markdown',
      },
    ],
  };

  const mockFileContent: FileContentResponse = {
    path: 'app/main.py',
    name: 'main.py',
    language: 'python',
    content: "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/')\ndef root():\n    return {'status': 'ok'}\n",
    size_bytes: 95,
    version_id: 'ver-alpha-1',
    version_number: 1,
    content_hash: 'hash-abc-001',
  };

  const mockVersionsList: DevelopmentVersionListResponse = {
    items: [
      {
        version_id: 'ver-alpha-1',
        project_id: 'proj-dev-test',
        version_number: 1,
        artifact_key: 'code-generation',
        status: 'VERIFIED' as any,
        is_active: true,
        content_hash: 'hash-ver-1',
        manifest_hash: 'man-ver-1',
        file_count: 3,
        total_size_bytes: 510,
        source_reason: 'INITIAL_GENERATION',
        created_by: 'system',
        requirement_ids: [],
        files_manifest: [],
        created_at: '2026-10-29T10:00:00Z',
      },
    ],
    total: 1,
    active_version_id: 'ver-alpha-1',
  };

  it('1. Renders the S-tier Code Studio toolbar with project context and panel controls', async () => {
    vi.spyOn(developmentVersionApi, 'list').mockResolvedValue(mockVersionsList);
    vi.spyOn(codeStudioApi, 'getFileTree').mockResolvedValue(mockFileTree);

    renderWithProviders(<CodeStudioWorkspace />);

    // Top Toolbar Brand & Controls
    expect(await screen.findByText('Code Studio')).toBeInTheDocument();
    expect(screen.getByText('v1 (Active)')).toBeInTheDocument();
    expect(screen.getByTitle('Refresh workspace files')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Download ZIP/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Split Preview/i })).toBeInTheDocument();

    // Explorer left panel
    expect(screen.getByText('Files & Folders')).toBeInTheDocument();
    expect(await screen.findByText('main.py')).toBeInTheDocument();
    expect(screen.getByText('README.md')).toBeInTheDocument();
  });

  it('2. Supports collapsing and expanding the Project Explorer panel', async () => {
    vi.spyOn(developmentVersionApi, 'list').mockResolvedValue(mockVersionsList);
    vi.spyOn(codeStudioApi, 'getFileTree').mockResolvedValue(mockFileTree);

    renderWithProviders(<CodeStudioWorkspace />);

    expect(await screen.findByText('Files & Folders')).toBeInTheDocument();

    // Collapse Explorer
    const toggleBtn = screen.getByTitle('Collapse Project Explorer');
    fireEvent.click(toggleBtn);

    // Explorer header is collapsed out of view
    expect(screen.queryByText('Files & Folders')).not.toBeInTheDocument();

    // Expand Explorer again
    const expandBtn = screen.getByTitle('Expand Project Explorer');
    fireEvent.click(expandBtn);

    expect(await screen.findByText('Files & Folders')).toBeInTheDocument();
  });

  it('3. Loads active file into CodeEditor with breadcrumb path and line numbers gutter', async () => {
    vi.spyOn(developmentVersionApi, 'list').mockResolvedValue(mockVersionsList);
    vi.spyOn(codeStudioApi, 'getFileTree').mockResolvedValue(mockFileTree);
    vi.spyOn(codeStudioApi, 'getFileContent').mockResolvedValue(mockFileContent);

    renderWithProviders(<CodeStudioWorkspace />);

    // Click on main.py
    const fileNode = await screen.findByText('main.py');
    fireEvent.click(fileNode);

    // Editor shows file tab and breadcrumbs
    expect(await screen.findByText('from fastapi import FastAPI', { exact: false })).toBeInTheDocument();
    expect(screen.getByTestId('line-numbers-gutter')).toBeInTheDocument();
    expect(screen.getByText(/UTF-8/i)).toBeInTheDocument();
    expect(screen.getByText(/python/i)).toBeInTheDocument();
    expect(screen.getByText('Save File')).toBeInTheDocument();
  });

  it('4. Toggles integrated Live Preview Split View alongside the Code Editor', async () => {
    vi.spyOn(developmentVersionApi, 'list').mockResolvedValue(mockVersionsList);
    vi.spyOn(codeStudioApi, 'getFileTree').mockResolvedValue(mockFileTree);
    vi.spyOn(previewRuntimeApi, 'getStatus').mockResolvedValue({
      status: 'RUNNING',
      port: 8001,
      active_mode: 'taskflow',
      is_healthy: true,
      detail: 'Running smoothly',
      preview_url: 'http://127.0.0.1:8001/',
    });

    renderWithProviders(<CodeStudioWorkspace />);

    await screen.findByText('Code Studio');

    // Split preview is initially closed
    expect(screen.queryByTitle('Live Application Preview')).not.toBeInTheDocument();

    // Toggle split preview
    const splitBtn = screen.getByRole('button', { name: /Split Preview/i });
    fireEvent.click(splitBtn);

    // Split pane appears with live preview iframe
    expect(await screen.findByTitle('Live Application Preview')).toBeInTheDocument();
    expect(screen.getByText(/RUNNING :8001/i)).toBeInTheDocument();

    // Viewport controls available
    expect(screen.getByTitle('Desktop View')).toBeInTheDocument();
    expect(screen.getByTitle('Tablet View')).toBeInTheDocument();
    expect(screen.getByTitle('Mobile View')).toBeInTheDocument();

    // Close split view
    fireEvent.click(splitBtn);
    expect(screen.queryByTitle('Live Application Preview')).not.toBeInTheDocument();
  });

  it('5. Saves modified code and displays verified outcome in ValidationPanel', async () => {
    vi.spyOn(developmentVersionApi, 'list').mockResolvedValue(mockVersionsList);
    vi.spyOn(codeStudioApi, 'getFileTree').mockResolvedValue(mockFileTree);
    vi.spyOn(codeStudioApi, 'getFileContent').mockResolvedValue(mockFileContent);

    const mockSaveResult: SaveFileResponse = {
      success: true,
      project_id: 'proj-dev-test',
      parent_version_id: 'ver-alpha-1',
      path: 'app/main.py',
      version_id: 'ver-alpha-2',
      version_number: 2,
      size_bytes: 120,
      content_hash: 'hash-new-002',
      version_content_hash: 'hash-version-002',
      message: 'Saved app/main.py and verified syntax',
      validation: {
        stage: 'syntax_validation',
        status: 'PASSED',
        message: 'AST check passed with 0 errors.',
        errors: [],
        warnings: [],
      },
    };
    vi.spyOn(codeStudioApi, 'saveFileContent').mockResolvedValue(mockSaveResult);

    renderWithProviders(<CodeStudioWorkspace />);

    const fileNode = await screen.findByText('main.py');
    fireEvent.click(fileNode);

    const textarea = await screen.findByPlaceholderText('Enter source code...');
    fireEvent.change(textarea, {
      target: { value: "from fastapi import FastAPI\napp = FastAPI()\n# updated\n" },
    });

    // Save File button is now active
    const saveBtn = screen.getByRole('button', { name: /Save File/i });
    expect(saveBtn).not.toBeDisabled();
    fireEvent.click(saveBtn);

    // ValidationPanel reports success
    expect(await screen.findByText('SAVED & VERIFIED')).toBeInTheDocument();
    expect(screen.getByText('Active: v2')).toBeInTheDocument();
  });
});
