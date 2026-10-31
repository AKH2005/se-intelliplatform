import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ProjectProvider } from '../context/ProjectContext';
import { CodeStudioWorkspace } from '../views/CodeStudioWorkspace';
import { FileExplorer } from '../components/studio/FileExplorer';
import { CodeEditor } from '../components/studio/CodeEditor';
import { UnsavedChangesModal } from '../components/studio/UnsavedChangesModal';
import { ValidationPanel } from '../components/studio/ValidationPanel';
import { codeStudioApi } from '../services/codeStudioApi';
import { developmentVersionApi } from '../services/developmentVersionApi';
import { workflowsApi } from '../services/workflowsApi';
import { FileTreeResponse, FileContentResponse, SaveFileResponse } from '../types/codeStudio';
import { DevelopmentVersionListResponse } from '../types/developmentVersion';

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

describe('Phase 2 Master Implementation: Integrated Code Studio UI', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.setItem('se_intelliplatform_active_project_id', 'proj-studio-test');
  });

  const mockFileTree: FileTreeResponse = {
    project_id: 'proj-studio-test',
    version_id: 'ver-111',
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
            size_bytes: 150,
            language: 'python',
          },
          {
            id: 'app/models.py',
            name: 'models.py',
            path: 'app/models.py',
            type: 'file',
            size_bytes: 220,
            language: 'python',
          },
        ],
      },
      {
        id: 'README.md',
        name: 'README.md',
        path: 'README.md',
        type: 'file',
        size_bytes: 80,
        language: 'markdown',
      },
    ],
  };

  const mockFileContent: FileContentResponse = {
    path: 'app/main.py',
    name: 'main.py',
    language: 'python',
    content: "def run():\n    return 'hello studio'\n",
    size_bytes: 35,
    version_id: 'ver-111',
    version_number: 1,
    content_hash: 'hash-abc-123',
  };

  const mockVersionsList: DevelopmentVersionListResponse = {
    items: [
      {
        version_id: 'ver-111',
        project_id: 'proj-studio-test',
        version_number: 1,
        artifact_key: 'code-generation',
        status: 'VERIFIED' as any,
        is_active: true,
        content_hash: 'hash-111',
        manifest_hash: 'man-111',
        file_count: 3,
        total_size_bytes: 450,
        source_reason: 'INITIAL_GENERATION',
        created_by: 'system',
        requirement_ids: [],
        files_manifest: [],
        created_at: '2026-10-26T10:00:00Z',
      },
    ],
    total: 1,
    active_version_id: 'ver-111',
  };

  it('renders FileExplorer with directory expansion and file nodes', () => {
    const handleSelect = vi.fn();
    const handleRefresh = vi.fn();

    render(
      <FileExplorer
        rootNodes={mockFileTree.root_nodes}
        selectedFilePath={null}
        dirtyFilePath={null}
        onSelectFile={handleSelect}
        onRefresh={handleRefresh}
        isLoading={false}
        hasGeneratedCode={true}
      />
    );

    // Verify root directory and top-level file are visible
    expect(screen.getByText('app')).toBeDefined();
    expect(screen.getByText('README.md')).toBeDefined();

    // Verify children within default expanded directory
    expect(screen.getByText('main.py')).toBeDefined();
    expect(screen.getByText('models.py')).toBeDefined();

    // Clicking file calls onSelectFile
    fireEvent.click(screen.getByText('main.py'));
    expect(handleSelect).toHaveBeenCalledWith('app/main.py');
  });

  it('renders empty project state when hasGeneratedCode is false', () => {
    render(
      <FileExplorer
        rootNodes={[]}
        selectedFilePath={null}
        dirtyFilePath={null}
        onSelectFile={vi.fn()}
        onRefresh={vi.fn()}
        isLoading={false}
        hasGeneratedCode={false}
      />
    );

    expect(screen.getByText('No Source Files Yet')).toBeDefined();
    expect(screen.getByText(/Source code has not yet been generated/)).toBeDefined();
  });

  it('renders CodeEditor with line numbers gutter and status bar', () => {
    const handleChange = vi.fn();
    const handleSave = vi.fn();

    render(
      <CodeEditor
        filePath="app/main.py"
        content={'line 1\nline 2\nline 3'}
        language="python"
        isDirty={false}
        isLoading={false}
        isSaving={false}
        onChangeContent={handleChange}
        onSave={handleSave}
      />
    );

    // Gutter line numbers
    expect(screen.getByText('1')).toBeDefined();
    expect(screen.getByText('2')).toBeDefined();
    expect(screen.getByText('3')).toBeDefined();

    // Status bar
    expect(screen.getByText('3 lines')).toBeDefined();
    expect(screen.getByText(/python/i)).toBeDefined();
    expect(screen.getByText('UTF-8')).toBeDefined();

    // Textarea content
    const textarea = screen.getByPlaceholderText('Enter source code...') as HTMLTextAreaElement;
    expect(textarea.value).toBe('line 1\nline 2\nline 3');

    // Editing code triggers change callback
    fireEvent.change(textarea, { target: { value: 'line 1\nline 2\nline 3\nline 4' } });
    expect(handleChange).toHaveBeenCalledWith('line 1\nline 2\nline 3\nline 4');
  });

  it('triggers Ctrl+S / Cmd+S keyboard shortcut to save when dirty', () => {
    const handleSave = vi.fn();

    render(
      <CodeEditor
        filePath="app/main.py"
        content="some code"
        language="python"
        isDirty={true}
        isLoading={false}
        isSaving={false}
        onChangeContent={vi.fn()}
        onSave={handleSave}
      />
    );

    const textarea = screen.getByPlaceholderText('Enter source code...');
    fireEvent.keyDown(textarea, { key: 's', ctrlKey: true });
    expect(handleSave).toHaveBeenCalledTimes(1);
  });

  it('UnsavedChangesModal presents Save, Discard, and Cancel options', () => {
    const handleSaveProceed = vi.fn();
    const handleDiscardProceed = vi.fn();
    const handleCancel = vi.fn();

    render(
      <UnsavedChangesModal
        isOpen={true}
        filePath="app/main.py"
        onSaveAndProceed={handleSaveProceed}
        onDiscardAndProceed={handleDiscardProceed}
        onCancel={handleCancel}
      />
    );

    expect(screen.getByText('Unsaved Changes')).toBeDefined();
    expect(screen.getByText(/You have unsaved modifications in/)).toBeDefined();

    fireEvent.click(screen.getByText('Cancel'));
    expect(handleCancel).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByText('Discard Changes'));
    expect(handleDiscardProceed).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByText(/Save & Continue/));
    expect(handleSaveProceed).toHaveBeenCalledTimes(1);
  });

  it('ValidationPanel accurately displays success, syntax errors, and conflict states', () => {
    const handleReload = vi.fn();

    // 1. Success state
    const { rerender } = render(
      <ValidationPanel
        data={{
          status: 'success',
          message: "File 'app/main.py' saved successfully.",
          newVersionNumber: 2,
        }}
      />
    );
    expect(screen.getByText('SAVED & VERIFIED')).toBeDefined();
    expect(screen.getByText('Active: v2')).toBeDefined();

    // 2. Syntax error state
    rerender(
      <ValidationPanel
        data={{
          status: 'syntax_error',
          message: 'Python syntax validation failed.',
          stageOutcome: {
            stage: 'syntax_validation',
            status: 'FAILED',
            message: 'Syntax error',
            errors: ['Line 4, Column 10: invalid syntax'],
            warnings: [],
          },
        }}
      />
    );
    expect(screen.getByText('SYNTAX VALIDATION FAILED')).toBeDefined();
    expect(screen.getByText('Line 4, Column 10: invalid syntax')).toBeDefined();

    // 3. Concurrency conflict state
    rerender(
      <ValidationPanel
        data={{
          status: 'conflict',
          message: 'Conflict: Active version advanced.',
          conflictDetails: 'The project was updated since you opened this file.',
        }}
        onReloadLatest={handleReload}
      />
    );
    expect(screen.getByText('VERSION CONFLICT')).toBeDefined();
    expect(screen.getByText('Reload Latest Version')).toBeDefined();

    fireEvent.click(screen.getByText('Reload Latest Version'));
    expect(handleReload).toHaveBeenCalledTimes(1);
  });

  it('loads file tree, opens file, edits content, and executes save in CodeStudioWorkspace', async () => {
    vi.spyOn(developmentVersionApi, 'list').mockResolvedValue(mockVersionsList);
    vi.spyOn(codeStudioApi, 'getFileTree').mockResolvedValue(mockFileTree);
    vi.spyOn(codeStudioApi, 'getFileContent').mockResolvedValue(mockFileContent);

    const mockSaveResponse: SaveFileResponse = {
      success: true,
      project_id: 'proj-studio-test',
      version_id: 'ver-222',
      version_number: 2,
      parent_version_id: 'ver-111',
      path: 'app/main.py',
      size_bytes: 45,
      content_hash: 'hash-new-222',
      version_content_hash: 'vhash-222',
      validation: {
        stage: 'syntax_validation',
        status: 'PASSED',
        message: 'Syntax validation passed.',
        errors: [],
        warnings: [],
      },
      message: "File 'app/main.py' saved. Created immutable version v2.",
    };
    vi.spyOn(codeStudioApi, 'saveFileContent').mockResolvedValue(mockSaveResponse);

    renderWithProviders(<CodeStudioWorkspace />);

    // Wait for file tree to load
    await waitFor(() => {
      expect(screen.getByText('main.py')).toBeDefined();
    });

    // Click file to open in editor
    fireEvent.click(screen.getByText('main.py'));

    await waitFor(() => {
      expect(codeStudioApi.getFileContent).toHaveBeenCalledWith('proj-studio-test', 'app/main.py', 'ver-111');
    });

    // Verify editor displays loaded code
    const textarea = screen.getByPlaceholderText('Enter source code...') as HTMLTextAreaElement;
    expect(textarea.value).toBe("def run():\n    return 'hello studio'\n");

    // Make an edit
    fireEvent.change(textarea, { target: { value: "def run():\n    return 'hello studio v2'\n" } });

    // Click Save File in toolbar
    const saveButton = screen.getByRole('button', { name: /Save File/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(codeStudioApi.saveFileContent).toHaveBeenCalledWith(
        'proj-studio-test',
        'app/main.py',
        expect.objectContaining({
          content: "def run():\n    return 'hello studio v2'\n",
          parent_version_id: 'ver-111',
        })
      );
    });

    // Verification result displayed in bottom panel
    await waitFor(() => {
      expect(screen.getByText(/SAVED & VERIFIED/i)).toBeDefined();
    });
  });

  it('retains unsaved content and displays error when save fails with syntax error', async () => {
    vi.spyOn(developmentVersionApi, 'list').mockResolvedValue(mockVersionsList);
    vi.spyOn(codeStudioApi, 'getFileTree').mockResolvedValue(mockFileTree);
    vi.spyOn(codeStudioApi, 'getFileContent').mockResolvedValue(mockFileContent);

    // Mock 422 error
    const validationError = {
      status: 422,
      response: {
        status: 422,
        data: {
          detail: 'Syntax validation failed for app/main.py',
          errors: [{ message: 'Line 2, Column 5: SyntaxError: invalid syntax' }],
        },
      },
    };
    vi.spyOn(codeStudioApi, 'saveFileContent').mockRejectedValue(validationError);

    renderWithProviders(<CodeStudioWorkspace />);

    await waitFor(() => {
      expect(screen.getByText('main.py')).toBeDefined();
    });

    fireEvent.click(screen.getByText('main.py'));

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Enter source code...')).toBeDefined();
    });

    const textarea = screen.getByPlaceholderText('Enter source code...') as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: 'def broken(:\n    return False' } });

    const saveButton = screen.getByRole('button', { name: /Save File/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(codeStudioApi.saveFileContent).toHaveBeenCalled();
    });

    // Verify error is displayed
    await waitFor(() => {
      expect(screen.getAllByText(/SYNTAX VALIDATION FAILED/i).length).toBeGreaterThan(0);
      expect(screen.getByText(/Line 2, Column 5: SyntaxError: invalid syntax/i)).toBeDefined();
    });

    // CRITICAL: Verify the user's edited text was NOT lost or overwritten!
    expect(textarea.value).toBe('def broken(:\n    return False');
  });

  it('prompts user with UnsavedChangesModal when attempting to switch files with unsaved edits', async () => {
    vi.spyOn(developmentVersionApi, 'list').mockResolvedValue(mockVersionsList);
    vi.spyOn(codeStudioApi, 'getFileTree').mockResolvedValue(mockFileTree);
    vi.spyOn(codeStudioApi, 'getFileContent').mockResolvedValue(mockFileContent);

    renderWithProviders(<CodeStudioWorkspace />);

    await waitFor(() => {
      expect(screen.getByText('main.py')).toBeDefined();
    });

    // Open first file
    fireEvent.click(screen.getByText('main.py'));

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Enter source code...')).toBeDefined();
    });

    const textarea = screen.getByPlaceholderText('Enter source code...') as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: 'def modified(): pass' } });

    // Now try to open README.md without saving
    fireEvent.click(screen.getByText('README.md'));

    // Modal should appear
    await waitFor(() => {
      expect(screen.getByText('Unsaved Changes')).toBeDefined();
      expect(screen.getByText(/You have unsaved modifications in/)).toBeDefined();
    });

    // Clicking Cancel closes modal and stays on main.py
    fireEvent.click(screen.getByText('Cancel'));
    expect(textarea.value).toBe('def modified(): pass');
  });

  it('FileExplorer displays empty state, disables button during generation, and renders generationError', () => {
    const handleGenerate = vi.fn();

    const { rerender } = render(
      <FileExplorer
        rootNodes={[]}
        selectedFilePath={null}
        dirtyFilePath={null}
        onSelectFile={vi.fn()}
        onRefresh={vi.fn()}
        isLoading={false}
        hasGeneratedCode={false}
        onGenerateCode={handleGenerate}
        isGeneratingCode={false}
      />
    );

    expect(screen.getByText('No Source Files Yet')).toBeDefined();
    const generateBtn = screen.getByRole('button', { name: /Generate Initial Code/i });
    expect(generateBtn).toBeDefined();

    fireEvent.click(generateBtn);
    expect(handleGenerate).toHaveBeenCalledTimes(1);

    // Re-render with error
    rerender(
      <FileExplorer
        rootNodes={[]}
        selectedFilePath={null}
        dirtyFilePath={null}
        onSelectFile={vi.fn()}
        onRefresh={vi.fn()}
        isLoading={false}
        hasGeneratedCode={false}
        onGenerateCode={handleGenerate}
        isGeneratingCode={false}
        generationError="Groq transient error (APIStatusError): Rate limit exceeded"
      />
    );

    expect(screen.getByText('Generation Failed')).toBeDefined();
    expect(screen.getByText(/Rate limit exceeded/i)).toBeDefined();
  });

  it('CodeStudioWorkspace handles failed code generation workflow and displays error without wiping UI', async () => {
    const emptyFileTree: FileTreeResponse = {
      project_id: 'proj-studio-test',
      version_id: null,
      version_number: null,
      has_generated_code: false,
      total_files: 0,
      root_nodes: [],
    };
    const emptyVersions: DevelopmentVersionListResponse = {
      items: [],
      total: 0,
      active_version_id: null,
    };

    vi.spyOn(developmentVersionApi, 'list').mockResolvedValue(emptyVersions);
    vi.spyOn(codeStudioApi, 'getFileTree').mockResolvedValue(emptyFileTree);

    // Mock failed workflow result (HTTP 200 with status: 'FAILED')
    const failedWorkflowResult = {
      workflow_execution_id: 'exec-fail-123',
      workflow_id: 'code-generation-workflow',
      workflow_version: '1.0.0',
      status: 'FAILED' as any,
      started_at: '2026-10-26T10:00:00Z',
      completed_at: '2026-10-26T10:00:05Z',
      step_results: [],
      artifacts: {},
      errors: ["Step 'database-design' failed: Groq transient error (APIStatusError): Rate limit exceeded"],
      warnings: [],
      metadata: {},
    };
    vi.spyOn(workflowsApi, 'execute').mockResolvedValue(failedWorkflowResult);

    renderWithProviders(<CodeStudioWorkspace />);

    // Wait for empty state
    await waitFor(() => {
      expect(screen.getByText('No Source Files Yet')).toBeDefined();
    });

    const generateBtn = screen.getByRole('button', { name: /Generate Initial Code/i });
    fireEvent.click(generateBtn);

    // Verify workflowsApi.execute was called
    await waitFor(() => {
      expect(workflowsApi.execute).toHaveBeenCalledWith('code-generation-workflow', {
        project_id: 'proj-studio-test',
      });
    });

    // Verify error is rendered in FileExplorer and ValidationPanel
    await waitFor(() => {
      expect(screen.getAllByText(/Generation Failed/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Rate limit exceeded/i).length).toBeGreaterThan(0);
    });
  });

  it('CodeStudioWorkspace refreshes workspace and loads files when code generation succeeds', async () => {
    const emptyFileTree: FileTreeResponse = {
      project_id: 'proj-studio-test',
      version_id: null,
      version_number: null,
      has_generated_code: false,
      total_files: 0,
      root_nodes: [],
    };
    const emptyVersions: DevelopmentVersionListResponse = {
      items: [],
      total: 0,
      active_version_id: null,
    };

    // First list call returns empty, second call returns mockVersionsList
    const listSpy = vi.spyOn(developmentVersionApi, 'list')
      .mockResolvedValueOnce(emptyVersions)
      .mockResolvedValue(mockVersionsList);

    // First tree call returns empty, second call returns mockFileTree
    const treeSpy = vi.spyOn(codeStudioApi, 'getFileTree')
      .mockResolvedValueOnce(emptyFileTree)
      .mockResolvedValue(mockFileTree);

    // Mock successful workflow
    const successWorkflowResult = {
      workflow_execution_id: 'exec-success-123',
      workflow_id: 'code-generation-workflow',
      workflow_version: '1.0.0',
      status: 'COMPLETED' as any,
      started_at: '2026-10-26T10:00:00Z',
      completed_at: '2026-10-26T10:00:05Z',
      step_results: [],
      artifacts: { 'code-generation': {} },
      errors: [],
      warnings: [],
      metadata: {},
    };
    vi.spyOn(workflowsApi, 'execute').mockResolvedValue(successWorkflowResult);

    renderWithProviders(<CodeStudioWorkspace />);

    await waitFor(() => {
      expect(screen.getByText('No Source Files Yet')).toBeDefined();
    });

    const generateBtn = screen.getByRole('button', { name: /Generate Initial Code/i });
    fireEvent.click(generateBtn);

    await waitFor(() => {
      expect(workflowsApi.execute).toHaveBeenCalledWith('code-generation-workflow', {
        project_id: 'proj-studio-test',
      });
    });

    // After success, file tree is reloaded and main.py becomes visible
    await waitFor(() => {
      expect(screen.getByText('main.py')).toBeDefined();
      expect(screen.getByText(/Initial project code scaffold generated successfully/i)).toBeDefined();
    });

    expect(listSpy).toHaveBeenCalled();
    expect(treeSpy).toHaveBeenCalled();
  });
});
