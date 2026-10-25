import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ArtifactViewer } from '../components/artifacts/ArtifactViewer';
import { remediationApi } from '../services/remediationApi';
import { CodeGenerationOutput } from '../types/artifacts';
import {
  ApplyRemediationResponse,
  RemediationProposal,
  RemediationVerificationResult,
} from '../types/remediation';

describe('Phase 11E: Human-in-the-Loop Remediation UI', () => {
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

  const mockDraftProposal: RemediationProposal = {
    proposal_id: 'prop-1234-abcd',
    diagnosis_id: 'diag-5678',
    project_id: 'project-123',
    workflow_execution_id: 'exec-456',
    title: 'Fix undefined variable in run()',
    summary: 'Replaces undefined_variable reference with defined dictionary return value.',
    rationale: 'The function fails at runtime with NameError because undefined_variable is unbound.',
    changes: [
      {
        file_path: 'app/main.py',
        operation: 'MODIFY',
        original_region: 'return undefined_variable',
        proposed_region: "return {'status': 'ok'}",
        reason: 'Return initialized dictionary',
        evidence_ids: ['ev-1'],
      },
    ],
    affected_files: ['app/main.py'],
    unified_diff:
      '--- app/main.py\n+++ app/main.py\n@@ -1,1 +1,1 @@\n-def run(): return undefined_variable\n+def run(): return {\'status\': \'ok\'}',
    expected_effect: 'Eliminates NameError and satisfies test runner.',
    verification_plan: 'Run static analysis and Docker sandbox test suite.',
    risk_level: 'LOW',
    status: 'AWAITING_APPROVAL',
    requirement_links: ['REQ-01'],
    architecture_links: ['CoreService'],
    database_links: [],
    model_metadata: { provider: 'groq', model: 'llama-3.3-70b-versatile' },
    parent_artifact_version: 1,
    resulting_artifact_version: null,
    created_at: new Date().toISOString(),
  };

  it('renders Propose Remediation button and displays proposal and unified diff on click', async () => {
    vi.spyOn(remediationApi, 'createProposal').mockResolvedValue(mockDraftProposal);

    render(
      <ArtifactViewer
        artifacts={{ 'code-generation': mockArtifact }}
        projectId="project-123"
        workflowExecutionId="exec-456"
      />
    );

    const proposeBtn = screen.getByText('Propose Remediation');
    expect(proposeBtn).toBeDefined();

    fireEvent.click(proposeBtn);

    await waitFor(() => {
      expect(screen.getByText('Fix undefined variable in run()')).toBeDefined();
    });

    // Check header and status
    expect(screen.getByText('AWAITING APPROVAL')).toBeDefined();
    expect(screen.getByText('LOW RISK')).toBeDefined();

    // Check diff display
    expect(screen.getByText('Deterministic Unified Diff')).toBeDefined();
    expect(screen.getByText('-def run(): return undefined_variable')).toBeDefined();
    expect(screen.getByText("+def run(): return {'status': 'ok'}")).toBeDefined();

    // Check affected files and traceability
    expect(screen.getAllByText('app/main.py').length).toBeGreaterThan(0);
    expect(screen.getByText('REQ-01')).toBeDefined();
  });

  it('disables Apply button before approval and enables it after explicit approval', async () => {
    const approvedProposal: RemediationProposal = {
      ...mockDraftProposal,
      status: 'APPROVED',
      approved_at: new Date().toISOString(),
    };

    vi.spyOn(remediationApi, 'approveProposal').mockResolvedValue(approvedProposal);

    render(
      <ArtifactViewer
        artifacts={{
          'code-generation': mockArtifact,
          remediation_proposal: mockDraftProposal,
        }}
        projectId="project-123"
        workflowExecutionId="exec-456"
      />
    );

    // Initial state: AWAITING_APPROVAL
    const applyBtn = screen.getByText('Apply Approved Patch');
    expect(applyBtn).toBeDefined();
    // It should be disabled before approval
    expect(applyBtn.hasAttribute('disabled')).toBe(true);

    const approveBtn = screen.getByText('Approve Proposal');
    expect(approveBtn).toBeDefined();

    fireEvent.click(approveBtn);

    await waitFor(() => {
      expect(screen.getByText('APPROVED')).toBeDefined();
    });

    // After approval, Apply button must be active and enabled
    const enabledApplyBtn = screen.getByText('Apply Approved Patch');
    expect(enabledApplyBtn.hasAttribute('disabled')).toBe(false);
  });

  it('handles explicit rejection state', async () => {
    const rejectedProposal: RemediationProposal = {
      ...mockDraftProposal,
      status: 'REJECTED',
      rejected_at: new Date().toISOString(),
      rejection_reason: 'Proposed return structure violates schema requirement.',
    };

    vi.spyOn(remediationApi, 'rejectProposal').mockResolvedValue(rejectedProposal);

    render(
      <ArtifactViewer
        artifacts={{
          'code-generation': mockArtifact,
          remediation_proposal: mockDraftProposal,
        }}
        projectId="project-123"
        workflowExecutionId="exec-456"
      />
    );

    const rejectBtn = screen.getByText('Reject Proposal');
    fireEvent.click(rejectBtn);

    await waitFor(() => {
      expect(screen.getByText('REJECTED')).toBeDefined();
      expect(
        screen.getByText(/Proposed return structure violates schema requirement/i)
      ).toBeDefined();
    });
  });

  it('applies approved patch and displays regression verification and version creation', async () => {
    const approvedProposal: RemediationProposal = {
      ...mockDraftProposal,
      status: 'APPROVED',
      approved_at: new Date().toISOString(),
    };

    const verifiedProposal: RemediationProposal = {
      ...approvedProposal,
      status: 'VERIFIED',
      resulting_artifact_version: 2,
      applied_at: new Date().toISOString(),
    };

    const mockVerification: RemediationVerificationResult = {
      proposal_id: 'prop-1234-abcd',
      status: 'VERIFIED',
      static_analysis_passed: true,
      sandbox_passed: true,
      resolved_diagnostic_codes: ['NameError'],
      new_critical_or_error_diagnostics: [],
      summary: 'Remediation verified: Static analysis and sandbox tests passed with zero errors.',
      verified_at: new Date().toISOString(),
    };

    const mockApplyResponse: ApplyRemediationResponse = {
      proposal: verifiedProposal,
      verification: mockVerification,
    };

    vi.spyOn(remediationApi, 'applyProposal').mockResolvedValue(mockApplyResponse);

    render(
      <ArtifactViewer
        artifacts={{
          'code-generation': mockArtifact,
          remediation_proposal: approvedProposal,
        }}
        projectId="project-123"
        workflowExecutionId="exec-456"
      />
    );

    const applyBtn = screen.getByText('Apply Approved Patch');
    fireEvent.click(applyBtn);

    await waitFor(() => {
      expect(screen.getByText('Regression Verification Passed')).toBeDefined();
    });

    expect(screen.getByText(/Created Artifact v2 \(v1 preserved\)/i)).toBeDefined();
    expect(screen.getByText('CLEAN')).toBeDefined();
    expect(screen.getByText('PASSED')).toBeDefined();
    expect(screen.getByText('NameError')).toBeDefined();
  });
});
