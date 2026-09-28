import React from 'react';
import { DatabaseDesignOutput } from '../../types/artifacts';
import { Badge } from '../common/Badge';

interface DatabaseArtifactProps {
  artifact: DatabaseDesignOutput;
}

export const DatabaseArtifact: React.FC<DatabaseArtifactProps> = ({ artifact }) => {
  const { summary, database_paradigm, entities, relationships } = artifact;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Summary */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <h4 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Database Schema Overview</h4>
          <Badge variant="in-progress">{database_paradigm}</Badge>
        </div>
        <p style={{ fontSize: '0.875rem', lineHeight: 1.6, color: 'var(--text-primary)' }}>
          {summary}
        </p>
      </div>

      {/* Entities */}
      {entities && entities.length > 0 && (
        <div>
          <h4 style={{ fontSize: '0.9rem', marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
            Entities & Tables ({entities.length})
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {entities.map((entity, idx) => (
              <div
                key={idx}
                style={{
                  background: 'var(--bg-surface)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                  padding: '1rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.95rem' }}>
                    {entity.name}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    PK: {entity.primary_key?.attributes?.join(', ') || 'None'}
                  </span>
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                  {entity.description}
                </div>

                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Attribute</th>
                        <th>Type</th>
                        <th>Nullable</th>
                        <th>Unique</th>
                        <th>Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {entity.attributes.map((attr, aIdx) => (
                        <tr key={aIdx}>
                          <td style={{ fontWeight: 500, fontFamily: 'monospace' }}>{attr.name}</td>
                          <td>
                            <Badge variant="draft">{attr.data_type}</Badge>
                          </td>
                          <td>{attr.nullable ? 'YES' : 'NO'}</td>
                          <td>{attr.unique ? 'YES' : 'NO'}</td>
                          <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                            {attr.description}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Relationships */}
      {relationships && relationships.length > 0 && (
        <div>
          <h4 style={{ fontSize: '0.9rem', marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
            Entity Relationships ({relationships.length})
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {relationships.map((rel, idx) => (
              <div
                key={idx}
                style={{
                  background: 'var(--bg-surface)',
                  padding: '0.75rem 1rem',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  fontSize: '0.85rem',
                }}
              >
                <div>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{rel.source_entity}</span>
                  <span style={{ margin: '0 0.5rem', color: 'var(--text-muted)' }}>→</span>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{rel.target_entity}</span>
                  <span style={{ marginLeft: '0.75rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    ({rel.description})
                  </span>
                </div>
                <Badge variant="draft">{rel.relationship_type}</Badge>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
