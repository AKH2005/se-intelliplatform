import React, { useState } from 'react';
import {
  GitPullRequest,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  ShieldAlert,
  ArrowRight,
  Layers,
} from 'lucide-react';
import { Card, CardBody, CardHeader } from '../common/Card';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { RegressionPlan, RegressionPlanMode } from '../../types/testing';
import { testingApi } from '../../services/testingApi';

interface RegressionPlannerViewProps {
  projectId: string;
  selectedVersionId?: string;
  initialChangedFiles?: string[];
  currentPlan: RegressionPlan | null;
  onPlanGenerated: (plan: RegressionPlan) => void;
  onProceedToExecution?: () => void;
}

export const RegressionPlannerView: React.FC<RegressionPlannerViewProps> = ({
  projectId,
  selectedVersionId,
  initialChangedFiles = [],
  currentPlan,
  onPlanGenerated,
  onProceedToExecution,
}) => {
  const [mode, setMode] = useState<RegressionPlanMode>('SELECTIVE');
  const [autoBroaden, setAutoBroaden] = useState<boolean>(true);
  const [changedFilesText, setChangedFilesText] = useState<string>(
    initialChangedFiles.length > 0 ? initialChangedFiles.join('\n') : 'app/api/v1/endpoints/testing.py'
  );
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorNotice, setErrorNotice] = useState<string | null>(null);

  const handleGeneratePlan = async () => {
    if (!projectId || isLoading) return;

    const files = changedFilesText
      .split('\n')
      .map((f) => f.trim())
      .filter((f) => f.length > 0);

    setIsLoading(true);
    setErrorNotice(null);

    try {
      const plan = await testingApi.planRegression(projectId, {
        mode,
        auto_broaden: autoBroaden,
        changed_files: files.length > 0 ? files : undefined,
        target_version_id: selectedVersionId || undefined,
      });
      onPlanGenerated(plan);
    } catch (err: any) {
      setErrorNotice(err?.message || 'Failed to generate regression plan');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
      {/* Configuration & Trigger Card */}
      <Card style={{ background: 'var(--bg-glass-card)' }}>
        <CardHeader>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <GitPullRequest size={18} color="var(--accent-primary)" />
            <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>
              Selective Regression Planner Configuration
            </span>
          </div>
        </CardHeader>
        <CardBody>
          <p style={{ margin: '0 0 1rem 0', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Deterministically identifies minimal regression test suites based on AST dependency analysis,
            requirement protection, and conservative safety invariants.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {/* Mode Selector */}
            <div>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.5rem' }}>
                Planning Scope Mode:
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem' }}>
                {[
                  {
                    key: 'SELECTIVE' as RegressionPlanMode,
                    title: 'Selective Mode',
                    desc: 'Minimal deterministic impact set. Safe only under high-confidence AST analysis.',
                  },
                  {
                    key: 'BROAD' as RegressionPlanMode,
                    title: 'Broad Mode',
                    desc: 'Impact set + all Unit and Smoke tests. Triggered automatically on uncertainty.',
                  },
                  {
                    key: 'FULL' as RegressionPlanMode,
                    title: 'Full Mode',
                    desc: 'Execute 100% of test inventory across all four testing tiers.',
                  },
                ].map((m) => {
                  const isSelected = mode === m.key;
                  return (
                    <div
                      key={m.key}
                      onClick={() => setMode(m.key)}
                      style={{
                        padding: '0.75rem 1rem',
                        borderRadius: 'var(--radius-sm)',
                        background: isSelected ? 'var(--bg-surface-active)' : 'var(--bg-surface)',
                        border: isSelected ? '1px solid var(--accent-primary)' : '1px solid var(--border-subtle)',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <strong style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>{m.title}</strong>
                        {isSelected && <CheckCircle2 size={16} color="var(--accent-primary)" />}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem', lineHeight: 1.4 }}>
                        {m.desc}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Changed Files Input (for Selective & Broad) */}
            {mode !== 'FULL' && (
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '0.35rem' }}>
                  Target Changed Files:
                </label>
                <textarea
                  value={changedFilesText}
                  onChange={(e) => setChangedFilesText(e.target.value)}
                  rows={2}
                  placeholder="One relative file path per line..."
                  style={{
                    width: '100%',
                    padding: '0.5rem 0.75rem',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-primary)',
                    fontFamily: 'monospace',
                    fontSize: '0.85rem',
                  }}
                />
              </div>
            )}

            {/* Auto-Broaden Toggle */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                id="auto-broaden-checkbox"
                checked={autoBroaden}
                onChange={(e) => setAutoBroaden(e.target.checked)}
                style={{ cursor: 'pointer' }}
              />
              <label htmlFor="auto-broaden-checkbox" style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                <strong>Auto-Broaden on Uncertainty:</strong> Automatically upgrade SELECTIVE to BROAD when dynamic imports
                or unmapped dependencies are discovered to guarantee execution safety.
              </label>
            </div>

            {/* Trigger Button */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
              <Button
                variant="primary"
                size="sm"
                icon={<GitPullRequest size={15} />}
                onClick={handleGeneratePlan}
                disabled={isLoading}
              >
                {isLoading ? 'Generating Plan...' : 'Generate Regression Plan'}
              </Button>
            </div>
          </div>

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

      {/* Loading state */}
      {isLoading && (
        <div style={{ padding: '2rem 0', display: 'flex', justifyContent: 'center' }}>
          <LoadingSpinner label="Consulting AST dependency closure and requirement protection invariants..." />
        </div>
      )}

      {/* Plan Details Display */}
      {currentPlan && !isLoading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
          {/* Plan Summary Header */}
          <Card
            style={{
              background: 'linear-gradient(135deg, rgba(22, 30, 52, 0.8) 0%, rgba(30, 41, 74, 0.6) 100%)',
              border: currentPlan.is_execution_safe
                ? '1px solid rgba(16, 185, 129, 0.3)'
                : '1px solid rgba(239, 68, 68, 0.3)',
            }}
          >
            <CardBody>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Badge variant="implemented">{currentPlan.mode} REGRESSION PLAN</Badge>
                    {currentPlan.is_execution_safe ? (
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 4,
                          fontSize: '0.75rem',
                          color: 'var(--status-completed)',
                          fontWeight: 600,
                        }}
                      >
                        <ShieldCheck size={16} /> SAFE FOR EXECUTION
                      </span>
                    ) : (
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 4,
                          fontSize: '0.75rem',
                          color: 'var(--status-failed)',
                          fontWeight: 600,
                        }}
                      >
                        <ShieldAlert size={16} /> EXECUTION BLOCKED (UNSAFE)
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.4rem' }}>
                    Source Inventory: <span style={{ fontFamily: 'monospace' }}>{currentPlan.inventory_id}</span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {currentPlan.selected_test_ids?.length ?? (currentPlan.selected_tests?.length ?? 0)}{' '}
                      <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                        / {currentPlan.total_inventory_tests ?? 0}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Tests Selected</div>
                  </div>

                  <div style={{ textAlign: 'center', borderLeft: '1px solid var(--border-subtle)', paddingLeft: '1.5rem' }}>
                    <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--status-completed)' }}>
                      {currentPlan.protected_requirement_ids?.length ?? 0}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Requirements Protected</div>
                  </div>

                  {onProceedToExecution && currentPlan.is_execution_safe && (
                    <Button
                      variant="primary"
                      size="sm"
                      icon={<ArrowRight size={15} />}
                      onClick={onProceedToExecution}
                    >
                      Proceed to Execution
                    </Button>
                  )}
                </div>
              </div>
            </CardBody>
          </Card>

          {/* Warnings & Broadening Reasons */}
          {((currentPlan.plan_warnings?.length ?? 0) > 0 || (currentPlan.broadening_reasons?.length ?? 0) > 0) && (
            <div
              style={{
                padding: '0.75rem 1rem',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(234, 179, 8, 0.08)',
                border: '1px solid rgba(234, 179, 8, 0.3)',
                fontSize: '0.85rem',
                color: 'var(--text-secondary)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, color: 'var(--status-pending)' }}>
                <AlertTriangle size={16} />
                <span>Planner Audit & Broadening Diagnostics</span>
              </div>
              <ul style={{ margin: '0.5rem 0 0 1rem', padding: 0 }}>
                {(currentPlan.broadening_reasons || []).map((r, i) => (
                  <li key={`broad-${i}`} style={{ color: 'var(--text-primary)' }}>
                    <strong>Broadened:</strong> {r}
                  </li>
                ))}
                {(currentPlan.plan_warnings || []).map((w, i) => (
                  <li key={`warn-${i}`} style={{ color: 'var(--status-pending)' }}>
                    <strong>Warning:</strong> {w}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Selected Tests by Tier Breakdown */}
          <Card style={{ background: 'var(--bg-glass-card)' }}>
            <CardHeader>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Layers size={18} color="var(--accent-cyan)" />
                <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>
                  Selected Tests by Tier ({currentPlan.selected_tests?.length ?? currentPlan.selected_test_ids?.length ?? 0} tests)
                </span>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                {Object.entries(currentPlan.selected_tests_by_tier || {}).map(([tier, ids]) => (
                  <Badge key={tier} variant="neutral">
                    {tier.replace('_', ' ')}: {Array.isArray(ids) ? ids.length : ids}
                  </Badge>
                ))}
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
                      <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Tier</th>
                      <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Test ID</th>
                      <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Target File</th>
                      <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                        Selection Rationale
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {currentPlan.selected_tests.map((st) => {
                      const reasons = currentPlan.selection_reasons_by_test[st.test_id] || st.selection_reasons || [];
                      return (
                        <tr
                          key={st.test_id}
                          style={{ borderBottom: '1px solid var(--border-subtle)' }}
                        >
                          <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                            <Badge variant="implemented">{st.tier.replace('_', ' ')}</Badge>
                          </td>
                          <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                            <div style={{ fontFamily: 'monospace', fontWeight: 600, color: 'var(--text-primary)' }}>
                              {st.test_id}
                            </div>
                            {st.target_symbol && (
                              <div style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)' }}>
                                ::{st.target_symbol}
                              </div>
                            )}
                          </td>
                          <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                            <div style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                              {st.target_file || '-'}
                            </div>
                          </td>
                          <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                              {reasons.map((r) => (
                                <Badge key={r} variant="neutral">
                                  {r.replace(/_/g, ' ')}
                                </Badge>
                              ))}
                            </div>
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
