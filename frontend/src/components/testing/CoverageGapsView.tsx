import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Search,
  FileQuestion,
  Sparkles,
} from 'lucide-react';
import { Card, CardBody, CardHeader } from '../common/Card';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { EmptyState } from '../common/EmptyState';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { CoverageGapsResponse } from '../../types/testing';

interface CoverageGapsViewProps {
  gapsResponse: CoverageGapsResponse | null;
  isLoading: boolean;
  onRefresh: () => void;
  onSelectTest?: (testId: string) => void;
  onRequestAssistantGaps?: () => void;
}

export const CoverageGapsView: React.FC<CoverageGapsViewProps> = ({
  gapsResponse,
  isLoading,
  onRefresh,
  onSelectTest,
  onRequestAssistantGaps,
}) => {
  const [searchQuery, setSearchQuery] = useState<string>('');

  if (isLoading && !gapsResponse) {
    return (
      <div style={{ padding: '3rem 0', display: 'flex', justifyContent: 'center' }}>
        <LoadingSpinner label="Deriving active requirement coverage gaps..." />
      </div>
    );
  }

  if (!gapsResponse || gapsResponse.gaps.length === 0) {
    return (
      <Card style={{ background: 'var(--bg-glass-card)' }}>
        <CardBody>
          <EmptyState
            title="Zero Coverage Gaps!"
            description="100% of active requirements have verified authoritative test coverage across platform testing tiers."
            icon={<CheckCircle2 size={32} color="var(--status-completed)" />}
            actionLabel="Re-check Gaps"
            onAction={onRefresh}
          />
        </CardBody>
      </Card>
    );
  }

  const filteredGaps = gapsResponse.gaps.filter((g) => {
    return (
      !searchQuery ||
      g.requirement_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      g.requirement_title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      g.priority.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
      {/* Gaps Alert Banner */}
      <div
        style={{
          padding: '1rem',
          borderRadius: 'var(--radius-md)',
          background: 'rgba(239, 68, 68, 0.08)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <AlertTriangle size={24} color="var(--status-failed)" style={{ flexShrink: 0 }} />
          <div>
            <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.95rem' }}>
              {gapsResponse.uncovered_count} Active Requirements Lack Authoritative Test Protection
            </div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.15rem' }}>
              These requirements have no passing or linked unit, AI-generated, or browser test cases in the authoritative inventory.
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {onRequestAssistantGaps && (
            <Button
              variant="secondary"
              size="sm"
              icon={<Sparkles size={14} color="var(--accent-cyan)" />}
              onClick={onRequestAssistantGaps}
            >
              Ask Assistant to Plan Tests
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            icon={<RefreshCw size={14} className={isLoading ? 'spin' : ''} />}
            onClick={onRefresh}
            disabled={isLoading}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Gaps List Table */}
      <Card style={{ background: 'var(--bg-glass-card)' }}>
        <CardHeader>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FileQuestion size={18} color="var(--status-failed)" />
            <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>
              Uncovered Requirements ({filteredGaps.length} shown)
            </span>
          </div>
        </CardHeader>
        <CardBody>
          {/* Search filter */}
          <div style={{ marginBottom: '1rem', position: 'relative' }}>
            <Search
              size={16}
              color="var(--text-muted)"
              style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)' }}
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search gaps by ID, title, or priority..."
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
                  <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Priority</th>
                  <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Lifecycle</th>
                  <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Covering Tiers</th>
                  <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 600 }}>Associated Tests</th>
                </tr>
              </thead>
              <tbody>
                {filteredGaps.map((gap) => (
                  <tr
                    key={gap.requirement_id}
                    style={{
                      borderBottom: '1px solid var(--border-subtle)',
                      background: 'transparent',
                      transition: 'background 0.15s ease',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-surface-hover)')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                  >
                    <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{gap.requirement_title}</div>
                      <div
                        style={{
                          fontFamily: 'monospace',
                          fontSize: '0.75rem',
                          color: 'var(--text-muted)',
                          marginTop: '0.2rem',
                        }}
                      >
                        {gap.requirement_id}
                      </div>
                      {gap.notes && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem', fontStyle: 'italic' }}>
                          {gap.notes}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                      <Badge
                        variant={
                          gap.priority === 'CRITICAL'
                            ? 'critical'
                            : gap.priority === 'HIGH'
                            ? 'high'
                            : gap.priority === 'MEDIUM'
                            ? 'medium'
                            : 'low'
                        }
                      >
                        {gap.priority}
                      </Badge>
                    </td>
                    <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                      <Badge variant="draft">{gap.status}</Badge>
                    </td>
                    <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                      {gap.covering_tiers && gap.covering_tiers.length > 0 ? (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                          {gap.covering_tiers.map((t) => (
                            <Badge key={t} variant="implemented">
                              {t}
                            </Badge>
                          ))}
                        </div>
                      ) : (
                        <span style={{ color: 'var(--status-failed)', fontSize: '0.75rem', fontWeight: 600 }}>
                          0 / 4 Tiers
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '0.75rem', verticalAlign: 'top' }}>
                      {gap.associated_test_ids && gap.associated_test_ids.length > 0 ? (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                          {gap.associated_test_ids.map((tid) => (
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
                              title={`Associated test: ${tid}`}
                            >
                              {tid}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem', fontStyle: 'italic' }}>
                          No tests associated
                        </span>
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
