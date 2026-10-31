import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useProject } from '../context/ProjectContext';
import { codeStudioApi } from '../services/codeStudioApi';
import { developmentVersionApi } from '../services/developmentVersionApi';
import { projectsApi } from '../services/projectsApi';
import { previewRuntimeApi } from '../services/previewRuntimeApi';
import { FileTreeResponse } from '../types/codeStudio';
import { DevelopmentVersionResponse } from '../types/developmentVersion';
import { FileExplorer } from '../components/studio/FileExplorer';
import { CodeEditor } from '../components/studio/CodeEditor';
import { UnsavedChangesModal } from '../components/studio/UnsavedChangesModal';
import { ValidationPanel, ValidationPanelData } from '../components/studio/ValidationPanel';
import {
  Code2,
  GitBranch,
  Download,
  RefreshCw,
  Save,
  FolderKanban,
  AlertTriangle,
  PanelLeftClose,
  PanelLeftOpen,
  Monitor,
  ExternalLink,
  RotateCw,
  Smartphone,
  Tablet,
} from 'lucide-react';
import { NavigationTab } from '../components/layout/Sidebar';
import { workflowsApi } from '../services/workflowsApi';

interface CodeStudioWorkspaceProps {
  onNavigate?: (tab: NavigationTab) => void;
}

