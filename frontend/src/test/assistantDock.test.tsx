import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AssistantDock } from '../components/assistant/AssistantDock';
import { assistantApi } from '../services/assistantApi';

vi.mock('../services/assistantApi', () => ({
  assistantApi: {
    createConversation: vi.fn(),
    deleteConversation: vi.fn(),
    listConversations: vi.fn(),
    getConversation: vi.fn(),
    sendMessage: vi.fn(),
    confirmAction: vi.fn(),
    executeActionDirect: vi.fn(),
  },
}));

vi.mock('../services/developmentVersionApi', () => ({
  developmentVersionApi: {
    getActiveVersion: vi.fn().mockResolvedValue({ version_number: 3, id: 'ver-3' }),
  },
}));

describe('Phase 11I: Intelli Assistant Dock UI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders dock with header, title, and initial preview chips', () => {
    vi.mocked(assistantApi.listConversations).mockResolvedValue({ items: [], total: 0 });

    render(
      <AssistantDock
        isOpen={true}
        onClose={() => {}}
        activeProjectName="Solaris Engine"
        projectId="proj-11i"
      />
    );

    expect(screen.getByText('Intelli Assistant')).toBeInTheDocument();
    expect(screen.getByText('Assistant Ready for Solaris Engine')).toBeInTheDocument();
    expect(screen.getByText('Which workflows are available to run?')).toBeInTheDocument();
  });

  it('does not render when isOpen is false', () => {
    const { container } = render(
      <AssistantDock
        isOpen={false}
        onClose={() => {}}
        activeProjectName="Solaris Engine"
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('sends user message and displays assistant response with version card', async () => {
    vi.mocked(assistantApi.listConversations).mockResolvedValue({ items: [], total: 0 });
    vi.mocked(assistantApi.sendMessage).mockResolvedValue({
      message_id: 'msg-resp-1',
      conversation_id: 'conv-1',
      role: 'assistant',
      content: 'Here is the active release version details.',
      action_id: 'GET_ACTIVE_VERSION',
      action_status: 'SUCCESS',
      action_result: {
        action_id: 'GET_ACTIVE_VERSION',
        status: 'SUCCESS',
        summary: 'Active version is v2.',
        data: {
          version_number: 2,
          status: 'ACTIVE',
          content_hash: 'abc1234567890',
          verification_snapshot: {
            summary: 'All 3 tests passed',
          },
        },
        requires_confirmation: false,
        warnings: [],
        errors: [],
      },
      created_at: new Date().toISOString(),
    });

    render(
      <AssistantDock
        isOpen={true}
        onClose={() => {}}
        activeProjectName="Solaris Engine"
        projectId="proj-11i"
      />
    );

    const input = screen.getByLabelText('Assistant message input');
    fireEvent.change(input, { target: { value: 'Show active version' } });

    const submitBtn = screen.getByLabelText('Send inquiry');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText('Show active version')).toBeInTheDocument();
      expect(screen.getByText('Here is the active release version details.')).toBeInTheDocument();
      expect(screen.getByTestId('version-card')).toBeInTheDocument();
      expect(screen.getByText('Version v2')).toBeInTheDocument();
      expect(screen.getByText('ACTIVE')).toBeInTheDocument();
    });
  });

  it('renders confirmation card for mutating action and invokes confirmAction on click', async () => {
    vi.mocked(assistantApi.listConversations).mockResolvedValue({ items: [], total: 0 });
    vi.mocked(assistantApi.sendMessage).mockResolvedValue({
      message_id: 'msg-resp-mutating',
      conversation_id: 'conv-1',
      role: 'assistant',
      content: 'I can activate version 3 for you, but this is a mutating action requiring confirmation.',
      action_id: 'ACTIVATE_VERSION',
      action_status: 'PENDING_CONFIRMATION',
      action_result: {
        action_id: 'ACTIVATE_VERSION',
        status: 'PENDING_CONFIRMATION',
        summary: 'Action ACTIVATE_VERSION requires explicit human confirmation.',
        confirmation_token: 'secret-anti-replay-token-12345',
        confirmation_prompt: 'Are you sure you want to activate version 3?',
        requires_confirmation: true,
        warnings: [],
        errors: [],
      },
      created_at: new Date().toISOString(),
    });

    vi.mocked(assistantApi.confirmAction).mockResolvedValue({
      action_id: 'ACTIVATE_VERSION',
      status: 'SUCCESS',
      summary: 'Version v3 is now active.',
      data: {
        activated_version: {
          version_number: 3,
          status: 'ACTIVE',
          content_hash: 'def456',
        },
      },
      requires_confirmation: false,
      warnings: [],
      errors: [],
    });

    render(
      <AssistantDock
        isOpen={true}
        onClose={() => {}}
        activeProjectName="Solaris Engine"
        projectId="proj-11i"
      />
    );

    const input = screen.getByLabelText('Assistant message input');
    fireEvent.change(input, { target: { value: 'Activate version 3' } });
    fireEvent.click(screen.getByLabelText('Send inquiry'));

    await waitFor(() => {
      expect(screen.getByTestId('confirmation-card')).toBeInTheDocument();
      expect(screen.getByText(/Confirmation Required: ACTIVATE_VERSION/i)).toBeInTheDocument();
      expect(screen.getByText('Confirm & Execute')).toBeInTheDocument();
    });

    const confirmBtn = screen.getByText('Confirm & Execute');
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(assistantApi.confirmAction).toHaveBeenCalledWith('proj-11i', {
        confirmation_token: 'secret-anti-replay-token-12345',
      });
      expect(screen.getByText(/Action ACTIVATE_VERSION confirmed and executed successfully/i)).toBeInTheDocument();
    });
  });

  it('displays error notice when API fails', async () => {
    vi.mocked(assistantApi.listConversations).mockResolvedValue({ items: [], total: 0 });
    vi.mocked(assistantApi.sendMessage).mockRejectedValue(new Error('Network connectivity lost'));

    render(
      <AssistantDock
        isOpen={true}
        onClose={() => {}}
        activeProjectName="Solaris Engine"
        projectId="proj-11i"
      />
    );

    const input = screen.getByLabelText('Assistant message input');
    fireEvent.change(input, { target: { value: 'Analyze failures' } });
    fireEvent.click(screen.getByLabelText('Send inquiry'));

    await waitFor(() => {
      expect(screen.getByText('Network connectivity lost')).toBeInTheDocument();
    });
  });

  it('displays active project name and active version badge in context strip', async () => {
    vi.mocked(assistantApi.listConversations).mockResolvedValue({ items: [], total: 0 });

    render(
      <AssistantDock
        isOpen={true}
        onClose={() => {}}
        activeProjectName="MiniTask App"
        projectId="proj-minitask"
        activeVersionNumber={2}
      />
    );

    expect(screen.getByTestId('assistant-project-badge')).toHaveTextContent('MiniTask App');
    expect(screen.getByTestId('assistant-version-badge')).toHaveTextContent('v2');
  });

  it('allows starting a new conversation via the New Chat button', async () => {
    vi.mocked(assistantApi.listConversations).mockResolvedValue({
      items: [
        {
          conversation_id: 'conv-old',
          project_id: 'proj-11i',
          title: 'Old Thread',
          messages: [
            {
              message_id: 'm1',
              conversation_id: 'conv-old',
              role: 'user',
              content: 'Old question',
              created_at: new Date().toISOString(),
            },
          ],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
      total: 1,
    });
    vi.mocked(assistantApi.createConversation).mockResolvedValue({
      conversation_id: 'conv-fresh',
      project_id: 'proj-11i',
      title: 'New Conversation',
      messages: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });

    render(
      <AssistantDock
        isOpen={true}
        onClose={() => {}}
        activeProjectName="Solaris Engine"
        projectId="proj-11i"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Old question')).toBeInTheDocument();
    });

    const newChatBtn = screen.getByTestId('new-conversation-btn');
    fireEvent.click(newChatBtn);

    await waitFor(() => {
      expect(assistantApi.createConversation).toHaveBeenCalledWith('proj-11i');
      expect(screen.queryByText('Old question')).not.toBeInTheDocument();
    });
  });

  it('prevents duplicate submissions when send action is triggered while loading', async () => {
    vi.mocked(assistantApi.listConversations).mockResolvedValue({ items: [], total: 0 });

    let resolveSendMessage: (val: any) => void;
    const pendingPromise = new Promise((resolve) => {
      resolveSendMessage = resolve;
    });
    vi.mocked(assistantApi.sendMessage).mockReturnValue(pendingPromise as any);

    render(
      <AssistantDock
        isOpen={true}
        onClose={() => {}}
        activeProjectName="Solaris Engine"
        projectId="proj-11i"
      />
    );

    const input = screen.getByLabelText('Assistant message input');
    fireEvent.change(input, { target: { value: 'Explain architecture' } });

    const sendBtn = screen.getByLabelText('Send inquiry');
    fireEvent.click(sendBtn);

    // Click again immediately while loading
    fireEvent.click(sendBtn);
    fireEvent.click(sendBtn);

    expect(assistantApi.sendMessage).toHaveBeenCalledTimes(1);

    // Resolve response to clear loading state
    resolveSendMessage!({
      message_id: 'msg-done',
      conversation_id: 'conv-done',
      role: 'assistant',
      content: 'Here is the architecture summary.',
      created_at: new Date().toISOString(),
    });

    await waitFor(() => {
      expect(screen.getByText('Here is the architecture summary.')).toBeInTheDocument();
    });
  });

  it('retries last failed prompt when retry button in error notice is clicked', async () => {
    vi.mocked(assistantApi.listConversations).mockResolvedValue({ items: [], total: 0 });
    vi.mocked(assistantApi.sendMessage)
      .mockRejectedValueOnce(new Error('503 Service Unavailable'))
      .mockResolvedValueOnce({
        message_id: 'msg-retry-ok',
        conversation_id: 'conv-retry-ok',
        role: 'assistant',
        content: 'Success after retry.',
        created_at: new Date().toISOString(),
      });

    render(
      <AssistantDock
        isOpen={true}
        onClose={() => {}}
        activeProjectName="Solaris Engine"
        projectId="proj-11i"
      />
    );

    const input = screen.getByLabelText('Assistant message input');
    fireEvent.change(input, { target: { value: 'Debug login issue' } });
    fireEvent.click(screen.getByLabelText('Send inquiry'));

    await waitFor(() => {
      expect(screen.getByTestId('assistant-error-banner')).toBeInTheDocument();
      expect(screen.getByTestId('retry-message-btn')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('retry-message-btn'));

    await waitFor(() => {
      expect(assistantApi.sendMessage).toHaveBeenCalledTimes(2);
      expect(screen.getByText('Success after retry.')).toBeInTheDocument();
    });
  });

  it('streams assistant response progressively when sendMessageStream is available', async () => {
    vi.mocked(assistantApi.listConversations).mockResolvedValue({ items: [], total: 0 });

    const mockStream = vi.fn().mockImplementation(async (_projectId, _payload, callbacks) => {
      callbacks?.onStart?.({ conversation_id: 'conv-stream-100' });
      callbacks?.onChunk?.('Streaming first chunk... ');
      callbacks?.onChunk?.('Streaming second chunk.');
      const finalMsg = {
        message_id: 'msg-stream-done',
        conversation_id: 'conv-stream-100',
        role: 'assistant',
        content: 'Streaming first chunk... Streaming second chunk.',
        created_at: new Date().toISOString(),
      };
      callbacks?.onDone?.(finalMsg);
      return finalMsg;
    });

    (assistantApi as any).sendMessageStream = mockStream;

    try {
      render(
        <AssistantDock
          isOpen={true}
          onClose={() => {}}
          activeProjectName="Solaris Engine"
          projectId="proj-stream"
        />
      );

      const input = screen.getByLabelText('Assistant message input');
      fireEvent.change(input, { target: { value: 'Test streaming output' } });
      fireEvent.click(screen.getByLabelText('Send inquiry'));

      await waitFor(() => {
        expect(mockStream).toHaveBeenCalled();
        expect(screen.getByText(/Streaming first chunk\.\.\. Streaming second chunk\./)).toBeInTheDocument();
      });
    } finally {
      delete (assistantApi as any).sendMessageStream;
    }
  });

  it('allows user to stop/cancel response generation while in progress', async () => {
    vi.mocked(assistantApi.listConversations).mockResolvedValue({ items: [], total: 0 });

    const mockStream = vi.fn().mockImplementation(async (_projectId, _payload, callbacks, options) => {
      callbacks?.onChunk?.('Partial answer before cancel...');
      return new Promise((_, reject) => {
        if (options?.signal) {
          options.signal.addEventListener('abort', () => {
            const abortErr = new Error('The user aborted a request.');
            abortErr.name = 'AbortError';
            reject(abortErr);
          });
        }
      });
    });

    (assistantApi as any).sendMessageStream = mockStream;

    try {
      render(
        <AssistantDock
          isOpen={true}
          onClose={() => {}}
          activeProjectName="Solaris Engine"
          projectId="proj-stream"
        />
      );

      const input = screen.getByLabelText('Assistant message input');
      fireEvent.change(input, { target: { value: 'Cancel me midway' } });
      fireEvent.click(screen.getByLabelText('Send inquiry'));

      await waitFor(() => {
        expect(screen.getByTestId('cancel-message-btn')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByTestId('cancel-message-btn'));

      await waitFor(() => {
        expect(screen.getByText(/Response generation was cancelled/)).toBeInTheDocument();
        expect(screen.getByText(/\*\(Generation stopped by user\)\*/)).toBeInTheDocument();
      });
    } finally {
      delete (assistantApi as any).sendMessageStream;
    }
  });

  describe('Diagnostic Error Handling & Guidance', () => {
    it('translates generic "Failed to fetch" into Backend Service Unavailable', async () => {
      vi.mocked(assistantApi.listConversations).mockResolvedValue({ items: [], total: 0 });
      vi.mocked(assistantApi.sendMessage).mockRejectedValue(new TypeError('Failed to fetch'));

      render(
        <AssistantDock
          isOpen={true}
          onClose={() => {}}
          activeProjectName="Carrom Master"
          projectId="proj-carrom"
        />
      );

      const input = screen.getByLabelText('Assistant message input');
      fireEvent.change(input, { target: { value: 'Add a login page.' } });
      fireEvent.click(screen.getByLabelText('Send inquiry'));

      await waitFor(() => {
        expect(screen.getByText('Backend Service Unavailable')).toBeInTheDocument();
        expect(
          screen.getByText(/Unable to reach the backend service\. Please check your network connection/i)
        ).toBeInTheDocument();
        expect(screen.getByTestId('retry-message-btn')).toBeInTheDocument();
      });
    });

    it('translates 401 Unauthorized into Authentication Session Expired', async () => {
      vi.mocked(assistantApi.listConversations).mockResolvedValue({ items: [], total: 0 });
      const authErr: any = new Error('Invalid token or token expired');
      authErr.status = 401;
      vi.mocked(assistantApi.sendMessage).mockRejectedValue(authErr);

      render(
        <AssistantDock
          isOpen={true}
          onClose={() => {}}
          activeProjectName="Carrom Master"
          projectId="proj-carrom"
        />
      );

      const input = screen.getByLabelText('Assistant message input');
      fireEvent.change(input, { target: { value: 'Add a login page.' } });
      fireEvent.click(screen.getByLabelText('Send inquiry'));

      await waitFor(() => {
        expect(screen.getByText('Authentication Session Expired')).toBeInTheDocument();
        expect(
          screen.getByText(/Your session token has expired or is invalid/i)
        ).toBeInTheDocument();
      });
    });

    it('translates 403 Forbidden into Permission Denied', async () => {
      vi.mocked(assistantApi.listConversations).mockResolvedValue({ items: [], total: 0 });
      const permErr: any = new Error('You do not have permission to access this project');
      permErr.status = 403;
      vi.mocked(assistantApi.sendMessage).mockRejectedValue(permErr);

      render(
        <AssistantDock
          isOpen={true}
          onClose={() => {}}
          activeProjectName="Carrom Master"
          projectId="proj-carrom"
        />
      );

      const input = screen.getByLabelText('Assistant message input');
      fireEvent.change(input, { target: { value: 'Add a login page.' } });
      fireEvent.click(screen.getByLabelText('Send inquiry'));

      await waitFor(() => {
        expect(screen.getByText('Permission Denied')).toBeInTheDocument();
        expect(
          screen.getByText(/You do not have permission to access or modify this project/i)
        ).toBeInTheDocument();
      });
    });

    it('translates 404 Not Found into Project Context Not Found', async () => {
      vi.mocked(assistantApi.listConversations).mockResolvedValue({ items: [], total: 0 });
      const notFoundErr: any = new Error("Project with identifier 'proj-xyz' was not found");
      notFoundErr.status = 404;
      vi.mocked(assistantApi.sendMessage).mockRejectedValue(notFoundErr);

      render(
        <AssistantDock
          isOpen={true}
          onClose={() => {}}
          activeProjectName="Carrom Master"
          projectId="proj-carrom"
        />
      );

      const input = screen.getByLabelText('Assistant message input');
      fireEvent.change(input, { target: { value: 'Add a login page.' } });
      fireEvent.click(screen.getByLabelText('Send inquiry'));

      await waitFor(() => {
        expect(screen.getByText('Project Context Not Found')).toBeInTheDocument();
      });
    });
  });
});


