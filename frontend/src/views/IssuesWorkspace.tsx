import React from 'react';
import { Card, CardBody, CardHeader } from '../components/common/Card';
import { CapabilityBadge } from '../components/common/CapabilityBadge';
import { EmptyState } from '../components/common/EmptyState';
import {
  Bug,
  Search,
  FileCheck,
  CheckCircle2,
  Wrench,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';
export const IssuesWorkspace: React.FC = () => {
  const pipelineSteps = [
    { name: 'Issue Reported', icon: <Bug size={14} />, desc: 'Defect filed via UI or automated test' },
    { name: 'Evidence Collection', icon: <Search size={14} />, desc: 'Logs, stack traces, and failure preconditions' },
    { name: 'Root Cause Analysis', icon: <FileCheck size={14} />, desc: 'AI fault localization & rationale analysis' },
    { name: 'Proposed Fix', icon: <Wrench size={14} />, desc: 'Minimal patch diff generated against source' },
    { name: 'Human Approval', icon: <CheckCircle2 size={14} />, desc: 'Developer reviews and confirms patch diff' },
    { name: 'Regression Test', icon: <ShieldCheck size={14} />, desc: 'Verifies no behavioral regressions introduced' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xl)' }}>
      {/* Workspace Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700 }}>Issues & Debugging Workspace</h1>
            <CapabilityBadge status="IMPLEMENTED" size="md" />
          </div>
          <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Closed-loop issue tracking, evidence collection, and AI-assisted defect remediation with human-in-the-loop approval.
          </p>
        </div>
      </div>

      {/* Conceptual Pipeline Visualization */}
      <Card style={{ background: 'var(--bg-glass-card)' }}>
        <CardHeader>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Bug size={17} color="var(--status-failed)" />
            <span style={{ fontWeight: 600 }}>Closed-Loop Defect Remediation Lifecycle</span>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--status-completed)' }}>
            Active Debug & Remediation Architecture
          </span>
        </CardHeader>
        <CardBody>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              overflowX: 'auto',
              padding: 'var(--space-sm) 0',
            }}
          >
            {pipelineSteps.map((step, idx) => (
              <React.Fragment key={step.name}>
                <div
                  style={{
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '0.65rem 0.85rem',
                    minWidth: '150px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.25rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--accent-cyan)', fontWeight: 600, fontSize: '0.78rem' }}>
                    {step.icon}
                    <span>{step.name}</span>
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', lineHeight: 1.3 }}>
                    {step.desc}
                  </div>
                </div>
                {idx < pipelineSteps.length - 1 && (
                  <ArrowRight size={14} color="var(--text-dim)" style={{ flexShrink: 0 }} />
                )}
              </React.Fragment>
            ))}
          </div>
        </CardBody>
      </Card>

      {/* Empty State */}
      <EmptyState
        icon={<Bug size={36} />}
        title="No issues have been reported."
        description="Issue tracking, evidence collection, AI-assisted debugging, and human-approved code fixes will appear here when defects are detected."
      />

      {/* Architecture Disclaimer */}
      <div
        style={{
          padding: 'var(--space-md)',
          borderRadius: 'var(--radius-md)',
          background: 'rgba(16, 185, 129, 0.08)',
          border: '1px solid rgba(16, 185, 129, 0.25)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          fontSize: '0.8rem',
          color: 'var(--text-secondary)',
        }}
      >
        <ShieldCheck size={20} color="var(--status-completed)" style={{ flexShrink: 0 }} />
        <div>
          Automated failure analysis, root-cause localization, and remediation patch synthesis are active with deterministic verification and mandatory human approval gates.
        </div>
      </div>
    </div>
  );
};
