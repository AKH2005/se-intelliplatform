import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../context/AuthContext';
import { ProjectProvider } from '../context/ProjectContext';
import { ModeProvider, MODE_STORAGE_KEY } from '../context/ModeContext';
import { App } from '../App';
import { FloatingAssistant } from '../components/assistant/FloatingAssistant';
import { chatApi } from '../services/chatApi';
import { authApi } from '../services/authApi';
import { projectsApi } from '../services/projectsApi';
import { ProjectResponse } from '../types/project';

const mockProjects: ProjectResponse[] = [
  {
    id: 'proj-p3-1',
    name: 'AI Code Reviewer',
    slug: 'ai-code-reviewer',
    description: 'Automated syntax and semantic review tool.',
    status: 'IN_PROGRESS',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const mockUser = {
  id: 'user-p3',
  name: 'Sam Engineer',
  email: 'sam@example.com',
  role: 'developer' as const,
  is_active: true,
  created_at: new Date().toISOString(),
};

function renderApp(initialMode: 'user' | 'developer' = 'user') {
  localStorage.clear();
  localStorage.setItem('se_auth_token', 'test-auth-token');
  localStorage.setItem(MODE_STORAGE_KEY, initialMode);

  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ProjectProvider>
          <ModeProvider>
            <App />
          </ModeProvider>
        </ProjectProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

describe('Phase 3: Global Floating AI Assistant & User Mode Dashboard', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    window.history.replaceState({}, '', '/projects');

    vi.spyOn(authApi, 'getMe').mockResolvedValue(mockUser);
    vi.spyOn(projectsApi, 'list').mockResolvedValue(mockProjects);
  });

  /* -------------------------------------------------------------------------
   * Part A: Floating AI Assistant
   * ----------------------------------------------------------------------- */
  it('1. Renders floating AI assistant launcher in both User Mode and Developer Mode', async () => {
    // In User Mode
    const { unmount } = renderApp('user');
    expect(await screen.findByRole('button', { name: /open global ai assistant/i })).toBeInTheDocument();
    unmount();

    // In Developer Mode
    renderApp('developer');
    expect(await screen.findByRole('button', { name: /open global ai assistant/i })).toBeInTheDocument();
  });

  it('2. Opens floating chat panel, renders welcome message, and handles conversation turns', async () => {
    vi.spyOn(chatApi, 'sendMessage').mockResolvedValue({
      response: 'In User Mode, beginners explore concepts and plan apps. In Developer Mode, you use Code Studio and previews.',
      provider: 'groq',
      model: 'openai/gpt-oss-20b',
    });

    render(<FloatingAssistant currentMode="user" />);

    // Click launcher
    const launcherBtn = screen.getByRole('button', { name: /open global ai assistant/i });
    fireEvent.click(launcherBtn);

    // Chat window appears
    expect(screen.getByRole('region', { name: /ai assistant chat window/i })).toBeInTheDocument();
    expect(screen.getByText(/I am your/i)).toBeInTheDocument();

    // Type and send a message
    const input = screen.getByPlaceholderText(/ask anything or request guidance/i);
    fireEvent.change(input, { target: { value: 'How do User Mode and Developer Mode differ?' } });

    const sendBtn = screen.getByRole('button', { name: /send message/i });
    fireEvent.click(sendBtn);

    // Verifies message sent and API called
    await waitFor(() => {
      expect(chatApi.sendMessage).toHaveBeenCalledWith(
        expect.objectContaining({
          message: 'How do User Mode and Developer Mode differ?',
        })
      );
    });

    // Displays real AI response
    expect(await screen.findByText(/In User Mode, beginners explore concepts/i)).toBeInTheDocument();
  });

  it('3. Displays genuine error message when AI service fails rather than fake answers', async () => {
    vi.spyOn(chatApi, 'sendMessage').mockRejectedValue(new Error('AI upstream provider rate limit reached'));

    render(<FloatingAssistant currentMode="developer" />);

    fireEvent.click(screen.getByRole('button', { name: /open global ai assistant/i }));
    const input = screen.getByPlaceholderText(/ask anything or request guidance/i);
    fireEvent.change(input, { target: { value: 'Will this fail gracefully?' } });

    fireEvent.click(screen.getByRole('button', { name: /send message/i }));

    await waitFor(() => {
      expect(chatApi.sendMessage).toHaveBeenCalled();
    });

    // Clearly displays error
    const errorElements = await screen.findAllByText(/AI upstream provider rate limit reached/i);
    expect(errorElements.length).toBeGreaterThanOrEqual(1);
  });

  it('4. Supports minimizing/closing the floating chat window', () => {
    render(<FloatingAssistant currentMode="user" />);

    // Open
    fireEvent.click(screen.getByRole('button', { name: /open global ai assistant/i }));
    expect(screen.getByRole('region', { name: /ai assistant chat window/i })).toBeInTheDocument();

    // Minimize
    fireEvent.click(screen.getByRole('button', { name: /minimize assistant/i }));
    expect(screen.queryByRole('region', { name: /ai assistant chat window/i })).not.toBeInTheDocument();
  });

  /* -------------------------------------------------------------------------
   * Part B: User Mode Dashboard & Guided App Creation
   * ----------------------------------------------------------------------- */
  it('5. User Mode renders welcoming heading, prompt input, real projects, and learning guides', async () => {
    renderApp('user');

    // Welcoming header & heading
    expect(await screen.findByText(/“Your ideas. Your AI. Your possibilities.”/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/describe what you want to build or ask anything/i)).toBeInTheDocument();

    // Real projects section
    expect(screen.getAllByText('AI Code Reviewer').length).toBeGreaterThanOrEqual(1);

    // Learning section
    expect(screen.getByText('Developer Mode Workspaces')).toBeInTheDocument();
    expect(screen.getByText('IntelliAssist vs Global AI')).toBeInTheDocument();
  });

  it('6. Conversational input synthesizes blueprint and creates actual application with Developer Mode transition', async () => {
    vi.spyOn(chatApi, 'synthesizeAppPlan').mockResolvedValue({
      name: 'EventHub 2026',
      slug: 'eventhub-2026',
      description: 'An interactive event management application.',
      requirements: [
        {
          title: 'Event registration checkout',
          description: 'Users can book seats for open events.',
          type: 'FUNCTIONAL',
          priority: 'HIGH',
        },
      ],
      suggested_features: ['Live notifications', 'Calendar export'],
    });

    const newCreatedProject: ProjectResponse = {
      id: 'proj-new-eventhub',
      name: 'EventHub 2026',
      slug: 'eventhub-2026',
      description: 'An interactive event management application.',
      status: 'IN_PROGRESS',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    vi.spyOn(projectsApi, 'create').mockResolvedValue(newCreatedProject);

    renderApp('user');

    // 1. Enter app description into conversational input
    const input = await screen.findByPlaceholderText(/describe what you want to build or ask anything/i);
    fireEvent.change(input, { target: { value: 'A modern event platform for booking tickets' } });

    const planBtn = screen.getByRole('button', { name: /plan app/i });
    fireEvent.click(planBtn);

    // 2. Blueprint appears
    expect(await screen.findByText('Synthesized Application Blueprint')).toBeInTheDocument();
    expect(screen.getByText('EventHub 2026')).toBeInTheDocument();
    expect(screen.getByText('Event registration checkout')).toBeInTheDocument();

    // 3. Click "Create Application Now"
    const createBtn = screen.getByRole('button', { name: /create application now/i });
    fireEvent.click(createBtn);

    // 4. Success card appears with "Open in Developer Mode"
    expect(await screen.findByText(/Project “EventHub 2026” Created Successfully!/i)).toBeInTheDocument();
    const openDevBtns = screen.getAllByRole('button', { name: /open in developer mode/i });
    expect(openDevBtns.length).toBeGreaterThanOrEqual(1);

    // 5. Click "Open in Developer Mode"
    fireEvent.click(openDevBtns[0]);

    // Transitions to Developer Mode
    await waitFor(() => {
      expect(localStorage.getItem(MODE_STORAGE_KEY)).toBe('developer');
      expect(screen.getByRole('radio', { name: /switch to developer mode/i })).toHaveAttribute(
        'aria-checked',
        'true'
      );
    });
  });
});
