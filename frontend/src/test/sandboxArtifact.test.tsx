import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ArtifactViewer } from '../components/artifacts/ArtifactViewer';
import { sandboxApi } from '../services/sandboxApi';
import { CodeGenerationOutput } from '../types/artifacts';
import { ExecutionResult } from '../types/sandbox';

describe('CodeGenerationArtifact & Sandbox Test Runner UI', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  const mockArtifact: CodeGenerationOutput = {
    plan: {
      project_type: 'backend-service',
      language: 'python',
      framework: 'fastapi',
      database: 'postgresql',
      package_manager: 'pip',
      files: [
        { path: 'app/main.py', purpose: 'Entry point', file_type: 'SOURCE' },
        { path: 'tests/test_main.py', purpose: 'Unit tests', file_type: 'SOURCE' },
      ],
      rationale: 'Modular FastAPI service.',
    },
    generated_files: [
      {
        path: 'app/main.py',
        content: 'def add(a, b): return a + b',
        language: 'python',
        size_bytes: 27,
      },
      {
        path: 'tests/test_main.py',
        content: 'def test_add(): assert 1 == 1',
        language: 'python',
        size_bytes: 30,
      },
    ],
    total_files: 2,
    total_size_bytes: 57,
    summary: 'FastAPI scaffold with tests.',
  };

  it('renders code generation artifact with file list and initial file content', () => {
    render(
      <ArtifactViewer
        artifacts={{ 'code-generation': mockArtifact }}
        projectId="project-123"
        workflowExecutionId="exec-456"
      />
    );

    expect(screen.getByText(/PYTHON \/ FASTAPI Scaffold/i)).toBeInTheDocument();
    expect(screen.getAllByText('app/main.py').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('tests/test_main.py')).toBeInTheDocument();
    expect(screen.getByText('def add(a, b): return a + b')).toBeInTheDocument();
  });

  it('switches active file content when clicking a file from the manifest', () => {
    render(
      <ArtifactViewer
        artifacts={{ 'code-generation': mockArtifact }}
        projectId="project-123"
        workflowExecutionId="exec-456"
      />
    );

    const testFileBtn = screen.getByText('tests/test_main.py');
    fireEvent.click(testFileBtn);

    expect(screen.getByText('def test_add(): assert 1 == 1')).toBeInTheDocument();
  });

  it('triggers sandbox execution and displays passed execution result badge and metrics', async () => {
    const mockResult: ExecutionResult = {
      execution_id: 'sand-789',
      project_id: 'project-123',
      workflow_execution_id: 'exec-456',
      execution_type: 'TEST',
      status: 'PASSED',
      exit_code: 0,
      duration_seconds: 0.85,
      stdout: '1 passed in 0.05s',
      stderr: '',
      is_truncated: false,
      tests_passed: 1,
      tests_failed: 0,
      tests_total: 1,
      validation_errors: [],
      metadata: {},
    };

    vi.spyOn(sandboxApi, 'execute').mockResolvedValue(mockResult);

    render(
      <ArtifactViewer
        artifacts={{ 'code-generation': mockArtifact }}
        projectId="project-123"
        workflowExecutionId="exec-456"
      />
    );

    const runBtn = screen.getByText('Run Tests in Sandbox');
    fireEvent.click(runBtn);

    await waitFor(() => {
      expect(screen.getByText('PASSED')).toBeInTheDocument();
    });

    expect(screen.getByText('1 passed in 0.05s')).toBeInTheDocument();
    expect(screen.getByText(/Duration: 0.85s/i)).toBeInTheDocument();
  });
});
