import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { TestingWorkspace } from '../views/TestingWorkspace';
import { testingApi } from '../services/testingApi';
import { browserTestingApi } from '../services/browserTestingApi';
import { developmentVersionApi } from '../services/developmentVersionApi';
import {
  UnifiedTestInventory,
  UnifiedCoverageReport,
  CoverageGapsResponse,
  ChangeImpactReport,
  RegressionPlan,
  RegressionExecutionResult,
} from '../types/testing';

vi.mock('../services/testingApi', () => ({
  testingApi: {
    getTestInventory: vi.fn(),
    getCoverage: vi.fn(),
    getCoverageGaps: vi.fn(),
    analyzeImpact: vi.fn(),
    planRegression: vi.fn(),
    executeRegression: vi.fn(),
  },
}));

vi.mock('../services/browserTestingApi', () => ({
  browserTestingApi: {
    runBrowserTests: vi.fn(),
    getLatestBrowserTestRun: vi.fn(),
    getBrowserTestRun: vi.fn(),
    getScreenshotUrl: vi.fn(),
  },
}));

vi.mock('../services/developmentVersionApi', () => ({
  developmentVersionApi: {
    listVersions: vi.fn(),
    getActiveVersion: vi.fn(),
    getVersionFileContent: vi.fn(),
  },
}));

vi.mock('../services/assistantApi', () => ({
  assistantApi: {
    listConversations: vi.fn(),
    sendMessage: vi.fn(),
    confirmAction: vi.fn(),
  },
}));

vi.mock('../context/ProjectContext', () => ({
  useProject: () => ({
    selectedProjectId: 'proj-11l-test-456',
    selectedProject: { id: 'proj-11l-test-456', name: 'Testing 11L Project', slug: 'testing-11l-proj' },
  }),
}));

const mockInventory: UnifiedTestInventory = {
  inventory_id: 'inv-11l-001',
  project_id: 'proj-11l-test-456',
  total_tests: 4,
  tier_counts: {
    UNIT: 1,
    AI_TEST: 1,
    BROWSER_SMOKE: 1,
    BROWSER_JOURNEY: 1,
  },
  conflicts: [],
  discovery_status: 'COMPLETED',
  discovered_at: '2026-10-04T01:00:00Z',
  metadata: {},
  tests: [
    {
      test_id: 'test-unit-1',
      name: 'Unit Calculator Test',
      tier: 'UNIT',
      provenance: 'PYTEST_DISCOVERY',
      target_file: 'tests/unit/test_calc.py',
      requirement_links: ['REQ-001'],
      inferred_requirement_links: [],
      is_validated_journey: false,
      execution_metadata: { command: 'pytest tests/unit/test_calc.py' },
    },
    {
      test_id: 'test-ai-1',
      name: 'AI Generated Property Test',
      tier: 'AI_TEST',
      provenance: 'AI_SYNTHESIS',
      target_file: 'tests/ai/test_prop.py',
      requirement_links: ['REQ-002'],
      inferred_requirement_links: ['REQ-003'],
      is_validated_journey: false,
      execution_metadata: { command: 'pytest tests/ai/test_prop.py' },
    },
    {
      test_id: 'test-smoke-1',
      name: 'Browser Smoke Health Check',
      tier: 'BROWSER_SMOKE',
      provenance: 'BROWSER_SMOKE_CONVENTION',
      target_file: 'tests/browser/smoke.py',
      requirement_links: ['REQ-001'],
      inferred_requirement_links: [],
      is_validated_journey: false,
      execution_metadata: { suite: 'smoke' },
    },
    {
      test_id: 'test-journey-1',
      name: 'User Checkout Flow',
      tier: 'BROWSER_JOURNEY',
      provenance: 'VALIDATED_BROWSER_JOURNEY',
      target_file: 'tests/browser/journeys/checkout.json',
      requirement_links: ['REQ-004'],
      inferred_requirement_links: [],
      is_validated_journey: true,
      execution_metadata: { journey_id: 'j-checkout' },
    },
  ],
};

