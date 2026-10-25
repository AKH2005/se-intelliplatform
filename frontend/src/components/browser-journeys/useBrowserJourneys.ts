import { useState, useEffect, useRef, useCallback } from 'react';
import { browserJourneyApi } from '../../services/browserJourneyApi';
import {
  BrowserJourney,
  BrowserJourneyWorkflowResponse,
  GenerateBrowserJourneysRequest,
} from '../../types/browserJourney';

const TERMINAL_STATUSES = new Set([
  'COMPLETED',
  'WORKFLOW_GENERATION_FAILED',
  'WORKFLOW_VALIDATION_FAILED',
  'WORKFLOW_ADAPTATION_FAILED',
  'WORKFLOW_BROWSER_EXECUTION_FAILED',
  'FAILED',
]);

export function isTerminalStatus(status: string | undefined): boolean {
  if (!status) return true;
  return TERMINAL_STATUSES.has(status) || status.endsWith('_FAILED');
}

export function extractJourneysFromResult(
  result: BrowserJourneyWorkflowResponse | null
): BrowserJourney[] {
  if (!result || !result.artifacts) return [];
  const suite = result.artifacts.browser_journey_suite;
  if (suite && Array.isArray(suite.journeys)) {
    return suite.journeys;
  }
  return [];
}

export interface UseBrowserJourneysOptions {
  projectId: string | null;
  autoFetch?: boolean;
}

export function useBrowserJourneys({ projectId, autoFetch = true }: UseBrowserJourneysOptions) {
  const [workflowResult, setWorkflowResult] = useState<BrowserJourneyWorkflowResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedJourney, setSelectedJourney] = useState<BrowserJourney | null>(null);

  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);
  const pollCountRef = useRef<number>(0);
  const isMountedRef = useRef<boolean>(true);

  const stopPolling = useCallback(() => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
    pollCountRef.current = 0;
  }, []);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      stopPolling();
    };
  }, [stopPolling]);

  const fetchLatest = useCallback(async () => {
    if (!projectId) {
      setWorkflowResult(null);
      setSelectedJourney(null);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const latest = await browserJourneyApi.getLatestBrowserJourneys(projectId);
      if (isMountedRef.current) {
        setWorkflowResult(latest);
        const journeys = extractJourneysFromResult(latest);
        if (journeys.length > 0) {
          setSelectedJourney(journeys[0]);
        }
      }
    } catch (err: any) {
      if (isMountedRef.current) {
        // If 404, no runs exist yet - this is a normal empty state
        if (err?.status === 404 || err?.response?.status === 404) {
          setWorkflowResult(null);
        } else {
          const msg = err?.problemDetails?.detail || err?.message || 'Failed to load browser journey records';
          setError(msg);
        }
      }
    } finally {
      if (isMountedRef.current) {
        setIsLoading(false);
      }
    }
  }, [projectId]);

  const startPolling = useCallback(
    (workflowExecutionId: string) => {
      stopPolling();
      if (!projectId) return;

      pollCountRef.current = 0;
      const MAX_POLL_ATTEMPTS = 30; // 30 attempts * 2000ms = 60s max
      const POLL_INTERVAL_MS = 2000;

      pollTimerRef.current = setInterval(async () => {
        if (!isMountedRef.current || !projectId) {
          stopPolling();
          return;
        }

        pollCountRef.current += 1;
        if (pollCountRef.current > MAX_POLL_ATTEMPTS) {
          stopPolling();
          if (isMountedRef.current) {
            setIsGenerating(false);
            setError('Workflow status poll timed out. Please refresh to inspect status.');
          }
          return;
        }

        try {
          const updated = await browserJourneyApi.getBrowserJourney(projectId, workflowExecutionId);
          if (!isMountedRef.current) return;

          setWorkflowResult(updated);
          const journeys = extractJourneysFromResult(updated);
          if (journeys.length > 0 && !selectedJourney) {
            setSelectedJourney(journeys[0]);
          }

          if (isTerminalStatus(updated.status)) {
            stopPolling();
            setIsGenerating(false);
          }
        } catch (pollErr: any) {
          stopPolling();
          if (isMountedRef.current) {
            setIsGenerating(false);
            setError(pollErr?.message || 'Failed to poll workflow execution status');
          }
        }
      }, POLL_INTERVAL_MS);
    },
    [projectId, selectedJourney, stopPolling]
  );

  const generate = useCallback(
    async (request: GenerateBrowserJourneysRequest = {}) => {
      if (!projectId || isGenerating) return;

      setIsGenerating(true);
      setError(null);
      stopPolling();

      try {
        const response = await browserJourneyApi.generateBrowserJourneys(projectId, request);
        if (!isMountedRef.current) return;

        setWorkflowResult(response);
        const journeys = extractJourneysFromResult(response);
        if (journeys.length > 0) {
          setSelectedJourney(journeys[0]);
        }

        if (!isTerminalStatus(response.status)) {
          // Asynchronous execution: begin bounded polling
          startPolling(response.workflow_execution_id);
        } else {
          setIsGenerating(false);
        }
      } catch (genErr: any) {
        if (isMountedRef.current) {
          setIsGenerating(false);
          const msg =
            genErr?.problemDetails?.detail ||
            genErr?.response?.data?.detail ||
            genErr?.message ||
            'Browser journey generation failed.';
          setError(msg);
        }
      }
    },
    [projectId, isGenerating, startPolling, stopPolling]
  );

  useEffect(() => {
    if (autoFetch && projectId) {
      fetchLatest();
    } else if (!projectId) {
      setWorkflowResult(null);
      setSelectedJourney(null);
    }
  }, [projectId, autoFetch, fetchLatest]);

  return {
    workflowResult,
    journeys: extractJourneysFromResult(workflowResult),
    selectedJourney,
    setSelectedJourney,
    isLoading,
    isGenerating,
    error,
    setError,
    fetchLatest,
    generate,
    stopPolling,
  };
}
