import React, { useState } from 'react';
import {
  Play,
  ShieldAlert,
  ServerCrash,
  Terminal,
} from 'lucide-react';
import { Card, CardBody, CardHeader } from '../common/Card';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { Modal } from '../common/Modal';
import { LoadingSpinner } from '../common/LoadingSpinner';
import {
  RegressionExecutionResult,
  RegressionPlan,
  TestTier,
} from '../../types/testing';
import { testingApi } from '../../services/testingApi';

interface RegressionExecutionViewProps {
  projectId: string;
  plan: RegressionPlan | null;
  selectedVersionId?: string;
  onExecuteComplete?: (result: RegressionExecutionResult) => void;
}

export const RegressionExecutionView: React.FC<RegressionExecutionViewProps> = ({
  projectId,
  plan,
  selectedVersionId,
  onExecuteComplete,
}) => {
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState<boolean>(false);
  const [skipBrowserTests, setSkipBrowserTests] = useState<boolean>(false);
  const [timeoutSeconds, setTimeoutSeconds] = useState<number>(300);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [executionResult, setExecutionResult] = useState<RegressionExecutionResult | null>(null);
  const [errorNotice, setErrorNotice] = useState<string | null>(null);

  const handleStartExecution = async () => {
    setIsConfirmModalOpen(false);
    setIsExecuting(true);
    setErrorNotice(null);

    try {
      const result = await testingApi.executeRegression(projectId, {
        plan: plan || undefined,
        mode: plan ? plan.mode : 'SELECTIVE',
        skip_browser_tests: skipBrowserTests,
        execution_timeout_seconds: timeoutSeconds,
        target_version_id: selectedVersionId || undefined,
      });
      setExecutionResult(result);
      if (onExecuteComplete) {
        onExecuteComplete(result);
      }
    } catch (err: any) {
      setErrorNotice(err?.message || 'Regression execution failed');
    } finally {
      setIsExecuting(false);
    }
  };

  const tiers: TestTier[] = ['UNIT', 'AI_TEST', 'BROWSER_SMOKE', 'BROWSER_JOURNEY'];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
      {/* Pre-Execution Configuration & Gate Card */}
      <Card style={{ background: 'var(--bg-glass-card)' }}>
        <CardHeader>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Play size={18} color="var(--status-completed)" />
            <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>
              Selective Regression Execution Authority
            </span>
          </div>
          {plan && (
            <Badge variant={plan.is_execution_safe ? 'success' : 'failed'}>
              {plan.is_execution_safe ? 'VALIDATED PLAN' : 'UNSAFE PLAN'}
            </Badge>
          )}
        </CardHeader>
        <CardBody>
          {plan ? (
            <div>
              <p style={{ margin: '0 0 1rem 0', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                Ready to execute <strong>{plan.selected_test_ids?.length ?? (plan.selected_tests?.length ?? 0)} selected tests</strong> in{' '}
                <strong>{plan.mode}</strong> scope across isolated container runners.
              </p>

              {!plan.is_execution_safe && (
                <div
                  style={{
                    padding: '0.75rem 1rem',
                    borderRadius: 'var(--radius-sm)',
                    background: 'rgba(239, 68, 68, 0.12)',
                    border: '1px solid rgba(239, 68, 68, 0.35)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    marginBottom: '1rem',
                    color: 'var(--status-failed)',
                    fontSize: '0.85rem',
                  }}
                >
                  <ShieldAlert size={18} style={{ flexShrink: 0 }} />
                  <div>
                    <strong>Execution Blocked by Safety Invariant:</strong> This plan has uncertainty or safety warnings
                    and cannot be executed in SELECTIVE mode. Please regenerate in BROAD mode or enable auto-broadening.
                  </div>
                </div>
              )}

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={skipBrowserTests}
                      onChange={(e) => setSkipBrowserTests(e.target.checked)}
                    />
                    Skip browser tier tests
                  </label>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    <span>Timeout:</span>
                    <input
                      type="number"
                      value={timeoutSeconds}
                      onChange={(e) => setTimeoutSeconds(Number(e.target.value))}
                      min={10}
                      max={1800}
                      style={{
                        width: 70,
                        padding: '0.2rem 0.4rem',
                        borderRadius: 'var(--radius-sm)',
                        background: 'var(--bg-surface)',
                        border: '1px solid var(--border-subtle)',
                        color: 'var(--text-primary)',
                      }}
                    />
                    <span>sec</span>
                  </div>
                </div>

                <Button
                  variant="primary"
                  size="sm"
                  icon={<Play size={15} />}
                  onClick={() => setIsConfirmModalOpen(true)}
                  disabled={isExecuting || !plan.is_execution_safe}
                >
                  {isExecuting ? 'Executing Regression...' : 'Run Regression Plan'}
                </Button>
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '1rem', color: 'var(--text-muted)' }}>
              No regression plan selected. Please generate a plan in the Regression Planner tab before executing.
            </div>
          )}

          {errorNotice && (
            <div
              style={{
                marginTop: '1rem',
                padding: '0.75rem 1rem',
                borderRadius: 'var(--radius-sm)',
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                color: 'var(--status-failed)',
                fontSize: '0.85rem',
              }}
            >
              {errorNotice}
            </div>
          )}
        </CardBody>
      </Card>

      {/* Confirmation Modal */}
      <Modal
        isOpen={isConfirmModalOpen}
        onClose={() => setIsConfirmModalOpen(false)}
        title="Confirm Regression Execution"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            You are about to execute an authoritative multi-tier regression run:
          </p>

          <div
            style={{
              padding: '0.75rem',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              fontSize: '0.85rem',
            }}
          >
            <div>
              <strong>Mode:</strong> {plan?.mode}
            </div>
            <div style={{ marginTop: '0.25rem' }}>
              <strong>Tests Selected:</strong> {plan?.selected_test_ids?.length ?? (plan?.selected_tests?.length ?? 0)} tests
            </div>
            <div style={{ marginTop: '0.25rem' }}>
              <strong>Safety Invariant:</strong>{' '}
              <span style={{ color: 'var(--status-completed)' }}>Verified Safe</span>
            </div>
            <div style={{ marginTop: '0.25rem' }}>
              <strong>Execution Runners:</strong> Docker Sandbox (Unit/AI) & Playwright (Browser)
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '0.5rem' }}>
            <Button variant="ghost" size="sm" onClick={() => setIsConfirmModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" icon={<Play size={15} />} onClick={handleStartExecution}>
              Confirm & Execute
            </Button>
          </div>
        </div>
      </Modal>

      {/* Executing Spinner */}
      {isExecuting && (
        <div style={{ padding: '3rem 0', display: 'flex', justifyContent: 'center' }}>
          <LoadingSpinner label="Dispatching tests across Docker sandbox and Playwright browser containers..." />
        </div>
      )}

      {/* Execution Results Display */}
      {executionResult && !isExecuting && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
          {/* Status Banner */}
          <Card
            style={{
              background:
                executionResult.status === 'PASSED'
                  ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(22, 30, 52, 0.8) 100%)'
                  : 'linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, rgba(22, 30, 52, 0.8) 100%)',
              border:
                executionResult.status === 'PASSED'
                  ? '1px solid rgba(16, 185, 129, 0.4)'
                  : '1px solid rgba(239, 68, 68, 0.4)',
            }}
          >
            <CardBody>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Badge
                      variant={
                        executionResult.status === 'PASSED'
                          ? 'success'
                          : executionResult.status === 'PARTIAL_FAILURE'
                          ? 'partial'
                          : 'failed'
                      }
                    >
                      REGRESSION {executionResult.status}
                    </Badge>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      Execution ID: <span style={{ fontFamily: 'monospace' }}>{executionResult.execution_id}</span>
                    </span>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.35rem' }}>
                    Completed {executionResult.total_tests ?? executionResult.test_results?.length ?? 0} tests in {(executionResult.duration_seconds ?? 0).toFixed(2)}s
                  </div>
                </div>

                {/* Counter Cards */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
                  <div style={{ textAlign: 'center', padding: '0 0.5rem' }}>
                    <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--status-completed)' }}>
                      {executionResult.passed_tests ?? 0}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>PASSED</div>
                  </div>

                  <div style={{ textAlign: 'center', padding: '0 0.5rem', borderLeft: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--status-failed)' }}>
                      {executionResult.failed_tests ?? 0}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>TEST FAILED</div>
                  </div>

                  <div style={{ textAlign: 'center', padding: '0 0.5rem', borderLeft: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--risk-high)' }}>
                      {executionResult.errored_tests ?? (executionResult as any).infrastructure_failures ?? 0}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>INFRA ERROR</div>
                  </div>

                  <div style={{ textAlign: 'center', padding: '0 0.5rem', borderLeft: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-muted)' }}>
                      {executionResult.blocked_tests ?? 0}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>BLOCKED</div>
                  </div>
                </div>
              </div>
            </CardBody>
          </Card>

          {/* Failure Semantics Clarity Banner if failures occurred */}
          {(executionResult.failed_tests > 0 || executionResult.errored_tests > 0) && (
            <div
              style={{
                padding: '0.75rem 1rem',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(249, 115, 22, 0.08)',
                border: '1px solid rgba(249, 115, 22, 0.3)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                fontSize: '0.85rem',
                color: 'var(--text-secondary)',
              }}
            >
              <ServerCrash size={18} color="var(--risk-high)" style={{ flexShrink: 0 }} />
              <span>
                <strong style={{ color: 'var(--risk-high)' }}>Deterministic Failure Classification:</strong> Platform
                strictly separates <strong>Assertion Test Failures</strong> (code defect) from{' '}
                <strong>Infrastructure Failures</strong> (container timeout or runtime crash).
              </span>
            </div>
          )}

          {/* Tier Summaries Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
            {tiers.map((tier) => {
              const summary = executionResult.tier_summaries?.[tier];
              if (!summary || summary.total_tests === 0) return null;

              return (
                <Card key={tier} style={{ background: 'var(--bg-glass-card)' }}>
                  <CardHeader>
                    <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{tier.replace('_', ' ')}</span>
                    <Badge variant={summary.failed === 0 && summary.errored === 0 ? 'success' : 'failed'}>
                      {summary.passed} / {summary.total_tests} passed
                    </Badge>
                  </CardHeader>
                  <CardBody>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      <span>Failed: <strong style={{ color: summary.failed > 0 ? 'var(--status-failed)' : 'inherit' }}>{summary.failed}</strong></span>
                      <span>Errors: <strong style={{ color: summary.errored > 0 ? 'var(--risk-high)' : 'inherit' }}>{summary.errored}</strong></span>
                      <span>Duration: {summary.duration_seconds.toFixed(2)}s</span>
                    </div>
                  </CardBody>
                </Card>
              );
            })}
          </div>

          {/* Individual Test Results Table */}
          <Card style={{ background: 'var(--bg-glass-card)' }}>
            <CardHeader>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Terminal size={18} color="var(--accent-cyan)" />
                <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>
                  Executed Test Cases ({executionResult.test_results?.length ?? 0})
                </span>
              </div>
            </CardHeader>
            <CardBody>
              <div style={{ overflowX: 'auto' }}>
                <table
                  style={{
                    width: '100%',
                    borderCollapse: 'collapse',
                    fontSize: '0.85rem',
                    color: 'var(--text-secondary)',
                  }}
                >
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left' }}>
                      <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Status</th>
                      <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Tier</th>
                      <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Test ID</th>
                      <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Duration</th>
                      <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Output / Failure Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(executionResult.test_results || []).map((tr) => {
                      const isInfra = tr.is_infrastructure_failure;
                      return (
                        <tr
                          key={tr.test_id}
                          style={{ borderBottom: '1px solid var(--border-subtle)' }}
                        >
                          <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                            {tr.status === 'PASSED' ? (
                              <Badge variant="success">PASSED</Badge>
                            ) : isInfra ? (
                              <Badge variant="critical">INFRA ERROR</Badge>
                            ) : tr.status === 'BLOCKED' ? (
                              <Badge variant="draft">BLOCKED</Badge>
                            ) : (
                              <Badge variant="failed">TEST FAILED</Badge>
                            )}
                          </td>
                          <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                            <Badge variant="neutral">{tr.tier.replace('_', ' ')}</Badge>
                          </td>
                          <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                            <span style={{ fontFamily: 'monospace', fontWeight: 600, color: 'var(--text-primary)' }}>
                              {tr.test_id}
                            </span>
                          </td>
                          <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                            {tr.duration_seconds.toFixed(2)}s
                          </td>
                          <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                            {tr.error_message ? (
                              <div style={{ color: 'var(--status-failed)', fontFamily: 'monospace', fontSize: '0.75rem' }}>
                                {tr.error_message}
                              </div>
                            ) : tr.output_snippet ? (
                              <div
                                style={{
                                  fontFamily: 'monospace',
                                  fontSize: '0.75rem',
                                  color: 'var(--text-muted)',
                                  maxHeight: 60,
                                  overflowY: 'auto',
                                }}
                              >
                                {tr.output_snippet}
                              </div>
                            ) : (
                              <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>-</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </CardBody>
          </Card>
        </div>
      )}
    </div>
  );
};