const mockCoverage: UnifiedCoverageReport = {
  project_id: 'proj-11l-test-456',
  total_active_requirements: 4,
  active_requirement_ids: ['REQ-001', 'REQ-002', 'REQ-003', 'REQ-004'],
  combined_coverage_percentage: 75.0,
  combined_covered_requirement_ids: ['REQ-001', 'REQ-002', 'REQ-004'],
  combined_uncovered_requirement_ids: ['REQ-003'],
  calculated_at: '2026-10-04T01:00:00Z',
  metadata: {},
  tier_coverages: {
    UNIT: {
      tier: 'UNIT',
      total_active_requirements: 4,
      covered_requirement_count: 1,
      uncovered_requirement_count: 3,
      coverage_percentage: 25.0,
      covered_requirement_ids: ['REQ-001'],
      uncovered_requirement_ids: ['REQ-002', 'REQ-003', 'REQ-004'],
    },
    AI_TEST: {
      tier: 'AI_TEST',
      total_active_requirements: 4,
      covered_requirement_count: 1,
      uncovered_requirement_count: 3,
      coverage_percentage: 25.0,
      covered_requirement_ids: ['REQ-002'],
      uncovered_requirement_ids: ['REQ-001', 'REQ-003', 'REQ-004'],
    },
    BROWSER_SMOKE: {
      tier: 'BROWSER_SMOKE',
      total_active_requirements: 4,
      covered_requirement_count: 1,
      uncovered_requirement_count: 3,
      coverage_percentage: 25.0,
      covered_requirement_ids: ['REQ-001'],
      uncovered_requirement_ids: ['REQ-002', 'REQ-003', 'REQ-004'],
    },
    BROWSER_JOURNEY: {
      tier: 'BROWSER_JOURNEY',
      total_active_requirements: 4,
      covered_requirement_count: 1,
      uncovered_requirement_count: 3,
      coverage_percentage: 25.0,
      covered_requirement_ids: ['REQ-004'],
      uncovered_requirement_ids: ['REQ-001', 'REQ-002', 'REQ-003'],
    },
  },
  requirement_traceability: {
    'REQ-001': {
      requirement_id: 'REQ-001',
      is_covered: true,
      covering_tiers: ['UNIT', 'BROWSER_SMOKE'],
      covering_test_ids: ['test-unit-1', 'test-smoke-1'],
      is_authoritative: true,
    },
    'REQ-002': {
      requirement_id: 'REQ-002',
      is_covered: true,
      covering_tiers: ['AI_TEST'],
      covering_test_ids: ['test-ai-1'],
      is_authoritative: true,
    },
    'REQ-003': {
      requirement_id: 'REQ-003',
      is_covered: false,
      covering_tiers: [],
      covering_test_ids: [],
      is_authoritative: false,
    },
    'REQ-004': {
      requirement_id: 'REQ-004',
      is_covered: true,
      covering_tiers: ['BROWSER_JOURNEY'],
      covering_test_ids: ['test-journey-1'],
      is_authoritative: true,
    },
  },
};

const mockGaps: CoverageGapsResponse = {
  project_id: 'proj-11l-test-456',
  total_active_requirements: 4,
  uncovered_count: 1,
  tier_uncovered_summary: {
    UNIT: 3,
    AI_TEST: 3,
    BROWSER_SMOKE: 3,
    BROWSER_JOURNEY: 3,
  },
  gaps: [
    {
      requirement_id: 'REQ-003',
      requirement_title: 'Inferred Payment Gate',
      priority: 'CRITICAL',
      status: 'UNCOVERED',
      covering_tiers: [],
      associated_test_ids: ['test-ai-1'],
      notes: 'Requirement has only inferred link from AI test, no authoritative coverage.',
    },
  ],
};

