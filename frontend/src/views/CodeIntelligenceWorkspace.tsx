import React, { useState, useEffect, useCallback } from 'react';
import { useProject } from '../context/ProjectContext';
import { codeIntelligenceApi } from '../services/codeIntelligenceApi';
import {
  CodeIntelligenceSummaryResponse,
  DependencyGraphResponse,
  FileCodeIntelligenceResponse,
  LanguageInventoryResponse,
  TechnologyDetectionDto,
} from '../types/codeIntelligence';
import { NavigationTab } from '../components/layout/Sidebar';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { EmptyState } from '../components/common/EmptyState';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import {
  Code2,
  FileCode,
  Network,
  AlertTriangle,
  Layers,
  ArrowRight,
  CheckCircle2,
  RefreshCw,
  Search,
  Database,
  Cpu,
  Check,
  X,
} from 'lucide-react';

interface CodeIntelligenceWorkspaceProps {
  onNavigate?: (tab: NavigationTab) => void;
}

export const CodeIntelligenceWorkspace: React.FC<CodeIntelligenceWorkspaceProps> = () => {
  const { selectedProjectId } = useProject();

  const [summary, setSummary] = useState<CodeIntelligenceSummaryResponse | null>(null);
  const [languages, setLanguages] = useState<LanguageInventoryResponse | null>(null);
  const [technologies, setTechnologies] = useState<TechnologyDetectionDto[]>([]);
  const [graph, setGraph] = useState<DependencyGraphResponse | null>(null);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileDetails, setFileDetails] = useState<FileCodeIntelligenceResponse | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isLoadingFile, setIsLoadingFile] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [fileFilter, setFileFilter] = useState<string>('');
  const [activeSubTab, setActiveSubTab] = useState<'overview' | 'technologies' | 'file' | 'uncertainty'>('overview');

  const loadData = useCallback(async () => {
    if (!selectedProjectId) return;
    setIsLoading(true);
    setError(null);
    try {
      const [sumRes, langRes, graphRes, techRes] = await Promise.all([
        codeIntelligenceApi.getSummary(selectedProjectId),
        codeIntelligenceApi.getLanguages(selectedProjectId),
        codeIntelligenceApi.getGraph(selectedProjectId),
        codeIntelligenceApi.getTechnologies(selectedProjectId).catch(() => ({ project_id: selectedProjectId, technologies: [] })),
      ]);
      setSummary(sumRes);
      setLanguages(langRes);
      setGraph(graphRes);
      setTechnologies(techRes.technologies || []);

      // Auto-select first file if available
      const files = Object.keys(graphRes.forward_adjacency);
      setSelectedFile((prev) => {
        if (prev && files.includes(prev)) return prev;
        return files.length > 0 ? files[0] : null;
      });
    } catch (err: any) {
      setError(err?.message || 'Failed to load code intelligence data.');
    } finally {
      setIsLoading(false);
    }
  }, [selectedProjectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Load selected file details
  useEffect(() => {
    if (!selectedProjectId || !selectedFile) return;
    setIsLoadingFile(true);
    codeIntelligenceApi
      .getFileDetails(selectedProjectId, selectedFile)
      .then((res) => setFileDetails(res))
      .catch((err) => {
        console.warn('Could not load file intelligence:', err);
        setFileDetails(null);
      })
      .finally(() => setIsLoadingFile(false));
  }, [selectedProjectId, selectedFile]);

  if (!selectedProjectId) {
    return (
      <EmptyState
        title="No Active Project Selected"
        description="Select or create a project to inspect its polyglot AST code intelligence, symbol definitions, and dependency graph."
      />
    );
  }

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
        <LoadingSpinner label="Analyzing polyglot AST code intelligence..." />
      </div>
    );
  }

  const allFiles = Array.from(
    new Set([
      ...(graph ? Object.keys(graph.forward_adjacency) : []),
      ...(graph ? Object.keys(graph.reverse_adjacency) : []),
    ])
  ).sort();

  const filteredFiles = allFiles.filter((f) =>
    f.toLowerCase().includes(fileFilter.toLowerCase())
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          borderBottom: '1px solid var(--border-color, #333)',
          paddingBottom: '1rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700 }}>
              Polyglot Code Intelligence
            </h1>
            <Badge variant="info">AST Engine</Badge>
          </div>
          <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary, #888)', fontSize: '0.875rem' }}>
            Unified deterministic AST analysis across Python, JavaScript, TypeScript, and Java.
          </p>
        </div>

        <Button
          variant="secondary"
          size="sm"
          onClick={() => loadData()}
          icon={<RefreshCw size={14} />}
        >
          Re-Analyze
        </Button>
      </div>

      {error && <ErrorAlert error={error} />}

      {/* Top Metric Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1rem',
        }}
      >
        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary, #888)' }}>
            <FileCode size={18} />
            <span style={{ fontSize: '0.85rem' }}>Analyzed Files</span>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '0.5rem' }}>
            {summary?.total_files ?? 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted, #666)', marginTop: '0.25rem' }}>
            Across {Object.keys(languages?.counts || {}).length} languages
          </div>
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary, #888)' }}>
            <Code2 size={18} />
            <span style={{ fontSize: '0.85rem' }}>Total Symbols</span>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '0.5rem' }}>
            {summary?.total_symbols ?? 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted, #666)', marginTop: '0.25rem' }}>
            Classes, methods, interfaces, functions
          </div>
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary, #888)' }}>
            <Network size={18} />
            <span style={{ fontSize: '0.85rem' }}>Dependency Edges</span>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '0.5rem' }}>
            {summary?.total_edges ?? 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted, #666)', marginTop: '0.25rem' }}>
            Forward & reverse dependency links
          </div>
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary, #888)' }}>
            <AlertTriangle size={18} />
            <span style={{ fontSize: '0.85rem' }}>Uncertainties / Fallbacks</span>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '0.5rem' }}>
            {summary?.uncertain_dependencies_count ?? 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted, #666)', marginTop: '0.25rem' }}>
            Dynamic imports & reflection flags
          </div>
        </div>
      </div>

      {/* Language Breakdown Ribbon */}
      <div className="card" style={{ padding: '1.25rem' }}>
        <h3 style={{ margin: '0 0 1rem 0', fontSize: '1rem', fontWeight: 600 }}>
          Deterministic Language Detection
        </h3>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          {languages &&
            Object.entries(languages.counts).map(([lang, count]) => {
              const pct = languages.percentages[lang] || 0;
              const isSupported = languages.supported_languages.includes(lang.toUpperCase());
              return (
                <div
                  key={lang}
                  style={{
                    flex: '1 1 180px',
                    padding: '0.875rem',
                    borderRadius: '8px',
                    background: 'var(--bg-secondary, #1a1a24)',
                    border: '1px solid var(--border-color, #2a2a38)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>{lang}</span>
                    <Badge variant={isSupported ? 'success' : 'warning'}>
                      {isSupported ? 'SUPPORTED' : 'UNSUPPORTED'}
                    </Badge>
                  </div>
                  <div style={{ marginTop: '0.5rem', display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                    <span>{count} files</span>
                    <span style={{ color: 'var(--text-secondary, #888)' }}>{pct.toFixed(1)}%</span>
                  </div>
                  {/* Progress bar */}
                  <div
                    style={{
                      height: '4px',
                      background: 'var(--border-color, #333)',
                      borderRadius: '2px',
                      marginTop: '0.5rem',
                      overflow: 'hidden',
                    }}
                  >
                    <div
                      style={{
                        width: `${pct}%`,
                        height: '100%',
                        background: 'var(--color-primary, #6366f1)',
                      }}
                    />
                  </div>
                </div>
              );
            })}
        </div>
      </div>

      {/* Subtab Navigation */}
      <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--border-color, #333)' }}>
        <button
          onClick={() => setActiveSubTab('overview')}
          style={{
            padding: '0.625rem 1rem',
            background: 'none',
            border: 'none',
            borderBottom: activeSubTab === 'overview' ? '2px solid var(--color-primary, #6366f1)' : '2px solid transparent',
            color: activeSubTab === 'overview' ? 'var(--text-primary, #fff)' : 'var(--text-secondary, #888)',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Graph Explorer
        </button>
        <button
          onClick={() => setActiveSubTab('technologies')}
          style={{
            padding: '0.625rem 1rem',
            background: 'none',
            border: 'none',
            borderBottom: activeSubTab === 'technologies' ? '2px solid var(--color-primary, #6366f1)' : '2px solid transparent',
            color: activeSubTab === 'technologies' ? 'var(--text-primary, #fff)' : 'var(--text-secondary, #888)',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Technologies & Capabilities ({technologies.length})
        </button>
        <button
          onClick={() => setActiveSubTab('file')}
          style={{
            padding: '0.625rem 1rem',
            background: 'none',
            border: 'none',
            borderBottom: activeSubTab === 'file' ? '2px solid var(--color-primary, #6366f1)' : '2px solid transparent',
            color: activeSubTab === 'file' ? 'var(--text-primary, #fff)' : 'var(--text-secondary, #888)',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          File & Symbol Details
        </button>
        <button
          onClick={() => setActiveSubTab('uncertainty')}
          style={{
            padding: '0.625rem 1rem',
            background: 'none',
            border: 'none',
            borderBottom: activeSubTab === 'uncertainty' ? '2px solid var(--color-primary, #6366f1)' : '2px solid transparent',
            color: activeSubTab === 'uncertainty' ? 'var(--text-primary, #fff)' : 'var(--text-secondary, #888)',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Uncertainty & Diagnostics ({summary?.uncertain_dependencies_count ?? 0})
        </button>
      </div>

      {/* Content for Graph Explorer */}
      {activeSubTab === 'overview' && (
        <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '1.25rem' }}>
          {/* File Selector Sidebar */}
          <div className="card" style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'var(--bg-secondary, #1a1a24)', padding: '0.4rem 0.6rem', borderRadius: '6px' }}>
              <Search size={14} color="#888" />
              <input
                type="text"
                placeholder="Filter files..."
                value={fileFilter}
                onChange={(e) => setFileFilter(e.target.value)}
                style={{
                  background: 'none',
                  border: 'none',
                  outline: 'none',
                  color: 'inherit',
                  fontSize: '0.85rem',
                  width: '100%',
                }}
              />
            </div>

            <div style={{ maxHeight: '420px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              {filteredFiles.map((file) => {
                const isSelected = selectedFile === file;
                const ext = file.split('.').pop() || '';
                return (
                  <button
                    key={file}
                    onClick={() => setSelectedFile(file)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '0.5rem 0.75rem',
                      borderRadius: '6px',
                      background: isSelected ? 'var(--bg-tertiary, #2a2a3c)' : 'transparent',
                      border: 'none',
                      color: isSelected ? 'var(--color-primary, #6366f1)' : 'inherit',
                      textAlign: 'left',
                      cursor: 'pointer',
                      fontSize: '0.825rem',
                    }}
                  >
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {file}
                    </span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted, #666)', marginLeft: '0.5rem' }}>
                      .{ext}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Adjacency Detail */}
          <div className="card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {selectedFile ? (
              <>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color, #333)', paddingBottom: '0.75rem' }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '1.1rem' }}>{selectedFile}</h3>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary, #888)', marginTop: '0.25rem' }}>
                      Language: {fileDetails?.language || 'DETECTING'}
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => setActiveSubTab('file')}
                  >
                    View File Symbols
                  </Button>
                </div>

                {/* Direct Forward Dependencies */}
                <div>
                  <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem', color: 'var(--text-secondary, #888)' }}>
                    Forward Dependencies (Imports / Depends On):
                  </h4>
                  {graph && graph.forward_adjacency[selectedFile]?.length ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      {graph.forward_adjacency[selectedFile].map((dep) => (
                        <div
                          key={dep}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            padding: '0.5rem 0.75rem',
                            background: 'var(--bg-secondary, #1a1a24)',
                            borderRadius: '6px',
                            fontSize: '0.85rem',
                          }}
                        >
                          <ArrowRight size={14} color="#6366f1" />
                          <span>{dep}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-muted, #666)' }}>
                      No internal forward dependencies.
                    </div>
                  )}
                </div>

                {/* Direct Reverse Dependents */}
                <div>
                  <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem', color: 'var(--text-secondary, #888)' }}>
                    Reverse Dependents (Consumed By / Impacted Consumers):
                  </h4>
                  {graph && graph.reverse_adjacency[selectedFile]?.length ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      {graph.reverse_adjacency[selectedFile].map((rev) => (
                        <div
                          key={rev}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            padding: '0.5rem 0.75rem',
                            background: 'var(--bg-secondary, #1a1a24)',
                            borderRadius: '6px',
                            fontSize: '0.85rem',
                          }}
                        >
                          <Layers size={14} color="#10b981" />
                          <span>{rev}</span>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted, #888)', marginLeft: 'auto' }}>
                            (Affected on change)
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-muted, #666)' }}>
                      No project files depend on this file.
                    </div>
                  )}
                </div>
              </>
            ) : (
              <EmptyState title="No File Selected" description="Select a file from the list to view its dependency links." />
            )}
          </div>
        </div>
      )}

      {/* Content for Polyglot & Database Technologies Matrix */}
      {activeSubTab === 'technologies' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Header Description */}
          <div className="card" style={{ padding: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
              <Cpu size={20} color="var(--color-primary, #6366f1)" />
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>
                Polyglot & Database Capabilities Matrix
              </h3>
            </div>
            <p style={{ margin: 0, color: 'var(--text-secondary, #888)', fontSize: '0.875rem' }}>
              Deterministic technology detection separating general-purpose programming languages, web technologies, and database engines (Relational vs. Document paradigms). Reports honest, un-fabricated capabilities for each technology.
            </p>
          </div>

          {/* Grouped by Category */}
          {technologies.length === 0 ? (
            <div className="card" style={{ padding: '2rem', textAlign: 'center' }}>
              <EmptyState
                title="No Technologies Detected"
                description="No recognized programming languages, manifests, or database connection indicators were found in this project version."
              />
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {/* Database Technologies Section */}
              {technologies.some((t) => t.category === 'DATABASE_ENGINE') && (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                    <Database size={18} color="#06b6d4" />
                    <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600 }}>
                      Database Technologies & Engines
                    </h3>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1rem' }}>
                    {technologies
                      .filter((t) => t.category === 'DATABASE_ENGINE')
                      .map((tech) => (
                        <div
                          key={tech.name}
                          className="card"
                          style={{
                            padding: '1.25rem',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '0.75rem',
                            borderLeft: tech.paradigm === 'DOCUMENT' ? '4px solid #a855f7' : '4px solid #06b6d4',
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                            <div>
                              <div style={{ fontSize: '1.15rem', fontWeight: 700 }}>{tech.name}</div>
                              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary, #888)', marginTop: '0.2rem' }}>
                                Detection Confidence: {(tech.confidence * 100).toFixed(0)}%
                              </div>
                            </div>
                            <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                              <Badge variant={tech.paradigm === 'DOCUMENT' ? 'warning' : 'info'}>
                                {tech.paradigm || 'DATABASE'}
                              </Badge>
                              <Badge variant="neutral">Database Engine</Badge>
                            </div>
                          </div>

                          {tech.detected_drivers && tech.detected_drivers.length > 0 && (
                            <div>
                              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary, #888)', fontWeight: 600, marginBottom: '0.3rem' }}>
                                Detected Drivers & Adapters:
                              </div>
                              <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                                {tech.detected_drivers.map((drv) => (
                                  <span
                                    key={drv}
                                    style={{
                                      fontSize: '0.75rem',
                                      padding: '0.2rem 0.5rem',
                                      borderRadius: '4px',
                                      background: 'rgba(6, 182, 212, 0.1)',
                                      color: '#06b6d4',
                                      border: '1px solid rgba(6, 182, 212, 0.25)',
                                    }}
                                  >
                                    {drv}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          {tech.evidence && tech.evidence.length > 0 && (
                            <div>
                              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary, #888)', fontWeight: 600, marginBottom: '0.3rem' }}>
                                Concrete Evidence:
                              </div>
                              <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.8rem', color: 'var(--text-primary, #ddd)' }}>
                                {tech.evidence.map((ev, idx) => (
                                  <li key={idx} style={{ marginBottom: '0.2rem' }}>{ev}</li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {/* Capabilities Grid */}
                          <div style={{ borderTop: '1px solid var(--border-color, #2a2a38)', paddingTop: '0.75rem', marginTop: 'auto' }}>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted, #777)', fontWeight: 600, marginBottom: '0.4rem' }}>
                              Platform Capabilities:
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem', fontSize: '0.75rem' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: tech.capabilities.can_detect ? '#10b981' : '#6b7280' }}>
                                {tech.capabilities.can_detect ? <Check size={13} /> : <X size={13} />}
                                <span>Detection</span>
                              </div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: tech.capabilities.can_syntax_highlight ? '#10b981' : '#6b7280' }}>
                                {tech.capabilities.can_syntax_highlight ? <Check size={13} /> : <X size={13} />}
                                <span>Syntax Highlighting</span>
                              </div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: tech.capabilities.can_inspect_source ? '#10b981' : '#6b7280' }}>
                                {tech.capabilities.can_inspect_source ? <Check size={13} /> : <X size={13} />}
                                <span>Schema Inspection</span>
                              </div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: tech.capabilities.can_ast_analyze ? '#10b981' : '#6b7280' }}>
                                {tech.capabilities.can_ast_analyze ? <Check size={13} /> : <X size={13} />}
                                <span>AST Analysis</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {/* Programming Languages Section */}
              {technologies.some((t) => t.category === 'PROGRAMMING_LANGUAGE') && (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                    <Code2 size={18} color="#6366f1" />
                    <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600 }}>
                      Programming Languages & Frameworks
                    </h3>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1rem' }}>
                    {technologies
                      .filter((t) => t.category === 'PROGRAMMING_LANGUAGE')
                      .map((tech) => (
                        <div
                          key={tech.name}
                          className="card"
                          style={{
                            padding: '1.25rem',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '0.75rem',
                            borderLeft: '4px solid #6366f1',
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                            <div>
                              <div style={{ fontSize: '1.15rem', fontWeight: 700 }}>{tech.name}</div>
                              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary, #888)', marginTop: '0.2rem' }}>
                                Detection Confidence: {(tech.confidence * 100).toFixed(0)}%
                              </div>
                            </div>
                            <Badge variant="primary">Language</Badge>
                          </div>

                          {tech.detected_frameworks && tech.detected_frameworks.length > 0 && (
                            <div>
                              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary, #888)', fontWeight: 600, marginBottom: '0.3rem' }}>
                                Detected Frameworks:
                              </div>
                              <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                                {tech.detected_frameworks.map((fw) => (
                                  <span
                                    key={fw}
                                    style={{
                                      fontSize: '0.75rem',
                                      padding: '0.2rem 0.5rem',
                                      borderRadius: '4px',
                                      background: 'rgba(99, 102, 241, 0.1)',
                                      color: '#818cf8',
                                      border: '1px solid rgba(99, 102, 241, 0.25)',
                                    }}
                                  >
                                    {fw}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          {tech.evidence && tech.evidence.length > 0 && (
                            <div>
                              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary, #888)', fontWeight: 600, marginBottom: '0.3rem' }}>
                                Evidence:
                              </div>
                              <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.8rem', color: 'var(--text-primary, #ddd)' }}>
                                {tech.evidence.map((ev, idx) => (
                                  <li key={idx} style={{ marginBottom: '0.2rem' }}>{ev}</li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {/* Capabilities Grid */}
                          <div style={{ borderTop: '1px solid var(--border-color, #2a2a38)', paddingTop: '0.75rem', marginTop: 'auto' }}>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted, #777)', fontWeight: 600, marginBottom: '0.4rem' }}>
                              Platform Capabilities (Honest Verification):
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.4rem', fontSize: '0.75rem' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: tech.capabilities.can_syntax_highlight ? '#10b981' : '#6b7280' }}>
                                {tech.capabilities.can_syntax_highlight ? <Check size={13} /> : <X size={13} />}
                                <span>Syntax Highlighting</span>
                              </div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: tech.capabilities.can_ast_analyze ? '#10b981' : '#6b7280' }}>
                                {tech.capabilities.can_ast_analyze ? <Check size={13} /> : <X size={13} />}
                                <span>AST Analysis</span>
                              </div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: tech.capabilities.can_dependency_analyze ? '#10b981' : '#6b7280' }}>
                                {tech.capabilities.can_dependency_analyze ? <Check size={13} /> : <X size={13} />}
                                <span>Dependency Graph</span>
                              </div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: tech.capabilities.can_generate_code ? '#10b981' : '#6b7280' }}>
                                {tech.capabilities.can_generate_code ? <Check size={13} /> : <X size={13} />}
                                <span>AI Code Gen</span>
                              </div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: tech.capabilities.can_execute ? '#10b981' : '#6b7280' }}>
                                {tech.capabilities.can_execute ? <Check size={13} /> : <X size={13} />}
                                <span>Execution</span>
                              </div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: tech.capabilities.can_live_preview ? '#10b981' : '#6b7280' }}>
                                {tech.capabilities.can_live_preview ? <Check size={13} /> : <X size={13} />}
                                <span>Live Preview</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {/* Web Technologies Section */}
              {technologies.some((t) => t.category === 'WEB_TECHNOLOGY') && (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                    <Layers size={18} color="#10b981" />
                    <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600 }}>
                      Web Technologies & Data Formats
                    </h3>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '0.75rem' }}>
                    {technologies
                      .filter((t) => t.category === 'WEB_TECHNOLOGY')
                      .map((tech) => (
                        <div
                          key={tech.name}
                          className="card"
                          style={{
                            padding: '1rem',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '0.5rem',
                            borderLeft: '4px solid #10b981',
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontWeight: 700, fontSize: '1rem' }}>{tech.name}</span>
                            <Badge variant="success">Web / Data</Badge>
                          </div>
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary, #888)' }}>
                            {tech.evidence.join(', ')}
                          </div>
                          <div style={{ fontSize: '0.75rem', color: '#10b981', display: 'flex', alignItems: 'center', gap: '0.25rem', marginTop: '0.25rem' }}>
                            <Check size={12} /> Deterministic Parsing & Inspection
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Content for File & Symbol Details */}
      {activeSubTab === 'file' && (
        <div className="card" style={{ padding: '1.25rem' }}>
          {isLoadingFile ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
              <LoadingSpinner label="Extracting normalized symbols..." />
            </div>
          ) : fileDetails ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h3 style={{ margin: 0 }}>{fileDetails.file_path}</h3>
                  <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.4rem' }}>
                    <Badge variant="info">{fileDetails.language.toUpperCase()}</Badge>
                    {fileDetails.is_test_file && <Badge variant="warning">TEST FILE</Badge>}
                    {fileDetails.has_dynamic_constructs && <Badge variant="error">DYNAMIC CONSTRUCTS</Badge>}
                  </div>
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted, #666)' }}>
                  Hash: {fileDetails.content_hash.substring(0, 12)}...
                </div>
              </div>

              {/* Symbols Table */}
              <div>
                <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '0.95rem' }}>
                  {`Extracted Symbols (${fileDetails.symbols.length})`}
                </h4>
                {fileDetails.symbols.length > 0 ? (
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid var(--border-color, #333)', textAlign: 'left' }}>
                          <th style={{ padding: '0.5rem' }}>Name</th>
                          <th style={{ padding: '0.5rem' }}>Kind</th>
                          <th style={{ padding: '0.5rem' }}>Exported</th>
                          <th style={{ padding: '0.5rem' }}>Signature</th>
                          <th style={{ padding: '0.5rem' }}>Line</th>
                        </tr>
                      </thead>
                      <tbody>
                        {fileDetails.symbols.map((sym, idx) => (
                          <tr key={idx} style={{ borderBottom: '1px solid var(--border-color, #222)' }}>
                            <td style={{ padding: '0.5rem', fontWeight: 600 }}>{sym.name}</td>
                            <td style={{ padding: '0.5rem' }}>
                              <Badge variant="neutral">{sym.kind}</Badge>
                            </td>
                            <td style={{ padding: '0.5rem' }}>
                              {sym.is_exported ? (
                                <span style={{ color: '#10b981' }}>Yes</span>
                              ) : (
                                <span style={{ color: '#666' }}>No</span>
                              )}
                            </td>
                            <td style={{ padding: '0.5rem', fontFamily: 'monospace', color: '#888' }}>
                              {sym.signature || '—'}
                            </td>
                            <td style={{ padding: '0.5rem', color: '#666' }}>{sym.line_number ?? '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted, #666)' }}>
                    No symbols found in this file.
                  </div>
                )}
              </div>

              {/* Imports & Exports */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div style={{ background: 'var(--bg-secondary, #1a1a24)', padding: '1rem', borderRadius: '8px' }}>
                  <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem' }}>Imports ({fileDetails.imports.length})</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', maxHeight: '200px', overflowY: 'auto' }}>
                    {fileDetails.imports.map((imp, i) => (
                      <div key={i} style={{ fontSize: '0.8rem', display: 'flex', justifyContent: 'space-between' }}>
                        <span>{imp.module}</span>
                        {imp.is_dynamic && <Badge variant="warning">Dynamic</Badge>}
                      </div>
                    ))}
                  </div>
                </div>

                <div style={{ background: 'var(--bg-secondary, #1a1a24)', padding: '1rem', borderRadius: '8px' }}>
                  <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem' }}>Exports ({fileDetails.exports.length})</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', maxHeight: '200px', overflowY: 'auto' }}>
                    {fileDetails.exports.map((exp, i) => (
                      <div key={i} style={{ fontSize: '0.8rem', display: 'flex', justifyContent: 'space-between' }}>
                        <span>{exp.name}</span>
                        {exp.is_default && <Badge variant="info">Default</Badge>}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <EmptyState title="No File Selected" description="Select a file from the explorer to view detailed code symbols." />
          )}
        </div>
      )}

      {/* Content for Uncertainty & Diagnostics */}
      {activeSubTab === 'uncertainty' && (
        <div className="card" style={{ padding: '1.25rem' }}>
          <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem' }}>
            Uncertainty & Diagnostic Audits
          </h3>
          <p style={{ margin: '0 0 1rem 0', color: 'var(--text-secondary, #888)', fontSize: '0.875rem' }}>
            The platform enforces conservative regression safety: when dynamic constructs (reflection, dynamic imports, eval) are detected, regression planning falls back safely rather than producing false negatives.
          </p>

          {graph && graph.uncertain_dependencies.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {graph.uncertain_dependencies.map((u, i) => (
                <div
                  key={i}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '0.75rem',
                    padding: '0.875rem',
                    background: 'var(--bg-secondary, #1a1a24)',
                    borderLeft: '4px solid #f59e0b',
                    borderRadius: '4px',
                  }}
                >
                  <AlertTriangle size={18} color="#f59e0b" style={{ marginTop: '2px', flexShrink: 0 }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{u.reason}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary, #888)', marginTop: '0.2rem' }}>
                      File: {u.file_path} {u.line_number ? `(Line ${u.line_number})` : ''}
                    </div>
                    {u.raw_statement && (
                      <div
                        style={{
                          marginTop: '0.4rem',
                          fontFamily: 'monospace',
                          fontSize: '0.75rem',
                          background: '#0d0d14',
                          padding: '0.35rem 0.5rem',
                          borderRadius: '4px',
                          color: '#e2e8f0',
                        }}
                      >
                        {u.raw_statement}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '1.5rem',
                background: 'var(--bg-secondary, #1a1a24)',
                borderRadius: '8px',
                color: '#10b981',
              }}
            >
              <CheckCircle2 size={24} />
              <div>
                <div style={{ fontWeight: 600 }}>Zero Uncertainty Flags</div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary, #888)' }}>
                  All dependency edges in this project are deterministically resolvable.
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
