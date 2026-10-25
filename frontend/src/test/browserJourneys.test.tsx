import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, renderHook, act } from '@testing-library/react';
import { TestingWorkspace } from '../views/TestingWorkspace';
import { DevelopmentWorkspace } from '../views/DevelopmentWorkspace';
import { AssistantDock } from '../components/assistant/AssistantDock';
import { browserJourneyApi } from '../services/browserJourneyApi';
import { browserTestingApi } from '../services/browserTestingApi';
import { developmentVersionApi } from '../services/developmentVersionApi';
import { assistantApi } from '../services/assistantApi';
import { apiClient } from '../services/apiClient';
import { BrowserJourneyWorkflowResponse } from '../types/browserJourney';
import { AssistantMessage } from '../types/assistant';
import {
  BrowserJourneyDetail,
  BrowserJourneyList,
  BrowserJourneyCoverage,
  BrowserJourneyStatus,
  BrowserJourneyFailure,
  BrowserJourneyEmptyState,
  useBrowserJourneys,
} from '../components/browser-journeys';



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
    selectedProjectId: 'proj-stage6-123',
    selectedProject: { id: 'proj-stage6-123', name: 'Stage 6 Project', slug: 'stage-6-proj' },
  }),
}));

const mockSuccessResponse: BrowserJourneyWorkflowResponse = {
  workflow_execution_id: 'wf-pass-123',
  project_id: 'proj-stage6-123',
  status: 'COMPLETED',
  stage_reached: 'completed',
  journey_count: 2,
  validation_passed: true,
  coverage_percentage: 75.0,
  covered_requirement_ids: ['REQ-001', 'REQ-002'],
  uncovered_requirement_ids: ['REQ-003'],
  test_definitions_count: 2,
  browser_tests_executed: true,
  browser_tests_passed: true,
  browser_test_run_id: 'run-pass-123',
  failure_reason: null,
  failure_diagnosis: null,
  artifacts: {
    browser_journey_suite: {
      journeys: [
        {
          journey_id: 'j-login',
          title: 'User Login Journey',
          description: 'Authenticate with credentials and verify dashboard landing',
          category: 'AUTHENTICATION',
          priority: 'CRITICAL',
          requirement_ids: ['REQ-001'],
          routes: ['/login', '/dashboard'],
          preconditions: ['User account exists'],
          steps: [
            { step_number: 1, action: 'NAVIGATE', value: '/login' },
            { step_number: 2, action: 'FILL', target_role: 'textbox', target_label: 'Username', value: 'admin' },
            { step_number: 3, action: 'CLICK', target_role: 'button', target_label: 'Log in' },
            { step_number: 4, action: 'ASSERT_URL', expected_value: '/dashboard' },
          ],
          expected_outcomes: ['Dashboard view is visible'],
        },
        {
          journey_id: 'j-profile',
          title: 'User Profile Journey',
          description: 'Navigate to profile and update user settings',
          category: 'CRUD_WORKFLOW',
          priority: 'HIGH',
          requirement_ids: ['REQ-002'],
          routes: ['/profile'],
          preconditions: ['User is logged in'],
          steps: [
            { step_number: 1, action: 'NAVIGATE', value: '/profile' },
            { step_number: 2, action: 'ASSERT_TEXT', expected_value: 'User Profile' },
          ],
          expected_outcomes: ['Profile information is displayed'],
        },
      ],
    },
    browser_journey_validation: {
      is_valid: true,
      coverage_report: {
        coverage_percentage: 75.0,
        covered_requirement_ids: ['REQ-001', 'REQ-002'],
        uncovered_requirement_ids: ['REQ-003'],
        requirement_to_journeys: {
          'REQ-001': ['j-login'],
          'REQ-002': ['j-profile'],
        },
      },
    },
  },
  started_at: '2026-10-02T10:00:00Z',
  completed_at: '2026-10-02T10:00:05Z',
  duration_seconds: 5.2,
};