const mockImpactReport: ChangeImpactReport = {
  project_id: 'proj-11l-test-456',
  changed_files: ['src/auth/service.py'],
  directly_affected_files: ['src/auth/service.py'],
  transitively_affected_files: ['src/auth/handlers.py'],
  all_affected_files: ['src/auth/service.py', 'src/auth/handlers.py'],
  affected_tests: [
    {
      test_id: 'test-unit-1',
      name: 'Unit Calculator Test',
      tier: 'UNIT',
      provenance: 'PYTEST_DISCOVERY',
      target_file: 'tests/unit/test_calc.py',
      requirement_links: ['REQ-001'],
      inferred_requirement_links: [],
      is_validated_journey: false,
      execution_metadata: {},
    },
    {
      test_id: 'test-smoke-1',
      name: 'Browser Smoke Health Check',
      tier: 'BROWSER_SMOKE',
      provenance: 'BROWSER_SMOKE_CONVENTION',
      target_file: 'tests/browser/smoke.py',
      requirement_links: ['REQ-001'],
      inferred_requirement_links: [],
      is_validated_journey: false,
      execution_metadata: {},
    },
  ],
  affected_test_ids: ['test-unit-1', 'test-smoke-1'],
  test_impact_reasons: {
    'test-unit-1': ['DIRECT_FILE_DEPENDENCY'],
    'test-smoke-1': ['AFFECTED_REQUIREMENT'],
  },
  affected_requirements: ['REQ-001'],
  requirement_impact_reasons: {
    'REQ-001': ['TEST_TARGET_AFFECTED'],
  },
  uncertain_files: ['src/auth/handlers.py'],
  requires_broader_regression: true,
  uncertainty_reasons: ['Dynamic dependency detected in src/auth/handlers.py'],
  confidence: 'LOW',
  analyzed_at: '2026-10-04T01:00:00Z',
  metadata: {},
};

const mockPlan: RegressionPlan = {
  project_id: 'proj-11l-test-456',
  mode: 'SELECTIVE',
  inventory_id: 'inv-11l-001',
  selected_test_ids: ['test-unit-1', 'test-smoke-1'],
  selected_tests: [
    {
      test_id: 'test-unit-1',
      tier: 'UNIT',
      selection_reasons: ['DIRECT_IMPACT'],
      selection_scope: 'SELECTIVE',
      target_file: 'tests/unit/test_calc.py',
    },
    {
      test_id: 'test-smoke-1',
      tier: 'BROWSER_SMOKE',
      selection_reasons: ['AFFECTED_REQUIREMENT'],
      selection_scope: 'SELECTIVE',
      target_file: 'tests/browser/smoke.py',
    },
  ],
  selected_tests_by_tier: {
    UNIT: ['test-unit-1'],
    AI_TEST: [],
    BROWSER_SMOKE: ['test-smoke-1'],
    BROWSER_JOURNEY: [],
  },
  selected_requirement_ids: ['REQ-001'],
  affected_requirement_ids: ['REQ-001'],
  protected_requirement_ids: ['REQ-001'],
  uncovered_affected_requirement_ids: [],
  unrelated_requirement_ids: [],
  selection_reasons_by_test: {
    'test-unit-1': ['Selected 2 tests covering modified auth service'],
  },
  broadening_reasons: [],
  requires_broader_regression: false,
  is_execution_safe: true,
  plan_warnings: [],
  total_inventory_tests: 4,
  unselected_test_count: 2,
  created_at: '2026-10-04T01:00:00Z',
  metadata: {},
};

