import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ArtifactViewer } from '../components/artifacts/ArtifactViewer';
import { sandboxApi } from '../services/sandboxApi';
import { CodeGenerationOutput } from '../types/artifacts';
import { StaticAnalysisResult } from '../types/sandbox';

describe('Static Analysis UI in CodeGenerationArtifact', () => {
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
        content: 'import os\ndef add(a, b): return a + b',
        language: 'python',
        size_bytes: 38,
      },
      {
        path: 'tests/test_main.py',
        content: 'def test_add(): assert 1 == 1',
        language: 'python',
        size_bytes: 30,
      },
    ],
    total_files: 2,
    total_size_bytes: 68,
    summary: 'FastAPI scaffold with tests.',
  };

  const mockAnalysisResult: StaticAnalysisResult = {
    analysis_id: 'sa-test-123',
    project_id: 'project-123',
    artifact_id: 'exec-456',
    status: 'ISSUES_FOUND',
    duration_seconds: 0.12,
    diagnostics: [
      {
        diagnostic_id: 'diag-1',
        category: 'LINT',
        severity: 'WARNING',
        code: 'F401',
        message: "'os' imported but unused",
        file_path: 'app/main.py',
        line: 1,
        column: 8,
        source: 'ruff',
        evidence: 'import os',
        metadata: {},
      },
      {
        diagnostic_id: 'diag-2',
        category: 'TEST',
        severity: 'INFO',
        code: 'TEST_DISCOVERED',
        message: 'Discovered 1 test files: tests/test_main.py',
        file_path: 'tests/test_main.py',
        source: 'test_discovery',
        evidence: null,
        metadata: { test_file_count: 1 },
      },
    ],
    files_analyzed: 2,
    files_skipped: 0,
    error_count: 0,
    warning_count: 1,
    info_count: 1,
    security_issue_count: 0,
    syntax_error_count: 0,
    lint_issue_count: 1,
    test_file_count: 1,
    summary: 'Static analysis completed with 1 issues.',
    metadata: {},
  };

  it('renders Run Static Analysis button and triggers analysis on click', async () => {
    vi.spyOn(sandboxApi, 'runStaticAnalysis').mockResolvedValue(mockAnalysisResult);

    render(
      <ArtifactViewer
        artifacts={{ 'code-generation': mockArtifact }}
        projectId="project-123"
        workflowExecutionId="exec-456"
      />
    );

    const runAnalysisBtn = screen.getByText('Run Static Analysis');
    expect(runAnalysisBtn).toBeInTheDocument();

    fireEvent.click(runAnalysisBtn);

    await waitFor(() => {
      expect(screen.getByText('ISSUES FOUND')).toBeInTheDocument();
    });

    expect(screen.getByText('Errors:')).toBeInTheDocument();
    expect(screen.getByText('Warnings:')).toBeInTheDocument();
    expect(screen.getByText('Info:')).toBeInTheDocument();
    expect(screen.getByText("'os' imported but unused")).toBeInTheDocument();
    expect(screen.getByText("Discovered 1 test files: tests/test_main.py")).toBeInTheDocument();
  });

  it('renders pre-existing static analysis result from workflow artifacts', () => {
    render(
      <ArtifactViewer
        artifacts={{
          'code-generation': mockArtifact,
          'static_analysis': mockAnalysisResult,
        }}
        projectId="project-123"
        workflowExecutionId="exec-456"
      />
    );

    expect(screen.getByText('ISSUES FOUND')).toBeInTheDocument();
    expect(screen.getByText("'os' imported but unused")).toBeInTheDocument();
  });

  it('clicking a diagnostic selects the relevant file in the code viewer', async () => {
    vi.spyOn(sandboxApi, 'runStaticAnalysis').mockResolvedValue(mockAnalysisResult);

    render(
      <ArtifactViewer
        artifacts={{ 'code-generation': mockArtifact }}
        projectId="project-123"
        workflowExecutionId="exec-456"
      />
    );

    fireEvent.click(screen.getByText('Run Static Analysis'));

    await waitFor(() => {
      expect(screen.getByText("Discovered 1 test files: tests/test_main.py")).toBeInTheDocument();
    });

    // Click on the test_discovery diagnostic row
    const testDiagRow = screen.getByText("Discovered 1 test files: tests/test_main.py");
    fireEvent.click(testDiagRow);

    // The active code view should now display tests/test_main.py content
    expect(screen.getByText('def test_add(): assert 1 == 1')).toBeInTheDocument();
  });
});
