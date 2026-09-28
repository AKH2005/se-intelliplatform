import React, { useState } from 'react';
import { Archive, Plus, Search, Tag } from 'lucide-react';
import { RequirementResponse } from '../../types/requirement';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { EmptyState } from '../common/EmptyState';
import { Card, CardBody, CardHeader, CardTitle } from '../common/Card';

interface RequirementListProps {
  requirements: RequirementResponse[];
  onOpenCreate: () => void;
  onArchive: (requirementId: string) => Promise<void>;
  isLoading?: boolean;
}

export const RequirementList: React.FC<RequirementListProps> = ({
  requirements,
  onOpenCreate,
  onArchive,
}) => {
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState<string>('ALL');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');

  const filtered = requirements.filter((r) => {
    if (r.is_archived) return false;
    if (filterType !== 'ALL' && r.type !== filterType) return false;
    if (filterStatus !== 'ALL' && r.status !== filterStatus) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      return r.title.toLowerCase().includes(q) || r.description.toLowerCase().includes(q);
    }
    return true;
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <Tag size={18} color="var(--accent-primary)" />
          Project Requirements ({requirements.filter((r) => !r.is_archived).length})
        </CardTitle>
        <Button variant="primary" size="sm" icon={<Plus size={14} />} onClick={onOpenCreate}>
          Add Requirement
        </Button>
      </CardHeader>

      <CardBody>
        {/* Filters */}
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '0.75rem',
            marginBottom: '1.25rem',
            alignItems: 'center',
          }}
        >
          <div style={{ flex: '1 1 200px', position: 'relative' }}>
            <input
              type="text"
              className="form-input"
              style={{ paddingLeft: '2rem' }}
              placeholder="Search requirements..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <Search
              size={14}
              style={{
                position: 'absolute',
                left: '0.7rem',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-muted)',
              }}
            />
          </div>

          <select
            className="form-select"
            style={{ width: 'auto' }}
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            aria-label="Filter by type"
          >
            <option value="ALL">All Types</option>
            <option value="FUNCTIONAL">FUNCTIONAL</option>
            <option value="NON_FUNCTIONAL">NON_FUNCTIONAL</option>
            <option value="CONSTRAINT">CONSTRAINT</option>
          </select>

          <select
            className="form-select"
            style={{ width: 'auto' }}
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            aria-label="Filter by status"
          >
            <option value="ALL">All Statuses</option>
            <option value="DRAFT">DRAFT</option>
            <option value="APPROVED">APPROVED</option>
            <option value="IMPLEMENTED">IMPLEMENTED</option>
            <option value="DEFERRED">DEFERRED</option>
            <option value="REJECTED">REJECTED</option>
          </select>
        </div>

        {/* Content table or empty state */}
        {requirements.length === 0 ? (
          <EmptyState
            title="No requirements found"
            description="Add requirements to build project context."
            actionLabel="Add First Requirement"
            onAction={onOpenCreate}
          />
        ) : filtered.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            No requirements match the current filters.
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: '40%' }}>Title & Description</th>
                  <th>Type</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((req) => (
                  <tr key={req.id}>
                    <td>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                        {req.title}
                      </div>
                      <div
                        style={{
                          fontSize: '0.8rem',
                          color: 'var(--text-muted)',
                          lineHeight: 1.4,
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                        }}
                      >
                        {req.description}
                      </div>
                    </td>
                    <td>
                      <Badge variant="draft">{req.type}</Badge>
                    </td>
                    <td>
                      <Badge variant={req.priority}>{req.priority}</Badge>
                    </td>
                    <td>
                      <Badge variant={req.status}>{req.status}</Badge>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={<Archive size={14} />}
                        title="Archive requirement"
                        onClick={() => onArchive(req.id)}
                      >
                        Archive
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardBody>
    </Card>
  );
};
