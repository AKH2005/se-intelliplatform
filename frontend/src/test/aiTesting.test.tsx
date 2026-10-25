import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ArtifactViewer } from '../components/artifacts/ArtifactViewer';
import { aiTestingApi } from '../services/aiTestingApi';
import { CodeGenerationOutput } from '../types/artifacts';
import { AITestExecutionResult, AITestSuite } from '../types/aiTesting';

describe('Phase 11F: AI-Generated Testing UI', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  const mockArtifact: CodeGenerationOutput = {
    plan: {
      project_type: 'backend-service',
      language: 'python',
      framework: 'fastapi',
      database: 'sqlite',
      package_manager: 'pip',
      files: [
        { path: 'app/calculator.py', purpose: 'Math calculations', file_type: 'SOURCE' },
      ],
      rationale: 'Modular calculator service.',
    },
    generated_files: [
      {
        path: 'app/calculator.py',
        content: 'def add(a, b): return a + b\n',
        language: 'python',
        size_bytes: 30,
      },
    ],
    total_files: 1,
    total_size_bytes: 30,
    summary: 'Calculator scaffold.',
  };

  const mockTestSuite: AITestSuite = {
    suite_id: 'suite-1234-abcd',
    project_id: 'project-123',
    workflow_execution_id: 'exec-456',
    summary: 'Automated test suite for calculator module',
    tests: [
      {
        test_id: 'TEST-001',
        name: 'test_calculator_add',
        description: 'Verifies adding two numbers',
        category: 'HAPPY_PATH',
        target_file: 'app/calculator.py',
        target_symbol: 'add',
        requirement_ids: ['REQ-01'],
        architecture_component: 'CalculatorService',
        rationale: 'Ensures addition behaves properly',
        code: 'def test_calculator_add():\n    from app.calculator import add\n    assert add(2, 3) == 5\n',
        expected_behavior: 'Returns 5',
      },
    ],
    test_count: 1,
    requirement_traceability: { 'REQ-01': ['TEST-001'] },
    source_artifact_reference: 'code_generation',
    test_files: {
      'tests/test_ai_generated.py': 'def test_calculator_add():\n    assert 2 + 3 == 5\n',
    },
    created_at: new Date().toISOString(),
  };

  const mockExecutionResult: AITestExecutionResult = {
    execution_id: 'exec-res-123',
    suite_id: 'suite-1234-abcd',
    project_id: 'project-123',
    workflow_execution_id: 'exec-456',
    status: 'PASSED',
    exit_code: 0,
    duration_seconds: 0.12,
    tests_total: 1,
    tests_passed: 1,
    tests_failed: 0,
    tests_skipped: 0,
    stdout: 'tests/test_ai_generated.py::test_calculator_add PASSED [100%]\n1 passed in 0.12s',
    stderr: '',
    failure_summaries: [],
    test_results: [
      {
        name: 'test_calculator_add',
        status: 'PASSED',
        duration_seconds: 0.12,
        message: null,
      },
    ],
    executed_at: new Date().toISOString(),
  };

  it('renders Generate AI Tests button and displays generated suite on click', async () => {
    vi.spyOn(aiTestingApi, 'generateTests').mockResolvedValue(mockTestSuite);

    render(
      <ArtifactViewer
        artifacts={{ 'code-generation': mockArtifact }}
        projectId="project-123"
        workflowExecutionId="exec-456"
      />
    );

    const generateBtn = screen.getByText('Generate AI Tests');
    expect(generateBtn).toBeDefined();

    fireEvent.click(generateBtn);

    await waitFor(() => {
      expect(screen.getByText('AI-Generated Test Suite')).toBeDefined();
    });

    expect(screen.getByText('VALIDATED')).toBeDefined();
    expect(screen.getByText('Automated test suite for calculator module')).toBeDefined();
    expect(screen.getByText('test_calculator_add')).toBeDefined();
    expect(screen.getByText('TEST-001')).toBeDefined();
    expect(screen.getByText('Run AI Tests in Sandbox')).toBeDefined();
  });

  it('executes AI tests in ephemeral sandbox and displays results', async () => {
    vi.spyOn(aiTestingApi, 'executeTests').mockResolvedValue(mockExecutionResult);

    render(
      <ArtifactViewer
        artifacts={{
          'code-generation': mockArtifact,
          'ai_test_suite': mockTestSuite,
        }}
        projectId="project-123"
        workflowExecutionId="exec-456"
      />
    );

    expect(screen.getByText('AI-Generated Test Suite')).toBeDefined();
    const runBtn = screen.getByText('Run AI Tests in Sandbox');
    expect(runBtn).toBeDefined();

    fireEvent.click(runBtn);

    await waitFor(() => {
      expect(screen.getByText('Execution Outcome:')).toBeDefined();
    });

    expect(screen.getByText('1 / 1 passed in 0.12s')).toBeDefined();
    expect(screen.getByText(/Ephemeral Test Run/i)).toBeDefined();
  });
});
