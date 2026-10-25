import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { TestingWorkspace } from '../views/TestingWorkspace';
import { AssistantDock } from '../components/assistant/AssistantDock';
import { browserTestingApi } from '../services/browserTestingApi';
import { developmentVersionApi } from '../services/developmentVersionApi';
import { assistantApi } from '../services/assistantApi';
import { BrowserTestRun } from '../types/browserTesting';
import { AssistantMessage } from '../types/assistant';

vi.mock('../services/assistantApi', () => ({
  assistantApi: {
    listConversations: vi.fn(),
    sendMessage: vi.fn(),
    confirmAction: vi.fn(),
  },
}));

vi.mock('../services/browserTestingApi', () => ({
  browserTestingApi: {
    runBrowserTests: vi.fn(),
    getLatestBrowserTestRun: vi.fn(),
    getBrowserTestRun: vi.fn(),
    getScreenshotUrl: vi.fn(
      (projectId, runId, filePath) =>
        `http://localhost:8000/api/v1/projects/${projectId}/browser/tests/${runId}/screenshots/${filePath}`
    ),
  },
}));

vi.mock('../services/developmentVersionApi', () => ({
  developmentVersionApi: {
    listVersions: vi.fn(),
    getActiveVersion: vi.fn(),
  },
}));

vi.mock('../context/ProjectContext', () => ({
  useProject: () => ({
    selectedProjectId: 'proj-stage5-123',
    selectedProject: { id: 'proj-stage5-123', name: 'Stage 5 Project', slug: 'stage-5-proj' },
  }),
}));

const mockPassedRun: BrowserTestRun = {
  run_id: 'run-pass-111',
  project_id: 'proj-stage5-123',
  version_id: 'ver-uuid-1',
  status: 'PASSED',
  tests_total: 2,
  tests_passed: 2,
  tests_failed: 0,
  tests_skipped: 0,
  duration_seconds: 1.45,
  summary: '2/2 browser smoke test cases passed in 1.45s.',
  artifacts: [
    {
      artifact_id: 'art-1',
      artifact_type: 'SCREENSHOT',
      file_path: 'health_check.png',
      size_bytes: 45000,
      content_type: 'image/png',
      caption: 'Application health route screenshot',
      created_at: new Date().toISOString(),
    },
  ],
  test_cases: [
    {
      test_id: 'smoke-health',
      name: 'Smoke Health Check',
      status: 'PASSED',
      duration_seconds: 0.65,
      assertion_summary: 'Target returned status code 200',
      screenshots: [
        {
          artifact_id: 'art-1',
          artifact_type: 'SCREENSHOT',
          file_path: 'health_check.png',
          size_bytes: 45000,
          content_type: 'image/png',
          caption: 'Application health route screenshot',
          created_at: new Date().toISOString(),
        },
      ],
      console_errors: [],
      network_errors: [],
    },
    {
      test_id: 'smoke-root',
      name: 'Smoke Root Navigation',
      status: 'PASSED',
      duration_seconds: 0.8,
      assertion_summary: 'Target page loaded without uncaught exceptions',
      screenshots: [],
      console_errors: [],
      network_errors: [],
    },
  ],
  started_at: new Date().toISOString(),
  completed_at: new Date().toISOString(),
};