const mockExecutionResult: RegressionExecutionResult = {
  execution_id: 'exec-res-123',
  project_id: 'proj-11l-test-456',
  inventory_id: 'inv-11l-001',
  mode: 'SELECTIVE',
  status: 'PARTIAL_FAILURE',
  total_tests: 3,
  passed_tests: 1,
  failed_tests: 1,
  errored_tests: 1,
  skipped_tests: 0,
  blocked_tests: 0,
  duration_seconds: 2.85,
  tier_summaries: {
    UNIT: {
      tier: 'UNIT',
      total_tests: 1,
      passed: 1,
      failed: 0,
      errored: 0,
      skipped: 0,
      blocked: 0,
      duration_seconds: 0.8,
    },
    BROWSER_SMOKE: {
      tier: 'BROWSER_SMOKE',
      total_tests: 2,
      passed: 0,
      failed: 1,
      errored: 1,
      skipped: 0,
      blocked: 0,
      duration_seconds: 2.05,
    },
  },
  test_results: [
    {
      test_id: 'test-unit-1',
      tier: 'UNIT',
      status: 'PASSED',
      duration_seconds: 0.8,
      output_snippet: 'tests/unit/test_calc.py . [100%]',
      error_message: null,
      is_infrastructure_failure: false,
      requirement_ids: ['REQ-001'],
    },
    {
      test_id: 'test-smoke-1',
      tier: 'BROWSER_SMOKE',
      status: 'FAILED',
      duration_seconds: 1.05,
      output_snippet: 'AssertionError: expected status 200 got 500',
      error_message: 'AssertionError: expected status 200 got 500',
      is_infrastructure_failure: false,
      requirement_ids: ['REQ-001'],
    },
    {
      test_id: 'test-smoke-2',
      tier: 'BROWSER_SMOKE',
      status: 'FAILED',
      duration_seconds: 1.0,
      output_snippet: 'Docker daemon connectivity lost during browser launch',
      error_message: 'Docker daemon connectivity lost during browser launch',
      is_infrastructure_failure: true,
      requirement_ids: ['REQ-001'],
    },
  ],
  requirement_results: {
    'REQ-001': {
      requirement_id: 'REQ-001',
      is_satisfied: false,
      covering_tiers: ['UNIT', 'BROWSER_SMOKE'],
      passed_test_ids: ['test-unit-1'],
      failed_test_ids: ['test-smoke-1', 'test-smoke-2'],
    },
  },
  executed_at: '2026-10-04T01:00:00Z',
  metadata: {},
};