const mockFailedResponse: BrowserJourneyWorkflowResponse = {
  workflow_execution_id: 'wf-fail-456',
  project_id: 'proj-stage6-123',
  status: 'WORKFLOW_BROWSER_EXECUTION_FAILED',
  stage_reached: 'browser_execution',
  journey_count: 1,
  validation_passed: true,
  coverage_percentage: 50.0,
  covered_requirement_ids: ['REQ-001'],
  uncovered_requirement_ids: ['REQ-002', 'REQ-003'],
  test_definitions_count: 1,
  browser_tests_executed: true,
  browser_tests_passed: false,
  browser_test_run_id: 'run-fail-456',
  failure_reason: 'Assertion failed: Target dashboard view was not reached in time.',
  failure_diagnosis: {
    summary: 'Selector timed out waiting for #dashboard-view',
    likely_cause: 'Backend auth service returned 401 Unauthorized during session check',
    affected_journey_id: 'j-login',
    affected_step_number: 4,
    evidence: ['Console error 401 on /api/auth/me', 'Navigation timed out after 5000ms'],
    remediation_hint: 'Verify user credentials seed in test environment database.',
  },
  artifacts: {
    browser_journey_suite: {
      journeys: [
        {
          journey_id: 'j-login',
          title: 'User Login Journey',
          description: 'Authenticate with credentials',
          category: 'AUTHENTICATION',
          priority: 'CRITICAL',
          requirement_ids: ['REQ-001'],
          routes: ['/login'],
          preconditions: [],
          steps: [{ step_number: 1, action: 'NAVIGATE', value: '/login' }],
          expected_outcomes: ['Dashboard view is visible'],
        },
      ],
    },
  },
  started_at: '2026-10-02T10:00:00Z',
  completed_at: '2026-10-02T10:00:06Z',
  duration_seconds: 6.1,
};