const mockFailedRun: BrowserTestRun = {
  run_id: 'run-fail-222',
  project_id: 'proj-stage5-123',
  version_id: 'ver-uuid-1',
  status: 'FAILED',
  tests_total: 2,
  tests_passed: 1,
  tests_failed: 1,
  tests_skipped: 0,
  duration_seconds: 2.15,
  summary: '1/2 browser smoke test cases passed in 2.15s.',
  failure_reason: 'smoke-root: Expected title element not found on root page.',
  artifacts: [
    {
      artifact_id: 'art-fail-1',
      artifact_type: 'SCREENSHOT',
      file_path: 'root_fail.png',
      size_bytes: 62000,
      content_type: 'image/png',
      caption: 'Root failure DOM screenshot',
      created_at: new Date().toISOString(),
    },
  ],
  test_cases: [
    {
      test_id: 'smoke-health',
      name: 'Smoke Health Check',
      status: 'PASSED',
      duration_seconds: 0.7,
      assertion_summary: 'Target returned status code 200',
      screenshots: [],
      console_errors: [],
      network_errors: [],
    },
    {
      test_id: 'smoke-root',
      name: 'Smoke Root Navigation',
      status: 'FAILED',
      duration_seconds: 1.45,
      failed_step: 'Target failed asserting page title.',
      assertion_summary: 'Target failed asserting page title.',
      screenshots: [
        {
          artifact_id: 'art-fail-1',
          artifact_type: 'SCREENSHOT',
          file_path: 'root_fail.png',
          size_bytes: 62000,
          content_type: 'image/png',
          caption: 'Root failure DOM screenshot',
          created_at: new Date().toISOString(),
        },
      ],
      console_errors: [
        {
          message: 'Uncaught TypeError: Cannot read properties of undefined',
          level: 'error',
          timestamp: new Date().toISOString(),
        },
      ],
      network_errors: [
        {
          url: 'http://app:8000/api/v1/missing',
          method: 'GET',
          status_code: 404,
          failure_text: 'HTTP 404 Not Found',
          response_time_ms: 12,
          timestamp: new Date().toISOString(),
        },
      ],
    },
  ],
  started_at: new Date().toISOString(),
  completed_at: new Date().toISOString(),
};