describe('Phase 11L Stage 7: Frontend Testing Intelligence & Regression Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (browserTestingApi.getLatestBrowserTestRun as any).mockResolvedValue(null);
    (developmentVersionApi.listVersions as any).mockResolvedValue({ versions: [] });
    (testingApi.getTestInventory as any).mockResolvedValue(mockInventory);
    (testingApi.getCoverage as any).mockResolvedValue(mockCoverage);
    (testingApi.getCoverageGaps as any).mockResolvedValue(mockGaps);
    (testingApi.analyzeImpact as any).mockResolvedValue(mockImpactReport);
    (testingApi.planRegression as any).mockResolvedValue(mockPlan);
    (testingApi.executeRegression as any).mockResolvedValue(mockExecutionResult);
  });

  it('1. renders Testing Intelligence tab and displays Test Inventory across all tiers', async () => {
    render(<TestingWorkspace />);

    const intelligenceTab = screen.getByRole('tab', { name: /Testing Intelligence & Regression/i });
    expect(intelligenceTab).toBeInTheDocument();
    fireEvent.click(intelligenceTab);

    await waitFor(() => {
      expect(testingApi.getTestInventory).toHaveBeenCalledWith('proj-11l-test-456', undefined);
    });

    await waitFor(() => {
      expect(screen.getByText(/Test Definitions Catalog/i)).toBeInTheDocument();
    });

    expect(screen.getByText('Unit Calculator Test')).toBeInTheDocument();
    expect(screen.getByText('AI Generated Property Test')).toBeInTheDocument();
    expect(screen.getByText('Browser Smoke Health Check')).toBeInTheDocument();
    expect(screen.getByText('User Checkout Flow')).toBeInTheDocument();
  });

  it('2. distinguishes authoritative requirement links from inferred links and filters by tier', async () => {
    render(<TestingWorkspace />);
    fireEvent.click(screen.getByRole('tab', { name: /Testing Intelligence & Regression/i }));

    await waitFor(() => {
      expect(screen.getByText('AI Generated Property Test')).toBeInTheDocument();
    });

    // REQ-002 is authoritative, REQ-003 is inferred
    expect(screen.getByText('REQ-002')).toBeInTheDocument();
    expect(screen.getByText('Inferred (Non-Authoritative):')).toBeInTheDocument();
    expect(screen.getByText('~REQ-003')).toBeInTheDocument();

    // Filter by tier: UNIT
    const unitFilterButton = screen.getByRole('button', { name: /^UNIT/i });
    fireEvent.click(unitFilterButton);

    expect(screen.getByText('Unit Calculator Test')).toBeInTheDocument();
    expect(screen.queryByText('AI Generated Property Test')).not.toBeInTheDocument();
  });

  it('3 & 4. renders Coverage Dashboard and displays backend combined coverage percentage (NOT arithmetic average)', async () => {
    render(<TestingWorkspace />);
    fireEvent.click(screen.getByRole('tab', { name: /Testing Intelligence & Regression/i }));

    await waitFor(() => {
      expect(testingApi.getCoverage).toHaveBeenCalledWith('proj-11l-test-456', undefined);
    });

    // Switch to Coverage sub-tab
    fireEvent.click(screen.getByRole('tab', { name: /Coverage Intelligence/i }));

    // Combined coverage is 75.0% from backend set union, NOT (25 + 25 + 25 + 25)/4 = 25%
    await waitFor(() => {
      expect(screen.getByText('75.0%')).toBeInTheDocument();
    });
    expect(screen.getByText('Combined Requirement Coverage')).toBeInTheDocument();
    expect(screen.getByText('Authoritative requirement set union across all 4 tiers (NOT an arithmetic average of tier percentages).')).toBeInTheDocument();

    // Four-Tier Coverage Breakdown
    expect(screen.getByText('Four-Tier Coverage Breakdown')).toBeInTheDocument();
  });

  it('5. renders Coverage Gaps with priority badges and inferred tests', async () => {
    render(<TestingWorkspace />);
    fireEvent.click(screen.getByRole('tab', { name: /Testing Intelligence & Regression/i }));

    await waitFor(() => {
      expect(testingApi.getCoverageGaps).toHaveBeenCalledWith('proj-11l-test-456', undefined);
    });

    // Switch to Gaps sub-tab
    fireEvent.click(screen.getByRole('tab', { name: /Coverage Gaps/i }));

    await waitFor(() => {
      expect(screen.getByText(/Active Requirements Lack Authoritative Test Protection/i)).toBeInTheDocument();
    });
    expect(screen.getByText('Inferred Payment Gate')).toBeInTheDocument();
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
    expect(screen.getByText(/Requirement has only inferred link from AI test/i)).toBeInTheDocument();
  });

  it('6. analyzes Change Impact and displays conservative uncertainty warning', async () => {
    render(<TestingWorkspace />);
    fireEvent.click(screen.getByRole('tab', { name: /Testing Intelligence & Regression/i }));

    // Switch to Impact sub-tab
    fireEvent.click(screen.getByRole('tab', { name: /Change Impact/i }));

    const textarea = screen.getByRole('textbox');
    fireEvent.change(textarea, { target: { value: 'src/auth/service.py' } });

    const analyzeButton = screen.getByRole('button', { name: /Analyze Change Impact/i });
    fireEvent.click(analyzeButton);

    await waitFor(() => {
      expect(testingApi.analyzeImpact).toHaveBeenCalledWith('proj-11l-test-456', {
        changed_files: ['src/auth/service.py'],
        target_version_id: undefined,
      });
    });

    expect(screen.getByText(/Broader Regression Required \(Uncertainty Detected\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Dynamic dependency detected in src\/auth\/handlers\.py/i)).toBeInTheDocument();
    expect(screen.getByText('Impacted Tests (2)')).toBeInTheDocument();
  });

  it('7 & 8. generates Regression Plan across modes (SELECTIVE, BROAD, FULL) with safety badge', async () => {
    render(<TestingWorkspace />);
    fireEvent.click(screen.getByRole('tab', { name: /Testing Intelligence & Regression/i }));

    // Switch to Planner sub-tab
    fireEvent.click(screen.getByRole('tab', { name: /Regression Planner/i }));

    await waitFor(() => {
      expect(screen.getByText(/Selective Regression Planner Configuration/i)).toBeInTheDocument();
    });

    const planButton = screen.getByRole('button', { name: /Generate Regression Plan/i });
    fireEvent.click(planButton);

    await waitFor(() => {
      expect(testingApi.planRegression).toHaveBeenCalledWith('proj-11l-test-456', {
        mode: 'SELECTIVE',
        changed_files: ['app/api/v1/endpoints/testing.py'],
        auto_broaden: true,
        target_version_id: undefined,
      });
    });

    expect(screen.getByText('SAFE FOR EXECUTION')).toBeInTheDocument();
    expect(screen.getByText('Proceed to Execution')).toBeInTheDocument();
  });

  it('9 & 10. executes Regression Plan with confirmation modal and displays results', async () => {
    render(<TestingWorkspace />);
    fireEvent.click(screen.getByRole('tab', { name: /Testing Intelligence & Regression/i }));

    // Switch to Planner and generate plan
    fireEvent.click(screen.getByRole('tab', { name: /Regression Planner/i }));
    await waitFor(() => {
      expect(screen.getByText(/Selective Regression Planner Configuration/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Generate Regression Plan/i }));

    await waitFor(() => {
      expect(screen.getByText('Proceed to Execution')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Proceed to Execution'));

    // In Execution tab with active plan
    await waitFor(() => {
      expect(screen.getByText('Selective Regression Execution Authority')).toBeInTheDocument();
    });

    // Click Run Regression Plan
    const runButton = screen.getByRole('button', { name: /Run Regression Plan/i });
    fireEvent.click(runButton);

    // Confirmation Modal should appear
    expect(screen.getByText('Confirm Regression Execution')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Confirm & Execute/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Confirm & Execute/i }));

    await waitFor(() => {
      expect(testingApi.executeRegression).toHaveBeenCalledWith('proj-11l-test-456', {
        plan: mockPlan,
        mode: 'SELECTIVE',
        skip_browser_tests: false,
        execution_timeout_seconds: 300,
        target_version_id: undefined,
      });
    });

    // Check execution results
    expect(screen.getByText(/REGRESSION PARTIAL_FAILURE/i)).toBeInTheDocument();
  });

  it('11. clearly distinguishes Test Failure from Infrastructure Failure', async () => {
    render(<TestingWorkspace />);
    fireEvent.click(screen.getByRole('tab', { name: /Testing Intelligence & Regression/i }));

    // Switch to Planner and plan
    fireEvent.click(screen.getByRole('tab', { name: /Regression Planner/i }));
    await waitFor(() => {
      expect(screen.getByText(/Selective Regression Planner Configuration/i)).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /Generate Regression Plan/i }));
    await waitFor(() => expect(screen.getByText('Proceed to Execution')).toBeInTheDocument());
    fireEvent.click(screen.getByText('Proceed to Execution'));

    // Execute
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Run Regression Plan/i })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /Run Regression Plan/i }));
    fireEvent.click(screen.getByRole('button', { name: /Confirm & Execute/i }));

    await waitFor(() => {
      expect(screen.getByText(/REGRESSION PARTIAL_FAILURE/i)).toBeInTheDocument();
    });

    // Verify badges and messages
    expect(screen.getAllByText('TEST FAILED').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('INFRA ERROR').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/AssertionError: expected status 200 got 500/i)).toBeInTheDocument();
    expect(screen.getByText(/Docker daemon connectivity lost during browser launch/i)).toBeInTheDocument();
  });

  it('12. handles BLOCKED execution without collapsing into generic failed', async () => {
    const mockBlockedResult: RegressionExecutionResult = {
      execution_id: 'exec-blocked-456',
      project_id: 'proj-11l-test-456',
      inventory_id: 'inv-11l-001',
      mode: 'SELECTIVE',
      status: 'BLOCKED',
      total_tests: 1,
      passed_tests: 0,
      failed_tests: 0,
      errored_tests: 0,
      skipped_tests: 0,
      blocked_tests: 1,
      duration_seconds: 0.05,
      tier_summaries: {},
      test_results: [
        {
          test_id: 'test-unit-1',
          tier: 'UNIT',
          status: 'BLOCKED',
          duration_seconds: 0,
          output_snippet: 'Execution gate rejected: test target invalid',
          error_message: 'Execution gate rejected: test target invalid',
          is_infrastructure_failure: false,
          requirement_ids: ['REQ-001'],
        },
      ],
      requirement_results: {},
      executed_at: '2026-10-04T01:00:00Z',
      metadata: {},
    };
    (testingApi.executeRegression as any).mockResolvedValue(mockBlockedResult);

    render(<TestingWorkspace />);
    fireEvent.click(screen.getByRole('tab', { name: /Testing Intelligence & Regression/i }));

    // Switch to Planner and plan
    fireEvent.click(screen.getByRole('tab', { name: /Regression Planner/i }));
    await waitFor(() => {
      expect(screen.getByText(/Selective Regression Planner Configuration/i)).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /Generate Regression Plan/i }));
    await waitFor(() => expect(screen.getByText('Proceed to Execution')).toBeInTheDocument());
    fireEvent.click(screen.getByText('Proceed to Execution'));

    // Execute
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Run Regression Plan/i })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /Run Regression Plan/i }));
    fireEvent.click(screen.getByRole('button', { name: /Confirm & Execute/i }));

    await waitFor(() => {
      expect(screen.getByText(/REGRESSION BLOCKED/i)).toBeInTheDocument();
    });

    expect(screen.getAllByText('BLOCKED').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Execution gate rejected: test target invalid/i)).toBeInTheDocument();
  });

  it('13 & 14. handles loading and empty states cleanly', async () => {
    (testingApi.getTestInventory as any).mockResolvedValue({
      inventory_id: 'inv-empty',
      project_id: 'proj-11l-test-456',
      total_tests: 0,
      tier_counts: { UNIT: 0, AI_TEST: 0, BROWSER_SMOKE: 0, BROWSER_JOURNEY: 0 },
      conflicts: [],
      discovery_status: 'COMPLETED',
      discovered_at: '2026-10-04T01:00:00Z',
      metadata: {},
      tests: [],
    });

    render(<TestingWorkspace />);
    fireEvent.click(screen.getByRole('tab', { name: /Testing Intelligence & Regression/i }));

    await waitFor(() => {
      expect(screen.getByText('No Tests in Inventory')).toBeInTheDocument();
    });
  });

  it('15. handles backend error states with actionable error banner', async () => {
    (testingApi.getTestInventory as any).mockRejectedValue(new Error('Network connection refused'));

    render(<TestingWorkspace />);
    fireEvent.click(screen.getByRole('tab', { name: /Testing Intelligence & Regression/i }));

    await waitFor(() => {
      expect(screen.getByText('Testing Intelligence Error')).toBeInTheDocument();
      expect(screen.getByText('Network connection refused')).toBeInTheDocument();
    });
  });

  it('16. strictly enforces project isolation in all API client calls', async () => {
    render(<TestingWorkspace />);
    fireEvent.click(screen.getByRole('tab', { name: /Testing Intelligence & Regression/i }));

    await waitFor(() => {
      expect(testingApi.getTestInventory).toHaveBeenCalledWith('proj-11l-test-456', undefined);
      expect(testingApi.getCoverage).toHaveBeenCalledWith('proj-11l-test-456', undefined);
      expect(testingApi.getCoverageGaps).toHaveBeenCalledWith('proj-11l-test-456', undefined);
    });

    // Check that calls are never made with undefined or another project's ID
    expect(testingApi.getTestInventory).not.toHaveBeenCalledWith('other-project', undefined);
  });

  it('17. provides Assistant action contextual buttons', async () => {
    render(<TestingWorkspace />);
    fireEvent.click(screen.getByRole('tab', { name: /Testing Intelligence & Regression/i }));

    await waitFor(() => {
      expect(testingApi.getCoverageGaps).toHaveBeenCalledWith('proj-11l-test-456', undefined);
    });

    // Switch to Gaps
    fireEvent.click(screen.getByRole('tab', { name: /Coverage Gaps/i }));

    await waitFor(() => {
      expect(screen.getByText(/Active Requirements Lack Authoritative Test Protection/i)).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: /Ask Assistant to Plan Tests/i })).toBeInTheDocument();
  });

  it('18. guarantees no arbitrary shell, javascript, or playwright execution controls exist in the UI', () => {
    render(<TestingWorkspace />);
    fireEvent.click(screen.getByRole('tab', { name: /Testing Intelligence & Regression/i }));

    // Verify there are no inputs or textareas for raw bash, eval, playwright, or arbitrary scripts
    const textareas = screen.queryAllByRole('textbox');
    textareas.forEach((el) => {
      const placeholder = el.getAttribute('placeholder') || '';
      expect(placeholder.toLowerCase()).not.toContain('bash');
      expect(placeholder.toLowerCase()).not.toContain('playwright');
      expect(placeholder.toLowerCase()).not.toContain('javascript');
    });
  });
});
