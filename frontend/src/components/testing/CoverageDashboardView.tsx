import React, { useState } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Search,
  Layers,
  ArrowRight,
} from 'lucide-react';
import { Card, CardBody, CardHeader } from '../common/Card';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { EmptyState } from '../common/EmptyState';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { TestTier, UnifiedCoverageReport } from '../../types/testing';

interface CoverageDashboardViewProps {
  coverage: UnifiedCoverageReport | null;
  isLoading: boolean;
  onRefresh: () => void;
  onViewGaps?: () => void;
  onSelectTest?: (testId: string) => void;
}

export const CoverageDashboardView: React.FC<CoverageDashboardViewProps> = ({
  coverage,
  isLoading,
  onRefresh,
  onViewGaps,
  onSelectTest,
}) => {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<'ALL' | 'COVERED' | 'UNCOVERED'>('ALL');

  if (isLoading && !coverage) {
    return (
      <div style={{ padding: '3rem 0', display: 'flex', justifyContent: 'center' }}>
        <LoadingSpinner label="Calculating authoritative multi-tier requirement coverage..." />
      </div>
    );
  }

  if (!coverage || coverage.total_active_requirements === 0) {
    return (
      <Card style={{ background: 'var(--bg-glass-card)' }}>
        <CardBody>
          <EmptyState
            title="No Active Requirements Found"
            description="There are no active or approved requirements in this project to measure testing coverage against."
            actionLabel="Recalculate Coverage"
            onAction={onRefresh}
          />
        </CardBody>
      </Card>
    );
  }

  const tiers: TestTier[] = ['UNIT', 'AI_TEST', 'BROWSER_SMOKE', 'BROWSER_JOURNEY'];

  const traceabilityEntries = Object.entries(coverage.requirement_traceability || {}).filter(([reqId, trace]) => {
    const matchesFilter =
      filterStatus === 'ALL' ||
      (filterStatus === 'COVERED' && trace.is_covered) ||
      (filterStatus === 'UNCOVERED' && !trace.is_covered);
    const matchesSearch =
      !searchQuery ||
      reqId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      trace.covering_test_ids.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesFilter && matchesSearch;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
      {/* Top Banner: Combined Requirement Coverage (Set-Union) */}
      <Card
        style={{
          background: 'linear-gradient(135deg, rgba(22, 30, 52, 0.8) 0%, rgba(30, 41, 74, 0.6) 100%)',
          border: '1px solid rgba(99, 102, 241, 0.3)',
        }}
      >
        <CardBody>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '1.5rem',
            }}
          >
            <div style={{ flex: 1, minWidth: 280 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <ShieldCheck size={24} color="var(--accent-cyan)" />
                <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Combined Requirement Coverage
                </h2>
                <Badge variant={coverage.combined_coverage_percentage >= 80 ? 'success' : 'partial'}>
                  {coverage.combined_coverage_percentage >= 80 ? 'HEALTHY' : 'NEEDS COVERAGE'}
                </Badge>
              </div>
              <p style={{ margin: '0.5rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                Authoritative requirement set union across all 4 tiers (NOT an arithmetic average of tier percentages).
              </p>

              {/* Progress bar */}
              <div
                style={{
                  marginTop: '1rem',
                  height: 10,
                  width: '100%',
                  background: 'var(--bg-surface)',
                  borderRadius: 'var(--radius-sm)',
                  overflow: 'hidden',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div
                  style={{
                    height: '100%',
                    width: `${Math.min(100, Math.max(0, coverage.combined_coverage_percentage))}%`,
                    background:
                      coverage.combined_coverage_percentage >= 80
                        ? 'linear-gradient(90deg, var(--accent-cyan), var(--status-completed))'
                        : 'linear-gradient(90deg, var(--status-partial), var(--accent-primary))',
                    borderRadius: 'var(--radius-sm)',
                    transition: 'width 0.4s ease',
                  }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1 }}>
                  {coverage.combined_coverage_percentage.toFixed(1)}%
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                  Unified Coverage
                </div>
              </div>

              <div style={{ borderLeft: '1px solid var(--border-subtle)', paddingLeft: '1.5rem' }}>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  Active Requirements:{' '}
                  <strong style={{ color: 'var(--text-primary)' }}>{coverage.total_active_requirements}</strong>
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--status-completed)', marginTop: '0.25rem' }}>
                  Covered:{' '}
                  <strong>{coverage.combined_covered_requirement_ids?.length ?? 0}</strong>
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--status-failed)', marginTop: '0.25rem' }}>
                  Uncovered Gaps:{' '}
                  <strong>{coverage.combined_uncovered_requirement_ids?.length ?? 0}</strong>
                </div>
              </div>

              {(coverage.combined_uncovered_requirement_ids?.length ?? 0) > 0 && onViewGaps && (
                <Button variant="secondary" size="sm" icon={<ArrowRight size={14} />} onClick={onViewGaps}>
                  Inspect Gaps
                </Button>
              )}
            </div>
          </div>
        </CardBody>
      </Card>

      {/* 4-Tier Breakdown Cards */}
      <div>
        <div style={{ marginBottom: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            Four-Tier Coverage Breakdown
          </h3>
          <Button
            variant="ghost"
            size="sm"
            icon={<RefreshCw size={14} className={isLoading ? 'spin' : ''} />}
            onClick={onRefresh}
            disabled={isLoading}
          >
            Recalculate
          </Button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
          {tiers.map((tier) => {
            const summary = coverage.tier_coverages?.[tier];
            const pct = summary ? summary.coverage_percentage : 0;
            const coveredCount = summary ? summary.covered_requirement_count : 0;
            const total = summary ? summary.total_active_requirements : coverage.total_active_requirements;

            return (
              <Card key={tier} style={{ background: 'var(--bg-glass-card)' }}>
                <CardHeader>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span
                      style={{
                        display: 'inline-block',
                        width: 10,
                        height: 10,
                        borderRadius: '50%',
                        background:
                          tier === 'UNIT'
                            ? 'var(--accent-primary)'
                            : tier === 'AI_TEST'
                            ? 'var(--accent-cyan)'
                            : tier === 'BROWSER_SMOKE'
                            ? 'var(--status-completed)'
                            : '#a855f7',
                      }}
                    />
                    <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{tier.replace('_', ' ')}</span>
                  </div>
                  <Badge variant={pct >= 70 ? 'success' : pct > 0 ? 'partial' : 'draft'}>
                    {pct.toFixed(1)}%
                  </Badge>
                </CardHeader>
                <CardBody>
                  <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {coveredCount} <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>/ {total}</span>
                    </span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>requirements</span>
                  </div>

                  <div
                    style={{
                      marginTop: '0.75rem',
                      height: 6,
                      background: 'var(--bg-surface)',
                      borderRadius: 'var(--radius-sm)',
                      overflow: 'hidden',
                    }}
                  >
                    <div
                      style={{
                        height: '100%',
                        width: `${Math.min(100, Math.max(0, pct))}%`,
                        background:
                          tier === 'UNIT'
                            ? 'var(--accent-primary)'
                            : tier === 'AI_TEST'
                            ? 'var(--accent-cyan)'
                            : tier === 'BROWSER_SMOKE'
                            ? 'var(--status-completed)'
                            : '#a855f7',
                      }}
                    />
                  </div>

                  <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {tier === 'UNIT' && 'Fast deterministic test execution'}
                    {tier === 'AI_TEST' && 'Synthesized automated unit/integration'}
                    {tier === 'BROWSER_SMOKE' && 'Playwright UI smoke endpoints'}
                    {tier === 'BROWSER_JOURNEY' && 'Multi-step user workflow journeys'}
                  </div>
                </CardBody>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Requirement Traceability Matrix */}
      <Card style={{ background: 'var(--bg-glass-card)' }}>
        <CardHeader>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Layers size={18} color="var(--accent-primary)" />
            <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>
              Requirement Traceability Matrix ({traceabilityEntries.length} items)
            </span>
          </div>
        </CardHeader>
        <CardBody>
          {/* Search & Filter */}
          <div style={{ marginBottom: '1rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: 260, position: 'relative' }}>
              <Search
                size={16}
                color="var(--text-muted)"
                style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)' }}
              />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search requirements or covering test IDs..."
                style={{
                  width: '100%',
                  padding: '0.5rem 0.75rem 0.5rem 2rem',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-primary)',
                  fontSize: '0.85rem',
                }}
              />
            </div>
            <div style={{ display: 'flex', gap: '0.25rem' }}>
              <Button
                variant={filterStatus === 'ALL' ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setFilterStatus('ALL')}
              >
                All
              </Button>
              <Button
                variant={filterStatus === 'COVERED' ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setFilterStatus('COVERED')}
              >
                Covered ({coverage.combined_covered_requirement_ids?.length ?? 0})
              </Button>
              <Button
                variant={filterStatus === 'UNCOVERED' ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setFilterStatus('UNCOVERED')}
              >
                Uncovered ({coverage.combined_uncovered_requirement_ids?.length ?? 0})
              </Button>
            </div>
          </div>

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
                  <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Requirement</th>
                  <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Status</th>
                  <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Covering Tiers</th>
                  <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                    Covering Test IDs
                  </th>
                </tr>
              </thead>
              <tbody>
                {traceabilityEntries.map(([reqId, trace]) => (
                  <tr
                    key={reqId}
                    style={{
                      borderBottom: '1px solid var(--border-subtle)',
                      background: 'transparent',
                      transition: 'background 0.15s ease',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-surface-hover)')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                  >
                    <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'monospace' }}>
                        {reqId}
                      </div>
                    </td>
                    <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                      {trace.is_covered ? (
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 4,
                            color: 'var(--status-completed)',
                            fontWeight: 600,
                            fontSize: '0.75rem',
                          }}
                        >
                          <CheckCircle2 size={14} /> COVERED
                        </span>
                      ) : (
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 4,
                            color: 'var(--status-failed)',
                            fontWeight: 600,
                            fontSize: '0.75rem',
                          }}
                        >
                          <XCircle size={14} /> UNCOVERED
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                      {trace.covering_tiers && trace.covering_tiers.length > 0 ? (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                          {trace.covering_tiers.map((t) => (
                            <Badge key={t} variant="implemented">
                              {t.replace('_', ' ')}
                            </Badge>
                          ))}
                        </div>
                      ) : (
                        <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>None</span>
                      )}
                    </td>
                    <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                      {trace.covering_test_ids && trace.covering_test_ids.length > 0 ? (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                          {trace.covering_test_ids.map((tid) => (
                            <span
                              key={tid}
                              onClick={() => onSelectTest && onSelectTest(tid)}
                              style={{
                                cursor: onSelectTest ? 'pointer' : 'default',
                                padding: '0.15rem 0.4rem',
                                borderRadius: 'var(--radius-sm)',
                                background: 'rgba(56, 189, 248, 0.1)',
                                border: '1px solid rgba(56, 189, 248, 0.3)',
                                color: 'var(--accent-cyan)',
                                fontSize: '0.75rem',
                                fontFamily: 'monospace',
                              }}
                              title={`Covering test: ${tid}`}
                            >
                              {tid}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>No covering tests</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};
