import React, { useEffect, useState } from 'react';
import { Card, CardBody, CardHeader } from '../components/common/Card';
import { CapabilityBadge } from '../components/common/CapabilityBadge';
import { Button } from '../components/common/Button';
import { Modal } from '../components/common/Modal';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { useProject } from '../context/ProjectContext';
import { developmentVersionApi } from '../services/developmentVersionApi';
import {
  DevelopmentChangeResponse,
  DevelopmentVersionResponse,
  VerificationSnapshot,
  VersionComparisonResponse,
  VersionFileSummary,
} from '../types/developmentVersion';
import {
  Code2,
  Play,
  GitBranch,
  Hammer,
  CheckCircle2,
  XCircle,
  RotateCcw,
  ShieldCheck,
  History,
  FileText,
  ArrowLeftRight,
  RefreshCw,
  Check,
  Loader2,
  Search,
  Copy,
} from 'lucide-react';
import { NavigationTab } from '../components/layout/Sidebar';
import { BrowserJourneyPanel, useBrowserJourneys } from '../components/browser-journeys';
import { workflowsApi } from '../services/workflowsApi';

interface DevelopmentWorkspaceProps {
  onNavigate?: (tab: NavigationTab) => void;
}

export const DevelopmentWorkspace: React.FC<DevelopmentWorkspaceProps> = ({ onNavigate }) => {
  const { selectedProjectId, selectedProject } = useProject();

  // Version state
  const [versions, setVersions] = useState<DevelopmentVersionResponse[]>([]);
  const [activeVersion, setActiveVersion] = useState<DevelopmentVersionResponse | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<DevelopmentVersionResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Browser journeys state (Phase 11K Stage 6)
  const {
    workflowResult: journeyResult,
    isGenerating: isGeneratingJourneys,
    generate: generateJourneys,
  } = useBrowserJourneys({ projectId: selectedProjectId });

  // Inspector tabs: 'manifest' | 'verification' | 'compare' | 'changes'
  const [activeTab, setActiveTab] = useState<'manifest' | 'verification' | 'compare' | 'changes'>('manifest');

  // File viewer state
  const [selectedFile, setSelectedFile] = useState<VersionFileSummary | null>(null);
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [loadingFile, setLoadingFile] = useState<boolean>(false);
  const [fileSearch, setFileSearch] = useState<string>('');
  const [isCopied, setIsCopied] = useState<boolean>(false);

  // Verification tab state
  const [verificationSnapshot, setVerificationSnapshot] = useState<VerificationSnapshot | null>(null);
  const [verifying, setVerifying] = useState<boolean>(false);

  // Comparison tab state
  const [compareTargetId, setCompareTargetId] = useState<string>('');
  const [comparison, setComparison] = useState<VersionComparisonResponse | null>(null);
  const [loadingComparison, setLoadingComparison] = useState<boolean>(false);

  // Changes tab state
  const [changes, setChanges] = useState<DevelopmentChangeResponse[]>([]);
  const [loadingChanges, setLoadingChanges] = useState<boolean>(false);

  // Action modals
  const [actionModalType, setActionModalType] = useState<'activate' | 'rollback' | null>(null);
  const [actionReason, setActionReason] = useState<string>('');
  const [actionSubmitting, setActionSubmitting] = useState<boolean>(false);
  const [actionSuccessMessage, setActionSuccessMessage] = useState<string | null>(null);

  // Active development stages across the platform
  const devStages = [
    {
      stage: 'BUILD',
      icon: <Hammer size={18} color="var(--sdlc-build)" />,
      badge: 'IMPLEMENTED' as const,
      title: 'Code Generation & Scaffolding',
      description:
        'Synthesis of runnable frontend and backend microservices from Specification and Architecture design artifacts.',
    },
    {
      stage: 'RUN',
      icon: <Play size={18} color="var(--sdlc-run)" />,
      badge: 'IMPLEMENTED' as const,
      title: 'Containerized Sandbox Runtime',
      description:
        'Live isolated runtime execution environment for generated services, hot-reload previews, and port forwarding.',
    },
    {
      stage: 'MODIFY',
      icon: <Code2 size={18} color="var(--accent-cyan)" />,
      badge: 'IMPLEMENTED' as const,
      title: 'AI-Assisted Code Iteration',
      description:
        'Selective code patch synthesis, interactive diff inspection, and guided human-in-the-loop modifications.',
    },
    {
      stage: 'VERSION',
      icon: <GitBranch size={18} color="var(--status-completed)" />,
      badge: 'IMPLEMENTED' as const,
      title: 'Artifact Versioning & Checkpoints',
      description:
        'Git-backed deterministic version snapshots preserving code state alongside requirement and architecture revisions.',
    },
  ];

  const [isGeneratingCode, setIsGeneratingCode] = useState<boolean>(false);

  const handleGenerateCode = async () => {
    if (!selectedProjectId) return;
    setIsGeneratingCode(true);
    setError(null);
    try {
      await workflowsApi.execute('code-generation-workflow', {
        project_id: selectedProjectId,
      });
      await fetchVersions();
      setActionSuccessMessage('Code generation workflow completed successfully. Initial version registered.');
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Failed to execute code generation workflow.';
      setError(msg);
    } finally {
      setIsGeneratingCode(false);
    }
  };

  // Fetch versions on project select
  const fetchVersions = async () => {
    if (!selectedProjectId) {
      setVersions([]);
      setActiveVersion(null);
      setSelectedVersion(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await developmentVersionApi.listVersions(selectedProjectId);
      setVersions(res.items);
      const active = res.items.find((v) => v.is_active) || null;
      setActiveVersion(active);

      // Default selected version to active or latest
      if (res.items.length > 0) {
        const defaultVer = active || res.items[res.items.length - 1];
        setSelectedVersion(defaultVer);
        if (defaultVer.files_manifest.length > 0) {
          setSelectedFile(defaultVer.files_manifest[0]);
        }
      } else {
        setSelectedVersion(null);
        setSelectedFile(null);
      }
    } catch (err: any) {
      // If error occurs, keep empty versions without breaking UI
      console.warn('Unable to load development versions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVersions();
  }, [selectedProjectId]);

  // Fetch file content when selectedFile changes
  useEffect(() => {
    if (!selectedProjectId || !selectedVersion || !selectedFile) {
      setFileContent(null);
      return;
    }
    let isMounted = true;
    setLoadingFile(true);
    developmentVersionApi
      .getVersionFileContent(selectedProjectId, selectedVersion.version_id, selectedFile.path)
      .then((content) => {
        if (isMounted) setFileContent(content);
      })
      .catch((e) => {
        if (isMounted) setFileContent(`// Error loading file: ${e.message}`);
      })
      .finally(() => {
        if (isMounted) setLoadingFile(false);
      });
    return () => {
      isMounted = false;
    };
  }, [selectedProjectId, selectedVersion?.version_id, selectedFile?.path]);

  // Fetch verification snapshot when verification tab opens
  useEffect(() => {
    if (activeTab === 'verification' && selectedProjectId && selectedVersion) {
      if (selectedVersion.verification_summary) {
        setVerificationSnapshot(selectedVersion.verification_summary);
      } else {
        developmentVersionApi
          .getVersionVerification(selectedProjectId, selectedVersion.version_id)
          .then(setVerificationSnapshot)
          .catch(console.error);
      }
    }
  }, [activeTab, selectedProjectId, selectedVersion?.version_id]);

  // Fetch change history when changes tab opens
  useEffect(() => {
    if (activeTab === 'changes' && selectedProjectId && selectedVersion) {
      setLoadingChanges(true);
      developmentVersionApi
        .getVersionChanges(selectedProjectId, selectedVersion.version_id)
        .then(setChanges)
        .catch(console.error)
        .finally(() => setLoadingChanges(false));
    }
  }, [activeTab, selectedProjectId, selectedVersion?.version_id]);

  // Fetch comparison when compare tab opens
  useEffect(() => {
    if (activeTab === 'compare' && selectedProjectId && selectedVersion) {
      // Find candidate to compare: parent version or previous version
      const otherVersions = versions.filter((v) => v.version_id !== selectedVersion.version_id);
      const target =
        otherVersions.find((v) => v.version_id === selectedVersion.parent_version_id) ||
        otherVersions[otherVersions.length - 1];
      if (target) {
        setCompareTargetId(target.version_id);
      }
    }
  }, [activeTab, selectedVersion?.version_id, versions]);

  useEffect(() => {
    if (activeTab === 'compare' && selectedProjectId && selectedVersion && compareTargetId) {
      setLoadingComparison(true);
      developmentVersionApi
        .compareVersions(selectedProjectId, compareTargetId, selectedVersion.version_id)
        .then(setComparison)
        .catch(console.error)
        .finally(() => setLoadingComparison(false));
    }
  }, [compareTargetId, activeTab, selectedProjectId, selectedVersion?.version_id]);

  // Handle re-verification
  const handleReverify = async () => {
    if (!selectedProjectId || !selectedVersion) return;
    setVerifying(true);
    try {
      const snap = await developmentVersionApi.reverifyVersion(
        selectedProjectId,
        selectedVersion.version_id
      );
      setVerificationSnapshot(snap);
      setActionSuccessMessage('Verification gate re-evaluated deterministically.');
      await fetchVersions();
    } catch (err: any) {
      setError(err.message || 'Failed to re-verify version.');
    } finally {
      setVerifying(false);
    }
  };

  // Handle Activate Version
  const handleActivate = async () => {
    if (!selectedProjectId || !selectedVersion) return;
    setActionSubmitting(true);
    try {
      await developmentVersionApi.activateVersion(
        selectedProjectId,
        selectedVersion.version_id,
        actionReason || undefined
      );
      setActionSuccessMessage(`Version v${selectedVersion.version_number} is now active.`);
      setActionModalType(null);
      setActionReason('');
      await fetchVersions();
    } catch (err: any) {
      setError(err.message || 'Failed to activate version.');
    } finally {
      setActionSubmitting(false);
    }
  };

  // Handle Rollback Version
  const handleRollback = async () => {
    if (!selectedProjectId || !selectedVersion) return;
    setActionSubmitting(true);
    try {
      await developmentVersionApi.rollbackVersion(
        selectedProjectId,
        selectedVersion.version_id,
        actionReason || undefined
      );
      setActionSuccessMessage(
        `Active pointer successfully rolled back to version v${selectedVersion.version_number}.`
      );
      setActionModalType(null);
      setActionReason('');
      await fetchVersions();
    } catch (err: any) {
      setError(err.message || 'Failed to roll back version.');
    } finally {
      setActionSubmitting(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xl)' }}>
      {/* Workspace Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700 }}>Development Workspace</h1>
            {versions.length > 0 ? (
              <span
                style={{
                  padding: '0.2rem 0.6rem',
                  borderRadius: '999px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  background: 'rgba(16, 185, 129, 0.15)',
                  color: '#10b981',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                }}
              >
                LIVE LOOP
              </span>
            ) : (
              <CapabilityBadge status="IMPLEMENTED" size="md" />
            )}
          </div>
          <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            {versions.length > 0
              ? 'Version-aware Continuous Engineering Loop: immutable releases, deterministic verification gates, and auditable rollbacks.'
              : 'Version-aware Continuous Engineering Loop: generate code, run in isolated sandboxes, verify deterministic gates, and manage immutable releases.'}
          </p>
        </div>

        {selectedProject && (
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Project: <strong style={{ color: 'var(--text-primary)' }}>{selectedProject.name}</strong>
          </div>
        )}
      </div>

      {actionSuccessMessage && (
        <div
          style={{
            padding: 'var(--space-sm) var(--space-md)',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(16, 185, 129, 0.12)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            color: '#10b981',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Check size={16} />
            <span>{actionSuccessMessage}</span>
          </div>
          <button
            onClick={() => setActionSuccessMessage(null)}
            style={{ background: 'transparent', border: 'none', color: '#10b981', cursor: 'pointer' }}
          >
            ✕
          </button>
        </div>
      )}

      {error && <ErrorAlert error={error} onRetry={() => setError(null)} />}

      {loading && versions.length === 0 && (
        <LoadingSpinner size={32} label="Loading software development versions..." />
      )}

      {/* ACTIVE VERSION BANNER (if versions exist) */}
      {versions.length > 0 && activeVersion && (
        <Card
          style={{
            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(99, 102, 241, 0.08) 100%)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
          }}
        >
          <CardBody>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div
                  style={{
                    width: '44px',
                    height: '44px',
                    borderRadius: 'var(--radius-md)',
                    background: 'rgba(16, 185, 129, 0.2)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#10b981',
                  }}
                >
                  <ShieldCheck size={26} />
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '1.15rem', fontWeight: 700 }}>
                      Active Release: v{activeVersion.version_number}
                    </span>
                    <span
                      style={{
                        padding: '0.15rem 0.5rem',
                        borderRadius: '4px',
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        background: '#10b981',
                        color: '#064e3b',
                      }}
                    >
                      ACTIVE
                    </span>
                    <span
                      style={{
                        padding: '0.15rem 0.5rem',
                        borderRadius: '4px',
                        fontSize: '0.7rem',
                        fontWeight: 600,
                        background: 'rgba(255, 255, 255, 0.1)',
                        color: 'var(--text-secondary)',
                      }}
                    >
                      {activeVersion.status}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                    Content SHA-256:{' '}
                    <code style={{ fontFamily: 'monospace', color: 'var(--text-secondary)' }}>
                      {(activeVersion.content_hash || '').substring(0, 16)}...
                    </code>{' '}
                    • {activeVersion.file_count || 0} files ({Math.round((activeVersion.total_size_bytes || 0) / 1024)} KB) • Created{' '}
                    {activeVersion.created_at ? new Date(activeVersion.created_at).toLocaleDateString() : 'N/A'}
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    setSelectedVersion(activeVersion);
                    setActiveTab('verification');
                  }}
                >
                  <ShieldCheck size={14} style={{ marginRight: '0.35rem' }} />
                  Verification Details
                </Button>
                {selectedVersion && selectedVersion.version_id !== activeVersion.version_id && (
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => setActionModalType('activate')}
                    disabled={selectedVersion.status !== 'VERIFIED' && selectedVersion.status !== 'SUPERSEDED'}
                  >
                    Activate Selected (v{selectedVersion.version_number})
                  </Button>
                )}
              </div>
            </div>
          </CardBody>
        </Card>
      )}

      {/* INTELLIGENT BROWSER JOURNEYS PANEL (Phase 11K Stage 6) */}
      <BrowserJourneyPanel
        workflowResult={journeyResult}
        onGenerate={() =>
          generateJourneys({
            development_version_id: activeVersion?.version_id || selectedVersion?.version_id,
          })
        }
        onViewResults={onNavigate ? () => onNavigate('testing') : undefined}
        isGenerating={isGeneratingJourneys}
      />

      {/* CONTINUOUS ENGINEERING LOOP MAIN INTERACTIVE WORKSPACE */}
      {versions.length > 0 && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '260px 1fr',
            gap: 'var(--space-md)',
            minHeight: '520px',
          }}
        >
          {/* LEFT RAIL: VERSION TIMELINE */}
          <Card style={{ background: 'var(--bg-glass-card)' }}>
            <CardHeader>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <History size={16} color="var(--accent-primary)" />
                <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>Version Timeline</span>
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{versions.length} versions</span>
            </CardHeader>
            <CardBody style={{ padding: 'var(--space-xs)' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                {versions.map((ver) => {
                  const isSelected = selectedVersion?.version_id === ver.version_id;
                  const isVerified = ver.status === 'VERIFIED' || ver.status === 'ACTIVE';

                  return (
                    <div
                      key={ver.version_id}
                      onClick={() => {
                        setSelectedVersion(ver);
                        if (ver.files_manifest.length > 0) {
                          setSelectedFile(ver.files_manifest[0]);
                        }
                      }}
                      style={{
                        padding: 'var(--space-sm)',
                        borderRadius: 'var(--radius-sm)',
                        cursor: 'pointer',
                        background: isSelected
                          ? 'rgba(99, 102, 241, 0.18)'
                          : 'rgba(255, 255, 255, 0.02)',
                        border: isSelected
                          ? '1px solid var(--accent-primary)'
                          : '1px solid transparent',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                          <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>v{ver.version_number}</span>
                          {ver.is_active && (
                            <span
                              style={{
                                fontSize: '0.65rem',
                                padding: '0.1rem 0.35rem',
                                borderRadius: '3px',
                                background: '#10b981',
                                color: '#064e3b',
                                fontWeight: 700,
                              }}
                            >
                              ACTIVE
                            </span>
                          )}
                        </div>
                        {isVerified ? (
                          <CheckCircle2 size={14} color="#10b981" />
                        ) : (
                          <XCircle size={14} color="#ef4444" />
                        )}
                      </div>
                      <div
                        style={{
                          fontSize: '0.72rem',
                          color: 'var(--text-muted)',
                          marginTop: '0.25rem',
                          display: 'flex',
                          justifyContent: 'space-between',
                        }}
                      >
                        <span>{ver.source_reason}</span>
                        <span>{ver.file_count} files</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardBody>
          </Card>

          {/* MAIN INSPECTOR PANEL */}
          <Card style={{ background: 'var(--bg-glass-card)', display: 'flex', flexDirection: 'column' }}>
            <CardHeader style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', flexWrap: 'wrap', gap: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <div style={{ display: 'flex', gap: '0.25rem' }}>
                    <button
                      onClick={() => setActiveTab('manifest')}
                      style={{
                        padding: '0.4rem 0.8rem',
                        borderRadius: 'var(--radius-sm)',
                        border: 'none',
                        background: activeTab === 'manifest' ? 'var(--accent-primary)' : 'transparent',
                        color: activeTab === 'manifest' ? '#fff' : 'var(--text-secondary)',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                      }}
                    >
                      <FileText size={14} />
                      Files & Code
                    </button>
                    <button
                      onClick={() => setActiveTab('verification')}
                      style={{
                        padding: '0.4rem 0.8rem',
                        borderRadius: 'var(--radius-sm)',
                        border: 'none',
                        background: activeTab === 'verification' ? 'var(--accent-primary)' : 'transparent',
                        color: activeTab === 'verification' ? '#fff' : 'var(--text-secondary)',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                      }}
                    >
                      <ShieldCheck size={14} />
                      Verification Gate
                    </button>
                    <button
                      onClick={() => setActiveTab('compare')}
                      style={{
                        padding: '0.4rem 0.8rem',
                        borderRadius: 'var(--radius-sm)',
                        border: 'none',
                        background: activeTab === 'compare' ? 'var(--accent-primary)' : 'transparent',
                        color: activeTab === 'compare' ? '#fff' : 'var(--text-secondary)',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                      }}
                    >
                      <ArrowLeftRight size={14} />
                      Diff & Compare
                    </button>
                    <button
                      onClick={() => setActiveTab('changes')}
                      style={{
                        padding: '0.4rem 0.8rem',
                        borderRadius: 'var(--radius-sm)',
                        border: 'none',
                        background: activeTab === 'changes' ? 'var(--accent-primary)' : 'transparent',
                        color: activeTab === 'changes' ? '#fff' : 'var(--text-secondary)',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                      }}
                    >
                      <History size={14} />
                      Change Log
                    </button>
                  </div>
                </div>

                {/* Version Controls */}
                {selectedVersion && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {!selectedVersion.is_active && (
                      <>
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => setActionModalType('activate')}
                          disabled={selectedVersion.status !== 'VERIFIED' && selectedVersion.status !== 'SUPERSEDED'}
                        >
                          <Check size={14} style={{ marginRight: '0.3rem' }} />
                          Activate v{selectedVersion.version_number}
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => setActionModalType('rollback')}
                          disabled={selectedVersion.status !== 'VERIFIED' && selectedVersion.status !== 'SUPERSEDED'}
                        >
                          <RotateCcw size={14} style={{ marginRight: '0.3rem' }} />
                          Rollback to v{selectedVersion.version_number}
                        </Button>
                      </>
                    )}
                  </div>
                )}
              </div>
            </CardHeader>

            <CardBody style={{ flex: 1, padding: 'var(--space-md)' }}>
              {/* TAB 1: MANIFEST & CODE VIEWER */}
              {activeTab === 'manifest' && selectedVersion && (
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '240px 1fr',
                    gap: 'var(--space-sm)',
                    height: '420px',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    overflow: 'hidden',
                  }}
                >
                  {/* File List */}
                  <div
                    style={{
                      borderRight: '1px solid var(--border-subtle)',
                      background: 'rgba(0, 0, 0, 0.15)',
                      padding: 'var(--space-xs)',
                      overflowY: 'auto',
                      display: 'flex',
                      flexDirection: 'column',
                    }}
                  >
                    <div style={{ padding: '0.25rem 0.35rem 0.4rem 0.35rem' }}>
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.35rem',
                          background: 'rgba(255, 255, 255, 0.04)',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: 'var(--radius-sm)',
                          padding: '0.2rem 0.45rem',
                        }}
                      >
                        <Search size={12} color="var(--text-muted)" />
                        <input
                          type="text"
                          placeholder="Filter files..."
                          value={fileSearch}
                          onChange={(e) => setFileSearch(e.target.value)}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            outline: 'none',
                            color: '#fff',
                            fontSize: '0.72rem',
                            width: '100%',
                          }}
                        />
                      </div>
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600, padding: '0.25rem 0.4rem' }}>
                      MANIFEST ({selectedVersion.files_manifest.length} FILES)
                    </div>
                    <div style={{ flex: 1, overflowY: 'auto' }}>
                      {selectedVersion.files_manifest
                        .filter((f) => !fileSearch || f.path.toLowerCase().includes(fileSearch.toLowerCase()))
                        .map((f) => {
                          const isFileSelected = selectedFile?.path === f.path;
                          return (
                            <div
                              key={f.path}
                              onClick={() => setSelectedFile(f)}
                              style={{
                                padding: '0.35rem 0.55rem',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '0.76rem',
                                fontFamily: 'monospace',
                                background: isFileSelected ? 'rgba(99, 102, 241, 0.25)' : 'transparent',
                                color: isFileSelected ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                              }}
                            >
                              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                {f.path}
                              </span>
                              <span style={{ fontSize: '0.65rem', color: 'var(--text-dim)' }}>
                                {Math.round(f.size_bytes / 1024) || 1}k
                              </span>
                            </div>
                          );
                        })}
                    </div>
                  </div>

                  {/* Code Editor Preview */}
                  <div style={{ display: 'flex', flexDirection: 'column', background: 'var(--bg-surface)' }}>
                    <div
                      style={{
                        padding: '0.4rem 0.8rem',
                        borderBottom: '1px solid var(--border-subtle)',
                        fontSize: '0.75rem',
                        fontFamily: 'monospace',
                        color: 'var(--text-muted)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <span>{selectedFile?.path || 'No file selected'}</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                        {selectedFile?.requirement_ids && selectedFile.requirement_ids.length > 0 && (
                          <span style={{ fontSize: '0.7rem' }}>Linked: {selectedFile.requirement_ids.join(', ')}</span>
                        )}
                        <button
                          type="button"
                          onClick={() => {
                            if (fileContent) {
                              navigator.clipboard.writeText(fileContent);
                              setIsCopied(true);
                              setTimeout(() => setIsCopied(false), 2000);
                            }
                          }}
                          disabled={!fileContent}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.25rem',
                            padding: '0.2rem 0.5rem',
                            fontSize: '0.72rem',
                            background: 'rgba(255, 255, 255, 0.05)',
                            border: '1px solid var(--border-subtle)',
                            borderRadius: 'var(--radius-sm)',
                            color: isCopied ? '#10b981' : 'var(--text-secondary)',
                            cursor: 'pointer',
                          }}
                        >
                          {isCopied ? <Check size={12} /> : <Copy size={12} />}
                          <span>{isCopied ? 'Copied' : 'Copy'}</span>
                        </button>
                      </div>
                    </div>
                    <div style={{ flex: 1, padding: 'var(--space-sm)', overflow: 'auto' }}>
                      {loadingFile ? (
                        <LoadingSpinner size={20} />
                      ) : (
                        <pre
                          style={{
                            margin: 0,
                            fontFamily: 'monospace',
                            fontSize: '0.8rem',
                            lineHeight: 1.45,
                            color: 'var(--text-primary)',
                            whiteSpace: 'pre-wrap',
                          }}
                        >
                          {fileContent || '// Select a file from the manifest to inspect source code.'}
                        </pre>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: DETERMINISTIC VERIFICATION GATE */}
              {activeTab === 'verification' && selectedVersion && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
                    <div>
                      <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600 }}>Deterministic Verification Snapshot</h3>
                      <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        All REQUIRED stages must pass cleanly without blocking errors before a version can be activated.
                      </p>
                    </div>
                    <Button variant="secondary" size="sm" onClick={handleReverify} disabled={verifying}>
                      <RefreshCw size={14} style={{ marginRight: '0.35rem' }} className={verifying ? 'spin' : ''} />
                      {verifying ? 'Re-evaluating...' : 'Recompute Verification Gate'}
                    </Button>
                  </div>

                  {verificationSnapshot && (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--space-sm)' }}>
                      {/* Static Analysis */}
                      <Card style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-subtle)' }}>
                        <CardHeader>
                          <span style={{ fontSize: '0.82rem', fontWeight: 600 }}>Static Analysis</span>
                          <span
                            style={{
                              fontSize: '0.7rem',
                              fontWeight: 700,
                              color: verificationSnapshot.static_analysis.status === 'PASSED' ? '#10b981' : '#ef4444',
                            }}
                          >
                            {verificationSnapshot.static_analysis.status}
                          </span>
                        </CardHeader>
                        <CardBody>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            Level: <strong>{verificationSnapshot.static_analysis.requirement_level}</strong>
                          </div>
                          <div style={{ fontSize: '0.75rem', marginTop: '0.25rem', color: 'var(--text-secondary)' }}>
                            {verificationSnapshot.static_analysis.details}
                          </div>
                        </CardBody>
                      </Card>

                      {/* Sandbox Execution */}
                      <Card style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-subtle)' }}>
                        <CardHeader>
                          <span style={{ fontSize: '0.82rem', fontWeight: 600 }}>Docker Sandbox</span>
                          <span
                            style={{
                              fontSize: '0.7rem',
                              fontWeight: 700,
                              color: verificationSnapshot.sandbox_execution.status === 'PASSED' ? '#10b981' : '#ef4444',
                            }}
                          >
                            {verificationSnapshot.sandbox_execution.status}
                          </span>
                        </CardHeader>
                        <CardBody>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            Level: <strong>{verificationSnapshot.sandbox_execution.requirement_level}</strong>
                          </div>
                          <div style={{ fontSize: '0.75rem', marginTop: '0.25rem', color: 'var(--text-secondary)' }}>
                            {verificationSnapshot.sandbox_execution.details}
                          </div>
                        </CardBody>
                      </Card>

                      {/* AI Test Suite */}
                      <Card style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-subtle)' }}>
                        <CardHeader>
                          <span style={{ fontSize: '0.82rem', fontWeight: 600 }}>AI Test Suite</span>
                          <span
                            style={{
                              fontSize: '0.7rem',
                              fontWeight: 700,
                              color: verificationSnapshot.ai_tests.status === 'PASSED' ? '#10b981' : '#ef4444',
                            }}
                          >
                            {verificationSnapshot.ai_tests.status}
                          </span>
                        </CardHeader>
                        <CardBody>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            Level: <strong>{verificationSnapshot.ai_tests.requirement_level}</strong>
                          </div>
                          <div style={{ fontSize: '0.75rem', marginTop: '0.25rem', color: 'var(--text-secondary)' }}>
                            {verificationSnapshot.ai_tests.details}
                          </div>
                        </CardBody>
                      </Card>

                      {/* Failure Analysis */}
                      <Card style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-subtle)' }}>
                        <CardHeader>
                          <span style={{ fontSize: '0.82rem', fontWeight: 600 }}>Failure Analysis</span>
                          <span
                            style={{
                              fontSize: '0.7rem',
                              fontWeight: 700,
                              color: verificationSnapshot.failure_analysis.status === 'PASSED' ? '#10b981' : '#ef4444',
                            }}
                          >
                            {verificationSnapshot.failure_analysis.status}
                          </span>
                        </CardHeader>
                        <CardBody>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            Level: <strong>{verificationSnapshot.failure_analysis.requirement_level}</strong>
                          </div>
                          <div style={{ fontSize: '0.75rem', marginTop: '0.25rem', color: 'var(--text-secondary)' }}>
                            {verificationSnapshot.failure_analysis.details}
                          </div>
                        </CardBody>
                      </Card>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 3: DIFF & COMPARE */}
              {activeTab === 'compare' && selectedVersion && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
                    <div style={{ fontSize: '0.85rem' }}>
                      Comparing <strong>v{selectedVersion.version_number}</strong> with:
                    </div>
                    <select
                      value={compareTargetId}
                      onChange={(e) => setCompareTargetId(e.target.value)}
                      style={{
                        padding: '0.4rem 0.6rem',
                        borderRadius: 'var(--radius-sm)',
                        background: 'var(--bg-surface)',
                        color: 'var(--text-primary)',
                        border: '1px solid var(--border-subtle)',
                        fontSize: '0.8rem',
                      }}
                    >
                      {versions
                        .filter((v) => v.version_id !== selectedVersion.version_id)
                        .map((v) => (
                          <option key={v.version_id} value={v.version_id}>
                            v{v.version_number} ({v.source_reason})
                          </option>
                        ))}
                    </select>
                  </div>

                  {loadingComparison ? (
                    <LoadingSpinner size={32} />
                  ) : comparison ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
                      <div
                        style={{
                          padding: 'var(--space-sm)',
                          borderRadius: 'var(--radius-sm)',
                          background: 'rgba(255, 255, 255, 0.03)',
                          fontSize: '0.8rem',
                          color: 'var(--text-secondary)',
                        }}
                      >
                        {comparison.verification_change_summary}
                      </div>

                      {/* Modified Files Unified Diffs */}
                      {comparison.files_modified.map((mod) => (
                        <div
                          key={mod.path}
                          style={{
                            border: '1px solid var(--border-subtle)',
                            borderRadius: 'var(--radius-sm)',
                            overflow: 'hidden',
                          }}
                        >
                          <div
                            style={{
                              padding: '0.35rem 0.75rem',
                              background: 'rgba(0, 0, 0, 0.25)',
                              fontSize: '0.78rem',
                              fontFamily: 'monospace',
                              fontWeight: 600,
                            }}
                          >
                            MODIFIED: {mod.path}
                          </div>
                          <pre
                            style={{
                              margin: 0,
                              padding: 'var(--space-sm)',
                              fontFamily: 'monospace',
                              fontSize: '0.75rem',
                              background: 'var(--bg-surface)',
                              lineHeight: 1.4,
                              overflowX: 'auto',
                              whiteSpace: 'pre-wrap',
                            }}
                          >
                            {mod.unified_diff}
                          </pre>
                        </div>
                      ))}

                      {/* Added Files */}
                      {comparison.files_added.map((add) => (
                        <div
                          key={add.path}
                          style={{
                            padding: '0.4rem 0.75rem',
                            borderRadius: '4px',
                            background: 'rgba(16, 185, 129, 0.1)',
                            border: '1px solid rgba(16, 185, 129, 0.25)',
                            fontSize: '0.78rem',
                            color: '#10b981',
                            fontFamily: 'monospace',
                          }}
                        >
                          + ADDED: {add.path} ({add.size_delta_bytes} bytes)
                        </div>
                      ))}

                      {/* Removed Files */}
                      {comparison.files_removed.map((rem) => (
                        <div
                          key={rem.path}
                          style={{
                            padding: '0.4rem 0.75rem',
                            borderRadius: '4px',
                            background: 'rgba(239, 68, 68, 0.1)',
                            border: '1px solid rgba(239, 68, 68, 0.25)',
                            fontSize: '0.78rem',
                            color: '#ef4444',
                            fontFamily: 'monospace',
                          }}
                        >
                          - REMOVED: {rem.path}
                        </div>
                      ))}
                    </div>
                  ) : null}
                </div>
              )}

              {/* TAB 4: CHANGE HISTORY AUDIT LOG */}
              {activeTab === 'changes' && selectedVersion && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                    Chronological audit log tracking code-producing modifications and project lifecycle events.
                  </div>

                  {loadingChanges ? (
                    <LoadingSpinner size={32} />
                  ) : (
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-dim)' }}>
                          <th style={{ padding: '0.5rem' }}>CATEGORY</th>
                          <th style={{ padding: '0.5rem' }}>TYPE</th>
                          <th style={{ padding: '0.5rem' }}>REASON</th>
                          <th style={{ padding: '0.5rem' }}>TIMESTAMP</th>
                        </tr>
                      </thead>
                      <tbody>
                        {changes.map((c) => (
                          <tr key={c.change_id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.03)' }}>
                            <td style={{ padding: '0.5rem', fontWeight: 600 }}>{c.change_category}</td>
                            <td style={{ padding: '0.5rem' }}>
                              <span
                                style={{
                                  padding: '0.15rem 0.4rem',
                                  borderRadius: '3px',
                                  fontSize: '0.7rem',
                                  background:
                                    c.change_category === 'CODE_PRODUCING'
                                      ? 'rgba(99, 102, 241, 0.15)'
                                      : 'rgba(16, 185, 129, 0.15)',
                                  color:
                                    c.change_category === 'CODE_PRODUCING'
                                      ? 'var(--accent-primary)'
                                      : '#10b981',
                                }}
                              >
                                {c.change_type}
                              </span>
                            </td>
                            <td style={{ padding: '0.5rem', color: 'var(--text-secondary)' }}>{c.reason}</td>
                            <td style={{ padding: '0.5rem', color: 'var(--text-dim)' }}>
                              {new Date(c.created_at).toLocaleString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}
            </CardBody>
          </Card>
        </div>
      )}

      {/* Continuous Engineering Loop Architecture Section */}
      <div
        style={{
          padding: 'var(--space-md)',
          borderRadius: 'var(--radius-md)',
          background: 'rgba(99, 102, 241, 0.08)',
          border: '1px solid rgba(99, 102, 241, 0.25)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
          fontSize: '0.85rem',
          color: 'var(--text-secondary)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', flex: 1 }}>
          <ShieldCheck size={22} color="var(--status-completed)" style={{ flexShrink: 0, marginTop: '0.1rem' }} />
          <div>
            <strong style={{ color: 'var(--text-primary)' }}>Continuous Engineering Pipeline Active:</strong>
            <div style={{ marginTop: '0.2rem', lineHeight: 1.5 }}>
              Code generation, container sandbox runtime, interactive remediation, and immutable version checkpoints are fully enabled.
              Generate a codebase from project specifications and design artifacts to initialize version v1.
            </div>
          </div>
        </div>
        <div>
          <Button
            variant="primary"
            onClick={handleGenerateCode}
            disabled={isGeneratingCode || !selectedProjectId}
          >
            {isGeneratingCode ? (
              <>
                <Loader2 size={16} className="animate-spin" style={{ marginRight: '0.4rem' }} />
                Synthesizing Codebase...
              </>
            ) : (
              <>
                <Hammer size={16} style={{ marginRight: '0.4rem' }} />
                Generate Project Codebase
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Conceptual Stages Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: 'var(--space-md)',
        }}
      >
        {devStages.map((s) => (
          <Card key={s.stage} style={{ background: 'var(--bg-glass-card)' }}>
            <CardHeader>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                {s.icon}
                <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{s.stage}</span>
              </div>
              <CapabilityBadge status={s.badge} size="sm" />
            </CardHeader>
            <CardBody>
              <div style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
                {s.title}
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: 0, lineHeight: 1.4 }}>
                {s.description}
              </p>
            </CardBody>
          </Card>
        ))}
      </div>



      {/* CONFIRMATION MODALS */}
      {actionModalType && selectedVersion && (
        <Modal
          isOpen={true}
          title={
            actionModalType === 'activate'
              ? `Activate Version v${selectedVersion.version_number}`
              : `Rollback to Version v${selectedVersion.version_number}`
          }
          onClose={() => setActionModalType(null)}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
            <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
              {actionModalType === 'activate'
                ? `Designating v${selectedVersion.version_number} as active will mark the previous active version as SUPERSEDED. Are you sure?`
                : `Non-destructively rolling back will point the active release to v${selectedVersion.version_number}. Historical versions remain immutable.`}
            </p>
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.3rem' }}>
                Reason for change (optional audit trail):
              </label>
              <input
                type="text"
                value={actionReason}
                onChange={(e) => setActionReason(e.target.value)}
                placeholder="e.g. Verified feature release"
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-primary)',
                  fontSize: '0.85rem',
                }}
              />
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
              <Button variant="secondary" onClick={() => setActionModalType(null)} disabled={actionSubmitting}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={actionModalType === 'activate' ? handleActivate : handleRollback}
                disabled={actionSubmitting}
              >
                {actionSubmitting ? 'Processing...' : actionModalType === 'activate' ? 'Confirm Activation' : 'Confirm Rollback'}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
