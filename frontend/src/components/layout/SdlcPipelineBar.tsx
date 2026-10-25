import React from 'react';
import { ArrowRight, CheckCircle2, CircleDashed } from 'lucide-react';

export type SdlcStageId =
  | 'describe'
  | 'analyze'
  | 'design'
  | 'build'
  | 'run'
  | 'test'
  | 'debug'
  | 'improve';

interface SdlcPipelineBarProps {
  currentStage?: SdlcStageId;
  onSelectStage?: (stage: SdlcStageId) => void;
}

interface StageConfig {
  id: SdlcStageId;
  label: string;
  implemented: boolean;
  navTab: string;
}

const STAGES: StageConfig[] = [
  { id: 'describe', label: 'DESCRIBE', implemented: true, navTab: 'specification' },
  { id: 'analyze', label: 'ANALYZE', implemented: true, navTab: 'intelligence' },
  { id: 'design', label: 'DESIGN', implemented: true, navTab: 'workflows' },
  { id: 'build', label: 'BUILD', implemented: true, navTab: 'development' },
  { id: 'run', label: 'RUN', implemented: true, navTab: 'development' },
  { id: 'test', label: 'TEST', implemented: true, navTab: 'testing' },
  { id: 'debug', label: 'DEBUG', implemented: true, navTab: 'issues' },
  { id: 'improve', label: 'IMPROVE', implemented: true, navTab: 'intelligence' },
];

export const SdlcPipelineBar: React.FC<SdlcPipelineBarProps> = ({ currentStage, onSelectStage }) => {
  return (
    <div
      className="sdlc-pipeline-bar"
      role="navigation"
      aria-label="Software Development Lifecycle Stages"
      style={{
        display: 'flex',
        alignItems: 'center',
        background: 'var(--bg-surface-subtle)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        padding: '0.45rem 0.75rem',
        overflowX: 'auto',
      }}
    >
      <span
        style={{
          fontSize: '0.7rem',
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
          color: 'var(--text-muted)',
          marginRight: '0.5rem',
          whiteSpace: 'nowrap',
        }}
      >
        SDLC Pipeline:
      </span>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
        {STAGES.map((stage, idx) => {
          const isActive = currentStage === stage.id;
          return (
            <React.Fragment key={stage.id}>
              <button
                type="button"
                onClick={() => onSelectStage && onSelectStage(stage.id)}
                className={`sdlc-step-pill ${isActive ? 'active' : ''}`}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  padding: '0.25rem 0.55rem',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  letterSpacing: '0.03em',
                  cursor: onSelectStage ? 'pointer' : 'default',
                  border: isActive ? '1px solid var(--accent-primary)' : '1px solid transparent',
                  background: isActive ? 'var(--bg-surface-active)' : 'transparent',
                  color: isActive
                    ? 'var(--text-primary)'
                    : stage.implemented
                    ? 'var(--text-secondary)'
                    : 'var(--text-muted)',
                }}
                title={
                  stage.implemented
                    ? `${stage.label} — Live multi-agent capabilities available`
                    : `${stage.label} — Planned SDLC capability`
                }
              >
                {stage.implemented ? (
                  <CheckCircle2 size={12} color="var(--status-completed)" />
                ) : (
                  <CircleDashed size={12} color="var(--text-dim)" />
                )}
                <span>{stage.label}</span>
                {!stage.implemented && (
                  <span
                    style={{
                      fontSize: '0.62rem',
                      padding: '0.05rem 0.3rem',
                      borderRadius: '3px',
                      background: 'rgba(255, 255, 255, 0.05)',
                      color: 'var(--text-dim)',
                    }}
                  >
                    PLAN
                  </span>
                )}
              </button>
              {idx < STAGES.length - 1 && (
                <ArrowRight size={11} className="sdlc-step-separator" style={{ opacity: 0.4 }} />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
