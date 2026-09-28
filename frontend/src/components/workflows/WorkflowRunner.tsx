import React, { useState } from 'react';
import { Play, Settings2 } from 'lucide-react';
import {
  WorkflowExecuteRequest,
  WorkflowMetadataResponse,
} from '../../types/workflow';
import { ContextSnapshotResponse } from '../../types/context';
import { Card, CardBody, CardHeader, CardTitle } from '../common/Card';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';

interface WorkflowRunnerProps {
  workflow: WorkflowMetadataResponse;
  projectId: string;
  snapshots: ContextSnapshotResponse[];
  onExecute: (request: WorkflowExecuteRequest) => Promise<void>;
  isExecuting: boolean;
}

export const WorkflowRunner: React.FC<WorkflowRunnerProps> = ({
  workflow,
  projectId,
  snapshots,
  onExecute,
  isExecuting,
}) => {
  const [selectedSnapshotVersion, setSelectedSnapshotVersion] = useState<string>('current');
  const [failFast, setFailFast] = useState<boolean>(true);
  const [explainabilityQuery, setExplainabilityQuery] = useState<string>('');
  const [explainabilityScope, setExplainabilityScope] = useState<string>('');

  const hasCodeReview = workflow.steps.some((s) => s.agent_id === 'code-review');
  const hasExplainability = workflow.steps.some((s) => s.agent_id === 'explainability-insights');

  const [sampleCode, setSampleCode] = useState<string>(
    'def calculate_tax(amount: float) -> float:\n    # In-memory evaluation\n    return amount * 0.15\n'
  );

  const handleRun = () => {
    const request: WorkflowExecuteRequest = {
      project_id: projectId,
      options: {
        fail_fast: failFast,
      },
    };

    if (selectedSnapshotVersion !== 'current') {
      request.snapshot_version = parseInt(selectedSnapshotVersion, 10);
    }

    if (hasExplainability) {
      if (explainabilityQuery.trim()) {
        request.explainability_user_query = explainabilityQuery.trim();
      }
      if (explainabilityScope.trim()) {
        request.explainability_target_scope = explainabilityScope.trim();
      }
    }

    if (hasCodeReview && sampleCode.trim()) {
      request.code_review_input = {
        files: [
          {
            file_path: 'main.py',
            language: 'python',
            content: sampleCode,
          },
        ],
        review_scope: 'Automated workflow audit',
      };
    }

    onExecute(request);
  };

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>
            <Settings2 size={18} color="var(--accent-primary)" />
            Configure & Run: {workflow.name}
          </CardTitle>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
            ID: {workflow.workflow_id} | Version: {workflow.version} | Steps: {workflow.step_count}
          </div>
        </div>
        <Button
          variant="primary"
          icon={<Play size={16} />}
          onClick={handleRun}
          isLoading={isExecuting}
          disabled={isExecuting}
        >
          {isExecuting ? 'Executing Workflow...' : 'Execute Workflow'}
        </Button>
      </CardHeader>

      <CardBody>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Pipeline Steps View */}
          <div>
            <div style={{ fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
              Pipeline Execution Sequence:
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center' }}>
              {workflow.steps.map((st, sIdx) => (
                <React.Fragment key={st.step_id}>
                  <div
                    style={{
                      background: 'var(--bg-surface)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '0.4rem 0.75rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.4rem',
                      fontSize: '0.8rem',
                    }}
                  >
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{st.step_id}</span>
                    <Badge variant={st.required ? 'critical' : 'draft'}>
                      {st.required ? 'REQUIRED' : 'OPTIONAL'}
                    </Badge>
                  </div>
                  {sIdx < workflow.steps.length - 1 && (
                    <span style={{ color: 'var(--text-dim)' }}>→</span>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* Form Parameters */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="wf-snapshot">
                Context Baseline
              </label>
              <select
                id="wf-snapshot"
                className="form-select"
                value={selectedSnapshotVersion}
                onChange={(e) => setSelectedSnapshotVersion(e.target.value)}
                disabled={isExecuting}
              >
                <option value="current">Current Canonical Context (Latest)</option>
                {snapshots.map((s) => (
                  <option key={s.id} value={s.version}>
                    Snapshot v{s.version} ({s.summary || 'Freeze'})
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="wf-fail-fast">
                Error Directive (fail_fast)
              </label>
              <select
                id="wf-fail-fast"
                className="form-select"
                value={failFast ? 'true' : 'false'}
                onChange={(e) => setFailFast(e.target.value === 'true')}
                disabled={isExecuting}
              >
                <option value="true">True (Stop pipeline immediately on step failure)</option>
                <option value="false">False (Continue remaining independent steps)</option>
              </select>
            </div>
          </div>

          {/* Optional Explainability Inputs */}
          {hasExplainability && (
            <div
              style={{
                background: 'var(--bg-surface)',
                padding: '1rem',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                Explainability Parameters
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label className="form-label">Developer Query (Optional)</label>
                  <input
                    type="text"
                    className="form-input"
                    value={explainabilityQuery}
                    onChange={(e) => setExplainabilityQuery(e.target.value)}
                    placeholder="e.g. Why is the risk band evaluated as MEDIUM?"
                    disabled={isExecuting}
                  />
                </div>
                <div>
                  <label className="form-label">Target Scope (Optional)</label>
                  <input
                    type="text"
                    className="form-input"
                    value={explainabilityScope}
                    onChange={(e) => setExplainabilityScope(e.target.value)}
                    placeholder="e.g. Database layer and risk mitigation"
                    disabled={isExecuting}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Optional Code Review Input */}
          {hasCodeReview && (
            <div
              style={{
                background: 'var(--bg-surface)',
                padding: '1rem',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                Source Code Payload for CodeReviewAgent
              </div>
              <textarea
                className="form-textarea"
                style={{ fontFamily: 'monospace', fontSize: '0.825rem', minHeight: '100px' }}
                value={sampleCode}
                onChange={(e) => setSampleCode(e.target.value)}
                disabled={isExecuting}
                placeholder="Python source code to review..."
              />
            </div>
          )}

          {isExecuting && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.85rem 1rem',
                background: 'rgba(56, 189, 248, 0.12)',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                borderRadius: 'var(--radius-sm)',
                color: '#38bdf8',
                fontSize: '0.85rem',
              }}
            >
              <div className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} />
              <div>
                Executing multi-agent pipeline synchronously. Waiting for backend agent coordination response...
              </div>
            </div>
          )}
        </div>
      </CardBody>
    </Card>
  );
};