describe('Phase 11J Stage 5: Frontend Browser Testing & Assistant Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(developmentVersionApi.listVersions).mockResolvedValue({
      items: [
        {
          version_id: 'ver-uuid-1',
          project_id: 'proj-stage5-123',
          version_number: 1,
          artifact_key: 'code-gen',
          status: 'VERIFIED' as any,
          is_active: true,
          content_hash: 'abc123456789',
          manifest_hash: 'man123456789',
          file_count: 5,
          total_size_bytes: 12000,
          source_reason: 'INITIAL_GENERATION',
          created_by: 'system',
          requirement_ids: [],
          files_manifest: [],
          created_at: new Date().toISOString(),
        },
      ],
      total: 1,
      active_version_id: 'ver-uuid-1',
    });
  });

  it('renders Browser Smoke Tests tab and version controls', async () => {
    vi.mocked(browserTestingApi.getLatestBrowserTestRun).mockResolvedValue(mockPassedRun);

    render(<TestingWorkspace />);

    // Switch to Browser Smoke Tests tab
    const browserTab = screen.getByRole('tab', { name: /Browser Smoke Tests \(Playwright\)/i });
    expect(browserTab).toBeInTheDocument();
    fireEvent.click(browserTab);

    // Verify controls render
    expect(screen.getByText('Browser Smoke Testing Controls')).toBeInTheDocument();
    expect(screen.getByTestId('run-browser-tests-btn')).toBeInTheDocument();

    // Verify version select populated
    await waitFor(() => {
      const select = screen.getByTestId('browser-version-select');
      expect(select).toBeInTheDocument();
      expect(screen.getByText(/v1 \(VERIFIED\) — Active/i)).toBeInTheDocument();
    });
  });

  it('executes browser tests and displays passed metrics, test cases, and screenshots', async () => {
    vi.mocked(browserTestingApi.getLatestBrowserTestRun).mockResolvedValue(mockPassedRun);
    vi.mocked(browserTestingApi.runBrowserTests).mockResolvedValue(mockPassedRun);

    render(<TestingWorkspace />);

    fireEvent.click(screen.getByRole('tab', { name: /Browser Smoke Tests \(Playwright\)/i }));

    await waitFor(() => {
      expect(screen.getByTestId('run-browser-tests-btn')).toBeInTheDocument();
    });

    const runBtn = screen.getByTestId('run-browser-tests-btn');
    fireEvent.click(runBtn);

    await waitFor(() => {
      expect(browserTestingApi.runBrowserTests).toHaveBeenCalledWith('proj-stage5-123', {
        development_version_id: 'ver-uuid-1',
      });
      expect(screen.getByTestId('browser-run-status')).toHaveTextContent('PASSED');
      expect(screen.getByText('Smoke Health Check')).toBeInTheDocument();
      expect(screen.getByText('Smoke Root Navigation')).toBeInTheDocument();
      expect(screen.getByText('Complete Diagnostic Artifact Gallery (1)')).toBeInTheDocument();
    });
  });

  it('renders failure diagnosis, console errors, network failures, and remediation proposal handoff on failure', async () => {
    vi.mocked(browserTestingApi.getLatestBrowserTestRun).mockResolvedValue(mockFailedRun);
    vi.mocked(browserTestingApi.runBrowserTests).mockResolvedValue(mockFailedRun);

    render(<TestingWorkspace />);

    fireEvent.click(screen.getByRole('tab', { name: /Browser Smoke Tests \(Playwright\)/i }));

    await waitFor(() => {
      expect(screen.getByTestId('browser-run-status')).toHaveTextContent('FAILED');
      expect(screen.getByTestId('remediation-handoff-banner')).toBeInTheDocument();
      expect(screen.getByText(/Cannot read properties of undefined/i)).toBeInTheDocument();
      expect(screen.getByText(/HTTP 404 Not Found/i)).toBeInTheDocument();
    });
  });

  it('renders error banner when browser execution API fails', async () => {
    vi.mocked(browserTestingApi.getLatestBrowserTestRun).mockRejectedValue(new Error('Network error'));
    vi.mocked(browserTestingApi.runBrowserTests).mockRejectedValue(new Error('Container startup timeout exceeded'));

    render(<TestingWorkspace />);

    fireEvent.click(screen.getByRole('tab', { name: /Browser Smoke Tests \(Playwright\)/i }));

    await waitFor(() => {
      expect(screen.getByTestId('run-browser-tests-btn')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('run-browser-tests-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('browser-error-banner')).toHaveTextContent('Container startup timeout exceeded');
    });
  });

  it('AssistantDock renders browser smoke test result action card', async () => {
    const mockMsg: AssistantMessage = {
      message_id: 'msg-assist-1',
      conversation_id: 'conv-123',
      role: 'assistant',
      content: 'I have executed browser smoke tests against version v1.',
      action_id: 'RUN_BROWSER_TESTS',
      action_status: 'SUCCESS',
      action_result: {
        action_id: 'RUN_BROWSER_TESTS',
        status: 'SUCCESS',
        summary: 'Browser test execution PASSED: 2/2 smoke test cases passed.',
        requires_confirmation: false,
        warnings: [],
        errors: [],
        data: {
          status: 'PASSED',
          tests_total: 2,
          tests_passed: 2,
          tests_failed: 0,
          duration_seconds: 1.45,
          summary: '2/2 smoke tests passed',
        },
      },
      created_at: new Date().toISOString(),
    };

    vi.mocked(assistantApi.listConversations).mockResolvedValue({
      items: [
        {
          conversation_id: 'conv-123',
          project_id: 'proj-stage5-123',
          title: 'Browser Testing Chat',
          messages: [mockMsg],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
      total: 1,
    });

    render(
      <AssistantDock
        isOpen={true}
        onClose={vi.fn()}
        projectId="proj-stage5-123"
        activeProjectName="Stage 5 Project"
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('browser-test-card')).toBeInTheDocument();
      expect(screen.getByText(/Browser Smoke Tests: PASSED/i)).toBeInTheDocument();
      expect(screen.getByText(/Passed: 2/i)).toBeInTheDocument();
      expect(screen.getByText(/Failed: 0/i)).toBeInTheDocument();
    });
  });
});