describe('Phase 11K Stage 6: Intelligent Browser Journeys Frontend Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (developmentVersionApi.listVersions as any).mockResolvedValue({
      items: [
        {
          version_id: 'ver-1',
          version_number: 1,
          status: 'VERIFIED',
          is_active: true,
          content_hash: '1234567890abcdef1234567890abcdef',
          file_count: 5,
          total_size_bytes: 45000,
          created_at: new Date().toISOString(),
          files_manifest: [],
        },
      ],
    });
    (browserTestingApi.getLatestBrowserTestRun as any).mockResolvedValue(null);
    (developmentVersionApi.getVersionFileContent as any).mockResolvedValue('// file content');
    (assistantApi.listConversations as any).mockResolvedValue({ items: [] });
    vi.spyOn(browserJourneyApi, 'getLatestBrowserJourneys').mockResolvedValue(null as any);
    vi.spyOn(browserJourneyApi, 'generateBrowserJourneys').mockResolvedValue(mockSuccessResponse);
    vi.spyOn(browserJourneyApi, 'getBrowserJourney').mockResolvedValue(mockSuccessResponse);
    vi.spyOn(browserJourneyApi, 'getBrowserJourneys').mockResolvedValue([mockSuccessResponse]);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // --------------------------------------------------------------------------
  // A. API Client Tests
  // --------------------------------------------------------------------------
  describe('A. API Client', () => {
    beforeEach(() => {
      vi.restoreAllMocks();
    });

    it('sends correct POST request with target parameters', async () => {
      const postSpy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce(mockSuccessResponse);

      const res = await browserJourneyApi.generateBrowserJourneys('proj-stage6-123', {
        development_version_id: 'ver-1',
        execute_browser_tests: true,
        max_journeys: 5,
      });

      expect(postSpy).toHaveBeenCalledWith(
        '/projects/proj-stage6-123/browser-journeys',
        {
          development_version_id: 'ver-1',
          execute_browser_tests: true,
          max_journeys: 5,
        }
      );
      expect(res.status).toBe('COMPLETED');
      expect(res.journey_count).toBe(2);
    });

    it('sends correct GET requests for latest and by execution id', async () => {
      const getSpy = vi.spyOn(apiClient, 'get').mockResolvedValue(mockSuccessResponse);

      await browserJourneyApi.getLatestBrowserJourneys('proj-stage6-123');
      expect(getSpy).toHaveBeenCalledWith('/projects/proj-stage6-123/browser-journeys/latest');

      await browserJourneyApi.getBrowserJourney('proj-stage6-123', 'wf-pass-123');
      expect(getSpy).toHaveBeenCalledWith('/projects/proj-stage6-123/browser-journeys/wf-pass-123');

      await browserJourneyApi.getBrowserJourneys('proj-stage6-123', 10, 5);
      expect(getSpy).toHaveBeenCalledWith('/projects/proj-stage6-123/browser-journeys', {
        params: { limit: 10, offset: 5 },
      });
    });
  });

  // --------------------------------------------------------------------------
  // B. Generation UI Tests (Development & Testing Workspaces)
  // --------------------------------------------------------------------------
  describe('B. Generation UI', () => {
    it('renders Browser Journey panel in DevelopmentWorkspace and triggers generation on click', async () => {
      (browserJourneyApi.getLatestBrowserJourneys as any).mockResolvedValueOnce(mockSuccessResponse);
      (browserJourneyApi.generateBrowserJourneys as any).mockResolvedValueOnce(mockSuccessResponse);

      render(<DevelopmentWorkspace />);

      await waitFor(() => {
        expect(screen.getByTestId('browser-journey-dev-panel')).toBeInTheDocument();
      });

      expect(screen.getByText('Intelligent Browser Journeys')).toBeInTheDocument();
      const generateBtn = screen.getByTestId('dev-panel-generate-btn');
      expect(generateBtn).toBeInTheDocument();

      fireEvent.click(generateBtn);

      await waitFor(() => {
        expect(browserJourneyApi.generateBrowserJourneys).toHaveBeenCalledWith(
          'proj-stage6-123',
          expect.objectContaining({ development_version_id: 'ver-1' })
        );
      });
    });

    it('renders Intelligent Browser Journeys tab in TestingWorkspace and protects against duplicate clicks', async () => {
      (browserJourneyApi.getLatestBrowserJourneys as any).mockResolvedValueOnce(mockSuccessResponse);
      let resolvePromise: any;
      (browserJourneyApi.generateBrowserJourneys as any).mockImplementation(
        () => new Promise((resolve) => { resolvePromise = resolve; })
      );

      render(<TestingWorkspace />);

      // Switch to Journeys tab
      const journeysTab = screen.getByRole('tab', { name: /Intelligent Browser Journeys/i });
      fireEvent.click(journeysTab);

      await waitFor(() => {
        expect(screen.getByTestId('journey-version-select')).toBeInTheDocument();
      });

      const generateBtn = screen.getByTestId('generate-browser-journeys-btn');
      expect(generateBtn).toBeInTheDocument();

      // Click once
      fireEvent.click(generateBtn);

      // Verify button is disabled during loading state
      expect(generateBtn).toBeDisabled();
      expect(screen.getByText(/Generating Journeys.../i)).toBeInTheDocument();

      // Attempt duplicate click while disabled
      fireEvent.click(generateBtn);
      expect(browserJourneyApi.generateBrowserJourneys).toHaveBeenCalledTimes(1);

      // Resolve the pending generation
      await act(async () => {
        resolvePromise(mockSuccessResponse);
      });
    });
  });

  // --------------------------------------------------------------------------
  // C. Status Banner Tests
  // --------------------------------------------------------------------------
  describe('C. Status UI', () => {
    it('renders completed status banner with stage and duration', () => {
      render(<BrowserJourneyStatus workflowResult={mockSuccessResponse} isGenerating={false} />);

      expect(screen.getByTestId('workflow-status-banner')).toBeInTheDocument();
      expect(screen.getByText('Workflow Completed Successfully')).toBeInTheDocument();
      expect(screen.getByText(/Stage reached:/i)).toBeInTheDocument();
      expect(screen.getByText('completed')).toBeInTheDocument();
      expect(screen.getByTestId('metric-journey-count')).toHaveTextContent('2');
      expect(screen.getByTestId('metric-coverage')).toHaveTextContent('75.0%');
      expect(screen.getByTestId('metric-validation')).toHaveTextContent('Passed');
      expect(screen.getByTestId('metric-browser-tests')).toHaveTextContent('Passed');
    });

    it('renders failed status banner when browser execution failed', () => {
      render(<BrowserJourneyStatus workflowResult={mockFailedResponse} isGenerating={false} />);

      expect(screen.getByText('Browser Container Execution Failed')).toBeInTheDocument();
      expect(screen.getByTestId('metric-browser-tests')).toHaveTextContent('Failed');
    });

    it('renders generating progress banner when isGenerating is true', () => {
      render(<BrowserJourneyStatus workflowResult={null} isGenerating={true} />);

      expect(screen.getByTestId('workflow-status-generating')).toBeInTheDocument();
      expect(screen.getByText(/Executing Intelligent Browser Journey Pipeline.../i)).toBeInTheDocument();
    });
  });

  // --------------------------------------------------------------------------
  // D. Coverage Visualization Tests
  // --------------------------------------------------------------------------
  describe('D. Requirement Coverage', () => {
    it('renders backend-provided coverage percentage and covered/uncovered lists without recalculation', () => {
      render(<BrowserJourneyCoverage workflowResult={mockSuccessResponse} />);

      // Must display 75.0% exactly as provided by backend
      const badge = screen.getByTestId('coverage-percentage-badge');
      expect(badge).toHaveTextContent('75.0%');

      const progressBar = screen.getByTestId('coverage-progress-bar');
      expect(progressBar).toHaveStyle({ width: '75%' });

      // Covered requirements
      expect(screen.getByTestId('covered-requirements-list')).toBeInTheDocument();
      expect(screen.getByTestId('covered-req-REQ-001')).toBeInTheDocument();
      expect(screen.getByTestId('covered-req-REQ-002')).toBeInTheDocument();

      // Uncovered requirements
      expect(screen.getByTestId('uncovered-requirements-list')).toBeInTheDocument();
      expect(screen.getByTestId('uncovered-req-REQ-003')).toBeInTheDocument();
    });
  });

  // --------------------------------------------------------------------------
  // E. Journey List Tests
  // --------------------------------------------------------------------------
  describe('E. Journey List', () => {
    it('renders journey list with category, priority, and metadata', () => {
      const onSelect = vi.fn();
      const journeys = mockSuccessResponse.artifacts.browser_journey_suite.journeys;

      render(
        <BrowserJourneyList
          journeys={journeys}
          selectedJourneyId="j-login"
          onSelectJourney={onSelect}
        />
      );

      expect(screen.getByTestId('journey-card-j-login')).toBeInTheDocument();
      expect(screen.getByTestId('journey-card-j-profile')).toBeInTheDocument();
      expect(screen.getByText('User Login Journey')).toBeInTheDocument();
      expect(screen.getByText('AUTHENTICATION')).toBeInTheDocument();
      expect(screen.getByText(/4 steps/i)).toBeInTheDocument();

      // Click card selects journey
      fireEvent.click(screen.getByTestId('journey-card-j-profile'));
      expect(onSelect).toHaveBeenCalledWith(journeys[1]);
    });
  });

  // --------------------------------------------------------------------------
  // F. Journey Detail & Steps Visualization Tests
  // --------------------------------------------------------------------------
  describe('F. Journey Detail & Semantic Steps', () => {
    it('renders semantic steps, requirements, routes, and preconditions', () => {
      const journey = mockSuccessResponse.artifacts.browser_journey_suite.journeys[0];

      render(<BrowserJourneyDetail journey={journey} executionStatus="PASSED" />);

      expect(screen.getByTestId('journey-detail-title')).toHaveTextContent('User Login Journey');
      expect(screen.getByTestId('journey-detail-requirements')).toHaveTextContent('REQ-001');
      expect(screen.getByTestId('journey-detail-routes')).toHaveTextContent('/login');
      expect(screen.getByTestId('journey-detail-routes')).toHaveTextContent('/dashboard');
      expect(screen.getByTestId('journey-detail-preconditions')).toHaveTextContent('User account exists');
      expect(screen.getByTestId('journey-detail-outcomes')).toHaveTextContent('Dashboard view is visible');
      expect(screen.getByTestId('journey-detail-execution-status')).toHaveTextContent('PASSED');

      // Semantic steps
      expect(screen.getByTestId('journey-steps-timeline')).toBeInTheDocument();
      expect(screen.getByTestId('journey-step-1')).toHaveTextContent('NAVIGATE');
      expect(screen.getByTestId('journey-step-2')).toHaveTextContent('FILL');
      expect(screen.getByTestId('journey-step-2')).toHaveTextContent('admin');
      expect(screen.getByTestId('journey-step-3')).toHaveTextContent('CLICK');
      expect(screen.getByTestId('journey-step-4')).toHaveTextContent('ASSERT_URL');
      expect(screen.getByTestId('journey-step-4')).toHaveTextContent('/dashboard');
    });

    it('renders empty detail notice when no journey is selected', () => {
      render(<BrowserJourneyDetail journey={null} />);
      expect(screen.getByTestId('journey-detail-empty')).toBeInTheDocument();
      expect(screen.getByText('Select a Journey')).toBeInTheDocument();
    });
  });

  // --------------------------------------------------------------------------
  // G & H. Failure Diagnostics Tests
  // --------------------------------------------------------------------------
  describe('G & H. Failure Diagnostics', () => {
    it('renders structured failure analysis without leaking internal details', () => {
      render(<BrowserJourneyFailure workflowResult={mockFailedResponse} />);

      expect(screen.getByTestId('journey-failure-panel')).toBeInTheDocument();
      expect(screen.getByTestId('failure-reason-text')).toHaveTextContent(
        'Assertion failed: Target dashboard view was not reached in time.'
      );
      expect(screen.getByTestId('structured-failure-diagnosis')).toBeInTheDocument();
      expect(screen.getByText(/Selector timed out waiting for #dashboard-view/i)).toBeInTheDocument();
      expect(screen.getByText(/Backend auth service returned 401/i)).toBeInTheDocument();
      expect(screen.getByText(/Verify user credentials seed in test environment/i)).toBeInTheDocument();
    });

    it('does not render failure panel when workflow completed successfully', () => {
      const { container } = render(<BrowserJourneyFailure workflowResult={mockSuccessResponse} />);
      expect(container.firstChild).toBeNull();
    });
  });

  // --------------------------------------------------------------------------
  // I. Empty State Tests
  // --------------------------------------------------------------------------
  describe('I. Empty State', () => {
    it('renders empty state when no journeys have been generated', () => {
      const onGen = vi.fn();
      render(<BrowserJourneyEmptyState onGenerate={onGen} isGenerating={false} />);

      expect(screen.getByTestId('journey-empty-state')).toBeInTheDocument();
      expect(screen.getByText('No Browser Journeys Generated Yet')).toBeInTheDocument();
      const btn = screen.getByTestId('empty-generate-journeys-btn');
      fireEvent.click(btn);
      expect(onGen).toHaveBeenCalledTimes(1);
    });
  });

  // --------------------------------------------------------------------------
  // J. AssistantDock Action Result Card Tests
  // --------------------------------------------------------------------------
  describe('J. AssistantDock Action Result Card', () => {
    it('renders browser journey action result card and navigates to testing on click', async () => {
      const onNavigate = vi.fn();

      const assistantMsgWithJourney: AssistantMessage = {
        message_id: 'msg-journey-1',
        conversation_id: 'conv-1',
        role: 'assistant',
        content: 'I have generated and executed the browser journeys.',
        action_id: 'GENERATE_BROWSER_JOURNEYS',
        action_status: 'SUCCESS',
        action_result: {
          action_id: 'GENERATE_BROWSER_JOURNEYS',
          status: 'SUCCESS',
          summary: 'Browser Journey Workflow COMPLETED: 2 journey(s) generated, validation passed, browser tests passed.',
          data: {
            status: 'COMPLETED',
            journey_count: 2,
            coverage_percentage: 75.0,
            browser_tests_executed: true,
            browser_tests_passed: true,
            duration_seconds: 5.2,
          },
          requires_confirmation: false,
          warnings: [],
          errors: [],
        },
        created_at: new Date().toISOString(),
      };

      (assistantApi.listConversations as any).mockResolvedValueOnce({
        items: [
          {
            conversation_id: 'conv-1',
            messages: [assistantMsgWithJourney],
          },
        ],
      });

      render(
        <AssistantDock
          isOpen={true}
          onClose={vi.fn()}
          projectId="proj-stage6-123"
          onNavigate={onNavigate}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('browser-journey-action-card')).toBeInTheDocument();
      });

      expect(screen.getByText(/Browser Journeys: COMPLETED/i)).toBeInTheDocument();
      expect(screen.getByText(/Journeys: 2/i)).toBeInTheDocument();
      expect(screen.getByText(/Coverage: 75%/i)).toBeInTheDocument();
      expect(screen.getByText(/Tests: Passed/i)).toBeInTheDocument();

      const viewBtn = screen.getByTestId('view-journeys-btn');
      expect(viewBtn).toBeInTheDocument();
      fireEvent.click(viewBtn);

      expect(onNavigate).toHaveBeenCalledWith('testing');
    });
  });

  // --------------------------------------------------------------------------
  // K. Bounded Polling Verification
  // --------------------------------------------------------------------------
  describe('K. Bounded Polling', () => {
    it('polls until reaching terminal state and stops', async () => {
      vi.useFakeTimers();

      const runningResponse: BrowserJourneyWorkflowResponse = {
        ...mockSuccessResponse,
        status: 'RUNNING',
      };

      (browserJourneyApi.getLatestBrowserJourneys as any).mockResolvedValueOnce(null);
      (browserJourneyApi.generateBrowserJourneys as any).mockResolvedValueOnce(runningResponse);
      (browserJourneyApi.getBrowserJourney as any)
        .mockResolvedValueOnce(runningResponse)
        .mockResolvedValueOnce(mockSuccessResponse);

      const { result } = renderHook(() =>
        useBrowserJourneys({ projectId: 'proj-stage6-123', autoFetch: false })
      );

      // Trigger generate
      await act(async () => {
        await result.current.generate({});
      });

      expect(result.current.isGenerating).toBe(true);

      // Advance by 2 seconds (first poll -> RUNNING)
      await act(async () => {
        await vi.advanceTimersByTimeAsync(2100);
      });
      expect(browserJourneyApi.getBrowserJourney).toHaveBeenCalledTimes(1);

      // Advance by 2 seconds (second poll -> COMPLETED terminal state)
      await act(async () => {
        await vi.advanceTimersByTimeAsync(2100);
      });
      expect(browserJourneyApi.getBrowserJourney).toHaveBeenCalledTimes(2);
      expect(result.current.isGenerating).toBe(false);
      expect(result.current.workflowResult?.status).toBe('COMPLETED');

      // Advance further -> polling must have stopped
      await act(async () => {
        await vi.advanceTimersByTimeAsync(4000);
      });
      expect(browserJourneyApi.getBrowserJourney).toHaveBeenCalledTimes(2);

      vi.useRealTimers();
    });
  });

  // --------------------------------------------------------------------------
  // L. Security & Untrusted Rendering Tests
  // --------------------------------------------------------------------------
  describe('L. Security & Text Escaping', () => {
    it('escapes untrusted malicious HTML strings without rendering script or elements', () => {
      const xssJourney = {
        ...mockSuccessResponse.artifacts.browser_journey_suite.journeys[0],
        title: '<script>alert("xss")</script>Injected Journey',
        description: '<img src=x onerror=alert(1)>Malicious Description',
        preconditions: ['<b onmouseover=alert(1)>Precondition</b>'],
        expected_outcomes: ['<iframe src="javascript:alert(1)"></iframe>Outcome'],
      };

      const { container } = render(<BrowserJourneyDetail journey={xssJourney} />);

      // Must not contain actual script or iframe elements
      expect(container.querySelector('script')).toBeNull();
      expect(container.querySelector('iframe')).toBeNull();
      expect(container.querySelector('img[src="x"]')).toBeNull();

      // Raw strings rendered safely as text
      expect(screen.getByText(/<script>alert\("xss"\)<\/script>Injected Journey/i)).toBeInTheDocument();
      expect(screen.getByText(/<img src=x onerror=alert\(1\)>Malicious Description/i)).toBeInTheDocument();
    });
  });
});
