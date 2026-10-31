import React, { useState } from 'react';
import {
  Sparkles,
  Code2,
  ArrowRight,
  X,
  Shield,
  Terminal,
  BookOpen,
  Layers,
  Wand2,
  Cpu,
  MonitorPlay,
  RotateCcw,
  CheckCircle2,
} from 'lucide-react';
import { AppMode } from '../context/ModeContext';

export interface ModeSelectionViewProps {
  onSelectMode: (mode: AppMode, remember?: boolean) => void;
  canClose?: boolean;
  onClose?: () => void;
  currentMode?: AppMode;
}

export const ModeSelectionView: React.FC<ModeSelectionViewProps> = ({
  onSelectMode,
  canClose = false,
  onClose,
  currentMode,
}) => {
  const [rememberPreference, setRememberPreference] = useState(true);
  const [hoveredMode, setHoveredMode] = useState<AppMode | null>(null);

  const handleSelect = (mode: AppMode) => {
    onSelectMode(mode, rememberPreference);
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="mode-selection-title"
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'radial-gradient(circle at 50% 10%, rgba(13, 17, 30, 0.95) 0%, rgba(5, 7, 13, 0.98) 100%)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        padding: 'clamp(0.75rem, 3vw, 2rem) clamp(0.5rem, 2vw, 1.25rem)',
        overflowY: 'auto',
      }}
    >
      <style>{`
        .mode-dialog-card {
          padding: 2.75rem 2.5rem;
          gap: 2.25rem;
        }
        .mode-card-item {
          padding: 2.25rem;
        }
        .mode-topbar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 1.25rem;
        }
        @media (max-width: 640px) {
          .mode-dialog-card {
            padding: 1.5rem 1rem !important;
            gap: 1.5rem !important;
            border-radius: 16px !important;
          }
          .mode-card-item {
            padding: 1.25rem 1rem !important;
          }
        }
        @media (max-width: 360px) {
          .mode-dialog-card {
            padding: 1rem 0.65rem !important;
            gap: 1.25rem !important;
          }
          .mode-card-item {
            padding: 1rem 0.75rem !important;
          }
          .mode-topbar {
            flex-direction: column !important;
            align-items: flex-start !important;
            gap: 0.6rem !important;
          }
          #mode-selection-title {
            font-size: 1.45rem !important;
          }
          .mode-badge {
            font-size: 0.68rem !important;
            padding: 0.2rem 0.5rem !important;
          }
        }
      `}</style>
      <div
        className="mode-dialog-card"
        style={{
          width: '100%',
          maxWidth: '1020px',
          background: 'linear-gradient(180deg, rgba(19, 25, 45, 0.85) 0%, rgba(10, 14, 25, 0.95) 100%)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '24px',
          boxShadow: '0 30px 90px rgba(0, 0, 0, 0.75), 0 0 60px rgba(99, 102, 241, 0.12)',
          position: 'relative',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Close Button if dismissible */}
        {canClose && onClose && (
          <button
            type="button"
            onClick={onClose}
            aria-label="Close mode selection"
            style={{
              position: 'absolute',
              top: '1.5rem',
              right: '1.5rem',
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '8px',
              padding: '0.45rem',
              color: 'var(--text-secondary, #94a3b8)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.15s ease',
            }}
          >
            <X size={18} />
          </button>
        )}

        {/* Header Section */}
        <div style={{ textAlign: 'center', maxWidth: '680px', margin: '0 auto' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.35rem 0.9rem',
              borderRadius: '9999px',
              background: 'rgba(99, 102, 241, 0.12)',
              border: '1px solid rgba(99, 102, 241, 0.35)',
              fontSize: '0.78rem',
              fontWeight: 650,
              color: '#c7d2fe',
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              marginBottom: '1rem',
            }}
          >
            <Shield size={13} color="#818cf8" />
            <span>Select Your Experience</span>
          </div>

          <h1
            id="mode-selection-title"
            style={{
              fontSize: '2.25rem',
              fontWeight: 800,
              color: '#ffffff',
              letterSpacing: '-0.03em',
              lineHeight: 1.2,
              marginBottom: '0.5rem',
            }}
          >
            How would you like to work today?
          </h1>

          <div
            style={{
              fontSize: '1rem',
              fontWeight: 650,
              color: '#c7d2fe',
              marginBottom: '0.5rem',
            }}
          >
            Choose Your Engineering Experience
          </div>

          <p
            style={{
              fontSize: '0.98rem',
              color: '#94a3b8',
              lineHeight: 1.55,
              margin: 0,
            }}
          >
            SE IntelliPlatform provides two tailored workflows powered by the same underlying intelligence engine,
            authenticated projects, and live container runtime. You can switch freely at any time.
          </p>
        </div>

        {/* 3D Perspective Cards Grid */}
        <div
          style={{
            perspective: '1200px',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 420px), 1fr))',
            gap: '1.75rem',
          }}
        >
          {/* ============================================================= */}
          {/* 1. BEGINNER MODE CARD                                         */}
          {/* ============================================================= */}
          <div
            className="mode-card-item"
            onMouseEnter={() => setHoveredMode('user')}
            onMouseLeave={() => setHoveredMode(null)}
            style={{
              background:
                hoveredMode === 'user' || currentMode === 'user'
                  ? 'linear-gradient(160deg, rgba(25, 20, 50, 0.95) 0%, rgba(13, 16, 32, 0.98) 100%)'
                  : 'rgba(15, 20, 36, 0.85)',
              border:
                hoveredMode === 'user' || currentMode === 'user'
                  ? '2px solid #8b5cf6'
                  : '1px solid rgba(139, 92, 246, 0.3)',
              borderRadius: '20px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              gap: '1.75rem',
              position: 'relative',
              boxShadow:
                hoveredMode === 'user' || currentMode === 'user'
                  ? '0 20px 45px rgba(139, 92, 246, 0.22), 0 0 35px rgba(139, 92, 246, 0.15)'
                  : '0 10px 30px rgba(0, 0, 0, 0.3)',
              transform:
                hoveredMode === 'user'
                  ? 'translateY(-4px) rotateY(1deg) scale(1.01)'
                  : 'translateY(0) rotateY(0) scale(1)',
              transition: 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
            }}
          >
            <div>
              {/* Badge & Icon Header */}
              <div
                className="mode-topbar"
              >
                <div
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: '12px',
                    background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(99, 102, 241, 0.35))',
                    border: '1px solid rgba(139, 92, 246, 0.5)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 4px 14px rgba(139, 92, 246, 0.3)',
                  }}
                >
                  <Sparkles size={24} color="#c4b5fd" />
                </div>
                <span
                  className="mode-badge"
                  style={{
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.06em',
                    padding: '0.25rem 0.75rem',
                    borderRadius: '9999px',
                    background: 'rgba(139, 92, 246, 0.18)',
                    color: '#ddd6fe',
                    border: '1px solid rgba(139, 92, 246, 0.35)',
                  }}
                >
                  No-Code • Natural Language AI
                </span>
              </div>

              {/* Title & Tagline */}
              <h2
                style={{
                  fontSize: '1.65rem',
                  fontWeight: 800,
                  color: '#ffffff',
                  marginBottom: '0.35rem',
                  letterSpacing: '-0.025em',
                }}
              >
                Beginner Mode
              </h2>
              <div
                style={{
                  fontSize: '0.88rem',
                  color: '#a78bfa',
                  fontWeight: 600,
                  marginBottom: '0.75rem',
                  fontStyle: 'italic',
                }}
              >
                “Your ideas. Your AI. Your possibilities.”
              </div>
              <p
                style={{
                  fontSize: '0.9rem',
                  color: '#94a3b8',
                  lineHeight: 1.55,
                  marginBottom: '1.5rem',
                }}
              >
                A welcoming, conversational environment designed for exploring ideas, synthesizing architectures,
                and creating running applications with guided AI workflows.
              </p>

              {/* Feature Checklist */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.65rem', fontSize: '0.86rem', color: '#e2e8f0' }}>
                  <div style={{ marginTop: 2, flexShrink: 0 }}>
                    <Wand2 size={15} color="#a78bfa" />
                  </div>
                  <span>
                    <strong style={{ color: '#ffffff' }}>Conversational App Creator:</strong> Turn natural language descriptions into live full-stack applications.
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.65rem', fontSize: '0.86rem', color: '#e2e8f0' }}>
                  <div style={{ marginTop: 2, flexShrink: 0 }}>
                    <Layers size={15} color="#a78bfa" />
                  </div>
                  <span>
                    <strong style={{ color: '#ffffff' }}>Template Library:</strong> Instant starters for Kanban boards, booking hubs, stores, and games.
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.65rem', fontSize: '0.86rem', color: '#e2e8f0' }}>
                  <div style={{ marginTop: 2, flexShrink: 0 }}>
                    <MonitorPlay size={15} color="#a78bfa" />
                  </div>
                  <span>
                    <strong style={{ color: '#ffffff' }}>Instant Live Preview:</strong> Test real containerized apps directly in your browser on port 8001.
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.65rem', fontSize: '0.86rem', color: '#e2e8f0' }}>
                  <div style={{ marginTop: 2, flexShrink: 0 }}>
                    <RotateCcw size={15} color="#a78bfa" />
                  </div>
                  <span>
                    <strong style={{ color: '#ffffff' }}>Continuous Refinement:</strong> Conversational edits with AST diff reviews and safe 1-click rollback.
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.65rem', fontSize: '0.86rem', color: '#e2e8f0' }}>
                  <div style={{ marginTop: 2, flexShrink: 0 }}>
                    <BookOpen size={15} color="#a78bfa" />
                  </div>
                  <span>
                    <strong style={{ color: '#ffffff' }}>Ambient AI Tutoring:</strong> Ask questions and learn software engineering concepts step-by-step.
                  </span>
                </div>
              </div>
            </div>

            {/* Action Button */}
            <button
              id="btn-enter-user-mode"
              data-testid="enter-beginner-mode"
              type="button"
              aria-label="Enter User Mode"
              onClick={() => handleSelect('user')}
              style={{
                width: '100%',
                padding: '0.9rem 1.5rem',
                borderRadius: '12px',
                background: 'linear-gradient(135deg, #7c3aed, #6366f1)',
                border: 'none',
                color: '#ffffff',
                fontWeight: 700,
                fontSize: '0.98rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.6rem',
                boxShadow: '0 6px 20px rgba(124, 58, 237, 0.4)',
                transition: 'all 0.2s ease',
              }}
            >
              <span>Enter Beginner Mode</span>
              <ArrowRight size={17} />
            </button>
          </div>

          {/* ============================================================= */}
          {/* 2. DEVELOPER MODE CARD                                        */}
          {/* ============================================================= */}
          <div
            className="mode-card-item"
            onMouseEnter={() => setHoveredMode('developer')}
            onMouseLeave={() => setHoveredMode(null)}
            style={{
              background:
                hoveredMode === 'developer' || currentMode === 'developer'
                  ? 'linear-gradient(160deg, rgba(16, 26, 48, 0.95) 0%, rgba(10, 15, 28, 0.98) 100%)'
                  : 'rgba(15, 20, 36, 0.85)',
              border:
                hoveredMode === 'developer' || currentMode === 'developer'
                  ? '2px solid #06b6d4'
                  : '1px solid rgba(99, 102, 241, 0.3)',
              borderRadius: '20px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              gap: '1.75rem',
              position: 'relative',
              boxShadow:
                hoveredMode === 'developer' || currentMode === 'developer'
                  ? '0 20px 45px rgba(6, 182, 212, 0.22), 0 0 35px rgba(99, 102, 241, 0.15)'
                  : '0 10px 30px rgba(0, 0, 0, 0.3)',
              transform:
                hoveredMode === 'developer'
                  ? 'translateY(-4px) rotateY(-1deg) scale(1.01)'
                  : 'translateY(0) rotateY(0) scale(1)',
              transition: 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
            }}
          >
            <div>
              {/* Badge & Icon Header */}
              <div
                className="mode-topbar"
              >
                <div
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: '12px',
                    background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(6, 182, 212, 0.35))',
                    border: '1px solid rgba(6, 182, 212, 0.5)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 4px 14px rgba(6, 182, 212, 0.3)',
                  }}
                >
                  <Code2 size={24} color="#38bdf8" />
                </div>
                <span
                  style={{
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.06em',
                    padding: '0.25rem 0.75rem',
                    borderRadius: '9999px',
                    background: 'rgba(6, 182, 212, 0.18)',
                    color: '#a5f3fc',
                    border: '1px solid rgba(6, 182, 212, 0.35)',
                  }}
                >
                  Full-Stack Code Studio • SDLC
                </span>
              </div>

              {/* Title & Tagline */}
              <h2
                style={{
                  fontSize: '1.65rem',
                  fontWeight: 800,
                  color: '#ffffff',
                  marginBottom: '0.35rem',
                  letterSpacing: '-0.025em',
                }}
              >
                Developer Mode
              </h2>
              <div
                style={{
                  fontSize: '0.88rem',
                  color: '#38bdf8',
                  fontWeight: 600,
                  marginBottom: '0.75rem',
                  fontStyle: 'italic',
                }}
              >
                “Your workspace. Your code. Your control.”
              </div>
              <p
                style={{
                  fontSize: '0.9rem',
                  color: '#94a3b8',
                  lineHeight: 1.55,
                  marginBottom: '1.5rem',
                }}
              >
                A professional software engineering IDE equipped with multi-file code editing, AST intelligence,
                terminal logging, and 14 integrated developer tools.
              </p>

              {/* Feature Checklist */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.65rem', fontSize: '0.86rem', color: '#e2e8f0' }}>
                  <div style={{ marginTop: 2, flexShrink: 0 }}>
                    <Terminal size={15} color="#38bdf8" />
                  </div>
                  <span>
                    <strong style={{ color: '#ffffff' }}>Monaco Code Studio:</strong> Multi-file tree explorer, AST checking, and tabbed code editor.
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.65rem', fontSize: '0.86rem', color: '#e2e8f0' }}>
                  <div style={{ marginTop: 2, flexShrink: 0 }}>
                    <Cpu size={15} color="#38bdf8" />
                  </div>
                  <span>
                    <strong style={{ color: '#ffffff' }}>IntelliAssist AI Engineer:</strong> Project-aware coding assistant with diff proposals & safe apply.
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.65rem', fontSize: '0.86rem', color: '#e2e8f0' }}>
                  <div style={{ marginTop: 2, flexShrink: 0 }}>
                    <Layers size={15} color="#38bdf8" />
                  </div>
                  <span>
                    <strong style={{ color: '#ffffff' }}>14 SDLC Workspaces:</strong> Specs, Architecture, Testing, Workflows, Issues & Run History.
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.65rem', fontSize: '0.86rem', color: '#e2e8f0' }}>
                  <div style={{ marginTop: 2, flexShrink: 0 }}>
                    <MonitorPlay size={15} color="#38bdf8" />
                  </div>
                  <span>
                    <strong style={{ color: '#ffffff' }}>Sandboxed Previews:</strong> Live Docker runtime verification with multi-device controls.
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.65rem', fontSize: '0.86rem', color: '#e2e8f0' }}>
                  <div style={{ marginTop: 2, flexShrink: 0 }}>
                    <CheckCircle2 size={15} color="#38bdf8" />
                  </div>
                  <span>
                    <strong style={{ color: '#ffffff' }}>Immutable Versioning:</strong> Non-destructive snapshot rollbacks, branch history, and diff logs.
                  </span>
                </div>
              </div>
            </div>

            {/* Action Button */}
            <button
              id="btn-enter-developer-mode"
              data-testid="enter-developer-mode"
              type="button"
              aria-label="Enter Developer Mode"
              onClick={() => handleSelect('developer')}
              style={{
                width: '100%',
                padding: '0.9rem 1.5rem',
                borderRadius: '12px',
                background: 'linear-gradient(135deg, #4f46e5, #0284c7)',
                border: 'none',
                color: '#ffffff',
                fontWeight: 700,
                fontSize: '0.98rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.6rem',
                boxShadow: '0 6px 20px rgba(79, 70, 229, 0.4)',
                transition: 'all 0.2s ease',
              }}
            >
              <span>Enter Developer Mode</span>
              <ArrowRight size={17} />
            </button>
          </div>
        </div>

        {/* Remember Preference Checkbox Section */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem',
            paddingTop: '0.5rem',
            borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          }}
        >
          <label
            htmlFor="checkbox-remember-mode"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.65rem',
              cursor: 'pointer',
              color: '#e2e8f0',
              fontSize: '0.88rem',
              fontWeight: 500,
              userSelect: 'none',
            }}
          >
            <input
              id="checkbox-remember-mode"
              type="checkbox"
              checked={rememberPreference}
              onChange={(e) => setRememberPreference(e.target.checked)}
              style={{
                width: 17,
                height: 17,
                accentColor: '#8b5cf6',
                cursor: 'pointer',
                borderRadius: 4,
              }}
            />
            <span>Remember my mode preference on this device</span>
          </label>
          <span style={{ fontSize: '0.78rem', color: '#64748b', textAlign: 'center' }}>
            You can always switch between Beginner Mode and Developer Mode anytime using the switcher in the top bar.
          </span>
        </div>
      </div>
    </div>
  );
};
