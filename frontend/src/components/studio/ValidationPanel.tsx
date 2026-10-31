import React, { useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  GitBranch,
  Terminal,
  ShieldAlert,
} from 'lucide-react';
import { ValidationStageOutcome } from '../../types/codeStudio';

export interface ValidationPanelData {
  status: 'idle' | 'success' | 'syntax_error' | 'conflict' | 'error';
  message: string;
  stageOutcome?: ValidationStageOutcome | null;
  newVersionNumber?: number | null;
  newVersionId?: string | null;
  conflictDetails?: string | null;
  timestamp?: string | null;
}

interface ValidationPanelProps {
  data: ValidationPanelData | null;
  onReloadLatest?: () => void;
  isReloading?: boolean;
}

export const ValidationPanel: React.FC<ValidationPanelProps> = ({
  data,
  onReloadLatest,
  isReloading = false,
}) => {
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);

  if (!data || data.status === 'idle') {
    return null;
  }

  const getStatusBadge = () => {
    switch (data.status) {
      case 'success':
        return (
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '2px 8px',
              borderRadius: '4px',
              fontSize: '11px',
              fontWeight: 650,
              backgroundColor: 'rgba(16, 185, 129, 0.15)',
              color: '#10b981',
              border: '1px solid rgba(16, 185, 129, 0.3)',
            }}
          >
            <CheckCircle2 size={13} /> SAVED & VERIFIED
          </span>
        );
      case 'syntax_error':
        return (
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '2px 8px',
              borderRadius: '4px',
              fontSize: '11px',
              fontWeight: 650,
              backgroundColor: 'rgba(239, 68, 68, 0.15)',
              color: '#ef4444',
              border: '1px solid rgba(239, 68, 68, 0.3)',
            }}
          >
            <XCircle size={13} /> SYNTAX VALIDATION FAILED
          </span>
        );
      case 'conflict':
        return (
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '2px 8px',
              borderRadius: '4px',
              fontSize: '11px',
              fontWeight: 650,
              backgroundColor: 'rgba(245, 158, 11, 0.15)',
              color: '#f59e0b',
              border: '1px solid rgba(245, 158, 11, 0.3)',
            }}
          >
            <AlertTriangle size={13} /> VERSION CONFLICT
          </span>
        );
      default:
        return (
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '2px 8px',
              borderRadius: '4px',
              fontSize: '11px',
              fontWeight: 650,
              backgroundColor: 'rgba(239, 68, 68, 0.15)',
              color: '#ef4444',
              border: '1px solid rgba(239, 68, 68, 0.3)',
            }}
          >
            <ShieldAlert size={13} /> SAVE ERROR
          </span>
        );
    }
  };

  return (
    <div
      style={{
        backgroundColor: 'var(--bg-secondary, #0f1422)',
        borderTop: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Panel Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '6px 14px',
          backgroundColor: 'var(--bg-surface-subtle, #0d121f)',
          cursor: 'pointer',
          borderBottom: isCollapsed ? 'none' : '1px solid var(--border-subtle, rgba(255, 255, 255, 0.06))',
        }}
        onClick={() => setIsCollapsed((prev) => !prev)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Terminal size={14} color="var(--accent-violet-light, #a78bfa)" />
          <span style={{ fontSize: '12px', fontWeight: 650, color: 'var(--text-primary, #ffffff)' }}>
            Validation & Verification Output
          </span>
          {getStatusBadge()}
          {data.newVersionNumber && (
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '3px',
                fontSize: '11px',
                color: 'var(--accent-violet-light, #a78bfa)',
                fontWeight: 600,
              }}
            >
              <GitBranch size={12} /> Active: v{data.newVersionNumber}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {data.timestamp && (
            <span style={{ fontSize: '11px', color: 'var(--text-dim, #64748b)', fontFamily: 'monospace' }}>
              {data.timestamp}
            </span>
          )}
          <button
            type="button"
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted, #94a3b8)',
              display: 'flex',
              padding: '2px',
              cursor: 'pointer',
            }}
          >
            {isCollapsed ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
          </button>
        </div>
      </div>

      {/* Panel Body */}
      {!isCollapsed && (
        <div
          style={{
            padding: '12px 16px',
            maxHeight: '160px',
            overflowY: 'auto',
            fontSize: '12px',
            backgroundColor: '#070a12',
            color: '#e2e8f0',
            fontFamily: "'JetBrains Mono', Menlo, Consolas, monospace",
          }}
        >
          {/* Main message */}
          <div style={{ marginBottom: '8px', lineHeight: '1.45' }}>{data.message}</div>

          {/* Conflict resolution call to action */}
          {data.status === 'conflict' && (
            <div
              style={{
                backgroundColor: 'rgba(245, 158, 11, 0.1)',
                border: '1px solid rgba(245, 158, 11, 0.3)',
                padding: '8px 12px',
                borderRadius: 'var(--radius-sm, 6px)',
                marginBottom: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span style={{ color: '#fbbf24', fontSize: '12px', lineHeight: 1.4 }}>
                {data.conflictDetails ||
                  'The project active version changed since you opened this file. Your changes remain preserved in the editor.'}
              </span>
              {onReloadLatest && (
                <button
                  type="button"
                  onClick={onReloadLatest}
                  disabled={isReloading}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '4px 10px',
                    fontSize: '11px',
                    fontWeight: 650,
                    backgroundColor: 'var(--accent-amber, #f59e0b)',
                    color: '#000000',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: isReloading ? 'not-allowed' : 'pointer',
                    boxShadow: '0 2px 6px rgba(245, 158, 11, 0.3)',
                  }}
                >
                  <RotateCcw size={12} />
                  {isReloading ? 'Reloading...' : 'Reload Latest Version'}
                </button>
              )}
            </div>
          )}

          {/* Granular errors list */}
          {data.stageOutcome && data.stageOutcome.errors && data.stageOutcome.errors.length > 0 && (
            <div style={{ marginTop: '6px' }}>
              <div style={{ color: '#ef4444', fontWeight: 650, marginBottom: '4px' }}>
                Syntax Validation Errors:
              </div>
              <ul style={{ margin: 0, paddingLeft: '18px', color: '#f87171' }}>
                {data.stageOutcome.errors.map((err, i) => (
                  <li key={i} style={{ marginBottom: '2px' }}>
                    {err}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Granular warnings list */}
          {data.stageOutcome && data.stageOutcome.warnings && data.stageOutcome.warnings.length > 0 && (
            <div style={{ marginTop: '6px' }}>
              <div style={{ color: '#fbbf24', fontWeight: 650, marginBottom: '4px' }}>Warnings:</div>
              <ul style={{ margin: 0, paddingLeft: '18px', color: '#fcd34d' }}>
                {data.stageOutcome.warnings.map((warn, i) => (
                  <li key={i} style={{ marginBottom: '2px' }}>
                    {warn}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
