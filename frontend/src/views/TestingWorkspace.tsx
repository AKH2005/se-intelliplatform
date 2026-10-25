import React, { useEffect, useState } from 'react';
import { Card, CardBody, CardHeader } from '../components/common/Card';
import { CapabilityBadge } from '../components/common/CapabilityBadge';
import { Button } from '../components/common/Button';
import { EmptyState } from '../components/common/EmptyState';
import { useProject } from '../context/ProjectContext';
import {
  FlaskConical,
  Bug,
  Code2,
  FileCheck2,
  Play,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Globe,
  Loader2,
  Image as ImageIcon,
  Check,
  XCircle,
  Clock,
  Terminal,
  Network,
  Wrench,
  X,
  Compass,
  Sparkles,
  Layers,
  RefreshCw,
} from 'lucide-react';
import { NavigationTab } from '../components/layout/Sidebar';
import { browserTestingApi } from '../services/browserTestingApi';
import { developmentVersionApi } from '../services/developmentVersionApi';
import { BrowserTestRun } from '../types/browserTesting';
import { DevelopmentVersionResponse } from '../types/developmentVersion';
import {
  BrowserJourneyStatus,
  BrowserJourneyCoverage,
  BrowserJourneyList,
  BrowserJourneyDetail,
  BrowserJourneyFailure,
  BrowserJourneyEmptyState,
  useBrowserJourneys,
} from '../components/browser-journeys';
import { testingApi } from '../services/testingApi';
import {
  UnifiedTestInventory,
  UnifiedCoverageReport,
  CoverageGapsResponse,
  RegressionPlan,
} from '../types/testing';
import {
  TestInventoryView,
  CoverageDashboardView,
  CoverageGapsView,
  ChangeImpactView,
  RegressionPlannerView,
  RegressionExecutionView,
} from '../components/testing';

interface TestingWorkspaceProps {
  onNavigate?: (tab: NavigationTab) => void;
}

