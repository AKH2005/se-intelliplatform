import React from 'react';
import { Database, Key, Link2 } from 'lucide-react';

export const ErdPreview: React.FC = () => {
  const entities = [
    {
      name: 'projects',
      fields: [
        { name: 'id', type: 'UUID (PK)', isKey: true },
        { name: 'name', type: 'VARCHAR(255)' },
        { name: 'slug', type: 'VARCHAR(100) UNIQUE' },
        { name: 'status', type: 'VARCHAR(50)' },
      ],
      relations: ['1:N requirements', '1:N context_snapshots', '1:N workflow_executions'],
    },
    {
      name: 'requirements',
      fields: [
        { name: 'id', type: 'UUID (PK)', isKey: true },
        { name: 'project_id', type: 'UUID (FK)', isKey: false },
        { name: 'title', type: 'VARCHAR(255)' },
        { name: 'type', type: 'VARCHAR(50)' },
        { name: 'status', type: 'VARCHAR(50)' },
      ],
      relations: ['N:1 projects'],
    },
    {
      name: 'context_snapshots',
      fields: [
        { name: 'id', type: 'UUID (PK)', isKey: true },
        { name: 'project_id', type: 'UUID (FK)', isKey: false },
        { name: 'version', type: 'INT' },
        { name: 'snapshot_data', type: 'JSONB' },
      ],
      relations: ['N:1 projects', '1:N workflow_executions'],
    },
    {
      name: 'workflow_executions',
      fields: [
        { name: 'id', type: 'UUID (PK)', isKey: true },
        { name: 'project_id', type: 'UUID (FK)', isKey: false },
        { name: 'workflow_id', type: 'VARCHAR(100)' },
        { name: 'status', type: 'VARCHAR(50)' },
      ],
      relations: ['1:N workflow_step_results', '1:N agent_artifacts'],
    },
  ];

  return (
    <div
      style={{
        background: 'var(--bg-surface-subtle)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        padding: 'var(--space-md)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-md)',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: '0.5rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 600, fontSize: '0.85rem' }}>
          <Database size={16} color="var(--status-completed)" />
          <span>Core Domain Schema (Entity Relationship)</span>
        </div>
        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
          PostgreSQL Relational Relational Models
        </span>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
          gap: 'var(--space-md)',
        }}
      >
        {entities.map((entity) => (
          <div
            key={entity.name}
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <div
              style={{
                background: 'var(--bg-surface-active)',
                padding: '0.45rem 0.75rem',
                fontWeight: 600,
                fontSize: '0.8rem',
                color: 'var(--text-primary)',
                fontFamily: 'monospace',
                borderBottom: '1px solid var(--border-subtle)',
              }}
            >
              {entity.name}
            </div>

            <div style={{ padding: '0.5rem 0.75rem', flex: 1, display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              {entity.fields.map((f, i) => (
                <div
                  key={i}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '0.72rem',
                    fontFamily: 'monospace',
                    color: f.isKey ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                  }}
                >
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    {f.isKey && <Key size={10} />}
                    {f.name}
                  </span>
                  <span style={{ color: 'var(--text-dim)', fontSize: '0.68rem' }}>{f.type}</span>
                </div>
              ))}
            </div>

            <div
              style={{
                padding: '0.35rem 0.75rem',
                borderTop: '1px solid var(--border-subtle)',
                background: 'rgba(0, 0, 0, 0.1)',
                fontSize: '0.68rem',
                color: 'var(--text-muted)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.3rem',
              }}
            >
              <Link2 size={11} />
              <span>{entity.relations[0]}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
