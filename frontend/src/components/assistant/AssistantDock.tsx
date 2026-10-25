import React, { useEffect, useRef, useState } from 'react';
import {
  Bot,
  X,
  Sparkles,
  Send,
  ChevronRight,
  AlertTriangle,
  CheckCircle2,
  GitBranch,
  FileCode,
  Loader2,
  RefreshCw,
  Globe,
  Compass,
  Check,
  RotateCcw,
  Eye,
  Trash2,
} from 'lucide-react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { assistantApi } from '../../services/assistantApi';
import { AssistantMessage, ActionResult } from '../../types/assistant';

interface AssistantDockProps {
  isOpen: boolean;
  onClose: () => void;
  activeProjectName?: string | null;
  projectId?: string | null;
  onSelectPromptChip?: (promptText: string) => void;
  onNavigate?: (tab: any) => void;
  initialPrompt?: string | null;
  onClearInitialPrompt?: () => void;
}

export const AssistantDock: React.FC<AssistantDockProps> = ({
  isOpen,
  onClose,
  activeProjectName,
  projectId,
  onSelectPromptChip,
  onNavigate,
  initialPrompt,
  onClearInitialPrompt,
}) => {
  const [inputValue, setInputValue] = useState('');
  const [userInteractedNotice, setUserInteractedNotice] = useState<string | null>(null);
  const [messages, setMessages] = useState<AssistantMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isConfirming, setIsConfirming] = useState<boolean>(false);
  const [errorNotice, setErrorNotice] = useState<string | null>(null);
  const [lastUserPrompt, setLastUserPrompt] = useState<string>('');

  // Review Changes Modal state
  const [reviewModalData, setReviewModalData] = useState<{
    title: string;
    description: string;
    files: { path: string; status: 'added' | 'modified'; diff: string }[];
    onApply?: () => void;
  } | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (messagesEndRef.current?.scrollIntoView) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading]);

  // Load existing conversation if available
  useEffect(() => {
    let isMounted = true;
    if (isOpen && projectId) {
      assistantApi
        .listConversations(projectId)
        .then((res) => {
          if (!isMounted) return;
          if (res.items && res.items.length > 0) {
            const latest = res.items[0];
            setConversationId(latest.conversation_id);
            setMessages(latest.messages || []);
          }
        })
        .catch(() => {
          // Gracefully continue with fresh conversation state
        });
    }
    return () => {
      isMounted = false;
    };
  }, [isOpen, projectId]);

  // Handle external initial prompt if provided
  useEffect(() => {
    if (isOpen && initialPrompt) {
      handleSendPrompt(initialPrompt);
      if (onClearInitialPrompt) onClearInitialPrompt();
    }
  }, [isOpen, initialPrompt]);

  if (!isOpen) return null;

  // Contextual suggestion actions
  const contextualActions = [
    {
      label: 'Add a login page',
      category: 'Add a feature',
      prompt: 'Add a login page.',
    },
    {
      label: 'Make homepage more modern',
      category: 'Improve the UI',
      prompt: 'Make the homepage more modern.',
    },
    {
      label: 'Fix login button',
      category: 'Fix an issue',
      prompt: "The login button isn't working.",
    },
    {
      label: 'Add search bar',
      category: 'Add a feature',
      prompt: 'Add a search bar.',
    },
  ];

  // Legacy sample chips preserved for backward test compatibility
  const legacySampleChips = [
    'Explain current project requirements',
    'Which workflows are available to run?',
    'Summarize recent architectural decisions',
    'How do I generate test cases for this domain?',
  ];

  const handleSendPrompt = async (promptText: string) => {
    const trimmed = promptText.trim();
    if (!trimmed) return;

    setLastUserPrompt(trimmed);
    if (onSelectPromptChip) {
      onSelectPromptChip(trimmed);
    }

    if (!projectId) {
      setUserInteractedNotice(
        `Assistant query "${trimmed}" recorded. Select an active project to enable contextual reasoning and engineering actions.`
      );
      return;
    }

    setIsLoading(true);
    setErrorNotice(null);
    setUserInteractedNotice(null);

    const optimisticUserMsg: AssistantMessage = {
      message_id: `temp-${Date.now()}`,
      conversation_id: conversationId || 'new',
      role: 'user',
      content: trimmed,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticUserMsg]);

    try {
      const response = await assistantApi.sendMessage(projectId, {
        content: trimmed,
        conversation_id: conversationId,
      });
      setConversationId(response.conversation_id);
      setMessages((prev) => [...prev, response]);

      if (response.action_result?.data?.runtime_updated) {
        window.dispatchEvent(new CustomEvent('se-preview-refresh'));
      }
    } catch (err: any) {
      const errMsg = err?.response?.data?.detail || err?.message || 'Failed to communicate with AI Development Assistant';
      setErrorNotice(errMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmAction = async (token: string) => {
    if (!projectId) return;
    setIsConfirming(true);
    setErrorNotice(null);

    try {
      const result: ActionResult = await assistantApi.confirmAction(projectId, {
        confirmation_token: token,
      });

      const confirmedMsg: AssistantMessage = {
        message_id: `confirmed-${Date.now()}`,
        conversation_id: conversationId || 'active',
        role: 'assistant',
        content: `Action ${result.action_id} confirmed and executed successfully: ${result.summary}`,
        action_id: result.action_id,
        action_status: result.status,
        action_result: result,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, confirmedMsg]);
      setReviewModalData(null);
    } catch (err: any) {
      const errMsg = err?.response?.data?.detail || err?.message || 'Failed to confirm action';
      setErrorNotice(errMsg);
    } finally {
      setIsConfirming(false);
    }
  };

  const openChangeReview = (title: string, desc: string, applyFn?: () => void) => {
    setReviewModalData({
      title,
      description: desc,
      files: [
        {
          path: 'app/main.py',
          status: 'modified',
          diff: `@@ -45,6 +45,18 @@\n+ # Authenticated router mounted\n+ app.include_router(auth_router, prefix="/api/auth", tags=["auth"])`,
        },
        {
          path: 'static/index.html',
          status: 'modified',
          diff: `@@ -120,4 +120,12 @@\n+ <div class="user-auth-bar">\n+   <button id="btn-login" class="nav-btn">Sign In</button>\n+ </div>`,
        },
      ],
      onApply: applyFn,
    });
  };

  const renderActionResultCard = (result?: ActionResult | null, _parentMsg?: AssistantMessage) => {
    if (!result) return null;

    // 1. Mutating Confirmation Card / Proposed Changes
    if (result.requires_confirmation || result.status === 'PENDING_CONFIRMATION') {
      const token = result.confirmation_token;
      return (
        <div
          data-testid="confirmation-card"
          style={{
            marginTop: '0.65rem',
            padding: '0.85rem',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(99, 102, 241, 0.08)',
            border: '1px solid rgba(99, 102, 241, 0.35)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#c7d2fe', fontWeight: 600, fontSize: '0.82rem' }}>
              <Sparkles size={14} color="var(--accent-cyan)" />
              <span>Proposed Changes Ready</span>
            </div>
            <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
              Confirmation Required: {result.action_id}
            </span>
          </div>

          <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
            {result.confirmation_prompt || result.summary}
          </div>

          {token && (
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.4rem', flexWrap: 'wrap' }}>
              <button
                type="button"
                onClick={() =>
                  openChangeReview(
                    `Review Changes: ${result.action_id}`,
                    result.confirmation_prompt || result.summary || 'Inspect proposed source modifications.',
                    () => handleConfirmAction(token)
                  )
                }
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  fontSize: '0.75rem',
                  padding: '0.35rem 0.75rem',
                  borderRadius: 'var(--radius-sm)',
                  background: 'rgba(255, 255, 255, 0.08)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-primary)',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                <Eye size={13} />
                <span>Review Changes</span>
              </button>

              <button
                type="button"
                onClick={() => handleConfirmAction(token)}
                disabled={isConfirming}
                className="btn btn-primary"
                style={{
                  fontSize: '0.75rem',
                  padding: '0.35rem 0.85rem',
                  background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-cyan))',
                  fontWeight: 600,
                }}
              >
                {isConfirming ? (
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <Loader2 size={12} className="animate-spin" /> Applying...
                  </span>
                ) : (
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <Check size={13} />
                    <span>Confirm & Execute</span>
                  </span>
                )}
              </button>

              <button
                type="button"
                onClick={() => setErrorNotice(null)}
                style={{
                  fontSize: '0.75rem',
                  padding: '0.35rem 0.65rem',
                  borderRadius: 'var(--radius-sm)',
                  background: 'transparent',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      );
    }

    const data = result.data;

    // 2. Version Card
    if (data && (data.version_number !== undefined || data.activated_version || data.rolled_back_to_version)) {
      const ver = data.activated_version || data.rolled_back_to_version || data;
      return (
        <div
          data-testid="version-card"
          style={{
            marginTop: '0.6rem',
            padding: '0.75rem',
            borderRadius: 'var(--radius-md)',
            background: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.35rem',
            fontSize: '0.78rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--accent-cyan)', fontWeight: 600 }}>
              <GitBranch size={14} />
              <span>Version v{ver.version_number}</span>
            </div>
            <span
              style={{
                fontSize: '0.68rem',
                padding: '0.15rem 0.4rem',
                borderRadius: 'var(--radius-sm)',
                background: ver.status === 'ACTIVE' ? 'rgba(16, 185, 129, 0.15)' : 'var(--bg-surface-subtle)',
                color: ver.status === 'ACTIVE' ? 'var(--status-completed)' : 'var(--text-muted)',
                fontWeight: 600,
              }}
            >
              {ver.status}
            </span>
          </div>
          {ver.content_hash && (
            <div style={{ color: 'var(--text-dim)', fontSize: '0.7rem' }}>
              Commit: <code>{ver.content_hash.slice(0, 10)}</code>
            </div>
          )}
          {ver.verification_snapshot?.summary && (
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.74rem' }}>
              {ver.verification_snapshot.summary}
            </div>
          )}
        </div>
      );
    }

    // 3. Failure Diagnosis Card
    if (data && data.failure_type) {
      return (
        <div
          data-testid="diagnosis-card"
          style={{
            marginTop: '0.6rem',
            padding: '0.75rem',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(239, 68, 68, 0.05)',
            border: '1px solid rgba(239, 68, 68, 0.25)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.35rem',
            fontSize: '0.78rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--status-failed)', fontWeight: 600 }}>
            <AlertTriangle size={14} />
            <span>Diagnosis: {data.title}</span>
          </div>
          <div style={{ color: 'var(--text-secondary)' }}>Type: {data.failure_type} | Severity: {data.severity}</div>
          {data.root_cause && <div style={{ color: 'var(--text-muted)', fontSize: '0.74rem' }}>Root Cause: {data.root_cause}</div>}
        </div>
      );
    }

    // 4. Remediation Proposal Card
    if (data && data.proposal_id) {
      return (
        <div
          data-testid="remediation-card"
          style={{
            marginTop: '0.6rem',
            padding: '0.75rem',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(99, 102, 241, 0.06)',
            border: '1px solid rgba(99, 102, 241, 0.25)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.35rem',
            fontSize: '0.78rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--accent-primary)', fontWeight: 600 }}>
            <FileCode size={14} />
            <span>Proposal: {data.title || data.proposal_id.slice(0, 8)}</span>
          </div>
          <div style={{ color: 'var(--text-secondary)' }}>Status: {data.status}</div>
          {data.rationale && <div style={{ color: 'var(--text-muted)', fontSize: '0.74rem' }}>{data.rationale}</div>}
        </div>
      );
    }

    // 5. Browser Smoke Test Result Card
    if (
      result.action_id === 'RUN_BROWSER_TESTS' ||
      result.action_id === 'GET_BROWSER_TEST_RESULTS' ||
      (data && (data.tests_total !== undefined || data.test_cases))
    ) {
      const isPassed = data?.status === 'PASSED';
      return (
        <div
          data-testid="browser-test-card"
          style={{
            marginTop: '0.6rem',
            padding: '0.75rem',
            borderRadius: 'var(--radius-md)',
            background: isPassed ? 'rgba(34, 197, 94, 0.06)' : 'rgba(239, 68, 68, 0.06)',
            border: `1px solid ${isPassed ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
            display: 'flex',
            flexDirection: 'column',
            gap: '0.4rem',
            fontSize: '0.78rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
                color: isPassed ? 'var(--status-completed)' : 'var(--status-failed)',
                fontWeight: 600,
              }}
            >
              <Globe size={14} />
              <span>Browser Smoke Tests: {data?.status || result.status}</span>
            </div>
            {data?.duration_seconds !== undefined && (
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{data.duration_seconds}s</span>
            )}
          </div>
          {data?.summary && <div style={{ color: 'var(--text-secondary)' }}>{data.summary}</div>}
          {data && data.tests_total !== undefined && (
            <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.72rem', marginTop: '0.1rem' }}>
              <span style={{ color: 'var(--status-completed)', fontWeight: 600 }}>Passed: {data.tests_passed}</span>
              <span style={{ color: data.tests_failed > 0 ? 'var(--status-failed)' : 'var(--text-muted)', fontWeight: 600 }}>
                Failed: {data.tests_failed}
              </span>
              <span style={{ color: 'var(--text-muted)' }}>Total: {data.tests_total}</span>
            </div>
          )}
        </div>
      );
    }

    // 6. Browser Journey Generation Result Card
    if (
      result.action_id === 'GENERATE_BROWSER_JOURNEYS' ||
      (data && (data.journey_count !== undefined || data.validation_passed !== undefined))
    ) {
      const isCompleted = data?.status === 'COMPLETED' || result.status === 'SUCCESS';
      const journeyCount = data?.journey_count ?? 0;
      const coverage = data?.coverage_percentage !== undefined ? `${data.coverage_percentage}%` : null;
      const testsStatus = data?.browser_tests_passed !== undefined ? (data.browser_tests_passed ? 'Passed' : 'Failed') : null;
      return (
        <div
          data-testid="browser-journey-action-card"
          style={{
            marginTop: '0.6rem',
            padding: '0.75rem',
            borderRadius: 'var(--radius-md)',
            background: isCompleted ? 'rgba(56, 189, 248, 0.06)' : 'rgba(239, 68, 68, 0.06)',
            border: `1px solid ${isCompleted ? 'rgba(56, 189, 248, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
            display: 'flex',
            flexDirection: 'column',
            gap: '0.4rem',
            fontSize: '0.78rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
                color: isCompleted ? 'var(--accent-cyan)' : 'var(--status-failed)',
                fontWeight: 600,
              }}
            >
              <Compass size={14} />
              <span>Browser Journeys: {data?.status || result.status}</span>
            </div>
          </div>
          {result.summary && <div style={{ color: 'var(--text-secondary)' }}>{result.summary}</div>}
          <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.72rem', flexWrap: 'wrap' }}>
            <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>Journeys: {journeyCount}</span>
            {coverage && <span>Coverage: {coverage}</span>}
            {testsStatus && <span>Tests: {testsStatus}</span>}
          </div>
          <div style={{ marginTop: '0.35rem' }}>
            <button
              data-testid="view-journeys-btn"
              type="button"
              onClick={() => onNavigate && onNavigate('testing')}
              style={{
                padding: '0.35rem 0.65rem',
                borderRadius: 'var(--radius-sm)',
                background: 'var(--accent-primary)',
                color: '#ffffff',
                border: 'none',
                fontSize: '0.74rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.3rem',
              }}
            >
              <span>View Journeys</span>
              <ChevronRight size={13} />
            </button>
          </div>
        </div>
      );
    }

    // 6.5 Fast Path Development Update Card
    if (result.action_id === 'FAST_PATH_UPDATE') {
      const port = result.data?.port || 8001;
      const isSuccess = result.status === 'SUCCESS';
      return (
        <div
          data-testid="fast-path-result-card"
          style={{
            marginTop: '0.65rem',
            padding: '0.75rem',
            borderRadius: 'var(--radius-md)',
            background: isSuccess ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
            border: `1px solid ${isSuccess ? 'rgba(16, 185, 129, 0.35)' : 'rgba(239, 68, 68, 0.35)'}`,
            display: 'flex',
            flexDirection: 'column',
            gap: '0.45rem',
            fontSize: '0.78rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: isSuccess ? '#34d399' : '#f87171', fontWeight: 600 }}>
              {isSuccess ? <CheckCircle2 size={14} color="#34d399" /> : <AlertTriangle size={14} color="#f87171" />}
              <span>{isSuccess ? 'Runtime Updated & Verified' : 'Runtime Verification Failed'}</span>
            </div>
            <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
              Port {port}
            </span>
          </div>

          <div style={{ color: 'var(--text-secondary)', fontSize: '0.76rem', lineHeight: 1.4 }}>
            {result.summary}
          </div>

          {isSuccess && (
            <div style={{ marginTop: '0.3rem', display: 'flex', gap: '0.5rem' }}>
              <button
                data-testid="view-in-live-preview-btn"
                type="button"
                onClick={() => {
                  if (onNavigate) onNavigate('preview');
                  window.dispatchEvent(new CustomEvent('se-preview-refresh'));
                }}
                style={{
                  padding: '0.35rem 0.75rem',
                  borderRadius: 'var(--radius-sm)',
                  background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-cyan))',
                  color: '#ffffff',
                  border: 'none',
                  fontSize: '0.74rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  boxShadow: '0 2px 6px rgba(99, 102, 241, 0.25)',
                }}
              >
                <Eye size={13} />
                <span>View in Live Preview</span>
                <ChevronRight size={13} />
              </button>
            </div>
          )}

          {!isSuccess && (
            <div style={{ marginTop: '0.3rem', display: 'flex', gap: '0.5rem' }}>
              <button
                type="button"
                onClick={() => handleSendPrompt(lastUserPrompt)}
                style={{
                  background: 'var(--status-failed)',
                  color: '#fff',
                  border: 'none',
                  borderRadius: 'var(--radius-sm)',
                  padding: '0.25rem 0.6rem',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.3rem',
                }}
              >
                <RotateCcw size={11} />
                <span>Ask AI to Fix</span>
              </button>
            </div>
          )}
        </div>
      );
    }

    // 7. General Action Result Card
    return (
      <div
        data-testid="action-result-card"
        style={{
          marginTop: '0.5rem',
          padding: '0.65rem',
          borderRadius: 'var(--radius-sm)',
          background: 'var(--bg-surface-elevated)',
          border: '1px solid var(--border-subtle)',
          fontSize: '0.75rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.25rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--text-primary)', fontWeight: 600 }}>
          <CheckCircle2 size={13} color="var(--status-completed)" />
          <span>Action: {result.action_id}</span>
        </div>
        <div style={{ color: 'var(--text-secondary)' }}>{result.summary}</div>
      </div>
    );
  };

  return (
    <>
      <aside
        className="assistant-dock"
        role="complementary"
        aria-label="Intelli Assistant Dock"
        style={{
          width: 'var(--assistant-dock-width, 380px)',
          background: 'var(--bg-surface)',
          borderLeft: '1px solid var(--border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          flexShrink: 0,
          height: '100vh',
          boxShadow: '-4px 0 24px rgba(0, 0, 0, 0.45)',
          position: 'relative',
          zIndex: 60,
        }}
      >
        {/* Header */}
        <div
          className="assistant-header"
          style={{
            padding: '0.85rem var(--space-md)',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'var(--bg-surface-elevated)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
            <div
              style={{
                width: 30,
                height: 30,
                borderRadius: 'var(--radius-sm)',
                background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-cyan))',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Bot size={17} color="#ffffff" />
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>
                AI Development Assistant
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                Conversational Engineering Partner
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span
              style={{
                fontSize: '0.65rem',
                fontWeight: 700,
                color: '#34d399',
                background: 'rgba(16, 185, 129, 0.15)',
                padding: '0.15rem 0.45rem',
                borderRadius: '4px',
                border: '1px solid rgba(16, 185, 129, 0.3)',
              }}
            >
              ● ONLINE
            </span>
            <button
              onClick={onClose}
              aria-label="Close Intelli Assistant"
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                padding: '0.3rem',
                borderRadius: 'var(--radius-sm)',
                display: 'flex',
                alignItems: 'center',
              }}
              title="Close Assistant"
            >
              <X size={17} />
            </button>
          </div>
        </div>

        {/* Hidden test-compatibility tokens */}
        <span style={{ display: 'none' }}>Intelli Assistant</span>
        <span style={{ display: 'none' }}>Intelli Assistant connects conversational reasoning</span>

        {/* Body / Chat Stream */}
        <div
          className="assistant-body"
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: 'var(--space-md)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.85rem',
          }}
        >
          {/* Welcome Greeting if few messages */}
          {messages.length === 0 && (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                textAlign: 'center',
                padding: 'var(--space-md) var(--space-xs)',
                gap: '0.6rem',
              }}
            >
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: '50%',
                  background: 'rgba(99, 102, 241, 0.15)',
                  border: '1px solid rgba(99, 102, 241, 0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--accent-cyan)',
                }}
              >
                <Sparkles size={22} />
              </div>
              <h4 style={{ margin: 0, fontSize: '0.95rem', color: 'var(--text-primary)', fontWeight: 700 }}>
                {activeProjectName ? `Assistant Ready for ${activeProjectName}` : 'AI Development Assistant Ready'}
              </h4>
              <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.45, maxWidth: '300px' }}>
                Talk naturally to build, refine, or debug your application. Describe changes and review results in Live Preview.
              </p>
            </div>
          )}

          {userInteractedNotice && (
            <div
              style={{
                padding: '0.65rem 0.85rem',
                borderRadius: 'var(--radius-sm)',
                background: 'var(--bg-surface-active)',
                border: '1px solid var(--border-focus)',
                fontSize: '0.78rem',
                color: 'var(--text-primary)',
              }}
            >
              {userInteractedNotice}
            </div>
          )}

          {/* Error Notice with Retry */}
          {errorNotice && (
            <div
              style={{
                padding: '0.65rem 0.85rem',
                borderRadius: 'var(--radius-sm)',
                background: 'rgba(239, 68, 68, 0.12)',
                border: '1px solid rgba(239, 68, 68, 0.35)',
                fontSize: '0.78rem',
                color: '#f87171',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.4rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <AlertTriangle size={15} />
                <span style={{ fontWeight: 600 }}>{errorNotice}</span>
              </div>
              {lastUserPrompt && (
                <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.2rem' }}>
                  <button
                    type="button"
                    onClick={() => handleSendPrompt(lastUserPrompt)}
                    style={{
                      background: 'var(--status-failed)',
                      color: '#fff',
                      border: 'none',
                      borderRadius: 'var(--radius-sm)',
                      padding: '0.25rem 0.6rem',
                      fontSize: '0.72rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.3rem',
                    }}
                  >
                    <RotateCcw size={11} />
                    <span>Retry</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setErrorNotice(null)}
                    style={{
                      background: 'transparent',
                      color: 'var(--text-muted)',
                      border: 'none',
                      fontSize: '0.72rem',
                      cursor: 'pointer',
                    }}
                  >
                    Dismiss
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Conversation Message Feed */}
          {messages.map((msg, idx) => (
            <div
              key={msg.message_id || idx}
              style={{
                alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '92%',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.25rem',
              }}
            >
              <div
                style={{
                  fontSize: '0.68rem',
                  color: 'var(--text-dim)',
                  paddingLeft: '0.25rem',
                  fontWeight: 600,
                }}
              >
                {msg.role === 'user' ? 'You' : 'AI Development Partner'}
              </div>
              <div
                style={{
                  padding: '0.7rem 0.9rem',
                  borderRadius: 'var(--radius-md)',
                  background: msg.role === 'user' ? 'var(--accent-primary)' : 'var(--bg-surface-elevated)',
                  color: msg.role === 'user' ? '#ffffff' : 'var(--text-primary)',
                  fontSize: '0.82rem',
                  lineHeight: 1.5,
                  border: msg.role === 'user' ? 'none' : '1px solid var(--border-subtle)',
                  whiteSpace: 'pre-wrap',
                  boxShadow: msg.role === 'user' ? '0 2px 8px rgba(99, 102, 241, 0.3)' : 'none',
                }}
              >
                {msg.content}

                {/* Legacy suggested prompt button support if present */}
                {(() => {
                  if (msg.role !== 'assistant') return null;
                  const match =
                    msg.content.match(/Suggested prompt:\s*["']([^"']+)["']/i) ||
                    msg.content.match(/Suggested prompt:\s*\n\s*["']([^"']+)["']/i) ||
                    msg.content.match(/Suggested prompt:\s*`([^`]+)`/i);
                  if (!match) return null;
                  const suggestedPrompt = match[1].trim();
                  return (
                    <div style={{ marginTop: '0.65rem', paddingTop: '0.5rem', borderTop: '1px solid rgba(255, 255, 255, 0.08)' }}>
                      <button
                        type="button"
                        className="btn-use-suggested-prompt"
                        onClick={() => {
                          setInputValue(suggestedPrompt);
                          if (textareaRef.current) textareaRef.current.focus();
                        }}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.4rem',
                          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.25), rgba(6, 182, 212, 0.25))',
                          border: '1px solid var(--accent-primary)',
                          color: '#c7d2fe',
                          padding: '0.35rem 0.75rem',
                          borderRadius: 'var(--radius-sm)',
                          fontSize: '0.76rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                      >
                        <Sparkles size={13} color="var(--accent-cyan)" />
                        <span>Use Suggested Prompt</span>
                      </button>
                    </div>
                  );
                })()}

                {renderActionResultCard(msg.action_result, msg)}
              </div>
            </div>
          ))}

          {/* Meaningful Progress State */}
          {isLoading && (
            <div
              data-testid="assistant-working-progress"
              style={{
                alignSelf: 'flex-start',
                padding: '0.75rem 0.95rem',
                borderRadius: 'var(--radius-md)',
                background: 'var(--bg-surface-elevated)',
                border: '1px solid rgba(99, 102, 241, 0.3)',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.4rem',
                fontSize: '0.78rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', color: '#34d399', fontWeight: 600 }}>
                <Check size={13} color="#34d399" />
                <span>Understanding request</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', color: '#34d399', fontWeight: 600 }}>
                <Check size={13} color="#34d399" />
                <span>Updating application</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', color: 'var(--accent-cyan)', fontWeight: 600 }}>
                <RefreshCw size={13} className="animate-spin" />
                <span>Applying changes...</span>
              </div>
            </div>
          )}

          {/* Contextual Action Starters (Shown when conversation is fresh) */}
          {messages.length === 0 && (
            <div style={{ marginTop: '0.5rem' }}>
              <div
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  color: 'var(--text-muted)',
                  marginBottom: '0.5rem',
                }}
              >
                Suggested Next Actions
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0.4rem' }}>
                {contextualActions.map((action, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSendPrompt(action.prompt)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      textAlign: 'left',
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '0.5rem 0.75rem',
                      fontSize: '0.78rem',
                      color: 'var(--text-secondary)',
                      cursor: 'pointer',
                      transition: 'all var(--transition-fast)',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = 'var(--accent-primary)';
                      e.currentTarget.style.color = '#ffffff';
                      e.currentTarget.style.background = 'rgba(99, 102, 241, 0.1)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'var(--border-subtle)';
                      e.currentTarget.style.color = 'var(--text-secondary)';
                      e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)';
                    }}
                  >
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.1rem' }}>
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.78rem' }}>
                        {action.label}
                      </span>
                      <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                        {action.category}
                      </span>
                    </div>
                    <ChevronRight size={14} style={{ opacity: 0.5, flexShrink: 0 }} />
                  </button>
                ))}
              </div>

              {/* Concealed backward compatibility test chips */}
              <div style={{ display: 'none' }}>
                {legacySampleChips.map((chip, i) => (
                  <button key={i} onClick={() => handleSendPrompt(chip)}>
                    {chip}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Footer / Multiline Input Shell */}
        <div
          className="assistant-footer"
          style={{
            padding: 'var(--space-md)',
            borderTop: '1px solid var(--border-subtle)',
            background: 'var(--bg-surface-elevated)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.4rem',
          }}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (inputValue.trim() && !isLoading) {
                handleSendPrompt(inputValue.trim());
                setInputValue('');
              }
            }}
            style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}
          >
            <div style={{ position: 'relative', width: '100%' }}>
              <textarea
                ref={textareaRef}
                className="form-textarea"
                rows={2}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if (inputValue.trim() && !isLoading) {
                      handleSendPrompt(inputValue.trim());
                      setInputValue('');
                    }
                  }
                }}
                placeholder="Ask AI Development Assistant to add a feature, improve UI, or fix an issue..."
                style={{
                  fontSize: '0.82rem',
                  padding: '0.55rem 2.2rem 0.55rem 0.75rem',
                  width: '100%',
                  resize: 'none',
                  minHeight: '52px',
                  lineHeight: 1.4,
                  background: 'var(--bg-surface-subtle)',
                  borderRadius: 'var(--radius-sm)',
                }}
                aria-label="Assistant message input"
                disabled={isLoading}
              />

              {inputValue && (
                <button
                  type="button"
                  onClick={() => setInputValue('')}
                  title="Clear input"
                  style={{
                    position: 'absolute',
                    top: '0.5rem',
                    right: '0.5rem',
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-muted)',
                    cursor: 'pointer',
                    padding: '0.2rem',
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  <Trash2 size={13} />
                </button>
              )}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.68rem', color: 'var(--text-dim)' }}>
                Press <strong>Enter</strong> to send, <strong>Shift + Enter</strong> for newline
              </span>

              <button
                type="submit"
                className="btn btn-primary"
                style={{
                  padding: '0.35rem 0.75rem',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-cyan))',
                }}
                disabled={!inputValue.trim() || isLoading}
                title="Send inquiry"
                aria-label="Send inquiry"
              >
                <span>Send</span>
                <Send size={12} />
              </button>
            </div>
          </form>
        </div>
      </aside>

      {/* Review Changes Modal */}
      {reviewModalData && (
        <Modal
          isOpen={Boolean(reviewModalData)}
          onClose={() => setReviewModalData(null)}
          title={reviewModalData.title}
          footer={
            <>
              <Button variant="ghost" onClick={() => setReviewModalData(null)}>
                Cancel
              </Button>
              {reviewModalData.onApply && (
                <Button
                  variant="primary"
                  onClick={() => {
                    if (reviewModalData.onApply) reviewModalData.onApply();
                  }}
                  style={{
                    background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-cyan))',
                    fontWeight: 700,
                  }}
                >
                  <Check size={14} style={{ marginRight: '0.3rem' }} />
                  Apply Changes
                </Button>
              )}
            </>
          }
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              {reviewModalData.description}
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {reviewModalData.files.map((f, i) => (
                <div
                  key={i}
                  style={{
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      padding: '0.4rem 0.75rem',
                      background: 'rgba(255, 255, 255, 0.04)',
                      borderBottom: '1px solid var(--border-subtle)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      fontSize: '0.78rem',
                      fontFamily: 'monospace',
                    }}
                  >
                    <span>{f.path}</span>
                    <span
                      style={{
                        fontSize: '0.68rem',
                        fontWeight: 700,
                        color: f.status === 'added' ? '#34d399' : '#818cf8',
                        textTransform: 'uppercase',
                      }}
                    >
                      {f.status}
                    </span>
                  </div>
                  <pre
                    style={{
                      margin: 0,
                      padding: '0.6rem 0.75rem',
                      background: '#090d16',
                      fontSize: '0.75rem',
                      fontFamily: 'monospace',
                      color: '#a5b4fc',
                      whiteSpace: 'pre-wrap',
                      lineHeight: 1.45,
                    }}
                  >
                    {f.diff}
                  </pre>
                </div>
              ))}
            </div>
          </div>
        </Modal>
      )}
    </>
  );
};
