import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CodeGenerationArtifact } from '../components/artifacts/CodeGenerationArtifact';
import { aiTestingApi } from '../services/aiTestingApi';
import { remediationApi } from '../services/remediationApi';
import { CodeGenerationOutput } from '../types/artifacts';
import { AITestSuite, AITestExecutionResult } from '../types/aiTesting';
import { FailureDiagnosis } from '../types/failureAnalysis';
import { RemediationProposal } from '../types/remediation';

describe('Phase 11G: AI Test Failure Analysis & Unified Verification UI', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  const mockArtifact: CodeGenerationOutput = {
    plan: {
      project_type: 'backend-service',
      language: 'python',
      framework: 'fastapi',
      database: 'none',
      package_manager: 'pip',
      files: [
        { path: 'app/calculator.py', purpose: 'Calculator logic', file_type: 'SOURCE' },
      ],
      rationale: 'Modular calculator implementation.',
    },
    generated_files: [
      {
        path: 'app/calculator.py',
        content: 'def divide(a, b):\n    return a / b\n',
        language: 'python',
        size_bytes: 40,
      },
    ],
    total_files: 1,
    total_size_bytes: 40,
    summary: 'Calculator project.',
  };

  const mockSuite: AITestSuite = {
    suite_id: 'suite-calc-101',
    project_id: 'project-123',
    summary: 'Calculator test suite',
    tests: [
      {
        test_id: 'TEST-001',
        name: 'test_divide_by_zero_raises',
        description: 'Verifies divide by zero raises ValueError',
        category: 'ERROR_HANDLING',
        target_file: 'app/calculator.py',
        target_symbol: 'divide',
        requirement_ids: [],
        rationale: 'Robustness check',
        code: 'def test_divide_by_zero_raises():\n    with pytest.raises(ValueError):\n        divide(10, 0)\n',
        expected_behavior: 'Raises ValueError',
      },
    ],
    test_count: 1,
    requirement_traceability: {},
    source_artifact_reference: 'code_generation',
    test_files: {
      'tests/test_ai_generated.py': 'def test_divide_by_zero_raises(): pass\n',
    },
    created_at: new Date().toISOString(),
  };

  const mockFailingExecution: AITestExecutionResult = {
    execution_id: 'exec-test-101',
    suite_id: 'suite-calc-101',
    project_id: 'project-123',
    status: 'FAILED',
    exit_code: 1,
    duration_seconds: 0.42,
    tests_total: 1,
    tests_passed: 0,
    tests_failed: 1,
    tests_skipped: 0,
    stdout: 'tests/test_ai_generated.py::test_divide_by_zero_raises FAILED [100%]',
    stderr: '',
    failure_summaries: [
      'ZeroDivisionError: division by zero in app/calculator.py:2',
    ],
    test_results: [
      {
        name: 'test_divide_by_zero_raises',
        status: 'FAILED',
        duration_seconds: 0.02,
        message: 'ZeroDivisionError: division by zero',
      },
    ],
    executed_at: new Date().toISOString(),
  };

  const mockDiagnosis: FailureDiagnosis = {
    diagnosis_id: 'diag-ai-test-999',
    failure_type: 'TEST_FAILURE',
    failure_source: 'AI_TEST',
    title: 'ZeroDivisionError in Calculator Division Handler',
    summary: 'AI test test_divide_by_zero_raises failed because division by zero was not guarded.',
    root_cause: 'The divide function does not check whether b == 0 before performing floating point division.',
    severity: 'ERROR',
    affected_files: ['app/calculator.py'],
    evidence: [
      {
        evidence_id: 'TEST-001',
        source: 'ai_test',
        code: 'test_divide_by_zero_raises',
        file_path: 'app/calculator.py',
        line: 2,
        snippet: 'return a / b',
        description: 'Failed assertion expecting handled ValueError',
      },
    ],
    claims: [
      {
        claim_type: 'FACT',
        statement: 'Test TEST-001 failed with ZeroDivisionError during division by zero.',
        evidence_ids: ['TEST-001'],
      },
      {
        claim_type: 'INTERPRETATION',
        statement: 'The function does not validate whether the denominator is non-zero.',
        evidence_ids: ['TEST-001'],
      },
    ],
    requirement_links: [],
    architecture_links: [],
    database_links: [],
    suggested_remediation: 'Verify that the denominator is non-zero before performing division.',
    limitations: ['Diagnosis based strictly on AI test execution trace and calculator module source.'],
    confidence: 'HIGH',
    model_metadata: {
      provider: 'groq',
      model: 'llama-3.3-70b-versatile',
    },
  };

  const mockProposal: RemediationProposal = {
    proposal_id: 'prop-101',
    diagnosis_id: 'diag-ai-test-999',
    project_id: 'project-123',
    title: 'Defensive Divisor Validation in Calculator',
    summary: 'Guard denominator against zero in divide function.',
    rationale: 'Preserves existing architecture while adding safety.',
    changes: [
      {
        file_path: 'app/calculator.py',
        operation: 'MODIFY',
        original_region: '    return a / b',
        proposed_region: '    if b == 0:\n        raise ValueError("Cannot divide by zero")\n    return a / b',
        reason: 'Raise ValueError on zero denominator',
        evidence_ids: ['TEST-001'],
      },
    ],
    affected_files: ['app/calculator.py'],
    unified_diff: '--- a/app/calculator.py\n+++ b/app/calculator.py\n@@ -1,2 +1,4 @@\n def divide(a, b):\n+    if b == 0:\n+        raise ValueError("Cannot divide by zero")\n     return a / b\n',
    expected_effect: 'Resolves TEST-001 ZeroDivisionError',
    verification_plan: 'Execute tests/test_ai_generated.py',
    risk_level: 'LOW',
    status: 'AWAITING_APPROVAL',
    requirement_links: [],
    architecture_links: [],
    database_links: [],
    model_metadata: {},
    created_at: new Date().toISOString(),
    parent_artifact_version: 1,
  };

  it('renders Analyze AI Test Failure button when AI test execution fails and produces diagnosis on click', async () => {
    const analyzeSpy = vi.spyOn(aiTestingApi, 'analyzeTestFailure').mockResolvedValue(mockDiagnosis);

    render(
      <CodeGenerationArtifact
        artifact={mockArtifact}
        projectId="project-123"
        workflowExecutionId="exec-456"
        existingAITestSuite={mockSuite}
        existingAITestExecution={mockFailingExecution}
      />
    );

    // Verify AI test execution outcome is rendered
    expect(screen.getByText(/AI-Generated Test Failures Detected/i)).toBeInTheDocument();
    const analyzeBtn = screen.getByRole('button', { name: /Analyze AI Test Failure/i });
    expect(analyzeBtn).toBeInTheDocument();

    // Click Analyze AI Test Failure
    fireEvent.click(analyzeBtn);

    await waitFor(() => {
      expect(analyzeSpy).toHaveBeenCalledWith('project-123', 'suite-calc-101', 'exec-456');
    });

    // Verify structured diagnosis is rendered
    await waitFor(() => {
      expect(screen.getByText('ZeroDivisionError in Calculator Division Handler')).toBeInTheDocument();
      expect(screen.getByText(/Source: AI_TEST/i)).toBeInTheDocument();
      expect(screen.getByText(/Test TEST-001 failed with ZeroDivisionError/i)).toBeInTheDocument();
      expect(screen.getByText(/Verify that the denominator is non-zero/i)).toBeInTheDocument();
    });

    // Verify call-to-action button to Propose Remediation is visible
    expect(
      screen.getByRole('button', { name: /Propose Remediation for Diagnosis/i })
    ).toBeInTheDocument();
  });

  it('allows user to trigger Phase 11E remediation proposal directly from AI test failure diagnosis', async () => {
    vi.spyOn(remediationApi, 'createProposal').mockResolvedValue(mockProposal);

    render(
      <CodeGenerationArtifact
        artifact={mockArtifact}
        projectId="project-123"
        workflowExecutionId="exec-456"
        existingAITestSuite={mockSuite}
        existingAITestExecution={mockFailingExecution}
        existingFailureAnalysis={mockDiagnosis}
      />
    );

    // Existing diagnosis is displayed
    expect(screen.getByText('ZeroDivisionError in Calculator Division Handler')).toBeInTheDocument();

    // Click Propose Remediation for Diagnosis
    const proposeBtn = screen.getByRole('button', { name: /Propose Remediation for Diagnosis/i });
    fireEvent.click(proposeBtn);

    // Proposal panel with human review gate appears
    await waitFor(() => {
      expect(screen.getByText(/Remediation Proposal \(Human Review\)/i)).toBeInTheDocument();
      expect(screen.getByText('Defensive Divisor Validation in Calculator')).toBeInTheDocument();
      expect(screen.getByText('AWAITING APPROVAL')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Approve Proposal/i })).toBeInTheDocument();
    });
  });
});
