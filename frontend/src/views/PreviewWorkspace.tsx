import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useProject } from '../context/ProjectContext';
import { Button } from '../components/common/Button';
import {
  ExternalLink,
  RotateCw,
  RefreshCw,
  Monitor,
  Tablet,
  Smartphone,
  Bot,
  Sparkles,
  Code2,
  Settings,
  CheckCircle2,
  AlertTriangle,
  Info,
  ChevronDown,
  ChevronUp,
  Layers,
} from 'lucide-react';
import { NavigationTab } from '../components/layout/Sidebar';
import { previewRuntimeApi } from '../services/previewRuntimeApi';
import { workflowsApi } from '../services/workflowsApi';
import { RuntimeLifecycleStatus } from '../types/previewRuntime';

interface PreviewWorkspaceProps {
  onNavigate?: (tab: NavigationTab) => void;
  onOpenAssistant?: () => void;
  onSendAssistantPrompt?: (prompt: string) => void;
  onOpenCreateProject?: () => void;
}

export const PreviewWorkspace: React.FC<PreviewWorkspaceProps> = ({
  onNavigate,
  onOpenAssistant,
  onSendAssistantPrompt,
  onOpenCreateProject,
}) => {
  const { selectedProject } = useProject();
  const [deviceViewport, setDeviceViewport] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');
  const [refreshKey, setRefreshKey] = useState<number>(Date.now());
  const [isReloading, setIsReloading] = useState<boolean>(false);

  // Active request tracking to avoid stale async state after project switching
  const activeRequestIdRef = useRef<number>(0);

  // Authoritative runtime lifecycle state
  const [runtimeStatus, setRuntimeStatus] = useState<RuntimeLifecycleStatus>('HEALTH_CHECKING');
  const [runtimePort, setRuntimePort] = useState<number>(8001);
  const [activeMode, setActiveMode] = useState<string>('taskflow');
  const [previewUrl, setPreviewUrl] = useState<string>('http://127.0.0.1:8001/');
  const [runtimeDetail, setRuntimeDetail] = useState<string>('');
  const [isChecking, setIsChecking] = useState<boolean>(false);
  const [isRestarting, setIsRestarting] = useState<boolean>(false);
  const [showDetails, setShowDetails] = useState<boolean>(false);

  // AI Code generation state
  const [isGeneratingCode, setIsGeneratingCode] = useState<boolean>(false);
  const [codeGenMessage, setCodeGenMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleGenerateCode = async () => {
    if (!selectedProject?.id || isGeneratingCode) return;
    setIsGeneratingCode(true);
    setCodeGenMessage(null);
    try {
      const res = await workflowsApi.execute('code-generation-workflow', {
        project_id: selectedProject.id,
      });
      if (res.status === 'COMPLETED' || res.status === 'PARTIAL_SUCCESS') {
        setCodeGenMessage({
          type: 'success',
          text: 'AI Code Generation completed successfully! Multi-file code scaffold is now registered in Code Studio.',
        });
      } else {
        const errorDetail =
          res.errors && res.errors.length > 0
            ? res.errors.join('; ')
            : 'Workflow did not produce completed artifacts.';
        setCodeGenMessage({
          type: 'error',
          text: `Workflow finished with status ${res.status}: ${errorDetail}`,
        });
      }
    } catch (err: any) {
      setCodeGenMessage({
        type: 'error',
        text: err?.response?.data?.detail || err?.message || 'Failed to execute code generation workflow.',
      });
    } finally {
      setIsGeneratingCode(false);
    }
  };


  const checkHealthAndSync = useCallback(
    async (autoStart = true) => {
      if (!selectedProject?.id) {
        setRuntimeStatus('IDLE');
        setIsChecking(false);
        return;
      }

      const reqId = ++activeRequestIdRef.current;
      setIsChecking(true);
      setRuntimeStatus('HEALTH_CHECKING');

      try {
        const res = await previewRuntimeApi.getStatus(selectedProject.id);
        if (activeRequestIdRef.current !== reqId) return;

        const previewToken = res.preview_token;
        const resolvedUrl = previewRuntimeApi.resolvePreviewUrl(
          selectedProject.id,
          res.preview_url,
          res.active_mode,
          previewToken
        );
        setActiveMode(res.active_mode || 'custom');

        if (res.is_healthy && (res.status === 'RUNNING' || res.status === 'READY')) {
          setRuntimeStatus('RUNNING');
          setRuntimePort(res.port || 8001);
          setPreviewUrl(resolvedUrl);
          setRuntimeDetail(res.detail || 'Application running.');
        } else if (autoStart) {
          // Attempt automatic start if runtime is not running
          setRuntimeStatus('STARTING');
          const startRes = await previewRuntimeApi.start(selectedProject.id);
          if (activeRequestIdRef.current !== reqId) return;

          const startPreviewToken = startRes.preview_token || res.preview_token;
          const startResolvedUrl = previewRuntimeApi.resolvePreviewUrl(
            selectedProject.id,
            startRes.preview_url,
            startRes.active_mode,
            startPreviewToken
          );
          setActiveMode(startRes.active_mode || res.active_mode || 'custom');

          if (startRes.is_healthy && (startRes.status === 'RUNNING' || startRes.status === 'READY')) {
            setRuntimeStatus('RUNNING');
            setRuntimePort(startRes.port || 8001);
            setPreviewUrl(startResolvedUrl);
            setRuntimeDetail(startRes.detail || 'Application running.');
          } else {
            setRuntimeStatus(startRes.status === 'FAILED' ? 'FAILED' : 'UNAVAILABLE');
            setRuntimeDetail(startRes.detail || 'Application runtime is unavailable.');
          }
        } else {
          setRuntimeStatus('UNAVAILABLE');
          setRuntimeDetail(res.detail || 'Application runtime is unavailable.');
        }
      } catch (err: any) {
        if (activeRequestIdRef.current !== reqId) return;
        setRuntimeStatus('UNAVAILABLE');
        setRuntimeDetail(err?.message || 'Failed to reach runtime management API.');
      } finally {
        if (activeRequestIdRef.current === reqId) {
          setIsChecking(false);
        }
      }
    },
    [selectedProject?.id]
  );

  useEffect(() => {
    if (selectedProject?.id) {
      checkHealthAndSync(true);
    }
  }, [selectedProject?.id, checkHealthAndSync]);

  const handleRefresh = useCallback(async () => {
    setIsReloading(true);
    if (selectedProject?.id) {
      try {
        const res = await previewRuntimeApi.getStatus(selectedProject.id);
        const previewToken = res.preview_token;
        const resolvedUrl = previewRuntimeApi.resolvePreviewUrl(
          selectedProject.id,
          res.preview_url,
          res.active_mode,
          previewToken
        );
        setActiveMode(res.active_mode || 'custom');
        if (res.is_healthy && res.status === 'RUNNING') {
          setRuntimeStatus('RUNNING');
          setPreviewUrl(resolvedUrl);
          setRefreshKey(Date.now());
        } else {
          setRuntimeStatus('UNAVAILABLE');
          setRuntimeDetail(res.detail);
        }
      } catch (err: any) {
        setRuntimeStatus('UNAVAILABLE');
        setRuntimeDetail(err?.message || 'Runtime health check failed.');
      }
    } else {
      setRefreshKey(Date.now());
    }
    setTimeout(() => setIsReloading(false), 400);
  }, [selectedProject?.id]);

  useEffect(() => {
    const handleRemoteRefresh = () => {
      handleRefresh();
    };
    window.addEventListener('se-preview-refresh', handleRemoteRefresh);
    return () => {
      window.removeEventListener('se-preview-refresh', handleRemoteRefresh);
    };
  }, [handleRefresh]);

  const handleRestart = async () => {
    if (!selectedProject?.id || isRestarting) return;
    setIsRestarting(true);
    setRuntimeStatus('STARTING');
    try {
      const res = await previewRuntimeApi.restart(selectedProject.id);
      const previewToken = res.preview_token;
      const resolvedUrl = previewRuntimeApi.resolvePreviewUrl(
        selectedProject.id,
        res.preview_url,
        res.active_mode,
        previewToken
      );
      setActiveMode(res.active_mode || 'custom');
      if (res.is_healthy && res.status === 'RUNNING') {
        setRuntimeStatus('RUNNING');
        setRuntimePort(res.port || 8001);
        setPreviewUrl(resolvedUrl);
        setRuntimeDetail(res.detail || 'Application restarted successfully.');
        setRefreshKey(Date.now());
      } else {
        setRuntimeStatus('FAILED');
        setRuntimeDetail(res.detail || 'Failed to restart application runtime.');
      }
    } catch (err: any) {
      setRuntimeStatus('FAILED');
      setRuntimeDetail(err?.message || 'Error occurred while restarting application runtime.');
    } finally {
      setIsRestarting(false);
    }
  };


  const viewportWidth =
    deviceViewport === 'mobile' ? '375px' : deviceViewport === 'tablet' ? '768px' : '100%';

  const promptSuggestions = [
    'make homepage better',
    "The registration button doesn't work",
    'Add event category filter',
    'What would be affected if I changed the Event model?',
  ];

  // EMPTY STATE: No application / project selected
  if (!selectedProject) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: 'calc(100vh - 65px)',
          background: 'var(--bg-primary)',
          padding: '2rem',
          textAlign: 'center',
        }}
      >
        <div
          style={{
            maxWidth: 480,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '1rem',
          }}
        >
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: '50%',
              background: 'rgba(99, 102, 241, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--accent-primary)',
            }}
          >
            <Sparkles size={28} />
          </div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, margin: 0, color: '#fff' }}>
            No application yet.
          </h2>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
            Describe what you want to build to generate a working application, interactive APIs, and live preview.
          </p>
          <Button
            variant="primary"
            onClick={() => (onOpenCreateProject ? onOpenCreateProject() : onNavigate?.('overview'))}
            style={{
              background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-cyan))',
              fontWeight: 700,
              padding: '0.65rem 1.4rem',
              marginTop: '0.5rem',
            }}
          >
            <Sparkles size={16} style={{ marginRight: '0.4rem' }} />
            Create Application
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100vh - 65px)',
        overflow: 'hidden',
        background: 'var(--bg-primary)',
      }}
    >
      {/* 1. Top Control Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0.65rem 1.25rem',
          background: 'var(--bg-secondary)',
          borderBottom: '1px solid var(--border-subtle)',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: runtimeStatus === 'RUNNING' ? '#10b981' : runtimeStatus === 'HEALTH_CHECKING' || runtimeStatus === 'STARTING' ? '#f59e0b' : '#ef4444',
                boxShadow: runtimeStatus === 'RUNNING' ? '0 0 8px #10b981' : 'none',
              }}
            />
            <span style={{ fontWeight: 700, fontSize: '0.92rem', color: '#fff' }}>
              {selectedProject?.name || 'Live Application'}
            </span>
          </div>

          {/* Authoritative Runtime Status Badge */}
          {runtimeStatus === 'RUNNING' ? (
            <span
              id="runtime-status-badge"
              style={{
                padding: '0.15rem 0.6rem',
                borderRadius: '9999px',
                fontSize: '0.72rem',
                fontWeight: 600,
                background: 'rgba(16, 185, 129, 0.15)',
                color: '#34d399',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.35rem',
              }}
            >
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#34d399' }} />
              ● Application running
            </span>
          ) : runtimeStatus === 'STARTING' || runtimeStatus === 'HEALTH_CHECKING' ? (
            <span
              id="runtime-status-badge"
              style={{
                padding: '0.15rem 0.6rem',
                borderRadius: '9999px',
                fontSize: '0.72rem',
                fontWeight: 600,
                background: 'rgba(245, 158, 11, 0.15)',
                color: '#fbbf24',
                border: '1px solid rgba(245, 158, 11, 0.3)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.35rem',
              }}
            >
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#fbbf24' }} />
              ○ Starting application...
            </span>
          ) : (
            <span
              id="runtime-status-badge"
              style={{
                padding: '0.15rem 0.6rem',
                borderRadius: '9999px',
                fontSize: '0.72rem',
                fontWeight: 600,
                background: 'rgba(239, 68, 68, 0.15)',
                color: '#f87171',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.35rem',
              }}
            >
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#f87171' }} />
              ○ Application unavailable
            </span>
          )}

          {/* Mode Badge */}
          <span
            id="preview-mode-badge"
            style={{
              padding: '0.15rem 0.55rem',
              borderRadius: '4px',
              fontSize: '0.72rem',
              fontWeight: 600,
              background: activeMode === 'snake_game' ? 'rgba(56, 189, 248, 0.15)' : 'rgba(99, 102, 241, 0.15)',
              color: activeMode === 'snake_game' ? '#38bdf8' : '#a5b4fc',
              border: `1px solid ${activeMode === 'snake_game' ? 'rgba(56, 189, 248, 0.3)' : 'rgba(99, 102, 241, 0.3)'}`,
            }}
          >
            {activeMode === 'snake_game'
              ? '🎮 Snake Game'
              : activeMode === 'eventhub'
              ? '🎪 EventHub'
              : activeMode === 'ecommerce'
              ? '🛍️ ShopSphere'
              : activeMode === 'management'
              ? '📊 Management System'
              : activeMode === 'taskflow'
              ? '📋 TaskFlow'
              : '🚀 Custom Prototype'}
          </span>

          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            {runtimePort === 443 ? 'HTTPS' : `Port ${runtimePort}`}
          </span>

        </div>

        {/* Device Switcher */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            background: 'var(--bg-surface-subtle)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            padding: '2px',
          }}
        >
          <button
            type="button"
            title="Desktop View"
            onClick={() => setDeviceViewport('desktop')}
            style={{
              background: deviceViewport === 'desktop' ? 'var(--accent-primary)' : 'transparent',
              color: deviceViewport === 'desktop' ? '#fff' : 'var(--text-muted)',
              border: 'none',
              borderRadius: 'var(--radius-sm)',
              padding: '0.35rem 0.6rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <Monitor size={15} />
          </button>
          <button
            type="button"
            title="Tablet View"
            onClick={() => setDeviceViewport('tablet')}
            style={{
              background: deviceViewport === 'tablet' ? 'var(--accent-primary)' : 'transparent',
              color: deviceViewport === 'tablet' ? '#fff' : 'var(--text-muted)',
              border: 'none',
              borderRadius: 'var(--radius-sm)',
              padding: '0.35rem 0.6rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <Tablet size={15} />
          </button>
          <button
            type="button"
            title="Mobile View"
            onClick={() => setDeviceViewport('mobile')}
            style={{
              background: deviceViewport === 'mobile' ? 'var(--accent-primary)' : 'transparent',
              color: deviceViewport === 'mobile' ? '#fff' : 'var(--text-muted)',
              border: 'none',
              borderRadius: 'var(--radius-sm)',
              padding: '0.35rem 0.6rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <Smartphone size={15} />
          </button>
        </div>

        {/* Right Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {onNavigate && (
            <Button
              variant="secondary"
              size="sm"
              icon={<Code2 size={13} />}
              onClick={() => onNavigate('development')}
              title="Open Development Workspace to synthesize or inspect full production code"
              style={{ fontSize: '0.78rem' }}
            >
              Generate Code
            </Button>
          )}

          <Button
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
            disabled={isReloading}
            style={{ fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
          >
            <RotateCw size={13} className={isReloading ? 'animate-spin' : ''} />
            <span>Reload</span>
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={handleRestart}
            disabled={isRestarting}
            title="Restart runtime process on Port 8001"
            style={{ fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
          >
            <RefreshCw size={13} className={isRestarting ? 'animate-spin' : ''} />
            <span>Restart</span>
          </Button>

          <a
            id="open-edge-tab-link"
            href={previewUrl}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.3rem',
              padding: '0.35rem 0.75rem',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.78rem',
              fontWeight: 600,
              color: 'var(--accent-cyan)',
              background: 'rgba(6, 182, 212, 0.1)',
              border: '1px solid rgba(6, 182, 212, 0.25)',
              textDecoration: 'none',
            }}
          >
            <span>Open in Edge Tab</span>
            <ExternalLink size={12} />
          </a>

          {onOpenAssistant && (
            <Button
              variant="primary"
              size="sm"
              onClick={onOpenAssistant}
              style={{
                fontSize: '0.78rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
                background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-cyan))',
              }}
            >
              <Bot size={14} />
              <span>Intelli Assistant</span>
            </Button>
          )}
        </div>
      </div>

      {/* 2. Embedded Application Preview Canvas */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'flex-start',
          padding: deviceViewport === 'desktop' ? '0.75rem' : '1.5rem',
          background: 'var(--bg-primary)',
          overflow: 'hidden',
        }}
      >
        {/* Informative Prototype & Code Responsibilities Banner */}
        <div
          style={{
            width: viewportWidth,
            display: 'flex',
            flexDirection: 'column',
            gap: '0.45rem',
            padding: '0.5rem 0.85rem',
            marginBottom: '0.5rem',
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
            flexShrink: 0,
            transition: 'width 0.3s ease',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Sparkles size={13} style={{ color: 'var(--accent-primary)', flexShrink: 0 }} />
              <span>
                <strong>Live Interactive Prototype:</strong> Testing UI, controls, and workflows (built-in interactive template). To synthesize multi-file backend & frontend source code, click Generate AI Code.
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Button
                id="btn-preview-generate-code"
                variant="primary"
                size="sm"
                onClick={handleGenerateCode}
                isLoading={isGeneratingCode}
                style={{
                  background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-cyan))',
                  fontWeight: 600,
                  fontSize: '0.75rem',
                  padding: '0.25rem 0.75rem',
                }}
              >
                <Sparkles size={13} style={{ marginRight: '0.3rem' }} />
                Generate AI Code
              </Button>
              {onNavigate && (
                <button
                  type="button"
                  onClick={() => onNavigate('development')}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--accent-cyan)',
                    fontWeight: 600,
                    cursor: 'pointer',
                    fontSize: '0.75rem',
                    textDecoration: 'underline',
                    whiteSpace: 'nowrap',
                  }}
                >
                  Open Code Studio →
                </button>
              )}
            </div>
          </div>
          {codeGenMessage && (
            <div
              id="preview-codegen-message"
              style={{
                padding: '0.35rem 0.65rem',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.73rem',
                background: codeGenMessage.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                color: codeGenMessage.type === 'success' ? '#34d399' : '#f87171',
                border: `1px solid ${codeGenMessage.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
              }}
            >
              {codeGenMessage.text}
            </div>
          )}
        </div>


        <div
          style={{
            width: viewportWidth,
            height: 'calc(100% - 35px)',
            maxWidth: '100%',
            display: 'flex',
            flexDirection: 'column',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border-subtle)',
            boxShadow: '0 12px 35px rgba(0, 0, 0, 0.6)',
            overflow: 'hidden',
            background: '#0b1120',
            transition: 'width 0.3s ease',
          }}
        >
          {/* Browser Mockup Chrome */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              padding: '0.5rem 1rem',
              background: 'var(--bg-secondary)',
              borderBottom: '1px solid var(--border-subtle)',
              fontSize: '0.75rem',
              flexShrink: 0,
            }}
          >
            <div style={{ display: 'flex', gap: '0.35rem' }}>
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#ef4444' }} />
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#f59e0b' }} />
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#10b981' }} />
            </div>

            <div
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.25rem 0.75rem',
                color: 'var(--text-muted)',
                fontSize: '0.75rem',
                fontFamily: 'monospace',
              }}
            >
              <span>{previewUrl}</span>
            </div>

            {runtimeStatus === 'RUNNING' ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#10b981' }}>
                <CheckCircle2 size={13} />
                <span style={{ fontSize: '0.7rem', fontWeight: 600 }}>Active</span>
              </div>
            ) : runtimeStatus === 'STARTING' || runtimeStatus === 'HEALTH_CHECKING' ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#f59e0b' }}>
                <RotateCw size={13} className="animate-spin" />
                <span style={{ fontSize: '0.7rem', fontWeight: 600 }}>Connecting</span>
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#ef4444' }}>
                <AlertTriangle size={13} />
                <span style={{ fontSize: '0.7rem', fontWeight: 600 }}>Offline</span>
              </div>
            )}
          </div>

          {/* Interactive Preview Canvas or Controlled Error UX */}
          {runtimeStatus === 'RUNNING' ? (
            <iframe
              key={refreshKey}
              id="live-app-iframe"
              src={previewUrl}
              title="Generated Application Live Preview"
              style={{
                flex: 1,
                width: '100%',
                height: '100%',
                border: 'none',
                background: '#0a0f1d',
              }}
            />
          ) : runtimeStatus === 'STARTING' || runtimeStatus === 'HEALTH_CHECKING' ? (
            <div
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '2.5rem',
                textAlign: 'center',
                background: '#090d16',
              }}
            >
              <RotateCw size={36} className="animate-spin" style={{ color: 'var(--accent-primary)', marginBottom: '1.25rem' }} />
              <h3 style={{ fontSize: '1.15rem', fontWeight: 600, margin: '0 0 0.5rem 0', color: '#fff' }}>
                Starting Application Runtime
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', maxWidth: 420, margin: 0, lineHeight: 1.5 }}>
                Probing runtime health on port {runtimePort}... The preview will display as soon as the live server responds.
              </p>
            </div>
          ) : (
            <div
              id="preview-error-card"
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '2.5rem',
                textAlign: 'center',
                background: '#090d16',
              }}
            >
              <div
                style={{
                  width: 52,
                  height: 52,
                  borderRadius: '50%',
                  background: 'rgba(239, 68, 68, 0.12)',
                  border: '1px solid rgba(239, 68, 68, 0.25)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#f87171',
                  marginBottom: '1rem',
                }}
              >
                <AlertTriangle size={26} />
              </div>

              <h3 style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0 0 0.5rem 0', color: '#fff' }}>
                Application unavailable
              </h3>

              <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', maxWidth: 460, margin: '0 0 1.5rem 0', lineHeight: 1.5 }}>
                The application started but is not responding yet.
              </p>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap', justifyContent: 'center' }}>
                <Button
                  id="btn-preview-retry"
                  variant="secondary"
                  onClick={() => checkHealthAndSync(false)}
                  isLoading={isChecking}
                  style={{ fontSize: '0.82rem', padding: '0.5rem 1rem' }}
                >
                  <RotateCw size={14} style={{ marginRight: '0.4rem' }} />
                  Retry
                </Button>

                <Button
                  id="btn-preview-restart"
                  variant="primary"
                  onClick={handleRestart}
                  isLoading={isRestarting}
                  style={{
                    fontSize: '0.82rem',
                    padding: '0.5rem 1rem',
                    background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-cyan))',
                    fontWeight: 600,
                  }}
                >
                  <RefreshCw size={14} style={{ marginRight: '0.4rem' }} />
                  Restart Application
                </Button>

                <Button
                  id="btn-preview-ask-ai"
                  variant="secondary"
                  onClick={() => {
                    const prompt = `The application runtime on port ${runtimePort} is unavailable. Status: ${runtimeStatus}. Diagnostic detail: ${runtimeDetail || 'connection refused'}. Please help diagnose and fix the application runtime.`;
                    if (onSendAssistantPrompt) {
                      onSendAssistantPrompt(prompt);
                    } else if (onOpenAssistant) {
                      onOpenAssistant();
                    }
                  }}
                  style={{ fontSize: '0.82rem', padding: '0.5rem 1rem' }}
                >
                  <Bot size={14} style={{ marginRight: '0.4rem', color: 'var(--accent-cyan)' }} />
                  Ask AI to Fix
                </Button>

                {onNavigate && (
                  <>
                    <Button
                      id="btn-preview-nav-code"
                      variant="ghost"
                      onClick={() => onNavigate('code-intelligence')}
                      style={{ fontSize: '0.82rem', padding: '0.5rem 1rem', border: '1px solid var(--border-subtle)' }}
                    >
                      <Code2 size={14} style={{ marginRight: '0.4rem' }} />
                      Code Intelligence
                    </Button>
                    <Button
                      id="btn-preview-nav-dev"
                      variant="ghost"
                      onClick={() => onNavigate('development')}
                      style={{ fontSize: '0.82rem', padding: '0.5rem 1rem', border: '1px solid var(--border-subtle)' }}
                    >
                      <Layers size={14} style={{ marginRight: '0.4rem' }} />
                      Development
                    </Button>
                  </>
                )}
              </div>

              {/* View Runtime Details (Controlled, safe diagnostics) */}
              <div style={{ marginTop: '1.5rem', width: '100%', maxWidth: 460 }}>
                <button
                  id="btn-toggle-runtime-details"
                  type="button"
                  onClick={() => setShowDetails(!showDetails)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-muted)',
                    fontSize: '0.78rem',
                    cursor: 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                  }}
                >
                  <Info size={13} />
                  <span>{showDetails ? 'Hide Runtime Details' : 'View Runtime Details'}</span>
                  {showDetails ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                </button>

                {showDetails && (
                  <div
                    id="runtime-details-panel"
                    style={{
                      marginTop: '0.75rem',
                      padding: '0.85rem 1rem',
                      borderRadius: 'var(--radius-md)',
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid var(--border-subtle)',
                      textAlign: 'left',
                      fontSize: '0.76rem',
                      fontFamily: 'monospace',
                      color: 'var(--text-secondary)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.35rem',
                    }}
                  >
                    <div><strong style={{ color: '#fff' }}>Target Port:</strong> {runtimePort}</div>
                    <div><strong style={{ color: '#fff' }}>Host:</strong> 127.0.0.1</div>
                    <div><strong style={{ color: '#fff' }}>Preview URL:</strong> {previewUrl}</div>
                    <div><strong style={{ color: '#fff' }}>Lifecycle State:</strong> {runtimeStatus}</div>
                    <div><strong style={{ color: '#fff' }}>Diagnostic Detail:</strong> {runtimeDetail || 'Server connection refused on port 8001.'}</div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 3. Bottom Development Helper Prompting Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0.6rem 1.25rem',
          background: 'var(--bg-secondary)',
          borderTop: '1px solid var(--border-subtle)',
          fontSize: '0.78rem',
          flexShrink: 0,
          gap: '1rem',
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}>
          <Sparkles size={14} color="var(--accent-cyan)" />
          <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Prompt Assistant to Improve:</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
          {promptSuggestions.map((promptText, i) => (
            <button
              key={i}
              type="button"
              onClick={() => {
                if (onSendAssistantPrompt) {
                  onSendAssistantPrompt(promptText);
                } else if (onOpenAssistant) {
                  onOpenAssistant();
                }
              }}
              style={{
                background: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid var(--border-subtle)',
                color: '#cbd5e1',
                padding: '0.25rem 0.65rem',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.74rem',
                cursor: 'pointer',
                transition: 'all 0.15s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--accent-primary)';
                e.currentTarget.style.color = '#fff';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border-subtle)';
                e.currentTarget.style.color = '#cbd5e1';
              }}
            >
              "{promptText}"
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {onNavigate && (
            <>
              <button
                type="button"
                onClick={() => onNavigate('development')}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-muted)',
                  fontSize: '0.75rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem',
                  cursor: 'pointer',
                }}
              >
                <Code2 size={13} />
                <span>Files & Code</span>
              </button>
              <button
                type="button"
                onClick={() => onNavigate('specification')}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-muted)',
                  fontSize: '0.75rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem',
                  cursor: 'pointer',
                }}
              >
                <Settings size={13} />
                <span>Advanced</span>
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
