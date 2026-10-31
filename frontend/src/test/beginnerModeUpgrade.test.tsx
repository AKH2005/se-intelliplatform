import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../context/AuthContext';
import { ProjectProvider } from '../context/ProjectContext';
import { ModeProvider, MODE_STORAGE_KEY } from '../context/ModeContext';
import { App } from '../App';
import { authApi } from '../services/authApi';
import { projectsApi } from '../services/projectsApi';
import { chatApi } from '../services/chatApi';
import { ProjectResponse } from '../types/project';

const mockProjects: ProjectResponse[] = [
  {
    id: 'proj-beginner-kanban',
    name: 'Real-Time Kanban Task Manager',
    slug: 'kanban-task-manager',
    description: 'A modern Kanban task board with drag-and-drop columns, priority tags, and due dates.',
    status: 'IN_PROGRESS',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'proj-beginner-event',
    name: 'Event & Conference Booking Hub',
    slug: 'event-booking-hub',
    description: 'Browse upcoming conferences with dates, location, and seat capacity limits.',
    status: 'IN_PROGRESS',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const mockUser = {
  id: 'user-beginner-tester',
  name: 'Alex Builder',
  email: 'alex@example.com',
  role: 'developer' as const,
  is_active: true,
  created_at: new Date().toISOString(),
};

function renderApp(initialMode: 'user' | 'developer' = 'user', projectList: ProjectResponse[] = mockProjects) {
  localStorage.clear();
  localStorage.setItem('se_auth_token', 'test-token');
  localStorage.setItem(MODE_STORAGE_KEY, initialMode);
  window.history.replaceState({}, '', '/projects');

  vi.spyOn(authApi, 'getMe').mockResolvedValue(mockUser);
  vi.spyOn(projectsApi, 'list').mockResolvedValue(projectList);

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

describe('S-Tier Upgrade: Beginner Mode & Welcome Dashboard', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it('1. Renders the welcoming home dashboard with prominent heading and three starting choices', async () => {
    renderApp('user');

    // Welcoming heading
    expect(await screen.findByText('What would you like to create today?')).toBeInTheDocument();
    expect(
      screen.getByText(/SE IntelliPlatform transforms your software concepts into live, running applications/i)
    ).toBeInTheDocument();

    // Three starting choices
    expect(screen.getByText('1. Build with AI')).toBeInTheDocument();
    expect(screen.getByText('2. Start from a Template')).toBeInTheDocument();
    expect(screen.getByText('3. Start from Scratch')).toBeInTheDocument();

    // Prominent Create New Project action
    const createBtn = screen.getByRole('button', { name: /Create New Project/i });
    expect(createBtn).toBeInTheDocument();

    // My Projects section
    expect(await screen.findByText('Your Applications & Projects')).toBeInTheDocument();
    expect(await screen.findAllByText('Real-Time Kanban Task Manager')).toHaveLength(3);
    expect(await screen.findAllByText('Event & Conference Booking Hub')).toHaveLength(2);
  });

  it('2. Choice 1: Build with AI guides user from prompt description to blueprint review', async () => {
    vi.spyOn(chatApi, 'synthesizeAppPlan').mockResolvedValue({
      name: 'Smart Inventory Tracker',
      slug: 'smart-inventory-tracker',
      description: 'A real-time stock and logistics tracker with barcode validation.',
      requirements: [
        {
          title: 'Stock Ledger Dashboard',
          description: 'Overview of stock quantities and low-inventory alerts.',
          type: 'FUNCTIONAL',
          priority: 'HIGH',
        },
        {
          title: 'Inventory REST APIs',
          description: 'CRUD endpoints for item quantities and warehouses.',
          type: 'FUNCTIONAL',
          priority: 'HIGH',
        },
      ],
      suggested_features: ['Barcode scanning', 'CSV reorder reports'],
    });

    renderApp('user');

    const input = await screen.findByPlaceholderText(/describe what you want to build or ask anything/i);
    fireEvent.change(input, { target: { value: 'Build a smart inventory tracker' } });

    const planBtn = screen.getByRole('button', { name: /plan app/i });
    fireEvent.click(planBtn);

    // Transitions to Stage 3 Review Blueprint
    expect(await screen.findByText('Synthesized Application Blueprint')).toBeInTheDocument();
    expect(screen.getByText('Smart Inventory Tracker')).toBeInTheDocument();
    expect(screen.getByText('Stock Ledger Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Inventory REST APIs')).toBeInTheDocument();

    // Actions available
    expect(screen.getByRole('button', { name: /create application now/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cancel \/ modify prompt/i })).toBeInTheDocument();

    // Canceling returns to dashboard with prompt input preserved
    fireEvent.click(screen.getByRole('button', { name: /cancel \/ modify prompt/i }));
    expect(screen.queryByText('Synthesized Application Blueprint')).not.toBeInTheDocument();
    expect(screen.getByText('What would you like to create today?')).toBeInTheDocument();
  });

  it('3. Choice 2: Start from a Template displays supported starters and populates blueprint', async () => {
    renderApp('user');

    await screen.findByText('What would you like to create today?');

    // Select Choice 2: Start from a Template
    const templateChoiceCard = screen.getByText('2. Start from a Template');
    fireEvent.click(templateChoiceCard);

    // Template gallery is revealed with genuine starters
    expect(await screen.findByText('Select a Production-Tested Starter Template')).toBeInTheDocument();
    expect(screen.getAllByText('Real-Time Kanban Task Manager').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Event & Conference Booking Hub').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Team Directory & Admin Portal')).toBeInTheDocument();
    expect(screen.getByText('E-Commerce Store & Catalog')).toBeInTheDocument();
    expect(screen.getByText('HTML5 Canvas 2D Arcade Game')).toBeInTheDocument();
    expect(screen.getAllByText('Executive Analytics Dashboard').length).toBeGreaterThanOrEqual(1);

    // Click "Use This Template" on Team Directory & Admin Portal
    const useTemplateBtns = screen.getAllByRole('button', { name: /use this template/i });
    expect(useTemplateBtns.length).toBeGreaterThanOrEqual(5);

    // Click third template (Team Directory)
    fireEvent.click(useTemplateBtns[2]);

    // Immediately populates Stage 3 Review Blueprint
    expect(await screen.findByText('Synthesized Application Blueprint')).toBeInTheDocument();
    expect(screen.getByText('Team Directory & Admin Portal')).toBeInTheDocument();
    expect(screen.getByText('Member Record Management & Status Toggling')).toBeInTheDocument();
    expect(screen.getByText('Client-Side CSV Dataset Export')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create application now/i })).toBeInTheDocument();
  });

  it('4. Choice 3: Start from Scratch guides through custom project setup', async () => {
    renderApp('user');

    await screen.findByText('What would you like to create today?');

    // Select Choice 3: Start from Scratch
    const scratchChoiceCard = screen.getByText('3. Start from Scratch');
    fireEvent.click(scratchChoiceCard);

    // Custom configuration form is revealed
    expect(await screen.findByText('Configure Your Custom Project')).toBeInTheDocument();
    expect(screen.getByLabelText(/Project Name \*/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Repository Slug \*/i)).toBeInTheDocument();

    // Fill in custom details
    const nameInput = screen.getByLabelText(/Project Name \*/i);
    fireEvent.change(nameInput, { target: { value: 'Telemetry Hub Pro' } });

    // Continue to Blueprint Review
    const continueBtn = screen.getByRole('button', { name: /continue to blueprint review/i });
    expect(continueBtn).not.toBeDisabled();
    fireEvent.click(continueBtn);

    // Transitions to Stage 3 Review Blueprint
    expect(await screen.findByText('Synthesized Application Blueprint')).toBeInTheDocument();
    expect(screen.getByText('Telemetry Hub Pro')).toBeInTheDocument();
    expect(screen.getByText(/Core Telemetry Hub Pro Navigation & Interface/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create application now/i })).toBeInTheDocument();
  });

  it('5. My Projects section renders helpful empty state when user has zero projects', async () => {
    renderApp('user', []);

    await screen.findByText('What would you like to create today?');

    // Empty state rendered
    expect(await screen.findByText('No applications yet')).toBeInTheDocument();
    expect(
      screen.getByText(/Use the options above to build with AI, launch a starter template, or configure a project from scratch/i)
    ).toBeInTheDocument();
    expect(screen.getByText('0 projects')).toBeInTheDocument();
  });
});

