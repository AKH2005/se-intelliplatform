import React, { useState } from 'react';
import { CodeGenerationOutput, GeneratedFile } from '../../types/artifacts';
import { ExecutionResult, StaticAnalysisResult } from '../../types/sandbox';
import { FailureDiagnosis } from '../../types/failureAnalysis';
import {
  RemediationProposal,
  RemediationVerificationResult,
} from '../../types/remediation';
import { AITestSuite, AITestExecutionResult } from '../../types/aiTesting';
import { sandboxApi } from '../../services/sandboxApi';
import { remediationApi } from '../../services/remediationApi';
import { aiTestingApi } from '../../services/aiTestingApi';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import {
  Code2,
  Play,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  ShieldCheck,
  FileCode,
  SearchCheck,
  Bug,
  FileText,
  Layers,
  Database,
  Wrench,
  Check,
  X,
  History,
  FlaskConical,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';

interface CodeGenerationArtifactProps {
  artifact: CodeGenerationOutput;
  projectId?: string;
  workflowExecutionId?: string;
  existingExecution?: ExecutionResult;
  existingAnalysis?: StaticAnalysisResult;
  existingFailureAnalysis?: FailureDiagnosis;
  existingRemediationProposal?: RemediationProposal;
  existingRemediationVerification?: RemediationVerificationResult;
  existingAITestSuite?: AITestSuite;
  existingAITestExecution?: AITestExecutionResult;
  originalArtifact?: CodeGenerationOutput;
}

export const CodeGenerationArtifact: React.FC<CodeGenerationArtifactProps> = ({
  artifact,
  projectId,
  workflowExecutionId,
  existingExecution,
  existingAnalysis,
  existingFailureAnalysis,
  existingRemediationProposal,
  existingRemediationVerification,
  existingAITestSuite,
  existingAITestExecution,
  originalArtifact,
}) => {
  const [selectedFileIdx, setSelectedFileIdx] = useState<number>(0);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [isDiagnosing, setIsDiagnosing] = useState<boolean>(false);
  const [isProposing, setIsProposing] = useState<boolean>(false);
  const [isApproving, setIsApproving] = useState<boolean>(false);
  const [isRejecting, setIsRejecting] = useState<boolean>(false);
  const [isApplying, setIsApplying] = useState<boolean>(false);
  const [viewOriginal, setViewOriginal] = useState<boolean>(false);

  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(
    existingExecution || null
  );
  const [analysisResult, setAnalysisResult] = useState<StaticAnalysisResult | null>(
    existingAnalysis || null
  );
  const [failureDiagnosis, setFailureDiagnosis] = useState<FailureDiagnosis | null>(
    existingFailureAnalysis || null
  );
  const [proposal, setProposal] = useState<RemediationProposal | null>(
    existingRemediationProposal || null
  );
  const [verification, setVerification] = useState<RemediationVerificationResult | null>(
    existingRemediationVerification || null
  );
  const [aiTestSuite, setAiTestSuite] = useState<AITestSuite | null>(
    existingAITestSuite || null
  );
  const [aiTestExecution, setAiTestExecution] = useState<AITestExecutionResult | null>(
    existingAITestExecution || null
  );
  const [isGeneratingTests, setIsGeneratingTests] = useState<boolean>(false);
  const [isExecutingAiTests, setIsExecutingAiTests] = useState<boolean>(false);
  const [isDiagnosingAiTest, setIsDiagnosingAiTest] = useState<boolean>(false);
  const [expandedTestId, setExpandedTestId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const activeArtifact = viewOriginal && originalArtifact ? originalArtifact : artifact;
  const files = activeArtifact.generated_files || [];
  const currentFile: GeneratedFile | undefined = files[selectedFileIdx];

  const handleRunTests = async () => {
    if (!projectId) {
      setErrorMessage('Project ID is required to execute sandbox tests.');
      return;
    }

    setIsRunning(true);
    setErrorMessage(null);

    try {
      const result = await sandboxApi.execute(projectId, {
        project_id: projectId,
        workflow_execution_id: workflowExecutionId || null,
        execution_type: 'TEST',
      });
      setExecutionResult(result);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to execute tests in sandbox.');
    } finally {
      setIsRunning(false);
    }
  };

  const handleRunAnalysis = async () => {
    if (!projectId) {
      setErrorMessage('Project ID is required to execute static analysis.');
      return;
    }

    setIsAnalyzing(true);
    setErrorMessage(null);

    try {
      const result = await sandboxApi.runStaticAnalysis(projectId, {
        project_id: projectId,
        workflow_execution_id: workflowExecutionId || null,
      });
      setAnalysisResult(result);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to execute static analysis.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleRunFailureAnalysis = async () => {
    if (!projectId) {
      setErrorMessage('Project ID is required to execute failure analysis.');
      return;
    }

    setIsDiagnosing(true);
    setErrorMessage(null);

    try {
      const result = await sandboxApi.runFailureAnalysis(projectId, {
        workflow_execution_id: workflowExecutionId || null,
        force: true,
      });
      setFailureDiagnosis(result);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to execute failure analysis.');
    } finally {
      setIsDiagnosing(false);
    }
  };

  const handleCreateProposal = async () => {
    if (!projectId) {
      setErrorMessage('Project ID is required to propose remediation.');
      return;
    }

    setIsProposing(true);
    setErrorMessage(null);

    try {
      const res = await remediationApi.createProposal(projectId, {
        workflow_execution_id: workflowExecutionId || null,
      });
      setProposal(res);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to create remediation proposal.');
    } finally {
      setIsProposing(false);
    }
  };

  const handleApproveProposal = async () => {
    if (!projectId || !proposal) return;

    setIsApproving(true);
    setErrorMessage(null);

    try {
      const res = await remediationApi.approveProposal(projectId, proposal.proposal_id);
      setProposal(res);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to approve remediation proposal.');
    } finally {
      setIsApproving(false);
    }
  };

  const handleRejectProposal = async () => {
    if (!projectId || !proposal) return;

    setIsRejecting(true);
    setErrorMessage(null);

    try {
      const res = await remediationApi.rejectProposal(projectId, proposal.proposal_id);
      setProposal(res);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to reject remediation proposal.');
    } finally {
      setIsRejecting(false);
    }
  };

  const handleApplyProposal = async () => {
    if (!projectId || !proposal) return;

    setIsApplying(true);
    setErrorMessage(null);

    try {
      const res = await remediationApi.applyProposal(projectId, proposal.proposal_id);
      setProposal(res.proposal);
      setVerification(res.verification);
      if (res.verification.static_analysis_result) {
        setAnalysisResult(res.verification.static_analysis_result);
      }
      if (res.verification.execution_result) {
        setExecutionResult(res.verification.execution_result);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to apply approved remediation patch.');
    } finally {
      setIsApplying(false);
    }
  };

  const handleGenerateAiTests = async () => {
    if (!projectId) {
      setErrorMessage('Project ID is required to generate AI tests.');
      return;
    }

    setIsGeneratingTests(true);
    setErrorMessage(null);

    try {
      const res = await aiTestingApi.generateTests(projectId, {
        workflow_execution_id: workflowExecutionId || null,
      });
      setAiTestSuite(res);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to generate AI tests.');
    } finally {
      setIsGeneratingTests(false);
    }
  };

  const handleExecuteAiTests = async () => {
    if (!projectId || !aiTestSuite) return;

    setIsExecutingAiTests(true);
    setErrorMessage(null);

    try {
      const res = await aiTestingApi.executeTests(projectId, aiTestSuite.suite_id, {
        workflow_execution_id: workflowExecutionId || null,
      });
      setAiTestExecution(res);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to execute AI tests.');
    } finally {
      setIsExecutingAiTests(false);
    }
  };

  const handleAnalyzeAiTestFailure = async () => {
    if (!projectId || !aiTestSuite) return;

    setIsDiagnosingAiTest(true);
    setErrorMessage(null);

    try {
      const res = await aiTestingApi.analyzeTestFailure(
        projectId,
        aiTestSuite.suite_id,
        workflowExecutionId || null
      );
      setFailureDiagnosis(res);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to analyze AI test failure.');
    } finally {
      setIsDiagnosingAiTest(false);
    }
  };

  const handleSelectDiagnosticFile = (filePath?: string | null) => {
    if (!filePath) return;
    const foundIdx = files.findIndex((f) => f.path === filePath || f.path.endsWith(filePath));
    if (foundIdx !== -1) {
      setSelectedFileIdx(foundIdx);
    }
  };

  const getProposalStatusBadge = (statusVal: string) => {
    switch (statusVal) {
      case 'AWAITING_APPROVAL':
        return <Badge variant="warning"><Clock size={12} style={{ marginRight: 4 }} /> AWAITING APPROVAL</Badge>;
      case 'APPROVED':
        return <Badge variant="info"><CheckCircle size={12} style={{ marginRight: 4 }} /> APPROVED</Badge>;
      case 'REJECTED':
        return <Badge variant="danger"><XCircle size={12} style={{ marginRight: 4 }} /> REJECTED</Badge>;
      case 'APPLIED':
        return <Badge variant="info"><Play size={12} style={{ marginRight: 4 }} /> APPLIED</Badge>;
      case 'VERIFIED':
        return <Badge variant="success"><CheckCircle size={12} style={{ marginRight: 4 }} /> VERIFIED</Badge>;
      case 'VERIFICATION_FAILED':
        return <Badge variant="danger"><XCircle size={12} style={{ marginRight: 4 }} /> VERIFICATION FAILED</Badge>;
      default:
        return <Badge variant="neutral">{statusVal}</Badge>;
    }
  };

  const getRiskBadge = (risk: string) => {
    switch (risk) {
      case 'LOW':
        return <Badge variant="success">LOW RISK</Badge>;
      case 'MEDIUM':
        return <Badge variant="warning">MEDIUM RISK</Badge>;
      case 'HIGH':
        return <Badge variant="danger">HIGH RISK</Badge>;
      default:
        return <Badge variant="neutral">{risk}</Badge>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PASSED':
        return <Badge variant="success"><CheckCircle size={12} style={{ marginRight: 4 }} /> PASSED</Badge>;
      case 'FAILED':
        return <Badge variant="danger"><XCircle size={12} style={{ marginRight: 4 }} /> FAILED</Badge>;
      case 'TIMEOUT':
        return <Badge variant="warning"><Clock size={12} style={{ marginRight: 4 }} /> TIMEOUT</Badge>;
      case 'SANDBOX_UNAVAILABLE':
        return <Badge variant="neutral"><AlertTriangle size={12} style={{ marginRight: 4 }} /> SANDBOX UNAVAILABLE</Badge>;
      case 'ISSUES_FOUND':
        return <Badge variant="warning"><AlertTriangle size={12} style={{ marginRight: 4 }} /> ISSUES FOUND</Badge>;
      case 'VALIDATION_ERROR':
        return <Badge variant="danger"><XCircle size={12} style={{ marginRight: 4 }} /> VALIDATION ERROR</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
      case 'ERROR':
        return <Badge variant="danger">{severity}</Badge>;
      case 'WARNING':
        return <Badge variant="warning">{severity}</Badge>;
      case 'INFO':
        return <Badge variant="neutral">{severity}</Badge>;
      default:
        return <Badge variant="neutral">{severity}</Badge>;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top Banner: Scaffold Metadata */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '0.75rem',
          padding: '1rem',
          background: 'var(--bg-surface-elevated, #1a1d24)',
          borderRadius: 'var(--radius-md, 8px)',
          border: '1px solid var(--border-subtle, #2d3139)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Code2 size={22} color="var(--accent-primary, #6366f1)" />
          <div>
            <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>
              {artifact.plan?.language?.toUpperCase()} / {artifact.plan?.framework?.toUpperCase()} Scaffold
            </div>
            <div style={{ color: 'var(--text-muted, #94a3b8)', fontSize: '0.8rem' }}>
              {artifact.total_files} files • {(artifact.total_size_bytes / 1024).toFixed(1)} KB total • {artifact.plan?.database} DB
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        {projectId && (
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {originalArtifact && (
              <Button
                variant="secondary"
                onClick={() => setViewOriginal(!viewOriginal)}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}
              >
                <History size={14} />
                {viewOriginal ? 'Viewing: Original (v1)' : `Viewing: Current (v${(artifact as any).version || 2})`}
              </Button>
            )}
            <Button
              variant="secondary"
              onClick={handleRunAnalysis}
              disabled={isAnalyzing}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}
            >
              <SearchCheck size={14} />
              {isAnalyzing ? 'Analyzing...' : 'Run Static Analysis'}
            </Button>
            <Button
              variant="secondary"
              onClick={handleRunFailureAnalysis}
              disabled={isDiagnosing}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}
            >
              <Bug size={14} />
              {isDiagnosing ? 'Diagnosing...' : 'Analyze Failure'}
            </Button>
            <Button
              variant="secondary"
              onClick={handleCreateProposal}
              disabled={isProposing}
              id="btn-propose-remediation"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}
            >
              <Wrench size={14} />
              {isProposing ? 'Proposing...' : 'Propose Remediation'}
            </Button>
            <Button
              variant="secondary"
              onClick={handleGenerateAiTests}
              disabled={isGeneratingTests}
              id="btn-generate-ai-tests"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}
            >
              <FlaskConical size={14} />
              {isGeneratingTests ? 'Generating Tests...' : 'Generate AI Tests'}
            </Button>
            <Button
              variant="primary"
              onClick={handleRunTests}
              disabled={isRunning}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}
            >
              <Play size={14} />
              {isRunning ? 'Executing...' : 'Run Tests in Sandbox'}
            </Button>
          </div>
        )}
      </div>

      {errorMessage && (
        <div
          style={{
            padding: '0.75rem 1rem',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid var(--accent-danger, #ef4444)',
            borderRadius: 'var(--radius-sm, 6px)',
            color: 'var(--accent-danger, #ef4444)',
            fontSize: '0.85rem',
          }}
        >
          {errorMessage}
        </div>
      )}

      {/* Static Analysis Results Panel */}
      {analysisResult && (
        <div
          style={{
            padding: '1rem',
            background: 'var(--bg-surface-active, #1e222b)',
            borderRadius: 'var(--radius-md, 8px)',
            border: '1px solid var(--border-focus, #4f46e5)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <SearchCheck size={18} color="var(--accent-primary, #6366f1)" />
              <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>Static Analysis & Linting</span>
              {getStatusBadge(analysisResult.status)}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted, #94a3b8)' }}>
              Duration: {analysisResult.duration_seconds.toFixed(2)}s • Analyzed: {analysisResult.files_analyzed} files
            </div>
          </div>

          {/* Counts Summary */}
          <div style={{ display: 'flex', gap: '1.25rem', fontSize: '0.85rem', flexWrap: 'wrap' }}>
            <div>
              <span style={{ color: 'var(--text-muted, #94a3b8)' }}>Errors: </span>
              <strong style={{ color: analysisResult.error_count > 0 ? 'var(--accent-danger, #ef4444)' : 'var(--text-primary)' }}>
                {analysisResult.error_count}
              </strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted, #94a3b8)' }}>Warnings: </span>
              <strong style={{ color: analysisResult.warning_count > 0 ? 'var(--accent-warning, #f59e0b)' : 'var(--text-primary)' }}>
                {analysisResult.warning_count}
              </strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted, #94a3b8)' }}>Info: </span>
              <strong>{analysisResult.info_count}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted, #94a3b8)' }}>Tests Discovered: </span>
              <strong style={{ color: 'var(--accent-success, #10b981)' }}>{analysisResult.test_file_count} file(s)</strong>
            </div>
          </div>

          {/* Diagnostics Table */}
          {analysisResult.diagnostics && analysisResult.diagnostics.length > 0 ? (
            <div style={{ overflowX: 'auto', marginTop: '0.5rem' }}>
              <table style={{ width: '100%', fontSize: '0.8rem', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle, #2d3139)', color: 'var(--text-muted, #94a3b8)' }}>
                    <th style={{ padding: '0.4rem 0.6rem' }}>Severity</th>
                    <th style={{ padding: '0.4rem 0.6rem' }}>Category</th>
                    <th style={{ padding: '0.4rem 0.6rem' }}>Code</th>
                    <th style={{ padding: '0.4rem 0.6rem' }}>Location</th>
                    <th style={{ padding: '0.4rem 0.6rem' }}>Message</th>
                  </tr>
                </thead>
                <tbody>
                  {analysisResult.diagnostics.map((diag, idx) => (
                    <tr
                      key={diag.diagnostic_id || idx}
                      onClick={() => handleSelectDiagnosticFile(diag.file_path)}
                      style={{
                        borderBottom: '1px solid rgba(255,255,255,0.05)',
                        cursor: diag.file_path ? 'pointer' : 'default',
                      }}
                    >
                      <td style={{ padding: '0.4rem 0.6rem' }}>{getSeverityBadge(diag.severity)}</td>
                      <td style={{ padding: '0.4rem 0.6rem' }}>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary, #cbd5e1)' }}>
                          {diag.category}
                        </span>
                      </td>
                      <td style={{ padding: '0.4rem 0.6rem', fontFamily: 'monospace' }}>{diag.code}</td>
                      <td style={{ padding: '0.4rem 0.6rem', color: diag.file_path ? 'var(--accent-primary, #6366f1)' : 'var(--text-muted)' }}>
                        {diag.file_path ? `${diag.file_path}${diag.line ? `:${diag.line}` : ''}` : '-'}
                      </td>
                      <td style={{ padding: '0.4rem 0.6rem' }}>
                        <div>{diag.message}</div>
                        {diag.evidence && (
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted, #94a3b8)', fontStyle: 'italic' }}>
                            {diag.evidence}
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div style={{ fontSize: '0.8rem', color: 'var(--accent-success, #10b981)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <CheckCircle size={14} /> Zero issues found across all static analyzers.
            </div>
          )}
        </div>
      )}

      {/* Sandbox Test Execution Result Panel */}
      {executionResult && (
        <div
          style={{
            padding: '1rem',
            background: 'var(--bg-surface-active, #1e222b)',
            borderRadius: 'var(--radius-md, 8px)',
            border: '1px solid var(--border-focus, #4f46e5)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <ShieldCheck size={18} color="var(--accent-success, #10b981)" />
              <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>Isolated Sandbox Execution</span>
              {getStatusBadge(executionResult.status)}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted, #94a3b8)' }}>
              Duration: {executionResult.duration_seconds.toFixed(2)}s • Exit Code: {executionResult.exit_code ?? 'N/A'}
            </div>
          </div>

          {/* Test Metrics */}
          <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.85rem' }}>
            <div>
              <span style={{ color: 'var(--text-muted, #94a3b8)' }}>Passed: </span>
              <strong style={{ color: 'var(--accent-success, #10b981)' }}>{executionResult.tests_passed}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted, #94a3b8)' }}>Failed: </span>
              <strong style={{ color: executionResult.tests_failed > 0 ? 'var(--accent-danger, #ef4444)' : 'var(--text-primary)' }}>
                {executionResult.tests_failed}
              </strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted, #94a3b8)' }}>Total: </span>
              <strong>{executionResult.tests_total}</strong>
            </div>
          </div>

          {/* Captured stdout / stderr */}
          {executionResult.stdout && (
            <div style={{ marginTop: '0.25rem' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted, #94a3b8)', marginBottom: '0.25rem' }}>
                Runner Output:
              </div>
              <pre
                style={{
                  margin: 0,
                  padding: '0.75rem',
                  background: '#0d1117',
                  borderRadius: 'var(--radius-sm, 6px)',
                  fontSize: '0.8rem',
                  fontFamily: 'monospace',
                  overflowX: 'auto',
                  maxHeight: '200px',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {executionResult.stdout}
              </pre>
            </div>
          )}

          {executionResult.stderr && (
            <div style={{ marginTop: '0.25rem' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--accent-danger, #ef4444)', marginBottom: '0.25rem' }}>
                Error Diagnostics:
              </div>
              <pre
                style={{
                  margin: 0,
                  padding: '0.75rem',
                  background: 'rgba(239, 68, 68, 0.05)',
                  border: '1px solid rgba(239, 68, 68, 0.2)',
                  borderRadius: 'var(--radius-sm, 6px)',
                  fontSize: '0.8rem',
                  fontFamily: 'monospace',
                  overflowX: 'auto',
                  maxHeight: '150px',
                  whiteSpace: 'pre-wrap',
                  color: 'var(--accent-danger, #ef4444)',
                }}
              >
                {executionResult.stderr}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Failure Analysis & Diagnostic Reasoning Panel */}
      {failureDiagnosis && (
        <div
          data-testid="failure-diagnosis-panel"
          style={{
            padding: '1.25rem',
            background: 'var(--bg-surface-elevated, #1a1d24)',
            borderRadius: 'var(--radius-md, 8px)',
            border: '1px solid var(--accent-warning, #f59e0b)',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
          }}
        >
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <Bug size={20} color="var(--accent-warning, #f59e0b)" />
              <div>
                <span style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--text-primary)' }}>
                  Failure Analysis
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted, #94a3b8)', marginLeft: '0.5rem' }}>
                  ID: {failureDiagnosis.diagnosis_id}
                </span>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
              {failureDiagnosis.failure_source && (
                <Badge variant="neutral">Source: {failureDiagnosis.failure_source}</Badge>
              )}
              <Badge variant="failed">{failureDiagnosis.failure_type}</Badge>
              {getSeverityBadge(failureDiagnosis.severity)}
              <Badge variant={failureDiagnosis.confidence.toLowerCase()}>
                Confidence: {failureDiagnosis.confidence}
              </Badge>
            </div>
          </div>

          {/* Title & Summary */}
          <div>
            <h4 style={{ margin: '0 0 0.4rem 0', fontSize: '0.95rem', color: 'var(--text-primary)' }}>
              {failureDiagnosis.title}
            </h4>
            <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary, #cbd5e1)', lineHeight: 1.5 }}>
              {failureDiagnosis.summary}
            </p>
          </div>

          {/* Root Cause Callout */}
          <div
            style={{
              padding: '0.75rem 1rem',
              background: 'rgba(239, 68, 68, 0.08)',
              borderLeft: '4px solid var(--accent-danger, #ef4444)',
              borderRadius: 'var(--radius-sm, 4px)',
            }}
          >
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-danger, #ef4444)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
              Root Cause
            </div>
            <div style={{ fontSize: '0.875rem', color: 'var(--text-primary)', lineHeight: 1.4 }}>
              {failureDiagnosis.root_cause}
            </div>
          </div>

          {/* Affected Files */}
          {failureDiagnosis.affected_files && failureDiagnosis.affected_files.length > 0 && (
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted, #94a3b8)', marginBottom: '0.35rem', textTransform: 'uppercase' }}>
                Affected Files ({failureDiagnosis.affected_files.length})
              </div>
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                {failureDiagnosis.affected_files.map((file, idx) => (
                  <span
                    key={idx}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.3rem',
                      fontSize: '0.75rem',
                      fontFamily: 'monospace',
                      padding: '0.2rem 0.5rem',
                      background: 'var(--bg-surface, #14171f)',
                      border: '1px solid var(--border-subtle, #2d3139)',
                      borderRadius: 'var(--radius-sm, 4px)',
                      color: 'var(--accent-warning, #f59e0b)',
                    }}
                  >
                    <FileCode size={12} />
                    {file}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Diagnostic Claims (Distinguishing FACT, INTERPRETATION, RECOMMENDATION, LIMITATION) */}
          {failureDiagnosis.claims && failureDiagnosis.claims.length > 0 && (
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted, #94a3b8)', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
                Diagnostic Claims & Reasoning
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {failureDiagnosis.claims.map((claim, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '0.6rem',
                      padding: '0.5rem 0.75rem',
                      background: 'var(--bg-surface, #14171f)',
                      border: '1px solid var(--border-subtle, #2d3139)',
                      borderRadius: 'var(--radius-sm, 4px)',
                    }}
                  >
                    <Badge variant={claim.claim_type.toLowerCase()}>{claim.claim_type}</Badge>
                    <div style={{ flex: 1, fontSize: '0.825rem', color: 'var(--text-secondary, #cbd5e1)', lineHeight: 1.4 }}>
                      {claim.statement}
                      {claim.evidence_ids && claim.evidence_ids.length > 0 && (
                        <span style={{ marginLeft: '0.5rem', fontSize: '0.72rem', color: 'var(--text-muted, #94a3b8)' }}>
                          [{claim.evidence_ids.join(', ')}]
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Deterministic Evidence References */}
          {failureDiagnosis.evidence && failureDiagnosis.evidence.length > 0 && (
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted, #94a3b8)', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
                Evidence Grounding ({failureDiagnosis.evidence.length})
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                {failureDiagnosis.evidence.map((ev, idx) => (
                  <div
                    key={idx}
                    style={{
                      fontSize: '0.775rem',
                      padding: '0.4rem 0.6rem',
                      background: 'var(--bg-surface, #14171f)',
                      border: '1px solid var(--border-subtle, #2d3139)',
                      borderRadius: 'var(--radius-sm, 4px)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      gap: '0.5rem',
                    }}
                  >
                    <div>
                      <strong style={{ color: 'var(--text-primary)' }}>[{ev.evidence_id}]</strong>{' '}
                      <span style={{ color: 'var(--text-muted, #94a3b8)' }}>({ev.source})</span>{' '}
                      {ev.code && <span style={{ color: 'var(--accent-danger, #ef4444)', fontFamily: 'monospace' }}>{ev.code}: </span>}
                      <span style={{ color: 'var(--text-secondary, #cbd5e1)' }}>{ev.description || ev.snippet}</span>
                    </div>
                    {ev.file_path && (
                      <span style={{ fontFamily: 'monospace', color: 'var(--text-muted, #94a3b8)', fontSize: '0.725rem' }}>
                        {ev.file_path}{ev.line ? `:${ev.line}` : ''}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Traceability Links: Requirements, Architecture, Database */}
          {((failureDiagnosis.requirement_links && failureDiagnosis.requirement_links.length > 0) ||
            (failureDiagnosis.architecture_links && failureDiagnosis.architecture_links.length > 0) ||
            (failureDiagnosis.database_links && failureDiagnosis.database_links.length > 0)) && (
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', fontSize: '0.8rem' }}>
              {failureDiagnosis.requirement_links && failureDiagnosis.requirement_links.length > 0 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <FileText size={14} color="var(--accent-primary, #6366f1)" />
                  <span style={{ color: 'var(--text-muted, #94a3b8)' }}>Requirements:</span>
                  {failureDiagnosis.requirement_links.map((req, idx) => (
                    <Badge key={idx} variant="neutral">{req}</Badge>
                  ))}
                </div>
              )}
              {failureDiagnosis.architecture_links && failureDiagnosis.architecture_links.length > 0 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Layers size={14} color="var(--accent-primary, #6366f1)" />
                  <span style={{ color: 'var(--text-muted, #94a3b8)' }}>Architecture:</span>
                  {failureDiagnosis.architecture_links.map((arch, idx) => (
                    <Badge key={idx} variant="neutral">{arch}</Badge>
                  ))}
                </div>
              )}
              {failureDiagnosis.database_links && failureDiagnosis.database_links.length > 0 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Database size={14} color="var(--accent-primary, #6366f1)" />
                  <span style={{ color: 'var(--text-muted, #94a3b8)' }}>Database:</span>
                  {failureDiagnosis.database_links.map((db, idx) => (
                    <Badge key={idx} variant="neutral">{db}</Badge>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Suggested Remediation (Descriptive, No Code Mod) */}
          <div
            style={{
              padding: '0.75rem 1rem',
              background: 'rgba(59, 130, 246, 0.08)',
              borderLeft: '4px solid var(--accent-primary, #3b82f6)',
              borderRadius: 'var(--radius-sm, 4px)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-primary, #3b82f6)', textTransform: 'uppercase' }}>
                Suggested Remediation
              </div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted, #94a3b8)', fontStyle: 'italic' }}>
                Descriptive guidance — no automated code modifications applied
              </span>
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>
              {failureDiagnosis.suggested_remediation}
            </div>
            {!proposal && (
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.75rem' }}>
                <Button
                  id="btn-propose-remediation-from-diagnosis"
                  variant="primary"
                  size="sm"
                  onClick={handleCreateProposal}
                  disabled={isProposing}
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem' }}
                >
                  <Wrench size={13} />
                  {isProposing ? 'Proposing...' : 'Propose Remediation for Diagnosis'}
                </Button>
              </div>
            )}
          </div>

          {/* Limitations & Epistemic Boundaries */}
          {failureDiagnosis.limitations && failureDiagnosis.limitations.length > 0 && (
            <div style={{ fontSize: '0.775rem', color: 'var(--text-muted, #94a3b8)' }}>
              <div style={{ fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.25rem', fontSize: '0.7rem' }}>
                Limitations
              </div>
              <ul style={{ margin: 0, paddingLeft: '1.25rem' }}>
                {failureDiagnosis.limitations.map((lim, idx) => (
                  <li key={idx}>{lim}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Model Metadata Footer */}
          {failureDiagnosis.model_metadata && (
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted, #64748b)', borderTop: '1px solid var(--border-subtle, #2d3139)', paddingTop: '0.5rem' }}>
              Provider: {failureDiagnosis.model_metadata.provider || 'unknown'} • Model: {failureDiagnosis.model_metadata.model || 'default'}
              {failureDiagnosis.model_metadata.prompt_tokens ? ` • Tokens: ${failureDiagnosis.model_metadata.prompt_tokens} in / ${failureDiagnosis.model_metadata.completion_tokens || 0} out` : ''}
            </div>
          )}
        </div>
      )}

      {/* Remediation Proposal (Human-in-the-Loop) Panel */}
      {proposal && (
        <div
          id="remediation-proposal-panel"
          style={{
            padding: '1rem',
            background: 'var(--bg-surface-active, #1e222b)',
            borderRadius: 'var(--radius-md, 8px)',
            border: '1px solid var(--accent-primary, #6366f1)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.85rem',
          }}
        >
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Wrench size={18} color="var(--accent-primary, #6366f1)" />
              <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>
                Remediation Proposal (Human Review)
              </span>
              {getProposalStatusBadge(proposal.status)}
              {getRiskBadge(proposal.risk_level)}
            </div>
            <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-muted, #94a3b8)' }}>
              ID: {proposal.proposal_id.slice(0, 8)} • v{proposal.parent_artifact_version}
            </div>
          </div>

          {/* Title & Summary */}
          <div>
            <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
              {proposal.title}
            </div>
            <div style={{ fontSize: '0.825rem', color: 'var(--text-secondary, #cbd5e1)', lineHeight: 1.4 }}>
              {proposal.summary}
            </div>
          </div>

          {/* Rationale */}
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted, #94a3b8)', lineHeight: 1.4 }}>
            <strong style={{ color: 'var(--text-secondary, #cbd5e1)' }}>Rationale: </strong>
            {proposal.rationale}
          </div>

          {/* Affected Files */}
          {proposal.affected_files && proposal.affected_files.length > 0 && (
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted, #94a3b8)', marginBottom: '0.35rem', textTransform: 'uppercase' }}>
                Affected Files ({proposal.affected_files.length})
              </div>
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                {proposal.affected_files.map((file, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSelectDiagnosticFile(file)}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.3rem',
                      fontSize: '0.75rem',
                      fontFamily: 'monospace',
                      padding: '0.2rem 0.5rem',
                      background: 'var(--bg-surface, #14171f)',
                      border: '1px solid var(--border-subtle, #2d3139)',
                      borderRadius: 'var(--radius-sm, 4px)',
                      color: 'var(--accent-primary, #818cf8)',
                      cursor: 'pointer',
                    }}
                    title="Click to view file in editor"
                  >
                    <FileCode size={12} />
                    {file}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Traceability: Requirements, Architecture, Database */}
          {((proposal.requirement_links && proposal.requirement_links.length > 0) ||
            (proposal.architecture_links && proposal.architecture_links.length > 0) ||
            (proposal.database_links && proposal.database_links.length > 0)) && (
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', fontSize: '0.775rem' }}>
              {proposal.requirement_links && proposal.requirement_links.length > 0 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <FileText size={13} color="var(--accent-primary, #6366f1)" />
                  <span style={{ color: 'var(--text-muted, #94a3b8)' }}>Reqs:</span>
                  {proposal.requirement_links.map((req, idx) => (
                    <Badge key={idx} variant="neutral">{req}</Badge>
                  ))}
                </div>
              )}
              {proposal.architecture_links && proposal.architecture_links.length > 0 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Layers size={13} color="var(--accent-primary, #6366f1)" />
                  <span style={{ color: 'var(--text-muted, #94a3b8)' }}>Arch:</span>
                  {proposal.architecture_links.map((arch, idx) => (
                    <Badge key={idx} variant="neutral">{arch}</Badge>
                  ))}
                </div>
              )}
              {proposal.database_links && proposal.database_links.length > 0 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Database size={13} color="var(--accent-primary, #6366f1)" />
                  <span style={{ color: 'var(--text-muted, #94a3b8)' }}>DB:</span>
                  {proposal.database_links.map((db, idx) => (
                    <Badge key={idx} variant="neutral">{db}</Badge>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Unified Diff Box */}
          {proposal.unified_diff && (
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted, #94a3b8)', marginBottom: '0.35rem', textTransform: 'uppercase' }}>
                Deterministic Unified Diff
              </div>
              <pre
                style={{
                  margin: 0,
                  padding: '0.75rem',
                  background: '#0a0d14',
                  border: '1px solid var(--border-subtle, #2d3139)',
                  borderRadius: 'var(--radius-sm, 4px)',
                  fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                  fontSize: '0.775rem',
                  lineHeight: '1.4',
                  maxHeight: '260px',
                  overflowY: 'auto',
                }}
              >
                {proposal.unified_diff.split('\n').map((line, idx) => {
                  let lineStyle: React.CSSProperties = { color: '#94a3b8' };
                  if (line.startsWith('+') && !line.startsWith('+++')) {
                    lineStyle = { color: '#34d399', background: 'rgba(52, 211, 153, 0.1)' };
                  } else if (line.startsWith('-') && !line.startsWith('---')) {
                    lineStyle = { color: '#f87171', background: 'rgba(248, 113, 113, 0.1)' };
                  } else if (line.startsWith('@@')) {
                    lineStyle = { color: '#818cf8', background: 'rgba(129, 140, 248, 0.1)' };
                  }
                  return (
                    <div key={idx} style={{ ...lineStyle, padding: '1px 4px', whiteSpace: 'pre-wrap' }}>
                      {line}
                    </div>
                  );
                })}
              </pre>
            </div>
          )}

          {/* Expected Effect & Verification Plan */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.8rem' }}>
            <div style={{ padding: '0.5rem 0.75rem', background: 'var(--bg-surface, #14171f)', borderRadius: '4px' }}>
              <div style={{ fontWeight: 600, color: 'var(--text-muted, #94a3b8)', marginBottom: '0.2rem', textTransform: 'uppercase', fontSize: '0.7rem' }}>
                Expected Effect
              </div>
              <div style={{ color: 'var(--text-secondary, #cbd5e1)' }}>{proposal.expected_effect}</div>
            </div>
            <div style={{ padding: '0.5rem 0.75rem', background: 'var(--bg-surface, #14171f)', borderRadius: '4px' }}>
              <div style={{ fontWeight: 600, color: 'var(--text-muted, #94a3b8)', marginBottom: '0.2rem', textTransform: 'uppercase', fontSize: '0.7rem' }}>
                Verification Plan
              </div>
              <div style={{ color: 'var(--text-secondary, #cbd5e1)' }}>{proposal.verification_plan}</div>
            </div>
          </div>

          {/* Authorization Boundary & Action Controls */}
          <div
            style={{
              padding: '0.75rem 1rem',
              background: 'var(--bg-surface, #14171f)',
              border: '1px solid var(--border-subtle, #2d3139)',
              borderRadius: 'var(--radius-sm, 6px)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '0.75rem',
            }}
          >
            {/* Context & Warning message */}
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted, #94a3b8)', maxWidth: '500px' }}>
              {(proposal.status === 'AWAITING_APPROVAL' || proposal.status === 'VALIDATED') && (
                <span>
                  <strong style={{ color: 'var(--accent-warning, #f59e0b)' }}>Human Authorization Gate: </strong>
                  Review the proposed patch above. Applying the patch is locked until explicitly approved.
                </span>
              )}
              {proposal.status === 'APPROVED' && (
                <span style={{ color: 'var(--accent-success, #10b981)' }}>
                  <CheckCircle size={14} style={{ display: 'inline', marginRight: 4 }} />
                  <strong>Explicitly Approved: </strong>
                  Ready to apply patch in isolated workspace and run verification.
                </span>
              )}
              {proposal.status === 'REJECTED' && (
                <span style={{ color: 'var(--accent-danger, #ef4444)' }}>
                  <XCircle size={14} style={{ display: 'inline', marginRight: 4 }} />
                  <strong>Rejected: </strong>
                  {proposal.rejection_reason || 'Proposal was rejected and will not be applied.'}
                </span>
              )}
              {(proposal.status === 'APPLIED' || proposal.status === 'VERIFIED' || proposal.status === 'VERIFICATION_FAILED') && (
                <span>
                  <strong>Applied: </strong>
                  Patch was applied to isolated workspace and evaluated via regression pipeline.
                </span>
              )}
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              {(proposal.status === 'AWAITING_APPROVAL' || proposal.status === 'VALIDATED') && (
                <>
                  <Button
                    id="btn-reject-proposal"
                    variant="secondary"
                    onClick={handleRejectProposal}
                    disabled={isRejecting || isApproving}
                    style={{ fontSize: '0.85rem' }}
                  >
                    <X size={14} style={{ marginRight: 4 }} />
                    {isRejecting ? 'Rejecting...' : 'Reject Proposal'}
                  </Button>
                  <Button
                    id="btn-approve-proposal"
                    variant="primary"
                    onClick={handleApproveProposal}
                    disabled={isApproving || isRejecting}
                    style={{ fontSize: '0.85rem' }}
                  >
                    <Check size={14} style={{ marginRight: 4 }} />
                    {isApproving ? 'Approving...' : 'Approve Proposal'}
                  </Button>
                  <Button
                    id="btn-apply-proposal"
                    variant="secondary"
                    disabled={true}
                    title="Proposal must be approved first"
                    style={{ fontSize: '0.85rem', opacity: 0.5, cursor: 'not-allowed' }}
                  >
                    Apply Approved Patch
                  </Button>
                </>
              )}

              {proposal.status === 'APPROVED' && (
                <>
                  <Button
                    id="btn-reject-proposal"
                    variant="secondary"
                    onClick={handleRejectProposal}
                    disabled={isRejecting || isApplying}
                    style={{ fontSize: '0.85rem' }}
                  >
                    <X size={14} style={{ marginRight: 4 }} />
                    Reject
                  </Button>
                  <Button
                    id="btn-apply-proposal"
                    variant="primary"
                    onClick={handleApplyProposal}
                    disabled={isApplying}
                    style={{ fontSize: '0.85rem' }}
                  >
                    <Play size={14} style={{ marginRight: 4 }} />
                    {isApplying ? 'Applying & Verifying...' : 'Apply Approved Patch'}
                  </Button>
                </>
              )}
            </div>
          </div>

          {/* Verification Results Block */}
          {verification && (
            <div
              id="remediation-verification-block"
              style={{
                marginTop: '0.5rem',
                padding: '0.75rem 1rem',
                background: verification.status === 'VERIFIED' ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
                border: `1px solid ${verification.status === 'VERIFIED' ? 'var(--accent-success, #10b981)' : 'var(--accent-danger, #ef4444)'}`,
                borderRadius: 'var(--radius-sm, 6px)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  {verification.status === 'VERIFIED' ? (
                    <CheckCircle size={16} color="var(--accent-success, #10b981)" />
                  ) : (
                    <XCircle size={16} color="var(--accent-danger, #ef4444)" />
                  )}
                  <strong style={{ fontSize: '0.85rem' }}>
                    Regression Verification {verification.status === 'VERIFIED' ? 'Passed' : 'Failed'}
                  </strong>
                  {getProposalStatusBadge(verification.status)}
                </div>
                {proposal.resulting_artifact_version && (
                  <div style={{ fontSize: '0.75rem', color: 'var(--accent-success, #10b981)' }}>
                    Created Artifact v{proposal.resulting_artifact_version} (v{proposal.parent_artifact_version} preserved)
                  </div>
                )}
              </div>

              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary, #cbd5e1)', marginBottom: '0.5rem' }}>
                {verification.summary}
              </div>

              <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.775rem' }}>
                <div>
                  <span style={{ color: 'var(--text-muted, #94a3b8)' }}>Static Analysis: </span>
                  <strong style={{ color: verification.static_analysis_passed ? 'var(--accent-success, #10b981)' : 'var(--accent-danger, #ef4444)' }}>
                    {verification.static_analysis_passed ? 'CLEAN' : 'ERRORS DETECTED'}
                  </strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted, #94a3b8)' }}>Sandbox Pytest Suite: </span>
                  <strong style={{ color: verification.sandbox_passed ? 'var(--accent-success, #10b981)' : 'var(--accent-danger, #ef4444)' }}>
                    {verification.sandbox_passed ? 'PASSED' : 'FAILED'}
                  </strong>
                </div>
                {verification.resolved_diagnostic_codes && verification.resolved_diagnostic_codes.length > 0 && (
                  <div>
                    <span style={{ color: 'var(--text-muted, #94a3b8)' }}>Resolved Codes: </span>
                    <strong style={{ color: 'var(--accent-success, #10b981)' }}>
                      {verification.resolved_diagnostic_codes.join(', ')}
                    </strong>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* AI-Generated Testing Section */}
      {aiTestSuite && (
        <div
          id="ai-testing-panel"
          style={{
            background: 'var(--bg-surface, #14171f)',
            borderRadius: 'var(--radius-md, 8px)',
            border: '1px solid var(--border-subtle, #2d3139)',
            padding: '1.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
          }}
        >
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FlaskConical size={18} color="var(--accent-cyan, #06b6d4)" />
              <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>AI-Generated Test Suite</div>
              <Badge variant="success">
                <ShieldCheck size={12} style={{ marginRight: 4 }} /> VALIDATED
              </Badge>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted, #94a3b8)' }}>
                {aiTestSuite.test_count} {aiTestSuite.test_count === 1 ? 'test' : 'tests'}
              </span>
            </div>

            <Button
              variant="primary"
              onClick={handleExecuteAiTests}
              disabled={isExecutingAiTests}
              id="btn-run-ai-tests"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}
            >
              <Play size={14} />
              {isExecutingAiTests ? 'Executing in Sandbox...' : 'Run AI Tests in Sandbox'}
            </Button>
          </div>

          <div style={{ fontSize: '0.825rem', color: 'var(--text-secondary, #cbd5e1)' }}>
            {aiTestSuite.summary}
          </div>

          {/* Test List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {aiTestSuite.tests.map((t) => {
              const isExpanded = expandedTestId === t.test_id;
              return (
                <div
                  key={t.test_id}
                  style={{
                    background: 'var(--bg-surface-elevated, #1a1d24)',
                    border: '1px solid var(--border-subtle, #2d3139)',
                    borderRadius: 'var(--radius-sm, 6px)',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    onClick={() => setExpandedTestId(isExpanded ? null : t.test_id)}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '0.6rem 0.85rem',
                      cursor: 'pointer',
                      userSelect: 'none',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                      {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                      <span style={{ fontWeight: 600, fontSize: '0.825rem', color: 'var(--text-primary, #f8fafc)' }}>
                        {t.name}
                      </span>
                      <Badge variant="neutral">{t.category}</Badge>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted, #94a3b8)' }}>
                        Target: {t.target_file} {t.target_symbol ? `-> ${t.target_symbol}` : ''}
                      </span>
                    </div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted, #94a3b8)' }}>
                      {t.test_id}
                    </span>
                  </div>

                  {isExpanded && (
                    <div style={{ padding: '0.75rem', borderTop: '1px solid var(--border-subtle, #2d3139)', background: '#0a0d14' }}>
                      <div style={{ fontSize: '0.775rem', color: 'var(--text-secondary, #cbd5e1)', marginBottom: '0.5rem' }}>
                        {t.description}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted, #94a3b8)', marginBottom: '0.5rem' }}>
                        Rationale: {t.rationale}
                      </div>
                      <pre
                        style={{
                          margin: 0,
                          padding: '0.75rem',
                          background: '#0d1117',
                          borderRadius: '4px',
                          fontSize: '0.8rem',
                          color: '#e2e8f0',
                          fontFamily: 'Consolas, Monaco, monospace',
                          overflow: 'auto',
                        }}
                      >
                        <code>{t.code}</code>
                      </pre>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Ephemeral Execution Outcome */}
          {aiTestExecution && (
            <div
              id="ai-test-execution-results"
              style={{
                marginTop: '0.5rem',
                padding: '1rem',
                background: 'var(--bg-surface-elevated, #1a1d24)',
                border: '1px solid var(--border-subtle, #2d3139)',
                borderRadius: 'var(--radius-sm, 6px)',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>Execution Outcome:</span>
                  {getStatusBadge(aiTestExecution.status)}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary, #cbd5e1)' }}>
                  {aiTestExecution.tests_passed} / {aiTestExecution.tests_total} passed in {aiTestExecution.duration_seconds.toFixed(2)}s
                </div>
              </div>

              {/* Individual Test Breakdown */}
              {aiTestExecution.test_results && aiTestExecution.test_results.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  {aiTestExecution.test_results.map((tr, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        fontSize: '0.775rem',
                        padding: '0.35rem 0.5rem',
                        background: 'var(--bg-surface, #14171f)',
                        borderRadius: '4px',
                      }}
                    >
                      <span style={{ fontFamily: 'monospace' }}>{tr.name}</span>
                      {getStatusBadge(tr.status)}
                    </div>
                  ))}
                </div>
              )}

              {/* Failure Summaries */}
              {aiTestExecution.failure_summaries && aiTestExecution.failure_summaries.length > 0 && (
                <div style={{ marginTop: '0.25rem' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--accent-danger, #ef4444)', marginBottom: '0.35rem' }}>
                    Failure Diagnostics:
                  </div>
                  {aiTestExecution.failure_summaries.map((f, idx) => (
                    <pre
                      key={idx}
                      style={{
                        margin: 0,
                        padding: '0.5rem',
                        background: '#0d1117',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        color: '#f87171',
                        fontFamily: 'Consolas, monospace',
                        overflow: 'auto',
                      }}
                    >
                      <code>{f}</code>
                    </pre>
                  ))}
                </div>
              )}

              {/* AI Test Failure Analysis Action */}
              {(aiTestExecution.status === 'FAILED' || aiTestExecution.tests_failed > 0) && (
                <div
                  id="ai-test-failure-action-box"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.65rem 0.85rem',
                    background: 'rgba(239, 68, 68, 0.08)',
                    border: '1px solid rgba(239, 68, 68, 0.25)',
                    borderRadius: 'var(--radius-sm, 6px)',
                    marginTop: '0.35rem',
                    flexWrap: 'wrap',
                    gap: '0.5rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem' }}>
                    <Bug size={16} color="var(--accent-danger, #ef4444)" />
                    <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                      AI-Generated Test Failures Detected ({aiTestExecution.tests_failed} failed)
                    </span>
                  </div>
                  <Button
                    id="btn-analyze-ai-test-failure"
                    variant="danger"
                    size="sm"
                    onClick={handleAnalyzeAiTestFailure}
                    disabled={isDiagnosingAiTest}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.775rem' }}
                  >
                    <Bug size={13} />
                    {isDiagnosingAiTest ? 'Analyzing Failures...' : 'Analyze AI Test Failure'}
                  </Button>
                </div>
              )}

              {/* Stdout / Stderr Logs */}
              {aiTestExecution.stdout && (
                <details style={{ fontSize: '0.75rem', color: 'var(--text-muted, #94a3b8)' }}>
                  <summary style={{ cursor: 'pointer', padding: '0.25rem 0' }}>Show Pytest Output Log</summary>
                  <pre
                    style={{
                      margin: '0.5rem 0 0 0',
                      padding: '0.75rem',
                      background: '#0d1117',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      color: '#94a3b8',
                      fontFamily: 'monospace',
                      overflow: 'auto',
                      maxHeight: '180px',
                    }}
                  >
                    <code>{aiTestExecution.stdout}</code>
                  </pre>
                </details>
              )}

              <div style={{ fontSize: '0.725rem', color: 'var(--text-muted, #64748b)', fontStyle: 'italic' }}>
                Ephemeral Test Run: Generated tests were executed in an isolated container without mutating the application artifact.
              </div>
            </div>
          )}
        </div>
      )}

      {/* File Navigation & Source Viewer */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '240px 1fr',
          gap: '1rem',
          minHeight: '360px',
        }}
      >
        {/* Left: File Tree / Manifest */}
        <div
          style={{
            background: 'var(--bg-surface, #14171f)',
            borderRadius: 'var(--radius-md, 8px)',
            border: '1px solid var(--border-subtle, #2d3139)',
            padding: '0.75rem',
            overflowY: 'auto',
          }}
        >
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted, #94a3b8)', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
            Generated Files ({files.length})
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
            {files.map((f, idx) => {
              const isSelected = idx === selectedFileIdx;
              return (
                <button
                  key={f.path}
                  onClick={() => setSelectedFileIdx(idx)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.4rem 0.6rem',
                    borderRadius: 'var(--radius-sm, 6px)',
                    border: 'none',
                    background: isSelected ? 'var(--bg-surface-active, #242936)' : 'transparent',
                    color: isSelected ? 'var(--accent-primary, #6366f1)' : 'var(--text-secondary, #cbd5e1)',
                    fontWeight: isSelected ? 600 : 400,
                    fontSize: '0.8rem',
                    textAlign: 'left',
                    cursor: 'pointer',
                    wordBreak: 'break-all',
                  }}
                >
                  <FileCode size={14} style={{ flexShrink: 0 }} />
                  <span>{f.path}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right: Code Viewer */}
        <div
          style={{
            background: '#0d1117',
            borderRadius: 'var(--radius-md, 8px)',
            border: '1px solid var(--border-subtle, #2d3139)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {currentFile ? (
            <>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '0.5rem 1rem',
                  background: 'var(--bg-surface, #161b22)',
                  borderBottom: '1px solid var(--border-subtle, #2d3139)',
                  fontSize: '0.8rem',
                  color: 'var(--text-muted, #94a3b8)',
                }}
              >
                <span style={{ fontWeight: 600, color: 'var(--text-primary, #f8fafc)' }}>
                  {currentFile.path}
                </span>
                <span>{(currentFile.size_bytes / 1024).toFixed(1)} KB</span>
              </div>
              <pre
                style={{
                  margin: 0,
                  padding: '1rem',
                  fontSize: '0.85rem',
                  fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                  overflow: 'auto',
                  flexGrow: 1,
                  lineHeight: '1.5',
                  color: '#e6edf3',
                }}
              >
                <code>{currentFile.content}</code>
              </pre>
            </>
          ) : (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              No file selected.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
