import React, { useState } from 'react';
import {
  Network,
  CheckCircle2,
  FileCode,
  ShieldAlert,
  ArrowRight,
} from 'lucide-react';
import { Card, CardBody, CardHeader } from '../common/Card';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ChangeImpactReport } from '../../types/testing';
import { testingApi } from '../../services/testingApi';

interface ChangeImpactViewProps {
  projectId: string;
  selectedVersionId?: string;
  onPlanRegressionWithImpact?: (changedFiles: string[]) => void;
}

export const ChangeImpactView: React.FC<ChangeImpactViewProps> = ({
  projectId,
  selectedVersionId,
  onPlanRegressionWithImpact,
}) => {
  const [changedFilesText, setChangedFilesText] = useState<string>('app/api/v1/endpoints/testing.py');
  const [report, setReport] = useState<ChangeImpactReport | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorNotice, setErrorNotice] = useState<string | null>(null);

  const handleAnalyzeImpact = async () => {
    if (!projectId || isLoading) return;

    const files = changedFilesText
      .split('\n')
      .map((f) => f.trim())
      .filter((f) => f.length > 0);

    if (files.length === 0) {
      setErrorNotice('Please specify at least one changed file path to analyze.');
      return;
    }

    setIsLoading(true);
    setErrorNotice(null);

    try {
      const res = await testingApi.analyzeImpact(projectId, {
        changed_files: files,
        target_version_id: selectedVersionId || undefined,
      });
      setReport(res);
    } catch (err: any) {
      setErrorNotice(err?.message || 'Failed to compute AST change impact analysis');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
      {/* Controls Card */}
      <Card style={{ background: 'var(--bg-glass-card)' }}>
        <CardHeader>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Network size={18} color="var(--accent-cyan)" />
            <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>
              AST Static Dependency Graph & Change Impact Analyzer
            </span>
          </div>
        </CardHeader>
        <CardBody>
          <p style={{ margin: '0 0 1rem 0', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Calculates deterministic dependency closures, identifying directly and transitively affected files,
            impacted tests, and active requirements. Flags dynamic imports and unsupported files conservatively.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Changed File Paths (One per line):
            </label>
            <textarea
              value={changedFilesText}
              onChange={(e) => setChangedFilesText(e.target.value)}
              rows={3}
              placeholder="e.g. app/services/auth.py&#10;app/models/user.py"
              style={{
                width: '100%',
                padding: '0.75rem',
                borderRadius: 'var(--radius-sm)',
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-primary)',
                fontFamily: 'monospace',
                fontSize: '0.85rem',
              }}
            />

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Target Scope:{' '}
                {selectedVersionId ? `Development Version (${selectedVersionId.slice(0, 8)})` : 'Active Project Baseline'}
              </div>
              <Button
                variant="primary"
                size="sm"
                icon={<Network size={15} />}
                onClick={handleAnalyzeImpact}
                disabled={isLoading}
              >
                {isLoading ? 'Computing AST Impact...' : 'Analyze Change Impact'}
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

      {/* Loading State */}
      {isLoading && (
        <div style={{ padding: '2rem 0', display: 'flex', justifyContent: 'center' }}>
          <LoadingSpinner label="Parsing Python AST & computing transitive closure..." />
        </div>
      )}

      {/* Impact Report Display */}
      {report && !isLoading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
          {/* Conservative Uncertainty Alert Banner */}
          {report.requires_broader_regression ? (
            <div
              style={{
                padding: '1rem',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(234, 179, 8, 0.1)',
                border: '1px solid rgba(234, 179, 8, 0.35)',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.75rem',
                fontSize: '0.85rem',
                color: 'var(--text-secondary)',
              }}
            >
              <ShieldAlert size={22} color="var(--status-pending)" style={{ flexShrink: 0, marginTop: 2 }} />
              <div>
                <strong style={{ color: 'var(--status-pending)', fontSize: '0.9rem' }}>
                  Broader Regression Required (Uncertainty Detected)
                </strong>
                <p style={{ margin: '0.25rem 0 0.5rem 0', color: 'var(--text-primary)' }}>
                  Static AST analysis detected dynamic imports, unsupported languages, or unmapped dependencies.
                  Per platform safety rules, <strong>unknown dependencies never imply zero impact</strong>.
                  Selective regression cannot be guaranteed safe without broader coverage.
                </p>
                {report.uncertainty_reasons && report.uncertainty_reasons.length > 0 && (
                  <ul style={{ margin: '0.25rem 0 0 1rem', padding: 0 }}>
                    {report.uncertainty_reasons.map((reason, i) => (
                      <li key={i} style={{ color: 'var(--text-secondary)' }}>
                        {reason}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          ) : (
            <div
              style={{
                padding: '0.75rem 1rem',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(16, 185, 129, 0.08)',
                border: '1px solid rgba(16, 185, 129, 0.25)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                fontSize: '0.85rem',
                color: 'var(--text-secondary)',
              }}
            >
              <CheckCircle2 size={18} color="var(--status-completed)" style={{ flexShrink: 0 }} />
              <span>
                <strong style={{ color: 'var(--status-completed)' }}>High Confidence AST Analysis:</strong> Zero
                dynamic imports or unknown dependencies. Selective regression can safely isolate exact impact set.
              </span>
            </div>
          )}

          {/* Metric Summary Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
            <div
              style={{
                padding: '1rem',
                borderRadius: 'var(--radius-md)',
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                Directly Changed
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.25rem' }}>
                {report.changed_files?.length ?? 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>source files</div>
            </div>

            <div
              style={{
                padding: '1rem',
                borderRadius: 'var(--radius-md)',
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                Total Affected Files
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--accent-cyan)', marginTop: '0.25rem' }}>
                {report.all_affected_files?.length ?? 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                {report.directly_affected_files?.length ?? 0} direct, {report.transitively_affected_files?.length ?? 0} transitive
              </div>
            </div>

            <div
              style={{
                padding: '1rem',
                borderRadius: 'var(--radius-md)',
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                Affected Tests
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--accent-primary)', marginTop: '0.25rem' }}>
                {report.affected_tests?.length ?? 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>across all tiers</div>
            </div>

            <div
              style={{
                padding: '1rem',
                borderRadius: 'var(--radius-md)',
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                Affected Requirements
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--status-completed)', marginTop: '0.25rem' }}>
                {report.affected_requirements?.length ?? 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>authoritatively linked</div>
            </div>
          </div>

          {/* Quick Action to Plan Regression */}
          {onPlanRegressionWithImpact && (
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="primary"
                size="sm"
                icon={<ArrowRight size={15} />}
                onClick={() => onPlanRegressionWithImpact(report.changed_files || [])}
              >
                Proceed to Regression Planning
              </Button>
            </div>
          )}

          {/* Affected Tests Detail Table */}
          <Card style={{ background: 'var(--bg-glass-card)' }}>
            <CardHeader>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <FileCode size={18} color="var(--accent-primary)" />
                <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>
                  Impacted Tests ({report.affected_tests?.length ?? 0})
                </span>
              </div>
            </CardHeader>
            <CardBody>
              {(report.affected_tests?.length ?? 0) === 0 ? (
                <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No tests in the inventory directly or transitively depend on the changed files.
                </div>
              ) : (
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
                        <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Test</th>
                        <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Target File</th>
                        <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Impact Rationale</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(report.affected_tests || []).map((test) => {
                        const reasons = report.test_impact_reasons?.[test.test_id] || [];
                        return (
                          <tr
                            key={test.test_id}
                            style={{ borderBottom: '1px solid var(--border-subtle)' }}
                          >
                            <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                              <Badge variant="implemented">{test.tier.replace('_', ' ')}</Badge>
                            </td>
                            <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{test.name}</div>
                              <div style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                {test.test_id}
                              </div>
                            </td>
                            <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                              <div style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: 'var(--text-primary)' }}>
                                {test.target_file}
                              </div>
                            </td>
                            <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
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
              )}
            </CardBody>
          </Card>
        </div>
      )}
    </div>
  );
};
