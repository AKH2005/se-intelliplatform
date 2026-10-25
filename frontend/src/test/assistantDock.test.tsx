import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AssistantDock } from '../components/assistant/AssistantDock';
import { assistantApi } from '../services/assistantApi';

vi.mock('../services/assistantApi', () => ({
  assistantApi: {
    listConversations: vi.fn(),
    sendMessage: vi.fn(),
    confirmAction: vi.fn(),
    executeActionDirect: vi.fn(),
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
});
