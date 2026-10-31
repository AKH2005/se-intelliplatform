import React, { useState, useMemo } from 'react';
import {
  Folder,
  FolderOpen,
  FileCode2,
  FileText,
  FileJson,
  Search,
  RefreshCw,
  ChevronRight,
  ChevronDown,
  Code2,
  Sparkles,
  FileSpreadsheet,
  Globe,
  Palette,
  File,
  AlertCircle,
  X,
} from 'lucide-react';
import { FileNode } from '../../types/codeStudio';

interface FileExplorerProps {
  rootNodes: FileNode[];
  selectedFilePath: string | null;
  dirtyFilePath: string | null;
  onSelectFile: (path: string) => void;
  onRefresh: () => void;
  isLoading: boolean;
  hasGeneratedCode: boolean;
  onGenerateCode?: () => void;
  isGeneratingCode?: boolean;
  generationError?: string | null;
}

// Helper to pick suitable icon based on file extension
const getFileIcon = (fileName: string, _language?: string) => {
  const ext = fileName.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'py':
      return <Code2 size={15} color="#38bdf8" />;
    case 'ts':
    case 'tsx':
      return <FileCode2 size={15} color="#818cf8" />;
    case 'js':
    case 'jsx':
      return <FileCode2 size={15} color="#fbbf24" />;
    case 'json':
      return <FileJson size={15} color="#34d399" />;
    case 'html':
    case 'htm':
      return <Globe size={15} color="#fb923c" />;
    case 'css':
    case 'scss':
      return <Palette size={15} color="#c084fc" />;
    case 'sql':
      return <FileSpreadsheet size={15} color="#f472b6" />;
    case 'md':
      return <FileText size={15} color="#94a3b8" />;
    default:
      return <File size={15} color="#94a3b8" />;
  }
};

