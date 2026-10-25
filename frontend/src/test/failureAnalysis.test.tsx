import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ArtifactViewer } from '../components/artifacts/ArtifactViewer';
import { sandboxApi } from '../services/sandboxApi';
import { CodeGenerationOutput } from '../types/artifacts';
import { FailureDiagnosis } from '../types/failureAnalysis';

describe('Failure Analysis UI in CodeGenerationArtifact', () => {
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
      ],
      rationale: 'Modular FastAPI service.',
    },
    generated_files: [
      {
        path: 'app/main.py',
        content: 'def run(): return undefined_variable',
        language: 'python',
        size_bytes: 36,
      },
    ],
    total_files: 1,
    total_size_bytes: 36,
    summary: 'FastAPI scaffold.',
  };

  const mockDiagnosis: FailureDiagnosis = {
    diagnosis_id: 'diag-exec-789',
    failure_type: 'RUNTIME_ERROR',
    title: 'Undefined variable referenced in run()',
    summary: 'Execution failed due to undefined symbol undefined_variable.',
    root_cause: "NameError: name 'undefined_variable' is not defined in app/main.py at line 1.",
    severity: 'ERROR',
    affected_files: ['app/main.py'],
    evidence: [
      {
        evidence_id: 'ev-1',
        source: 'execution_stderr',
        code: 'NameError',
        file_path: 'app/main.py',
        line: 1,
        snippet: 'return undefined_variable',
        description: 'Traceback points to undefined symbol',
      },
    ],
    claims: [
      {
        claim_type: 'FACT',
        statement: 'Execution terminated with exit code 1 due to NameError.',
        evidence_ids: ['ev-1'],
      },
      {
        claim_type: 'INTERPRETATION',
        statement: 'The variable was referenced before assignment or import.',
        evidence_ids: ['ev-1'],
      },
      {
        claim_type: 'RECOMMENDATION',
        statement: 'Define or pass undefined_variable as an argument.',
        evidence_ids: [],
      },
      {
        claim_type: 'LIMITATION',
        statement: 'Static inspection cannot infer the intended runtime type of the variable.',
        evidence_ids: [],
      },
    ],
    requirement_links: ['REQ-01'],
    architecture_links: ['AuthService'],
    database_links: ['users'],
    suggested_remediation: 'Declare or import undefined_variable before returning it in app/main.py.',
    limitations: ['Only captured sandbox execution traces were evaluated.'],
    confidence: 'HIGH',
    model_metadata: {
      provider: 'groq',
      model: 'llama-3.3-70b-versatile',
      prompt_tokens: 420,
      completion_tokens: 180,
    },
  };

  it('renders Analyze Failure button and displays complete diagnosis on click', async () => {
    vi.spyOn(sandboxApi, 'runFailureAnalysis').mockResolvedValue(mockDiagnosis);

    render(
      <ArtifactViewer
        artifacts={{ 'code-generation': mockArtifact }}
        projectId="project-123"
        workflowExecutionId="exec-789"
      />
    );

    const analyzeBtn = screen.getByText('Analyze Failure');
    expect(analyzeBtn).toBeInTheDocument();

    fireEvent.click(analyzeBtn);

    await waitFor(() => {
      expect(screen.getByTestId('failure-diagnosis-panel')).toBeInTheDocument();
    });

    // Check header and metadata
    expect(screen.getByText('Failure Analysis')).toBeInTheDocument();
    expect(screen.getByText('ID: diag-exec-789')).toBeInTheDocument();
    expect(screen.getByText('RUNTIME_ERROR')).toBeInTheDocument();
    expect(screen.getByText('Confidence: HIGH')).toBeInTheDocument();

    // Check title and summary
    expect(screen.getByText('Undefined variable referenced in run()')).toBeInTheDocument();
    expect(screen.getByText('Execution failed due to undefined symbol undefined_variable.')).toBeInTheDocument();

    // Check root cause
    expect(screen.getByText('Root Cause')).toBeInTheDocument();
    expect(screen.getByText("NameError: name 'undefined_variable' is not defined in app/main.py at line 1.")).toBeInTheDocument();

    // Check affected files
    expect(screen.getByText('Affected Files (1)')).toBeInTheDocument();
    expect(screen.getAllByText('app/main.py').length).toBeGreaterThanOrEqual(1);

    // Check claim types (FACT, INTERPRETATION, RECOMMENDATION, LIMITATION)
    expect(screen.getByText('FACT')).toBeInTheDocument();
    expect(screen.getByText('INTERPRETATION')).toBeInTheDocument();
    expect(screen.getByText('RECOMMENDATION')).toBeInTheDocument();
    expect(screen.getByText('LIMITATION')).toBeInTheDocument();
    expect(screen.getByText('Execution terminated with exit code 1 due to NameError.')).toBeInTheDocument();

    // Check evidence
    expect(screen.getByText('Evidence Grounding (1)')).toBeInTheDocument();
    expect(screen.getAllByText(/ev-1/).length).toBeGreaterThanOrEqual(1);

    // Check traceability links
    expect(screen.getByText('Requirements:')).toBeInTheDocument();
    expect(screen.getByText('REQ-01')).toBeInTheDocument();
    expect(screen.getByText('Architecture:')).toBeInTheDocument();
    expect(screen.getByText('AuthService')).toBeInTheDocument();
    expect(screen.getByText('Database:')).toBeInTheDocument();
    expect(screen.getByText('users')).toBeInTheDocument();

    // Check suggested remediation
    expect(screen.getByText('Suggested Remediation')).toBeInTheDocument();
    expect(screen.getByText('Declare or import undefined_variable before returning it in app/main.py.')).toBeInTheDocument();

    // Check limitations
    expect(screen.getByText('Limitations')).toBeInTheDocument();
    expect(screen.getByText('Only captured sandbox execution traces were evaluated.')).toBeInTheDocument();

    // Check model metadata
    expect(screen.getByText(/Provider: groq • Model: llama-3\.3-70b-versatile/)).toBeInTheDocument();

    // Verify READ-ONLY constraint: NO Apply Fix, Auto Repair, or Regenerate buttons
    expect(screen.queryByText(/Apply Fix/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Fix Automatically/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Auto Repair/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Regenerate/i)).not.toBeInTheDocument();
  });

  it('renders pre-existing failure analysis from workflow execution artifacts', () => {
    render(
      <ArtifactViewer
        artifacts={{
          'code-generation': mockArtifact,
          'failure_analysis': mockDiagnosis,
        }}
        projectId="project-123"
        workflowExecutionId="exec-789"
      />
    );

    expect(screen.getByTestId('failure-diagnosis-panel')).toBeInTheDocument();
    expect(screen.getByText('RUNTIME_ERROR')).toBeInTheDocument();
    expect(screen.getByText("NameError: name 'undefined_variable' is not defined in app/main.py at line 1.")).toBeInTheDocument();
  });

  it('handles API error gracefully and displays error banner', async () => {
    vi.spyOn(sandboxApi, 'runFailureAnalysis').mockRejectedValue(new Error('Failure analysis agent timeout.'));

    render(
      <ArtifactViewer
        artifacts={{ 'code-generation': mockArtifact }}
        projectId="project-123"
        workflowExecutionId="exec-789"
      />
    );

    fireEvent.click(screen.getByText('Analyze Failure'));

    await waitFor(() => {
      expect(screen.getByText('Failure analysis agent timeout.')).toBeInTheDocument();
    });

    expect(screen.queryByTestId('failure-diagnosis-panel')).not.toBeInTheDocument();
  });
});
