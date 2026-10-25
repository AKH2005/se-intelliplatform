import React, { useState } from 'react';
import {
  FileText,
  CheckCircle2,
  AlertTriangle,
  Search,
  RefreshCw,
  Layers,
  Info,
} from 'lucide-react';
import { Card, CardBody, CardHeader } from '../common/Card';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { EmptyState } from '../common/EmptyState';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { TestTier, UnifiedTestInventory } from '../../types/testing';

interface TestInventoryViewProps {
  inventory: UnifiedTestInventory | null;
  isLoading: boolean;
  onRefresh: () => void;
  onSelectRequirement?: (reqId: string) => void;
}

export const TestInventoryView: React.FC<TestInventoryViewProps> = ({
  inventory,
  isLoading,
  onRefresh,
  onSelectRequirement,
}) => {
  const [selectedTier, setSelectedTier] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  if (isLoading && !inventory) {
    return (
      <div style={{ padding: '3rem 0', display: 'flex', justifyContent: 'center' }}>
        <LoadingSpinner label="Loading authoritative test inventory across all tiers..." />
      </div>
    );
  }

  if (!inventory || inventory.total_tests === 0) {
    return (
      <Card style={{ background: 'var(--bg-glass-card)' }}>
        <CardBody>
          <EmptyState
            title="No Tests in Inventory"
            description="No tests were discovered across UNIT, AI_TEST, BROWSER_SMOKE, or BROWSER_JOURNEY tiers for this project."
            actionLabel="Scan & Discover Tests"
            onAction={onRefresh}
          />
        </CardBody>
      </Card>
    );
  }

  const tiersList: TestTier[] = ['UNIT', 'AI_TEST', 'BROWSER_SMOKE', 'BROWSER_JOURNEY'];

  const filteredTests = inventory.tests.filter((t) => {
    const matchesTier = selectedTier === 'ALL' || t.tier === selectedTier;
    const matchesSearch =
      !searchQuery ||
      t.test_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.target_file.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (t.target_symbol && t.target_symbol.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesTier && matchesSearch;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
      {/* Tier Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        <div
          onClick={() => setSelectedTier('ALL')}
          style={{
            padding: '1rem',
            borderRadius: 'var(--radius-md)',
            background: selectedTier === 'ALL' ? 'var(--bg-surface-active)' : 'var(--bg-surface)',
            border: selectedTier === 'ALL' ? '1px solid var(--accent-primary)' : '1px solid var(--border-subtle)',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Total Tests
            </span>
            <Layers size={16} color="var(--accent-primary)" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '0.5rem', color: 'var(--text-primary)' }}>
            {inventory.total_tests}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            All 4 tiers combined
          </div>
        </div>

        {tiersList.map((tier) => {
          const count = inventory.tier_counts?.[tier] ?? 0;
          const isSelected = selectedTier === tier;
          return (
            <div
              key={tier}
              onClick={() => setSelectedTier(tier)}
              style={{
                padding: '1rem',
                borderRadius: 'var(--radius-md)',
                background: isSelected ? 'var(--bg-surface-active)' : 'var(--bg-surface)',
                border: isSelected ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                  {tier.replace('_', ' ')}
                </span>
                <span
                  style={{
                    display: 'inline-block',
                    width: 8,
                    height: 8,
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
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '0.5rem', color: 'var(--text-primary)' }}>
                {count}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                {tier === 'UNIT' && 'Fast determinism'}
                {tier === 'AI_TEST' && 'Synthesized coverage'}
                {tier === 'BROWSER_SMOKE' && 'Playwright UI smoke'}
                {tier === 'BROWSER_JOURNEY' && 'Multi-step journeys'}
              </div>
            </div>
          );
        })}
      </div>

      {/* Traceability Distinction Notice */}
      <div
        style={{
          padding: '0.75rem 1rem',
          borderRadius: 'var(--radius-md)',
          background: 'rgba(99, 102, 241, 0.08)',
          border: '1px solid rgba(99, 102, 241, 0.25)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          fontSize: '0.85rem',
          color: 'var(--text-secondary)',
        }}
      >
        <Info size={18} color="var(--accent-primary)" style={{ flexShrink: 0 }} />
        <span>
          <strong style={{ color: 'var(--text-primary)' }}>Authoritative vs Inferred Links:</strong> Only{' '}
          <strong style={{ color: 'var(--status-completed)' }}>authoritative requirement links</strong> provide verified
          traceability and contribute to unified requirement coverage. Inferred links are strictly informational.
        </span>
      </div>

      {/* Search & Filter Bar */}
      <Card style={{ background: 'var(--bg-glass-card)' }}>
        <CardHeader>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FileText size={18} color="var(--accent-cyan)" />
            <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>
              Test Definitions Catalog ({filteredTests.length} shown)
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Button
              variant="secondary"
              size="sm"
              icon={<RefreshCw size={14} className={isLoading ? 'spin' : ''} />}
              onClick={onRefresh}
              disabled={isLoading}
            >
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardBody>
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
                placeholder="Search by test ID, name, file path, or symbol..."
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
              {['ALL', ...tiersList].map((t) => (
                <Button
                  key={t}
                  variant={selectedTier === t ? 'primary' : 'ghost'}
                  size="sm"
                  onClick={() => setSelectedTier(t)}
                >
                  {t.replace('_', ' ')}
                </Button>
              ))}
            </div>
          </div>

          {/* Test Definitions Table */}
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
                  <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Test Identity</th>
                  <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Target Code</th>
                  <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                    Requirement Traceability
                  </th>
                  <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Provenance</th>
                </tr>
              </thead>
              <tbody>
                {filteredTests.map((test) => {
                  const hasAuthoritative = test.requirement_links && test.requirement_links.length > 0;
                  const hasInferred = test.inferred_requirement_links && test.inferred_requirement_links.length > 0;

                  return (
                    <tr
                      key={test.test_id}
                      style={{
                        borderBottom: '1px solid var(--border-subtle)',
                        background: 'transparent',
                        transition: 'background 0.15s ease',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-surface-hover)')}
                      onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                    >
                      <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                        <Badge
                          variant={
                            test.tier === 'UNIT'
                              ? 'implemented'
                              : test.tier === 'AI_TEST'
                              ? 'in_progress'
                              : test.tier === 'BROWSER_SMOKE'
                              ? 'approved'
                              : 'high'
                          }
                        >
                          {test.tier.replace('_', ' ')}
                        </Badge>
                      </td>
                      <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{test.name}</div>
                        <div
                          style={{
                            fontFamily: 'monospace',
                            fontSize: '0.75rem',
                            color: 'var(--text-muted)',
                            marginTop: '0.2rem',
                          }}
                        >
                          {test.test_id}
                        </div>
                        {test.tier === 'BROWSER_JOURNEY' && (
                          <div style={{ marginTop: '0.3rem' }}>
                            {test.is_validated_journey ? (
                              <span
                                style={{
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: 4,
                                  fontSize: '0.75rem',
                                  color: 'var(--status-completed)',
                                }}
                              >
                                <CheckCircle2 size={12} /> Validated Journey
                              </span>
                            ) : (
                              <span
                                style={{
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: 4,
                                  fontSize: '0.75rem',
                                  color: 'var(--status-failed)',
                                }}
                              >
                                <AlertTriangle size={12} /> Unvalidated Journey Identity
                              </span>
                            )}
                          </div>
                        )}
                      </td>
                      <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                        <div style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: 'var(--text-primary)' }}>
                          {test.target_file}
                        </div>
                        {test.target_symbol && (
                          <div
                            style={{
                              fontFamily: 'monospace',
                              fontSize: '0.75rem',
                              color: 'var(--accent-cyan)',
                              marginTop: '0.15rem',
                            }}
                          >
                            ::{test.target_symbol}
                          </div>
                        )}
                      </td>
                      <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                        {hasAuthoritative ? (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                            <span style={{ fontSize: '0.75rem', color: 'var(--status-completed)', fontWeight: 600 }}>
                              Authoritative ({test.requirement_links.length}):
                            </span>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                              {test.requirement_links.map((reqId) => (
                                <span
                                  key={reqId}
                                  onClick={() => onSelectRequirement && onSelectRequirement(reqId)}
                                  style={{
                                    cursor: onSelectRequirement ? 'pointer' : 'default',
                                    padding: '0.15rem 0.4rem',
                                    borderRadius: 'var(--radius-sm)',
                                    background: 'rgba(16, 185, 129, 0.15)',
                                    border: '1px solid rgba(16, 185, 129, 0.35)',
                                    color: 'var(--status-completed)',
                                    fontSize: '0.75rem',
                                    fontFamily: 'monospace',
                                  }}
                                  title={`Authoritative Requirement Link: ${reqId}`}
                                >
                                  {reqId}
                                </span>
                              ))}
                            </div>
                          </div>
                        ) : null}

                        {hasInferred ? (
                          <div
                            style={{
                              marginTop: hasAuthoritative ? '0.4rem' : '0',
                              display: 'flex',
                              flexDirection: 'column',
                              gap: '0.25rem',
                            }}
                          >
                            <span style={{ fontSize: '0.75rem', color: 'var(--status-partial)', fontWeight: 600 }}>
                              Inferred (Non-Authoritative):
                            </span>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                              {test.inferred_requirement_links.map((reqId) => (
                                <span
                                  key={reqId}
                                  style={{
                                    padding: '0.15rem 0.4rem',
                                    borderRadius: 'var(--radius-sm)',
                                    background: 'rgba(245, 158, 11, 0.1)',
                                    border: '1px dashed rgba(245, 158, 11, 0.4)',
                                    color: 'var(--status-partial)',
                                    fontSize: '0.75rem',
                                    fontFamily: 'monospace',
                                  }}
                                  title={`Inferred Link: ${reqId} (Does not contribute to authoritative coverage)`}
                                >
                                  ~{reqId}
                                </span>
                              ))}
                            </div>
                          </div>
                        ) : null}

                        {!hasAuthoritative && !hasInferred && (
                          <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem', fontStyle: 'italic' }}>
                            No requirement link
                          </span>
                        )}
                      </td>
                      <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                        <span
                          style={{
                            fontSize: '0.75rem',
                            color: 'var(--text-muted)',
                            fontFamily: 'monospace',
                          }}
                        >
                          {test.provenance.toLowerCase().replace(/_/g, ' ')}
                        </span>
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
  );
};