const formatBytes = (bytes?: number): string => {
  if (bytes === undefined || bytes === null) return '';
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(1)} KB`;
};

export const FileExplorer: React.FC<FileExplorerProps> = ({
  rootNodes,
  selectedFilePath,
  dirtyFilePath,
  onSelectFile,
  onRefresh,
  isLoading,
  hasGeneratedCode,
  onGenerateCode,
  isGeneratingCode,
  generationError,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(() => {
    const initial = new Set<string>();
    rootNodes.forEach((node) => {
      if (node.type === 'directory') initial.add(node.path);
    });
    return initial;
  });

  // Automatically expand top-level folders when rootNodes are loaded
  React.useEffect(() => {
    if (rootNodes.length > 0) {
      setExpandedFolders((prev) => {
        const next = new Set(prev);
        rootNodes.forEach((node) => {
          if (node.type === 'directory') next.add(node.path);
        });
        return next;
      });
    }
  }, [rootNodes]);

  const toggleFolder = (path: string) => {
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  };

  // Filter nodes matching search query
  const filterNodes = (nodes: FileNode[], query: string): FileNode[] => {
    if (!query.trim()) return nodes;
    const lower = query.toLowerCase();

    const result: FileNode[] = [];
    for (const node of nodes) {
      if (node.type === 'file') {
        if (node.name.toLowerCase().includes(lower) || node.path.toLowerCase().includes(lower)) {
          result.push(node);
        }
      } else if (node.type === 'directory') {
        const filteredChildren = filterNodes(node.children || [], query);
        if (
          filteredChildren.length > 0 ||
          node.name.toLowerCase().includes(lower) ||
          node.path.toLowerCase().includes(lower)
        ) {
          result.push({
            ...node,
            children: filteredChildren,
          });
        }
      }
    }
    return result;
  };

  const visibleNodes = useMemo(() => {
    return filterNodes(rootNodes, searchQuery);
  }, [rootNodes, searchQuery]);

  // Expand all folders when searching
  React.useEffect(() => {
    if (searchQuery.trim()) {
      const allDirs = new Set<string>();
      const collectDirs = (nodes: FileNode[]) => {
        for (const n of nodes) {
          if (n.type === 'directory') {
            allDirs.add(n.path);
            if (n.children) collectDirs(n.children);
          }
        }
      };
      collectDirs(rootNodes);
      setExpandedFolders(allDirs);
    }
  }, [searchQuery, rootNodes]);

  const renderTree = (nodes: FileNode[], depth = 0) => {
    return (
      <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
        {nodes.map((node) => {
          const isDir = node.type === 'directory';
          const isExpanded = expandedFolders.has(node.path);
          const isSelected = selectedFilePath === node.path;
          const isDirty = dirtyFilePath === node.path;

          return (
            <li key={node.id} style={{ userSelect: 'none' }}>
              <div
                role="button"
                tabIndex={0}
                onClick={() => {
                  if (isDir) {
                    toggleFolder(node.path);
                  } else {
                    onSelectFile(node.path);
                  }
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    if (isDir) toggleFolder(node.path);
                    else onSelectFile(node.path);
                  }
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: `5px 8px 5px ${8 + depth * 14}px`,
                  cursor: 'pointer',
                  borderRadius: '4px',
                  margin: '1px 4px',
                  fontSize: '13px',
                  backgroundColor: isSelected
                    ? 'linear-gradient(90deg, rgba(139, 92, 246, 0.16) 0%, rgba(99, 102, 241, 0.05) 100%)'
                    : 'transparent',
                  color: isSelected ? '#ffffff' : 'var(--text-secondary, #cbd5e1)',
                  fontWeight: isSelected ? 650 : isDir ? 550 : 400,
                  borderLeft: isSelected
                    ? '2px solid var(--accent-violet, #8b5cf6)'
                    : '2px solid transparent',
                  boxShadow: isSelected ? 'inset 1px 0 0 0 rgba(167, 139, 250, 0.35)' : 'none',
                  transition: 'background-color 0.15s ease',
                }}
                className="file-explorer-row"
              >
                {/* Folder chevron or leaf spacer */}
                <span
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '16px',
                    marginRight: '4px',
                    color: 'var(--text-dim, #64748b)',
                  }}
                >
                  {isDir ? (
                    isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />
                  ) : (
                    <span style={{ width: '14px' }} />
                  )}
                </span>

                {/* Node icon */}
                <span style={{ marginRight: '6px', display: 'flex', alignItems: 'center' }}>
                  {isDir ? (
                    isExpanded ? (
                      <FolderOpen size={16} color="var(--accent-cyan, #06b6d4)" />
                    ) : (
                      <Folder size={16} color="var(--accent-violet-light, #a78bfa)" />
                    )
                  ) : (
                    getFileIcon(node.name, node.language)
                  )}
                </span>

                {/* Node name */}
                <span
                  style={{
                    flex: 1,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    letterSpacing: '-0.01em',
                  }}
                  title={node.path}
                >
                  {node.name}
                  {isDirty && (
                    <span
                      style={{
                        marginLeft: '5px',
                        color: 'var(--accent-amber, #fbbf24)',
                        fontWeight: 'bold',
                      }}
                      title="Unsaved changes"
                    >
                      *
                    </span>
                  )}
                </span>

                {/* File size indicator */}
                {!isDir && node.size_bytes !== undefined && (
                  <span
                    style={{
                      fontSize: '10px',
                      color: 'var(--text-dim, #64748b)',
                      marginLeft: '6px',
                      fontFamily: 'monospace',
                    }}
                  >
                    {formatBytes(node.size_bytes)}
                  </span>
                )}
              </div>

              {/* Render recursive children if folder is open */}
              {isDir && isExpanded && node.children && (
                <div>{renderTree(node.children, depth + 1)}</div>
              )}
            </li>
          );
        })}
      </ul>
    );
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: 'var(--bg-secondary, #0f1422)',
        borderRight: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
        overflow: 'hidden',
      }}
    >
      {/* Explorer Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 12px',
          borderBottom: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
          backgroundColor: 'var(--bg-surface-subtle, #0d121f)',
          minHeight: '38px',
        }}
      >
        <span
          style={{
            fontSize: '11px',
            fontWeight: 750,
            letterSpacing: '0.08em',
            color: 'var(--text-muted, #94a3b8)',
            textTransform: 'uppercase',
          }}
        >
          Files & Folders
        </span>
        <button
          type="button"
          onClick={onRefresh}
          disabled={isLoading}
          title="Refresh file tree"
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--text-muted, #94a3b8)',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            padding: '4px',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center',
            transition: 'color 0.15s ease',
          }}
        >
          <RefreshCw
            size={13}
            style={{
              animation: isLoading ? 'spin 1s linear infinite' : 'none',
            }}
          />
        </button>
      </div>

      {/* Search Input */}
      {hasGeneratedCode && (
        <div style={{ padding: '8px', borderBottom: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              backgroundColor: 'var(--bg-canvas, #07090e)',
              borderRadius: 'var(--radius-sm, 6px)',
              border: '1px solid var(--border-medium, rgba(255, 255, 255, 0.12))',
              padding: '4px 8px',
              boxShadow: 'inset 0 1px 2px rgba(0, 0, 0, 0.4)',
            }}
          >
            <Search size={13} color="var(--text-dim, #64748b)" style={{ marginRight: '6px', flexShrink: 0 }} />
            <input
              type="text"
              placeholder="Filter files..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                background: 'transparent',
                border: 'none',
                outline: 'none',
                color: 'var(--text-primary, #ffffff)',
                fontSize: '12px',
                width: '100%',
              }}
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-dim, #64748b)',
                  cursor: 'pointer',
                  padding: 0,
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                <X size={12} />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Explorer Content */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '4px 0',
        }}
      >
        {isLoading && rootNodes.length === 0 ? (
          <div
            style={{
              padding: '24px 16px',
              textAlign: 'center',
              color: 'var(--text-muted, #94a3b8)',
              fontSize: '12px',
            }}
          >
            <RefreshCw
              size={18}
              color="var(--accent-primary, #6366f1)"
              style={{ animation: 'spin 1s linear infinite', margin: '0 auto 8px auto' }}
            />
            <span>Loading project files...</span>
          </div>
        ) : null}

        {!isLoading && !hasGeneratedCode && rootNodes.length === 0 ? (
          <div
            style={{
              padding: '24px 16px',
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '10px',
            }}
          >
            <Folder size={36} color="var(--border-medium, rgba(255, 255, 255, 0.15))" />
            <h4
              style={{
                margin: 0,
                fontSize: '13px',
                fontWeight: 650,
                color: 'var(--text-primary, #ffffff)',
              }}
            >
              No Source Files Yet
            </h4>
            <p
              style={{
                margin: 0,
                fontSize: '11px',
                color: 'var(--text-muted, #94a3b8)',
                lineHeight: 1.5,
              }}
            >
              Source code has not yet been generated for this project.
            </p>

            {onGenerateCode && (
              <button
                type="button"
                onClick={onGenerateCode}
                disabled={isGeneratingCode}
                style={{
                  marginTop: '8px',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 14px',
                  borderRadius: 'var(--radius-sm, 6px)',
                  fontSize: '11px',
                  fontWeight: 650,
                  backgroundColor: 'var(--accent-gradient, linear-gradient(135deg, #7c3aed, #6366f1))',
                  color: '#ffffff',
                  border: 'none',
                  cursor: isGeneratingCode ? 'not-allowed' : 'pointer',
                  boxShadow: '0 2px 8px rgba(124, 58, 237, 0.35)',
                }}
              >
                <Sparkles size={13} />
                <span>{isGeneratingCode ? 'Generating...' : 'Generate Initial Code'}</span>
              </button>
            )}

            {generationError && (
              <div
                style={{
                  marginTop: '8px',
                  padding: '6px 10px',
                  borderRadius: '4px',
                  backgroundColor: 'rgba(239, 68, 68, 0.15)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  color: '#ef4444',
                  fontSize: '11px',
                  textAlign: 'left',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '6px',
                }}
              >
                <AlertCircle size={14} style={{ flexShrink: 0, marginTop: '2px' }} />
                <div>
                  <strong style={{ display: 'block', marginBottom: '2px' }}>Generation Failed</strong>
                  <span>{generationError}</span>
                </div>
              </div>
            )}
          </div>
        ) : null}

        {visibleNodes.length > 0 ? renderTree(visibleNodes) : null}

        {searchQuery && visibleNodes.length === 0 && (
          <div
            style={{
              padding: '24px 16px',
              textAlign: 'center',
              color: 'var(--text-dim, #64748b)',
              fontSize: '12px',
            }}
          >
            No matching files found.
          </div>
        )}
      </div>
    </div>
  );
};