export const CodeStudioWorkspace: React.FC<CodeStudioWorkspaceProps> = ({ onNavigate }) => {
  const { selectedProjectId, selectedProject } = useProject();

  // Project versions state
  const [versions, setVersions] = useState<DevelopmentVersionResponse[]>([]);
  const [activeVersion, setActiveVersion] = useState<DevelopmentVersionResponse | null>(null);
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);

  // File tree state
  const [treeResponse, setTreeResponse] = useState<FileTreeResponse | null>(null);
  const [isLoadingTree, setIsLoadingTree] = useState<boolean>(false);
  const [treeError, setTreeError] = useState<string | null>(null);

  // Active file editor state
  const [activeFilePath, setActiveFilePath] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [initialContent, setInitialContent] = useState<string>('');
  const [fileLanguage, setFileLanguage] = useState<string>('plaintext');
  const [fileVersionId, setFileVersionId] = useState<string | null>(null);
  const [fileContentHash, setFileContentHash] = useState<string | null>(null);
  const [isLoadingFile, setIsLoadingFile] = useState<boolean>(false);
  const [isSavingFile, setIsSavingFile] = useState<boolean>(false);

  // Workspace layout state (Explorer collapse & Split Live Preview)
  const [isExplorerOpen, setIsExplorerOpen] = useState<boolean>(true);
  const [isPreviewSplitOpen, setIsPreviewSplitOpen] = useState<boolean>(false);
  const [previewViewport, setPreviewViewport] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');
  const [previewRefreshKey, setPreviewRefreshKey] = useState<number>(Date.now());
  const [runtimeStatus, setRuntimeStatus] = useState<string>('STOPPED');
  const [runtimePort, setRuntimePort] = useState<number>(8001);
  const [isStartingRuntime, setIsStartingRuntime] = useState<boolean>(false);

  // Validation output panel state
  const [validationData, setValidationData] = useState<ValidationPanelData | null>(null);

  // Unsaved changes protection modal state
  const [pendingFilePath, setPendingFilePath] = useState<string | null>(null);
  const [isUnsavedModalOpen, setIsUnsavedModalOpen] = useState<boolean>(false);

  // Code generation state for empty projects
  const [isGeneratingCode, setIsGeneratingCode] = useState<boolean>(false);
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState<boolean>(false);

  // Computed dirty state
  const isDirty = activeFilePath !== null && fileContent !== initialContent;

  // Track previous project ID to reset state on project switch
  const prevProjectIdRef = useRef<string | null>(null);

  // Reset state when project changes
  useEffect(() => {
    if (selectedProjectId !== prevProjectIdRef.current) {
      prevProjectIdRef.current = selectedProjectId || null;
      setActiveFilePath(null);
      setFileContent('');
      setInitialContent('');
      setFileVersionId(null);
      setFileContentHash(null);
      setValidationData(null);
      setSelectedVersionId(null);
      setIsUnsavedModalOpen(false);
      setPendingFilePath(null);
      setGenerationError(null);
      setIsPreviewSplitOpen(false);
    }
  }, [selectedProjectId]);

  // Load versions and file tree
  const loadWorkspaceData = useCallback(async (targetVersionId?: string) => {
    if (!selectedProjectId) {
      setTreeResponse(null);
      setVersions([]);
      setActiveVersion(null);
      return;
    }

    setIsLoadingTree(true);
    setTreeError(null);

    try {
      // 1. Fetch versions list
      const versList = await developmentVersionApi.list(selectedProjectId);
      setVersions(versList.items || []);

      const active =
        versList.items.find((v) => v.is_active) || versList.items[versList.items.length - 1] || null;
      setActiveVersion(active);

      const effectiveVersionId = targetVersionId || (active ? active.version_id : undefined);
      setSelectedVersionId(effectiveVersionId || null);

      // 2. Fetch hierarchical file tree
      const tree = await codeStudioApi.getFileTree(selectedProjectId, effectiveVersionId);
      setTreeResponse(tree);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Failed to load project files.';
      setTreeError(msg);
    } finally {
      setIsLoadingTree(false);
    }
  }, [selectedProjectId]);

  // Initial load
  useEffect(() => {
    loadWorkspaceData();
  }, [loadWorkspaceData]);

  // Check preview runtime status if split preview is open
  useEffect(() => {
    if (selectedProjectId && isPreviewSplitOpen) {
      previewRuntimeApi
        .getStatus(selectedProjectId)
        .then((res) => {
          setRuntimeStatus(res.status || 'STOPPED');
          setRuntimePort(res.port || 8001);
        })
        .catch(() => {
          setRuntimeStatus('STOPPED');
        });
    }
  }, [selectedProjectId, isPreviewSplitOpen, previewRefreshKey]);

  // Start preview runtime if requested from split preview pane
  const handleStartSplitRuntime = async () => {
    if (!selectedProjectId || isStartingRuntime) return;
    setIsStartingRuntime(true);
    try {
      const res = await previewRuntimeApi.start(selectedProjectId);
      setRuntimeStatus(res.status || 'RUNNING');
      setRuntimePort(res.port || 8001);
      setPreviewRefreshKey(Date.now());
    } catch (err: any) {
      alert(`Runtime start error: ${err?.message || 'Failed to start runtime'}`);
    } finally {
      setIsStartingRuntime(false);
    }
  };

  // Load individual file content
  const loadFile = async (path: string, versionId?: string) => {
    if (!selectedProjectId) return;
    setIsLoadingFile(true);
    try {
      const resp = await codeStudioApi.getFileContent(
        selectedProjectId,
        path,
        versionId || selectedVersionId || undefined
      );
      setActiveFilePath(resp.path);
      setFileContent(resp.content);
      setInitialContent(resp.content);
      setFileLanguage(resp.language);
      setFileVersionId(resp.version_id);
      setFileContentHash(resp.content_hash);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || `Failed to load '${path}'.`;
      setValidationData({
        status: 'error',
        message: msg,
        timestamp: new Date().toLocaleTimeString(),
      });
    } finally {
      setIsLoadingFile(false);
    }
  };

  // Safe file selection handler (guards unsaved changes)
  const handleSelectFile = (newPath: string) => {
    if (newPath === activeFilePath) return;

    if (isDirty) {
      setPendingFilePath(newPath);
      setIsUnsavedModalOpen(true);
      return;
    }

    loadFile(newPath);
  };

  // Save active file changes
  const handleSave = async () => {
    if (!selectedProjectId || !activeFilePath) return;

    // Use current fileVersionId or activeVersion id for optimistic concurrency
    const parentVerId = fileVersionId || activeVersion?.version_id;
    if (!parentVerId) {
      setValidationData({
        status: 'error',
        message: 'No active parent version found to base save operation on.',
        timestamp: new Date().toLocaleTimeString(),
      });
      return;
    }

    setIsSavingFile(true);

    try {
      const result = await codeStudioApi.saveFileContent(selectedProjectId, activeFilePath, {
        content: fileContent,
        parent_version_id: parentVerId,
        expected_content_hash: fileContentHash || undefined,
        reason: `Edited ${activeFilePath} in Code Studio`,
      });

      // Update baseline content to reset dirty state
      setInitialContent(fileContent);
      setFileVersionId(result.version_id);
      setFileContentHash(result.content_hash);

      // Refresh file tree and active version without closing editor
      await loadWorkspaceData(result.version_id);

      // Trigger preview update if preview split is open
      if (isPreviewSplitOpen) {
        setPreviewRefreshKey(Date.now());
      }

      // Update validation output panel
      setValidationData({
        status: 'success',
        message: result.message,
        stageOutcome: result.validation,
        newVersionNumber: result.version_number,
        newVersionId: result.version_id,
        timestamp: new Date().toLocaleTimeString(),
      });
    } catch (err: any) {
      const status = err?.response?.status || err?.status;
      const detail = err?.response?.data?.detail || err?.detail || err?.message || 'Save failed.';

      if (status === 409) {
        // Concurrency conflict: active version has advanced
        setValidationData({
          status: 'conflict',
          message: 'Conflict: This file was not saved because the project active version has changed.',
          conflictDetails: typeof detail === 'string' ? detail : JSON.stringify(detail),
          timestamp: new Date().toLocaleTimeString(),
        });
      } else if (status === 422) {
        // Validation error (e.g. Python syntax error)
        const errorsList: string[] = [];
        if (Array.isArray(err?.response?.data?.errors)) {
          err.response.data.errors.forEach((e: any) => {
            if (e.message) errorsList.push(e.message);
          });
        }
        setValidationData({
          status: 'syntax_error',
          message: typeof detail === 'string' ? detail : 'Syntax validation failed.',
          stageOutcome: {
            stage: 'syntax_validation',
            status: 'FAILED',
            message: typeof detail === 'string' ? detail : 'Syntax validation failed.',
            errors: errorsList.length > 0 ? errorsList : [String(detail)],
            warnings: [],
          },
          timestamp: new Date().toLocaleTimeString(),
        });
      } else {
        setValidationData({
          status: 'error',
          message: `Save error: ${typeof detail === 'string' ? detail : JSON.stringify(detail)}`,
          timestamp: new Date().toLocaleTimeString(),
        });
      }
    } finally {
      setIsSavingFile(false);
    }
  };

  // Unsaved modal action: Save & Proceed
  const handleModalSaveAndProceed = async () => {
    await handleSave();
    setIsUnsavedModalOpen(false);
    if (pendingFilePath) {
      loadFile(pendingFilePath);
      setPendingFilePath(null);
    }
  };

  // Unsaved modal action: Discard & Proceed
  const handleModalDiscardAndProceed = () => {
    setIsUnsavedModalOpen(false);
    if (pendingFilePath) {
      loadFile(pendingFilePath);
      setPendingFilePath(null);
    }
  };

  // Unsaved modal action: Cancel
  const handleModalCancel = () => {
    setIsUnsavedModalOpen(false);
    setPendingFilePath(null);
  };

  // Trigger code generation workflow for empty projects
  const handleGenerateInitialCode = async () => {
    if (!selectedProjectId || isGeneratingCode) return;
    setIsGeneratingCode(true);
    setGenerationError(null);
    setTreeError(null);
    try {
      const result = await workflowsApi.execute('code-generation-workflow', {
        project_id: selectedProjectId,
      });

      if (result.status === 'FAILED') {
        const errorMsg =
          result.errors && result.errors.length > 0
            ? result.errors.join('; ')
            : 'Code generation workflow failed. Please check the logs.';
        setGenerationError(errorMsg);
        setValidationData({
          status: 'error',
          message: `Generation failed: ${errorMsg}`,
          timestamp: new Date().toLocaleTimeString(),
        });
        return;
      }

      // Workflow succeeded or produced code
      await loadWorkspaceData();
      setGenerationError(null);
      setValidationData({
        status: 'success',
        message: 'Initial project code scaffold generated successfully.',
        timestamp: new Date().toLocaleTimeString(),
      });
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Failed to generate code.';
      setGenerationError(msg);
      setValidationData({
        status: 'error',
        message: `Generation error: ${msg}`,
        timestamp: new Date().toLocaleTimeString(),
      });
    } finally {
      setIsGeneratingCode(false);
    }
  };

  // Download project ZIP archive
  const handleDownloadZip = async () => {
    if (!selectedProjectId) return;
    setIsDownloading(true);
    try {
      await projectsApi.download(selectedProjectId, `${selectedProject?.slug || 'project'}.zip`);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Download failed.';
      setValidationData({
        status: 'error',
        message: msg,
        timestamp: new Date().toLocaleTimeString(),
      });
    } finally {
      setIsDownloading(false);
    }
  };

  if (!selectedProjectId) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          backgroundColor: 'var(--bg-primary, #0a0d14)',
          color: 'var(--text-secondary, #94a3b8)',
          padding: '32px',
          textAlign: 'center',
        }}
      >
        <FolderKanban
          size={48}
          color="var(--border-medium, rgba(255, 255, 255, 0.15))"
          style={{ marginBottom: '16px' }}
        />
        <h2
          style={{
            margin: '0 0 8px 0',
            color: 'var(--text-primary, #ffffff)',
            fontSize: '18px',
            fontWeight: 700,
          }}
        >
          Select a Project
        </h2>
        <p
          style={{
            margin: '0 0 16px 0',
            fontSize: '13px',
            maxWidth: '360px',
            color: 'var(--text-muted, #94a3b8)',
            lineHeight: 1.5,
          }}
        >
          Please select an active project from the top navigation to inspect and edit its source code in
          Code Studio.
        </p>
        {onNavigate && (
          <button
            type="button"
            onClick={() => onNavigate('projects')}
            style={{
              padding: '8px 18px',
              fontSize: '12px',
              fontWeight: 650,
              backgroundColor: 'var(--accent-gradient, linear-gradient(135deg, #7c3aed, #6366f1))',
              color: '#ffffff',
              border: 'none',
              borderRadius: 'var(--radius-sm, 6px)',
              cursor: 'pointer',
              boxShadow: '0 2px 8px rgba(124, 58, 237, 0.35)',
            }}
          >
            Browse Projects
          </button>
        )}
      </div>
    );
  }

  const hasGeneratedCode = treeResponse?.has_generated_code ?? false;
  const isVersionHistorical =
    activeVersion && selectedVersionId && activeVersion.version_id !== selectedVersionId;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: 'var(--bg-primary, #0a0d14)',
        overflow: 'hidden',
      }}
    >
      {/* Top Studio Toolbar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 16px',
          backgroundColor: 'var(--bg-surface-subtle, #0d121f)',
          borderBottom: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
          minHeight: '48px',
          gap: '12px',
          flexWrap: 'nowrap',
          overflowX: 'auto',
        }}
      >
        {/* Project & Version Info */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
          {/* Toggle Explorer Button */}
          <button
            type="button"
            onClick={() => setIsExplorerOpen((prev) => !prev)}
            title={isExplorerOpen ? 'Collapse Project Explorer' : 'Expand Project Explorer'}
            style={{
              background: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
              color: 'var(--text-muted, #94a3b8)',
              cursor: 'pointer',
              padding: '5px 7px',
              borderRadius: 'var(--radius-sm, 6px)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.15s ease',
            }}
          >
            {isExplorerOpen ? <PanelLeftClose size={14} /> : <PanelLeftOpen size={14} />}
          </button>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div
              style={{
                width: 24,
                height: 24,
                borderRadius: '5px',
                background: 'linear-gradient(135deg, var(--accent-violet, #8b5cf6), var(--accent-primary, #6366f1))',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 2px 6px rgba(139, 92, 246, 0.3)',
              }}
            >
              <Code2 size={14} color="#ffffff" />
            </div>
            <span
              style={{
                fontWeight: 750,
                fontSize: '13px',
                color: 'var(--text-primary, #ffffff)',
                letterSpacing: '-0.01em',
              }}
            >
              Code Studio
            </span>
          </div>

          <span style={{ color: 'var(--border-medium, rgba(255, 255, 255, 0.15))' }}>|</span>

          <span
            style={{
              fontSize: '13px',
              fontWeight: 650,
              color: 'var(--text-secondary, #cbd5e1)',
              maxWidth: '180px',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
            title={selectedProject?.name || 'Project'}
          >
            {selectedProject?.name || 'Project'}
          </span>

          {/* Active Version Badge */}
          {activeVersion && (
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: '2px 8px',
                borderRadius: '9999px',
                fontSize: '11px',
                fontWeight: 650,
                backgroundColor: 'rgba(139, 92, 246, 0.16)',
                color: 'var(--accent-violet-light, #a78bfa)',
                border: '1px solid rgba(139, 92, 246, 0.35)',
              }}
            >
              <GitBranch size={11} />
              <span>v{activeVersion.version_number} (Active)</span>
            </div>
          )}

          {/* Version Switcher Dropdown */}
          {versions.length > 1 && (
            <select
              aria-label="Select development version"
              value={selectedVersionId || ''}
              onChange={(e) => {
                const targetId = e.target.value;
                if (isDirty) {
                  alert('Please save or discard your unsaved changes before switching versions.');
                  return;
                }
                loadWorkspaceData(targetId);
                setActiveFilePath(null);
              }}
              style={{
                backgroundColor: 'var(--bg-surface-elevated, #1a2238)',
                color: 'var(--text-primary, #ffffff)',
                border: '1px solid var(--border-medium, rgba(255, 255, 255, 0.12))',
                borderRadius: 'var(--radius-sm, 6px)',
                fontSize: '11px',
                padding: '3px 8px',
                outline: 'none',
                cursor: 'pointer',
              }}
            >
              {versions.map((v) => (
                <option key={v.version_id} value={v.version_id}>
                  v{v.version_number} {v.is_active ? '(Active)' : `(${v.status})`}
                </option>
              ))}
            </select>
          )}

          {isVersionHistorical && (
            <span
              style={{
                padding: '2px 6px',
                borderRadius: '4px',
                fontSize: '10px',
                fontWeight: 650,
                backgroundColor: 'rgba(245, 158, 11, 0.15)',
                color: '#f59e0b',
                border: '1px solid rgba(245, 158, 11, 0.3)',
              }}
            >
              HISTORICAL SNAPSHOT
            </span>
          )}
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
          {/* Toggle Split Live Preview */}
          <button
            type="button"
            onClick={() => setIsPreviewSplitOpen((prev) => !prev)}
            title={isPreviewSplitOpen ? 'Close Live Preview Split Pane' : 'Open Live Preview Split Pane'}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
              padding: '5px 10px',
              borderRadius: 'var(--radius-sm, 6px)',
              fontSize: '12px',
              fontWeight: 600,
              backgroundColor: isPreviewSplitOpen
                ? 'rgba(16, 185, 129, 0.16)'
                : 'rgba(255, 255, 255, 0.04)',
              color: isPreviewSplitOpen ? '#34d399' : 'var(--text-secondary, #cbd5e1)',
              border: isPreviewSplitOpen
                ? '1px solid rgba(16, 185, 129, 0.4)'
                : '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
              cursor: 'pointer',
              boxShadow: isPreviewSplitOpen ? '0 0 10px rgba(16, 185, 129, 0.2)' : 'none',
              transition: 'all 0.15s ease',
            }}
          >
            <Monitor size={13} color={isPreviewSplitOpen ? '#34d399' : 'inherit'} />
            <span>Split Preview</span>
          </button>

          <button
            type="button"
            onClick={() => loadWorkspaceData(selectedVersionId || undefined)}
            disabled={isLoadingTree}
            title="Refresh workspace files"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
              padding: '5px 10px',
              borderRadius: 'var(--radius-sm, 6px)',
              fontSize: '12px',
              backgroundColor: 'rgba(255, 255, 255, 0.04)',
              color: 'var(--text-secondary, #cbd5e1)',
              border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
              cursor: isLoadingTree ? 'not-allowed' : 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            <RefreshCw
              size={13}
              style={{ animation: isLoadingTree ? 'spin 1s linear infinite' : 'none' }}
            />
            <span>Refresh</span>
          </button>

          {hasGeneratedCode && (
            <button
              type="button"
              onClick={handleDownloadZip}
              disabled={isDownloading}
              title="Download project as ZIP package"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                padding: '5px 12px',
                borderRadius: 'var(--radius-sm, 6px)',
                fontSize: '12px',
                fontWeight: 600,
                backgroundColor: 'var(--bg-surface-elevated, #1a2238)',
                color: 'var(--text-primary, #ffffff)',
                border: '1px solid var(--border-medium, rgba(255, 255, 255, 0.12))',
                cursor: isDownloading ? 'not-allowed' : 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              <Download size={13} color="#38bdf8" />
              <span>{isDownloading ? 'Packaging...' : 'Download ZIP'}</span>
            </button>
          )}

          {activeFilePath && !isVersionHistorical && (
            <button
              type="button"
              onClick={handleSave}
              disabled={isSavingFile || !isDirty}
              title="Save changes to backend (Ctrl+S / Cmd+S)"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '5px 14px',
                borderRadius: 'var(--radius-sm, 6px)',
                fontSize: '12px',
                fontWeight: 650,
                backgroundColor: isDirty
                  ? 'var(--accent-gradient, linear-gradient(135deg, #7c3aed, #6366f1))'
                  : 'var(--bg-surface-elevated, #1a2238)',
                color: isDirty ? '#ffffff' : 'var(--text-dim, #64748b)',
                border: 'none',
                cursor: isDirty && !isSavingFile ? 'pointer' : 'default',
                opacity: isSavingFile ? 0.7 : 1,
                boxShadow: isDirty ? '0 2px 10px rgba(124, 58, 237, 0.35)' : 'none',
                transition: 'all 0.15s ease',
              }}
            >
              <Save size={13} />
              <span>{isSavingFile ? 'Saving...' : 'Save File'}</span>
            </button>
          )}
        </div>
      </div>

      {treeError && (
        <div
          style={{
            backgroundColor: 'rgba(239, 68, 68, 0.12)',
            borderBottom: '1px solid rgba(239, 68, 68, 0.3)',
            padding: '6px 16px',
            color: '#ef4444',
            fontSize: '12px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <AlertTriangle size={14} />
          <span>{treeError}</span>
        </div>
      )}

      {/* Main Workspace Workspace Layout */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left Panel: File Explorer */}
        {isExplorerOpen && (
          <div
            style={{
              width: '260px',
              flexShrink: 0,
              height: '100%',
              transition: 'width 0.2s ease',
            }}
          >
            <FileExplorer
              rootNodes={treeResponse?.root_nodes || []}
              selectedFilePath={activeFilePath}
              dirtyFilePath={isDirty ? activeFilePath : null}
              onSelectFile={handleSelectFile}
              onRefresh={() => loadWorkspaceData(selectedVersionId || undefined)}
              isLoading={isLoadingTree}
              hasGeneratedCode={hasGeneratedCode}
              onGenerateCode={handleGenerateInitialCode}
              isGeneratingCode={isGeneratingCode}
              generationError={generationError}
            />
          </div>
        )}

        {/* Center Panel: Code Editor */}
        <div
          style={{
            flex: isPreviewSplitOpen ? 1.2 : 1,
            display: 'flex',
            flexDirection: 'column',
            height: '100%',
            overflow: 'hidden',
            borderRight: isPreviewSplitOpen
              ? '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))'
              : 'none',
          }}
        >
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <CodeEditor
              filePath={activeFilePath}
              content={fileContent}
              language={fileLanguage}
              isDirty={isDirty}
              isLoading={isLoadingFile}
              isSaving={isSavingFile}
              isReadOnly={Boolean(isVersionHistorical)}
              onChangeContent={(val) => setFileContent(val)}
              onSave={handleSave}
              onCreateFirstFile={() => {
                setActiveFilePath('main.py');
                setFileContent('# Entrypoint: main.py\n\ndef main():\n    print("Hello from SE IntelliPlatform!")\n\nif __name__ == "__main__":\n    main()\n');
                setFileLanguage('python');
                setInitialContent('');
              }}
              onGenerateScaffolding={handleGenerateInitialCode}
              isGeneratingScaffolding={isGeneratingCode}
              onCloseTab={() => {
                if (isDirty) {
                  if (confirm('Close file without saving changes?')) {
                    setActiveFilePath(null);
                  }
                } else {
                  setActiveFilePath(null);
                }
              }}
            />
          </div>

          {/* Bottom Panel: Validation & Build Output */}
          <ValidationPanel
            data={validationData}
            onReloadLatest={() => {
              if (activeFilePath) loadFile(activeFilePath);
            }}
            isReloading={isLoadingFile}
          />
        </div>

        {/* Right Panel: Integrated Live Preview Split View */}
        {isPreviewSplitOpen && (
          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              height: '100%',
              backgroundColor: 'var(--bg-secondary, #0f1422)',
              overflow: 'hidden',
            }}
          >
            {/* Split Preview Header */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '6px 12px',
                backgroundColor: 'var(--bg-surface-subtle, #0d121f)',
                borderBottom: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
                minHeight: '38px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Monitor size={14} color="#34d399" />
                <span
                  style={{
                    fontSize: '12px',
                    fontWeight: 700,
                    color: 'var(--text-primary, #ffffff)',
                  }}
                >
                  Live Preview
                </span>
                <span
                  style={{
                    fontSize: '10px',
                    fontWeight: 650,
                    padding: '2px 6px',
                    borderRadius: '4px',
                    backgroundColor:
                      runtimeStatus === 'RUNNING' || runtimeStatus === 'HEALTHY'
                        ? 'rgba(16, 185, 129, 0.16)'
                        : 'rgba(239, 68, 68, 0.16)',
                    color:
                      runtimeStatus === 'RUNNING' || runtimeStatus === 'HEALTHY'
                        ? '#34d399'
                        : '#ef4444',
                    border:
                      runtimeStatus === 'RUNNING' || runtimeStatus === 'HEALTHY'
                        ? '1px solid rgba(16, 185, 129, 0.3)'
                        : '1px solid rgba(239, 68, 68, 0.3)',
                  }}
                >
                  {runtimeStatus} :{runtimePort}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                {/* Viewport controls */}
                <button
                  type="button"
                  onClick={() => setPreviewViewport('desktop')}
                  title="Desktop View"
                  style={{
                    background: previewViewport === 'desktop' ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                    border: 'none',
                    color: previewViewport === 'desktop' ? '#ffffff' : 'var(--text-dim, #64748b)',
                    padding: '3px',
                    cursor: 'pointer',
                    borderRadius: '4px',
                  }}
                >
                  <Monitor size={13} />
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewViewport('tablet')}
                  title="Tablet View"
                  style={{
                    background: previewViewport === 'tablet' ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                    border: 'none',
                    color: previewViewport === 'tablet' ? '#ffffff' : 'var(--text-dim, #64748b)',
                    padding: '3px',
                    cursor: 'pointer',
                    borderRadius: '4px',
                  }}
                >
                  <Tablet size={13} />
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewViewport('mobile')}
                  title="Mobile View"
                  style={{
                    background: previewViewport === 'mobile' ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                    border: 'none',
                    color: previewViewport === 'mobile' ? '#ffffff' : 'var(--text-dim, #64748b)',
                    padding: '3px',
                    cursor: 'pointer',
                    borderRadius: '4px',
                  }}
                >
                  <Smartphone size={13} />
                </button>

                <button
                  type="button"
                  onClick={() => setPreviewRefreshKey(Date.now())}
                  title="Reload Preview"
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-muted, #94a3b8)',
                    padding: '3px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  <RotateCw size={13} />
                </button>

                {onNavigate && (
                  <button
                    type="button"
                    onClick={() => onNavigate('preview')}
                    title="Open Fullscreen Preview Tab"
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--accent-violet-light, #a78bfa)',
                      padding: '3px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                    }}
                  >
                    <ExternalLink size={13} />
                  </button>
                )}
              </div>
            </div>

            {/* Preview Iframe Container */}
            <div
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: '#05070d',
                overflow: 'hidden',
                padding: '8px',
              }}
            >
              {runtimeStatus === 'STOPPED' || runtimeStatus === 'FAILED' ? (
                <div
                  style={{
                    textAlign: 'center',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '24px',
                    color: 'var(--text-muted, #94a3b8)',
                  }}
                >
                  <Monitor size={36} color="var(--border-medium, rgba(255, 255, 255, 0.15))" />
                  <span style={{ fontSize: '13px', fontWeight: 650, color: 'var(--text-primary, #ffffff)' }}>
                    Preview Runtime Stopped
                  </span>
                  <span style={{ fontSize: '11px', maxWidth: '240px', lineHeight: 1.4 }}>
                    Start the isolated Docker preview runtime on port {runtimePort} to view the live application.
                  </span>
                  <button
                    type="button"
                    onClick={handleStartSplitRuntime}
                    disabled={isStartingRuntime}
                    style={{
                      marginTop: '6px',
                      padding: '6px 14px',
                      borderRadius: 'var(--radius-sm, 6px)',
                      fontSize: '11px',
                      fontWeight: 650,
                      backgroundColor: 'rgba(16, 185, 129, 0.18)',
                      color: '#34d399',
                      border: '1px solid rgba(16, 185, 129, 0.35)',
                      cursor: isStartingRuntime ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {isStartingRuntime ? 'Starting Container...' : 'Start Runtime Container'}
                  </button>
                </div>
              ) : (
                <div
                  style={{
                    width:
                      previewViewport === 'mobile'
                        ? '375px'
                        : previewViewport === 'tablet'
                        ? '768px'
                        : '100%',
                    height: '100%',
                    borderRadius: 'var(--radius-sm, 6px)',
                    overflow: 'hidden',
                    border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
                    backgroundColor: '#ffffff',
                    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.5)',
                  }}
                >
                  <iframe
                    key={previewRefreshKey}
                    src={`http://127.0.0.1:${runtimePort}/`}
                    title="Live Application Preview"
                    style={{
                      width: '100%',
                      height: '100%',
                      border: 'none',
                    }}
                  />
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Unsaved Changes Confirmation Modal */}
      <UnsavedChangesModal
        isOpen={isUnsavedModalOpen}
        filePath={activeFilePath}
        onSaveAndProceed={handleModalSaveAndProceed}
        onDiscardAndProceed={handleModalDiscardAndProceed}
        onCancel={handleModalCancel}
        isSaving={isSavingFile}
      />
    </div>
  );
};