export const TestingWorkspace: React.FC<TestingWorkspaceProps> = ({ onNavigate }) => {
  const { selectedProjectId } = useProject();
  const [activeCategory, setActiveCategory] = useState<'analysis' | 'browser' | 'journeys' | 'regression' | 'execution'>('analysis');
  const [maxJourneys, setMaxJourneys] = useState<number>(10);
  const [executeBrowserTests, setExecuteBrowserTests] = useState<boolean>(true);

  // Phase 11L: Testing Intelligence State
  const [testingSubTab, setTestingSubTab] = useState<'inventory' | 'coverage' | 'gaps' | 'impact' | 'planner' | 'execution'>('inventory');
  const [testInventory, setTestInventory] = useState<UnifiedTestInventory | null>(null);
  const [coverageReport, setCoverageReport] = useState<UnifiedCoverageReport | null>(null);
  const [coverageGaps, setCoverageGaps] = useState<CoverageGapsResponse | null>(null);
  const [currentPlan, setCurrentPlan] = useState<RegressionPlan | null>(null);
  const [plannedChangedFiles, setPlannedChangedFiles] = useState<string[]>([]);
  const [isLoadingInventory, setIsLoadingInventory] = useState<boolean>(false);
  const [isLoadingCoverage, setIsLoadingCoverage] = useState<boolean>(false);
  const [isLoadingGaps, setIsLoadingGaps] = useState<boolean>(false);
  const [testingError, setTestingError] = useState<string | null>(null);

  // Browser journeys state (Phase 11K Stage 6)
  const {
    workflowResult: journeyResult,
    journeys,
    selectedJourney,
    setSelectedJourney,
    isLoading: isLoadingJourneys,
    isGenerating: isGeneratingJourneys,
    error: journeyError,
    fetchLatest: fetchLatestJourneys,
    generate: generateJourneys,
  } = useBrowserJourneys({ projectId: selectedProjectId });

  // Browser Testing State
  const [versions, setVersions] = useState<DevelopmentVersionResponse[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<string>('');
  const [browserRun, setBrowserRun] = useState<BrowserTestRun | null>(null);
  const [isLoadingVersions, setIsLoadingVersions] = useState<boolean>(false);
  const [isLoadingRun, setIsLoadingRun] = useState<boolean>(false);
  const [isRunningTests, setIsRunningTests] = useState<boolean>(false);
  const [errorNotice, setErrorNotice] = useState<string | null>(null);
  const [selectedScreenshotUrl, setSelectedScreenshotUrl] = useState<string | null>(null);

  // Load versions when project changes
  useEffect(() => {
    if (!selectedProjectId) {
      setVersions([]);
      setSelectedVersionId('');
      setBrowserRun(null);
      return;
    }

    let isMounted = true;
    setIsLoadingVersions(true);
    setErrorNotice(null);

    developmentVersionApi
      .listVersions(selectedProjectId)
      .then((res) => {
        if (!isMounted) return;
        const items = res.items || [];
        setVersions(items);
        if (items.length > 0) {
          const activeVer = items.find((v) => v.is_active) || items[0];
          setSelectedVersionId(activeVer.version_id);
        } else {
          setSelectedVersionId('');
        }
      })
      .catch((err) => {
        if (!isMounted) return;
        setErrorNotice(err?.message || 'Failed to load project versions');
      })
      .finally(() => {
        if (isMounted) setIsLoadingVersions(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedProjectId]);

  // Load latest browser run whenever selected version changes
  useEffect(() => {
    if (!selectedProjectId || !selectedVersionId) {
      setBrowserRun(null);
      return;
    }

    let isMounted = true;
    setIsLoadingRun(true);

    browserTestingApi
      .getLatestBrowserTestRun(selectedProjectId, selectedVersionId)
      .then((run) => {
        if (isMounted) setBrowserRun(run);
      })
      .catch(() => {
        if (isMounted) setBrowserRun(null);
      })
      .finally(() => {
        if (isMounted) setIsLoadingRun(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedProjectId, selectedVersionId]);

  // Phase 11L Loaders
  const loadTestingInventory = async () => {
    if (!selectedProjectId) return;
    setIsLoadingInventory(true);
    setTestingError(null);
    try {
      const inv = await testingApi.getTestInventory(selectedProjectId, selectedVersionId || undefined);
      setTestInventory(inv);
    } catch (err: any) {
      setTestingError(err?.message || 'Failed to fetch test inventory');
    } finally {
      setIsLoadingInventory(false);
    }
  };

  const loadTestingCoverage = async () => {
    if (!selectedProjectId) return;
    setIsLoadingCoverage(true);
    setTestingError(null);
    try {
      const cov = await testingApi.getCoverage(selectedProjectId, selectedVersionId || undefined);
      setCoverageReport(cov);
    } catch (err: any) {
      setTestingError(err?.message || 'Failed to calculate coverage');
    } finally {
      setIsLoadingCoverage(false);
    }
  };

  const loadTestingGaps = async () => {
    if (!selectedProjectId) return;
    setIsLoadingGaps(true);
    setTestingError(null);
    try {
      const gaps = await testingApi.getCoverageGaps(selectedProjectId, selectedVersionId || undefined);
      setCoverageGaps(gaps);
    } catch (err: any) {
      setTestingError(err?.message || 'Failed to fetch coverage gaps');
    } finally {
      setIsLoadingGaps(false);
    }
  };

  // Trigger Phase 11L loading when regression tab becomes active or version/project changes
  useEffect(() => {
    if (activeCategory === 'regression' && selectedProjectId) {
      loadTestingInventory();
      loadTestingCoverage();
      loadTestingGaps();
    }
  }, [activeCategory, selectedProjectId, selectedVersionId]);

  const handleRunBrowserTests = async () => {
    if (!selectedProjectId || isRunningTests) return;

    setIsRunningTests(true);
    setErrorNotice(null);

    try {
      const run = await browserTestingApi.runBrowserTests(selectedProjectId, {
        development_version_id: selectedVersionId || undefined,
      });
      setBrowserRun(run);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Failed to execute browser tests';
      setErrorNotice(msg);
    } finally {
      setIsRunningTests(false);
    }
  };

  const handleGenerateJourneys = async () => {
    if (!selectedProjectId || isGeneratingJourneys) return;
    await generateJourneys({
      development_version_id: selectedVersionId || undefined,
      execute_browser_tests: executeBrowserTests,
      max_journeys: maxJourneys,
    });
  };

  if (!selectedProjectId) {
    return (
      <EmptyState
        title="No Active Project Selected"
        description="Select or create a project to inspect quality reports, test generation artifacts, and browser testing plans."
      />
    );
  }

  const analysisCapabilities = [
    {
      title: 'Test Case Generation Agent',
      agentId: 'test-case-generation',
      status: 'IMPLEMENTED' as const,
      icon: <FileCheck2 size={18} color="var(--accent-cyan)" />,
      description:
        'Derives structured unit, integration, and edge-case test specifications directly from requirements and architecture.',
      detail:
        'Analyzes requirements to formulate parameterized test assertions, inputs, expected outputs, and preconditions.',
    },
    {
      title: 'Bug Prediction Agent',
      agentId: 'bug-prediction',
      status: 'IMPLEMENTED' as const,
      icon: <Bug size={18} color="var(--status-failed)" />,
      description:
        'Machine learning and heuristic assessment of defect-prone components and high-risk software modules.',
      detail:
        'Scores defect probability across architectural components and highlights fault hazard spots.',
    },
    {
      title: 'Code Review Agent',
      agentId: 'code-review',
      status: 'IMPLEMENTED' as const,
      icon: <Code2 size={18} color="var(--sdlc-design)" />,
      description:
        'Static analysis and policy enforcement for security, maintainability, and code style compliance.',
      detail:
        'Inspects submitted code files against architectural rules, flagging potential vulnerabilities and anti-patterns.',
    },
    {
      title: 'Explainability & Audit Agent',
      agentId: 'explainability',
      status: 'IMPLEMENTED' as const,
      icon: <ShieldCheck size={18} color="var(--status-completed)" />,
      description:
        'Detailed audit trail and rationale synthesis explaining analytical outcomes and decisions.',
      detail:
        'Traces decision rationale so engineers understand why specific tests, risks, or architectural patterns were recommended.',
    },
  ];

  const executionCapabilities = [
    {
      title: 'Automated Pytest & Jest Sandbox Runner',
      status: 'IMPLEMENTED' as const,
      icon: <Play size={18} color="var(--accent-primary)" />,
      description:
        'Execution of synthesized test cases inside isolated Linux container environments.',
      detail:
        'Executes pytest and vitest suites against generated microservice code and collects live stdout/stderr results.',
    },
    {
      title: 'End-to-End Application Testing',
      status: 'IMPLEMENTED' as const,
      icon: <FlaskConical size={18} color="var(--accent-cyan)" />,
      description:
        'Full-stack integration testing with simulated user sessions and API endpoint probing.',
      detail:
        'Headless browser and API gateway integration runs validating full user journeys.',
    },
    {
      title: 'Automated Regression Suites',
      status: 'IMPLEMENTED' as const,
      icon: <AlertTriangle size={18} color="var(--status-completed)" />,
      description:
        'Continuous regression verification detecting unexpected behavior drifts after code or requirement mutations.',
      detail:
        'Ensures that subsequent code edits or requirement alterations do not invalidate previously verified test passes.',
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xl)' }}>
      {/* Workspace Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700 }}>Testing & Quality Workspace</h1>
          <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Multi-stage verification environment with deterministic Playwright UI smoke testing and analytical quality gates.
          </p>
        </div>

        {onNavigate && (
          <Button
            variant="secondary"
            size="sm"
            icon={<Play size={15} />}
            onClick={() => onNavigate('workflows')}
          >
            Workflow Studio
          </Button>
        )}
      </div>

      {/* Distinction Alert Banner */}
      <div
        style={{
          padding: 'var(--space-md)',
          borderRadius: 'var(--radius-md)',
          background: 'rgba(56, 189, 248, 0.08)',
          border: '1px solid rgba(56, 189, 248, 0.25)',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '0.75rem',
          fontSize: '0.85rem',
          color: 'var(--text-secondary)',
        }}
      >
        <ShieldCheck size={20} color="var(--accent-cyan)" style={{ flexShrink: 0, marginTop: '0.1rem' }} />
        <div>
          <strong style={{ color: 'var(--text-primary)' }}>Architectural Distinction: Analysis vs Execution</strong>
          <div style={{ marginTop: '0.2rem', lineHeight: 1.5 }}>
            Current analytical capabilities provide <strong>Test-Case Generation and Static Analysis</strong>.
            Live test execution executes deterministic <strong>Playwright Browser Smoke Tests</strong> in isolated Docker containers.
          </div>
        </div>
      </div>

      {/* Mode Filter Tabs */}
      <div className="tabs-nav" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={activeCategory === 'analysis'}
          className={`tab-btn ${activeCategory === 'analysis' ? 'active' : ''}`}
          onClick={() => setActiveCategory('analysis')}
        >
          <CheckCircle2 size={16} color="var(--status-completed)" />
          <span>Analytical Capabilities (Implemented)</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeCategory === 'browser'}
          className={`tab-btn ${activeCategory === 'browser' ? 'active' : ''}`}
          onClick={() => setActiveCategory('browser')}
        >
          <Globe size={16} color="var(--accent-cyan)" />
          <span>Browser Smoke Tests (Playwright)</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeCategory === 'journeys'}
          className={`tab-btn ${activeCategory === 'journeys' ? 'active' : ''}`}
          onClick={() => setActiveCategory('journeys')}
        >
          <Compass size={16} color="var(--accent-cyan)" />
          <span>Intelligent Browser Journeys</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeCategory === 'regression'}
          className={`tab-btn ${activeCategory === 'regression' ? 'active' : ''}`}
          onClick={() => setActiveCategory('regression')}
        >
          <Layers size={16} color="var(--accent-primary)" />
          <span>Testing Intelligence & Regression</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeCategory === 'execution'}
          className={`tab-btn ${activeCategory === 'execution' ? 'active' : ''}`}
          onClick={() => setActiveCategory('execution')}
        >
          <CheckCircle2 size={16} color="var(--status-completed)" />
          <span>Test Execution Engine</span>
        </button>
      </div>

      {/* Error Notice */}
      {errorNotice && (
        <div
          data-testid="browser-error-banner"
          style={{
            padding: 'var(--space-md)',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(239, 68, 68, 0.08)',
            border: '1px solid rgba(239, 68, 68, 0.35)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '0.75rem',
            fontSize: '0.85rem',
            color: 'var(--status-failed)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertTriangle size={18} />
            <span>{errorNotice}</span>
          </div>
          <button
            type="button"
            onClick={() => setErrorNotice(null)}
            style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* 1. BROWSER SMOKE TESTING TAB (Phase 11J Stage 5) */}
      {/* ------------------------------------------------------------------- */}
      {activeCategory === 'browser' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
          {/* Controls Card */}
          <Card style={{ background: 'var(--bg-glass-card)' }}>
            <CardHeader>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Globe size={18} color="var(--accent-cyan)" />
                <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>Browser Smoke Testing Controls</span>
              </div>
              <CapabilityBadge status="IMPLEMENTED" size="sm" />
            </CardHeader>
            <CardBody>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '1rem',
                }}
              >
                {/* Version Selector */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <label htmlFor="browser-version-select" style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    Target Version:
                  </label>
                  {isLoadingVersions ? (
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Loading versions...</span>
                  ) : versions.length > 0 ? (
                    <select
                      id="browser-version-select"
                      data-testid="browser-version-select"
                      value={selectedVersionId}
                      onChange={(e) => setSelectedVersionId(e.target.value)}
                      disabled={isRunningTests}
                      style={{
                        padding: '0.4rem 0.75rem',
                        borderRadius: 'var(--radius-sm)',
                        background: 'var(--bg-surface-elevated)',
                        color: 'var(--text-primary)',
                        border: '1px solid var(--border-subtle)',
                        fontSize: '0.85rem',
                      }}
                    >
                      {versions.map((v) => (
                        <option key={v.version_id} value={v.version_id}>
                          v{v.version_number} ({v.status}){v.is_active ? ' — Active' : ''}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-dim)' }}>
                      No versions generated yet. Generate code first.
                    </span>
                  )}
                </div>

                {/* Run Button */}
                <Button
                  data-testid="run-browser-tests-btn"
                  variant="primary"
                  onClick={handleRunBrowserTests}
                  disabled={isRunningTests || !selectedVersionId}
                  icon={isRunningTests ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
                >
                  {isRunningTests ? 'Running Browser Tests...' : 'Run Browser Tests'}
                </Button>
              </div>

              {/* Informational Subtext */}
              <div
                style={{
                  marginTop: 'var(--space-md)',
                  fontSize: '0.78rem',
                  color: 'var(--text-muted)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                }}
              >
                <ShieldCheck size={14} color="var(--status-completed)" />
                <span>
                  Isolated container execution on ephemeral internal bridge network with zero WAN access and deterministic Playwright Chromium automation.
                </span>
              </div>
            </CardBody>
          </Card>

          {/* Running State Indicator */}
          {isRunningTests && (
            <Card style={{ background: 'var(--bg-glass-card)', textAlign: 'center', padding: '2rem' }}>
              <Loader2 size={32} className="animate-spin" style={{ margin: '0 auto', color: 'var(--accent-cyan)' }} />
              <h3 style={{ margin: '1rem 0 0.25rem 0', fontSize: '1.1rem' }}>Executing Browser Smoke Tests</h3>
              <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Launching containerized application and headless Playwright Chromium to verify routes, navigation, and console health...
              </p>
            </Card>
          )}

          {/* Test Results Section */}
          {!isRunningTests && isLoadingRun && (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
              Loading browser test results...
            </div>
          )}

          {!isRunningTests && !isLoadingRun && !browserRun && (
            <EmptyState
              title="No Browser Test Run Available"
              description="No browser smoke test run has been executed for this version yet. Click 'Run Browser Tests' above to execute tests in an isolated Docker container."
            />
          )}

          {!isRunningTests && !isLoadingRun && browserRun && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
              {/* Summary Metrics Bar */}
              <div
                data-testid="browser-summary-bar"
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                  gap: 'var(--space-md)',
                }}
              >
                <Card style={{ background: 'var(--bg-glass-card)' }}>
                  <CardBody>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                      Session Status
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.35rem' }}>
                      {browserRun.status === 'PASSED' ? (
                        <CheckCircle2 size={20} color="var(--status-completed)" />
                      ) : (
                        <XCircle size={20} color="var(--status-failed)" />
                      )}
                      <span
                        data-testid="browser-run-status"
                        style={{
                          fontWeight: 700,
                          fontSize: '1.1rem',
                          color: browserRun.status === 'PASSED' ? 'var(--status-completed)' : 'var(--status-failed)',
                        }}
                      >
                        {browserRun.status}
                      </span>
                    </div>
                  </CardBody>
                </Card>

                <Card style={{ background: 'var(--bg-glass-card)' }}>
                  <CardBody>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                      Tests Passed
                    </div>
                    <div style={{ marginTop: '0.35rem', fontSize: '1.25rem', fontWeight: 700 }}>
                      <span style={{ color: 'var(--status-completed)' }}>{browserRun.tests_passed}</span>
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}> / {browserRun.tests_total}</span>
                    </div>
                  </CardBody>
                </Card>

                <Card style={{ background: 'var(--bg-glass-card)' }}>
                  <CardBody>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                      Tests Failed
                    </div>
                    <div style={{ marginTop: '0.35rem', fontSize: '1.25rem', fontWeight: 700 }}>
                      <span style={{ color: browserRun.tests_failed > 0 ? 'var(--status-failed)' : 'var(--text-primary)' }}>
                        {browserRun.tests_failed}
                      </span>
                    </div>
                  </CardBody>
                </Card>

                <Card style={{ background: 'var(--bg-glass-card)' }}>
                  <CardBody>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                      Elapsed Duration
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.35rem' }}>
                      <Clock size={16} color="var(--text-muted)" />
                      <span style={{ fontSize: '1.1rem', fontWeight: 600 }}>{browserRun.duration_seconds}s</span>
                    </div>
                  </CardBody>
                </Card>
              </div>

              {/* High-Level Outcome Banner */}
              <div
                style={{
                  padding: 'var(--space-md)',
                  borderRadius: 'var(--radius-md)',
                  background:
                    browserRun.status === 'PASSED'
                      ? 'rgba(34, 197, 94, 0.08)'
                      : 'rgba(239, 68, 68, 0.08)',
                  border: `1px solid ${
                    browserRun.status === 'PASSED'
                      ? 'rgba(34, 197, 94, 0.3)'
                      : 'rgba(239, 68, 68, 0.3)'
                  }`,
                  fontSize: '0.85rem',
                  lineHeight: 1.5,
                }}
              >
                <strong>Outcome Summary:</strong> {browserRun.summary}
                {browserRun.failure_reason && (
                  <div style={{ marginTop: '0.4rem', color: 'var(--status-failed)', fontWeight: 500 }}>
                    <strong>Failure Diagnosis:</strong> {browserRun.failure_reason}
                  </div>
                )}
              </div>

              {/* Failed Remediation Handoff Banner */}
              {browserRun.status !== 'PASSED' && (
                <div
                  data-testid="remediation-handoff-banner"
                  style={{
                    padding: 'var(--space-md)',
                    borderRadius: 'var(--radius-md)',
                    background: 'rgba(245, 158, 11, 0.08)',
                    border: '1px solid rgba(245, 158, 11, 0.35)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: '1rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <Wrench size={20} color="var(--accent-amber)" />
                    <div>
                      <strong style={{ color: 'var(--text-primary)', fontSize: '0.88rem' }}>
                        Browser Smoke Tests Failed
                      </strong>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        Failure analysis has recorded root-cause evidence. Trigger a human-approved remediation workflow to generate a v2 fix.
                      </div>
                    </div>
                  </div>
                  {onNavigate && (
                    <Button
                      variant="primary"
                      size="sm"
                      icon={<Wrench size={14} />}
                      onClick={() => onNavigate('development')}
                    >
                      Inspect in Development
                    </Button>
                  )}
                </div>
              )}

              {/* Granular Test Case Cards */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
                <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>Test Case Outcomes</h3>
                {browserRun.test_cases.map((tc) => (
                  <Card key={tc.test_id} style={{ background: 'var(--bg-glass-card)' }}>
                    <CardHeader>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        {tc.status === 'PASSED' ? (
                          <Check size={16} color="var(--status-completed)" />
                        ) : (
                          <XCircle size={16} color="var(--status-failed)" />
                        )}
                        <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{tc.name}</span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>({tc.test_id})</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{tc.duration_seconds}s</span>
                        <span
                          style={{
                            fontSize: '0.72rem',
                            fontWeight: 600,
                            padding: '0.15rem 0.5rem',
                            borderRadius: 'var(--radius-sm)',
                            background:
                              tc.status === 'PASSED'
                                ? 'rgba(34, 197, 94, 0.15)'
                                : 'rgba(239, 68, 68, 0.15)',
                            color:
                              tc.status === 'PASSED'
                                ? 'var(--status-completed)'
                                : 'var(--status-failed)',
                          }}
                        >
                          {tc.status}
                        </span>
                      </div>
                    </CardHeader>
                    <CardBody>
                      {/* Assertion & Step Summary */}
                      {tc.assertion_summary && (
                        <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                          <strong>Assertion:</strong> {tc.assertion_summary}
                        </div>
                      )}
                      {tc.failed_step && (
                        <div style={{ fontSize: '0.82rem', color: 'var(--status-failed)', marginBottom: '0.5rem' }}>
                          <strong>Failed Step:</strong> {tc.failed_step}
                        </div>
                      )}

                      {/* Console Errors */}
                      {tc.console_errors && tc.console_errors.length > 0 && (
                        <div style={{ marginTop: '0.5rem' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.78rem', fontWeight: 600, color: 'var(--status-failed)' }}>
                            <Terminal size={14} />
                            <span>Browser Console Errors ({tc.console_errors.length}):</span>
                          </div>
                          <div
                            style={{
                              marginTop: '0.3rem',
                              padding: '0.5rem',
                              borderRadius: 'var(--radius-sm)',
                              background: 'var(--bg-surface-elevated)',
                              fontSize: '0.75rem',
                              fontFamily: 'monospace',
                              color: 'var(--text-secondary)',
                              maxHeight: '120px',
                              overflowY: 'auto',
                            }}
                          >
                            {tc.console_errors.map((ce, idx) => (
                              <div key={idx} style={{ marginBottom: '0.25rem', whiteSpace: 'pre-wrap' }}>
                                [{ce.level}] {ce.message}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Network Errors */}
                      {tc.network_errors && tc.network_errors.length > 0 && (
                        <div style={{ marginTop: '0.5rem' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.78rem', fontWeight: 600, color: 'var(--accent-amber)' }}>
                            <Network size={14} />
                            <span>Network Telemetry Failures ({tc.network_errors.length}):</span>
                          </div>
                          <div
                            style={{
                              marginTop: '0.3rem',
                              padding: '0.5rem',
                              borderRadius: 'var(--radius-sm)',
                              background: 'var(--bg-surface-elevated)',
                              fontSize: '0.75rem',
                              fontFamily: 'monospace',
                              color: 'var(--text-secondary)',
                            }}
                          >
                            {tc.network_errors.map((ne, idx) => (
                              <div key={idx} style={{ marginBottom: '0.2rem' }}>
                                {ne.method} {ne.url} &rarr; {ne.status_code} ({ne.failure_text || 'Error'})
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Screenshots for Case */}
                      {tc.screenshots && tc.screenshots.length > 0 && (
                        <div style={{ marginTop: '0.75rem' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                            <ImageIcon size={14} />
                            <span>Captured Step Screenshots:</span>
                          </div>
                          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                            {tc.screenshots.map((s) => {
                              const imgUrl = browserTestingApi.getScreenshotUrl(
                                selectedProjectId,
                                browserRun.run_id,
                                s.file_path
                              );
                              return (
                                <button
                                  type="button"
                                  key={s.artifact_id}
                                  onClick={() => setSelectedScreenshotUrl(imgUrl)}
                                  style={{
                                    border: '1px solid var(--border-subtle)',
                                    borderRadius: 'var(--radius-sm)',
                                    padding: '2px',
                                    background: 'var(--bg-surface-elevated)',
                                    cursor: 'pointer',
                                  }}
                                  title={s.caption || 'Screenshot thumbnail'}
                                >
                                  <img
                                    src={imgUrl}
                                    alt={s.caption || 'Step screenshot'}
                                    style={{ width: '90px', height: '56px', objectFit: 'cover', borderRadius: '2px', display: 'block' }}
                                  />
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </CardBody>
                  </Card>
                ))}
              </div>

              {/* Complete Screenshots Gallery */}
              {browserRun.artifacts && browserRun.artifacts.length > 0 && (
                <Card style={{ background: 'var(--bg-glass-card)' }}>
                  <CardHeader>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <ImageIcon size={18} color="var(--accent-cyan)" />
                      <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>
                        Complete Diagnostic Artifact Gallery ({browserRun.artifacts.length})
                      </span>
                    </div>
                  </CardHeader>
                  <CardBody>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
                      {browserRun.artifacts.map((art) => {
                        const imgUrl = browserTestingApi.getScreenshotUrl(
                          selectedProjectId,
                          browserRun.run_id,
                          art.file_path
                        );
                        return (
                          <div
                            key={art.artifact_id}
                            style={{
                              border: '1px solid var(--border-subtle)',
                              borderRadius: 'var(--radius-sm)',
                              overflow: 'hidden',
                              background: 'var(--bg-surface-elevated)',
                              cursor: 'pointer',
                            }}
                            onClick={() => setSelectedScreenshotUrl(imgUrl)}
                          >
                            <img
                              src={imgUrl}
                              alt={art.caption || 'Screenshot'}
                              style={{ width: '100%', height: '120px', objectFit: 'cover', display: 'block' }}
                            />
                            <div style={{ padding: '0.5rem', fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                              <div style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                {art.caption || art.artifact_id}
                              </div>
                              <div style={{ color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                                {(art.size_bytes / 1024).toFixed(1)} KB
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </CardBody>
                </Card>
              )}
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* 2. INTELLIGENT BROWSER JOURNEYS TAB (Phase 11K Stage 6) */}
      {/* ------------------------------------------------------------------- */}
      {activeCategory === 'journeys' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
          {/* Controls Card */}
          <Card style={{ background: 'var(--bg-glass-card)' }}>
            <CardHeader>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Compass size={18} color="var(--accent-cyan)" />
                <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>
                  Intelligent Browser Journey Synthesis & Execution Controls
                </span>
              </div>
              <CapabilityBadge status="IMPLEMENTED" size="sm" />
            </CardHeader>
            <CardBody>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '1rem',
                }}
              >
                {/* Left controls: Version, Max journeys, Execute toggle */}
                <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                  {/* Version Selector */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <label htmlFor="journey-version-select" style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      Target Version:
                    </label>
                    {isLoadingVersions ? (
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Loading...</span>
                    ) : versions.length > 0 ? (
                      <select
                        id="journey-version-select"
                        data-testid="journey-version-select"
                        value={selectedVersionId}
                        onChange={(e) => setSelectedVersionId(e.target.value)}
                        disabled={isGeneratingJourneys}
                        style={{
                          padding: '0.4rem 0.75rem',
                          borderRadius: 'var(--radius-sm)',
                          background: 'var(--bg-surface-elevated)',
                          color: 'var(--text-primary)',
                          border: '1px solid var(--border-subtle)',
                          fontSize: '0.85rem',
                        }}
                      >
                        {versions.map((v) => (
                          <option key={v.version_id} value={v.version_id}>
                            v{v.version_number} ({v.status}){v.is_active ? ' — Active' : ''}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-dim)' }}>
                        No version generated yet
                      </span>
                    )}
                  </div>

                  {/* Max Journeys Selector (1-10) */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <label htmlFor="max-journeys-select" style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      Max Journeys:
                    </label>
                    <select
                      id="max-journeys-select"
                      data-testid="max-journeys-select"
                      value={maxJourneys}
                      onChange={(e) => setMaxJourneys(Number(e.target.value))}
                      disabled={isGeneratingJourneys}
                      style={{
                        padding: '0.4rem 0.5rem',
                        borderRadius: 'var(--radius-sm)',
                        background: 'var(--bg-surface-elevated)',
                        color: 'var(--text-primary)',
                        border: '1px solid var(--border-subtle)',
                        fontSize: '0.85rem',
                      }}
                    >
                      {[1, 2, 3, 5, 8, 10].map((num) => (
                        <option key={num} value={num}>
                          {num}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Execute Browser Tests Checkbox */}
                  <label
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.4rem',
                      fontSize: '0.85rem',
                      color: 'var(--text-secondary)',
                      cursor: 'pointer',
                    }}
                  >
                    <input
                      type="checkbox"
                      data-testid="execute-browser-tests-toggle"
                      checked={executeBrowserTests}
                      onChange={(e) => setExecuteBrowserTests(e.target.checked)}
                      disabled={isGeneratingJourneys}
                    />
                    <span>Run browser tests after generation</span>
                  </label>
                </div>

                {/* Right controls: Generate Button and Refresh */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={fetchLatestJourneys}
                    disabled={isGeneratingJourneys || isLoadingJourneys}
                    icon={<RefreshCw size={14} className={isLoadingJourneys ? 'animate-spin' : ''} />}
                  >
                    Refresh
                  </Button>

                  <Button
                    data-testid="generate-browser-journeys-btn"
                    variant="primary"
                    onClick={handleGenerateJourneys}
                    disabled={isGeneratingJourneys}
                    icon={
                      isGeneratingJourneys ? (
                        <Loader2 size={16} className="animate-spin" />
                      ) : (
                        <Sparkles size={16} />
                      )
                    }
                  >
                    {isGeneratingJourneys ? 'Generating Journeys...' : 'Generate Browser Journeys'}
                  </Button>
                </div>
              </div>
            </CardBody>
          </Card>

          {/* Workflow Status Banner */}
          <BrowserJourneyStatus
            workflowResult={journeyResult}
            isGenerating={isGeneratingJourneys}
          />

          {/* Journey Error Banner if any */}
          {journeyError && (
            <div
              data-testid="journey-error-banner"
              style={{
                padding: 'var(--space-md)',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(239, 68, 68, 0.08)',
                border: '1px solid rgba(239, 68, 68, 0.35)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                fontSize: '0.85rem',
                color: 'var(--status-failed)',
              }}
            >
              <AlertTriangle size={18} />
              <span>{journeyError}</span>
            </div>
          )}

          {/* Failure Diagnostics if present */}
          <BrowserJourneyFailure workflowResult={journeyResult} />

          {/* If No Journeys and Not Generating -> Empty State */}
          {!journeyResult && !isGeneratingJourneys && (
            <BrowserJourneyEmptyState
              onGenerate={handleGenerateJourneys}
              isGenerating={isGeneratingJourneys}
            />
          )}

          {/* If Workflow Result exists */}
          {journeyResult && (
            <>
              {/* Authoritative Requirement Coverage */}
              <BrowserJourneyCoverage workflowResult={journeyResult} />

              {/* 2-Column Inspector: Journey List + Journey Detail */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'minmax(280px, 340px) 1fr',
                  gap: 'var(--space-md)',
                  alignItems: 'flex-start',
                }}
              >
                {/* Left Column: Journey List */}
                <Card style={{ background: 'var(--bg-glass-card)' }}>
                  <CardHeader>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <Layers size={16} color="var(--accent-cyan)" />
                      <span style={{ fontWeight: 600, fontSize: '0.88rem' }}>
                        Candidate Journeys ({journeys.length})
                      </span>
                    </div>
                  </CardHeader>
                  <CardBody style={{ maxHeight: '640px', overflowY: 'auto' }}>
                    <BrowserJourneyList
                      journeys={journeys}
                      selectedJourneyId={selectedJourney?.journey_id}
                      onSelectJourney={setSelectedJourney}
                    />
                  </CardBody>
                </Card>

                {/* Right Column: Journey Detail Inspector */}
                <Card style={{ background: 'var(--bg-glass-card)', minHeight: '380px' }}>
                  <CardHeader>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <Compass size={16} color="var(--accent-primary)" />
                      <span style={{ fontWeight: 600, fontSize: '0.88rem' }}>
                        Journey Details & Action Steps
                      </span>
                    </div>
                  </CardHeader>
                  <CardBody style={{ maxHeight: '640px', overflowY: 'auto' }}>
                    <BrowserJourneyDetail
                      journey={selectedJourney}
                      executionStatus={
                        journeyResult.browser_tests_passed === true
                          ? 'PASSED'
                          : journeyResult.browser_tests_passed === false
                          ? 'FAILED'
                          : null
                      }
                    />
                  </CardBody>
                </Card>
              </div>
            </>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* 4. PHASE 11L: TESTING INTELLIGENCE & REGRESSION DASHBOARD */}
      {/* ------------------------------------------------------------------- */}
      {activeCategory === 'regression' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
          {/* Top Scope & Version Controls Card */}
          <Card style={{ background: 'var(--bg-glass-card)' }}>
            <CardHeader>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Layers size={18} color="var(--accent-primary)" />
                <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>
                  Testing Intelligence Scope & Version Target
                </span>
              </div>
              <CapabilityBadge status="IMPLEMENTED" size="sm" />
            </CardHeader>
            <CardBody>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <label htmlFor="testing-version-select" style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    Target Version:
                  </label>
                  <select
                    id="testing-version-select"
                    data-testid="testing-version-select"
                    value={selectedVersionId}
                    onChange={(e) => setSelectedVersionId(e.target.value)}
                    style={{
                      padding: '0.4rem 0.75rem',
                      borderRadius: 'var(--radius-sm)',
                      background: 'var(--bg-surface-elevated)',
                      color: 'var(--text-primary)',
                      border: '1px solid var(--border-subtle)',
                      fontSize: '0.85rem',
                    }}
                  >
                    <option value="">Current Active Codebase (Baseline)</option>
                    {versions.map((v) => (
                      <option key={v.version_id} value={v.version_id}>
                        v{v.version_number} ({v.status}){v.is_active ? ' — Active' : ''}
                      </option>
                    ))}
                  </select>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Button
                    variant="secondary"
                    size="sm"
                    icon={<RefreshCw size={14} className={isLoadingInventory || isLoadingCoverage || isLoadingGaps ? 'spin' : ''} />}
                    onClick={() => {
                      loadTestingInventory();
                      loadTestingCoverage();
                      loadTestingGaps();
                    }}
                    disabled={isLoadingInventory || isLoadingCoverage || isLoadingGaps}
                  >
                    Refresh All Intelligence
                  </Button>
                </div>
              </div>

              {testingError && (
                <div
                  style={{
                    marginTop: '1rem',
                    padding: '0.75rem 1rem',
                    borderRadius: 'var(--radius-sm)',
                    background: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    color: 'var(--status-failed)',
                    fontSize: '0.85rem',
                  }}
                >
                  <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Testing Intelligence Error</div>
                  {testingError}
                </div>
              )}
            </CardBody>
          </Card>

          {/* Sub-Navigation Tabs */}
          <div className="tabs-nav" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={testingSubTab === 'inventory'}
              className={`tab-btn ${testingSubTab === 'inventory' ? 'active' : ''}`}
              onClick={() => setTestingSubTab('inventory')}
            >
              <FileCheck2 size={15} />
              <span>Test Inventory (11L-1)</span>
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={testingSubTab === 'coverage'}
              className={`tab-btn ${testingSubTab === 'coverage' ? 'active' : ''}`}
              onClick={() => setTestingSubTab('coverage')}
            >
              <ShieldCheck size={15} />
              <span>Coverage Intelligence (11L-2)</span>
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={testingSubTab === 'gaps'}
              className={`tab-btn ${testingSubTab === 'gaps' ? 'active' : ''}`}
              onClick={() => setTestingSubTab('gaps')}
            >
              <AlertTriangle size={15} />
              <span>Coverage Gaps</span>
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={testingSubTab === 'impact'}
              className={`tab-btn ${testingSubTab === 'impact' ? 'active' : ''}`}
              onClick={() => setTestingSubTab('impact')}
            >
              <Network size={15} />
              <span>Change Impact (11L-3)</span>
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={testingSubTab === 'planner'}
              className={`tab-btn ${testingSubTab === 'planner' ? 'active' : ''}`}
              onClick={() => setTestingSubTab('planner')}
            >
              <Layers size={15} />
              <span>Regression Planner (11L-4)</span>
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={testingSubTab === 'execution'}
              className={`tab-btn ${testingSubTab === 'execution' ? 'active' : ''}`}
              onClick={() => setTestingSubTab('execution')}
            >
              <Play size={15} />
              <span>Regression Execution (11L-5)</span>
            </button>
          </div>

          {/* Active Sub-Tab Content */}
          {testingSubTab === 'inventory' && (
            <TestInventoryView
              inventory={testInventory}
              isLoading={isLoadingInventory}
              onRefresh={loadTestingInventory}
              onSelectRequirement={() => setTestingSubTab('gaps')}
            />
          )}

          {testingSubTab === 'coverage' && (
            <CoverageDashboardView
              coverage={coverageReport}
              isLoading={isLoadingCoverage}
              onRefresh={loadTestingCoverage}
              onViewGaps={() => setTestingSubTab('gaps')}
              onSelectTest={() => setTestingSubTab('inventory')}
            />
          )}

          {testingSubTab === 'gaps' && (
            <CoverageGapsView
              gapsResponse={coverageGaps}
              isLoading={isLoadingGaps}
              onRefresh={loadTestingGaps}
              onSelectTest={() => setTestingSubTab('inventory')}
              onRequestAssistantGaps={() => {
                // Invokes contextual Assistant testing actions
              }}
            />
          )}

          {testingSubTab === 'impact' && (
            <ChangeImpactView
              projectId={selectedProjectId}
              selectedVersionId={selectedVersionId}
              onPlanRegressionWithImpact={(files) => {
                setPlannedChangedFiles(files);
                setTestingSubTab('planner');
              }}
            />
          )}

          {testingSubTab === 'planner' && (
            <RegressionPlannerView
              projectId={selectedProjectId}
              selectedVersionId={selectedVersionId}
              initialChangedFiles={plannedChangedFiles}
              currentPlan={currentPlan}
              onPlanGenerated={(p) => setCurrentPlan(p)}
              onProceedToExecution={() => setTestingSubTab('execution')}
            />
          )}

          {testingSubTab === 'execution' && (
            <RegressionExecutionView
              projectId={selectedProjectId}
              plan={currentPlan}
              selectedVersionId={selectedVersionId}
              onExecuteComplete={() => {
                loadTestingInventory();
                loadTestingCoverage();
              }}
            />
          )}
        </div>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* 5. ANALYTICAL CAPABILITIES TAB */}
      {/* ------------------------------------------------------------------- */}
      {activeCategory === 'analysis' && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: 'var(--space-md)',
          }}
        >
          {analysisCapabilities.map((cap) => (
            <Card key={cap.title} style={{ background: 'var(--bg-glass-card)' }}>
              <CardHeader>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  {cap.icon}
                  <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{cap.title}</span>
                </div>
                <CapabilityBadge status={cap.status} size="sm" />
              </CardHeader>
              <CardBody>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', marginBottom: '0.4rem' }}>
                  {cap.description}
                </div>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: 0, lineHeight: 1.4 }}>
                  {cap.detail}
                </p>
                <div style={{ marginTop: 'var(--space-md)', display: 'flex', justifyContent: 'flex-end' }}>
                  {onNavigate && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => onNavigate('workflows')}
                    >
                      Execute via Workflow Studio
                    </Button>
                  )}
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* 3. TEST EXECUTION CAPABILITIES TAB */}
      {/* ------------------------------------------------------------------- */}
      {activeCategory === 'execution' && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: 'var(--space-md)',
          }}
        >
          {executionCapabilities.map((cap) => (
            <Card key={cap.title} style={{ background: 'var(--bg-glass-card)', opacity: 0.9 }}>
              <CardHeader>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  {cap.icon}
                  <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{cap.title}</span>
                </div>
                <CapabilityBadge status={cap.status} size="sm" />
              </CardHeader>
              <CardBody>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', marginBottom: '0.4rem' }}>
                  {cap.description}
                </div>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: 0, lineHeight: 1.4 }}>
                  {cap.detail}
                </p>
                <div
                  style={{
                    marginTop: 'var(--space-md)',
                    padding: '0.4rem 0.65rem',
                    borderRadius: 'var(--radius-sm)',
                    background: 'rgba(16, 185, 129, 0.08)',
                    border: '1px solid rgba(16, 185, 129, 0.25)',
                    fontSize: '0.72rem',
                    color: '#10b981',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                  }}
                >
                  <ShieldCheck size={13} />
                  <span>Integrated with Isolated Sandbox Runner & Regression Engine</span>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}

      {/* Screenshot Enlarge Modal */}
      {selectedScreenshotUrl && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.75)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '2rem',
          }}
          onClick={() => setSelectedScreenshotUrl(null)}
        >
          <div
            style={{
              position: 'relative',
              maxWidth: '90vw',
              maxHeight: '90vh',
              background: 'var(--bg-surface-elevated)',
              borderRadius: 'var(--radius-md)',
              padding: '1rem',
              border: '1px solid var(--border-subtle)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              onClick={() => setSelectedScreenshotUrl(null)}
              style={{
                position: 'absolute',
                top: '0.5rem',
                right: '0.5rem',
                background: 'rgba(0, 0, 0, 0.5)',
                border: 'none',
                borderRadius: '50%',
                color: '#fff',
                padding: '0.25rem',
                cursor: 'pointer',
              }}
            >
              <X size={18} />
            </button>
            <img
              src={selectedScreenshotUrl}
              alt="Enlarged screenshot preview"
              style={{ maxWidth: '85vw', maxHeight: '80vh', objectFit: 'contain', display: 'block', borderRadius: '4px' }}
            />
          </div>
        </div>
      )}
    </div>
  );
};
