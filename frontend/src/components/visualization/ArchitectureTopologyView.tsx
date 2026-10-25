import React from 'react';
import { Layers, Server, Database, Globe, Cpu, ArrowDown } from 'lucide-react';

export const ArchitectureTopologyView: React.FC = () => {
  const tiers = [
    {
      title: 'Presentation & Interaction Tier',
      icon: <Globe size={16} color="var(--accent-cyan)" />,
      badge: 'Vite / React 18 / TypeScript',
      components: ['Project Context Workspace', 'Workflow Studio & DAG Runner', 'Artifact Inspectors (9 Agents)', 'Intelli Assistant Dock'],
      color: 'var(--accent-cyan)',
    },
    {
      title: 'API Gateway & Orchestration Tier',
      icon: <Server size={16} color="var(--accent-primary)" />,
      badge: 'FastAPI / Python 3.12 / Pydantic v2',
      components: ['REST API Routes (/api/v1)', 'WorkflowCoordinator', 'AgentExecutor (Synchronous)', 'Audit & Context Engine'],
      color: 'var(--accent-primary)',
    },
    {
      title: 'Domain Engineering Agents Tier',
      icon: <Cpu size={16} color="var(--sdlc-design)" />,
      badge: '9 Deterministic Multi-Agent Pipelines',
      components: [
        'Requirement Analysis & Architecture',
        'Database Design & Risk/Timeline Prediction',
        'Bug Prediction & Test Case Generation',
        'Code Review & Rationale Explainability',
      ],
      color: 'var(--sdlc-design)',
    },
    {
      title: 'Canonical Persistence Tier',
      icon: <Database size={16} color="var(--status-completed)" />,
      badge: 'PostgreSQL / SQLAlchemy Async / Alembic',
      components: ['projects & requirements', 'context_snapshots', 'workflow_executions & step_results', 'agent_artifacts'],
      color: 'var(--status-completed)',
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
          <Layers size={16} color="var(--accent-primary)" />
          <span>SE IntelliPlatform System Topology</span>
        </div>
        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
          Multi-Tier Architectural Blueprint
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
        {tiers.map((tier, idx) => (
          <React.Fragment key={idx}>
            <div
              style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.75rem 1rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.4rem',
                borderLeft: `3px solid ${tier.color}`,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, fontSize: '0.82rem' }}>
                  {tier.icon}
                  <span>{tier.title}</span>
                </div>
                <span
                  style={{
                    fontSize: '0.7rem',
                    color: 'var(--text-muted)',
                    fontFamily: 'monospace',
                    background: 'var(--bg-surface-active)',
                    padding: '0.15rem 0.45rem',
                    borderRadius: 'var(--radius-sm)',
                  }}
                >
                  {tier.badge}
                </span>
              </div>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                  gap: '0.4rem',
                  marginTop: '0.2rem',
                }}
              >
                {tier.components.map((comp, compIdx) => (
                  <div
                    key={compIdx}
                    style={{
                      fontSize: '0.74rem',
                      color: 'var(--text-secondary)',
                      background: 'rgba(255, 255, 255, 0.02)',
                      padding: '0.25rem 0.5rem',
                      borderRadius: '3px',
                      border: '1px solid rgba(255, 255, 255, 0.04)',
                    }}
                  >
                    • {comp}
                  </div>
                ))}
              </div>
            </div>
            {idx < tiers.length - 1 && (
              <div style={{ display: 'flex', justifyContent: 'center', margin: '-0.3rem 0', color: 'var(--text-dim)' }}>
                <ArrowDown size={14} />
              </div>
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};
