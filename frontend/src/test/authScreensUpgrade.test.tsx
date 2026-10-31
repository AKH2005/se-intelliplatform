import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../context/AuthContext';
import { ProjectProvider } from '../context/ProjectContext';
import { LoginView } from '../views/auth/LoginView';
import { AuthModal } from '../views/auth/AuthModal';
import { authApi } from '../services/authApi';

const mockUser = {
  id: 'user-789',
  name: 'Dev Engineer',
  email: 'dev@example.com',
  role: 'developer' as const,
  is_active: true,
  created_at: new Date().toISOString(),
};

function renderWithAuth(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ProjectProvider>{ui}</ProjectProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

describe('S-Tier Upgrade: Login & Signup Screens', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    window.history.replaceState({}, '', '/login');
  });

  it('1. Renders the split-screen brand showcase with platform architecture layers and capabilities', () => {
    renderWithAuth(<LoginView initialMode="login" />);

    // Brand showcase identity
    expect(screen.getAllByText('SE IntelliPlatform').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Autonomous AI Engineering')).toBeInTheDocument();
    expect(screen.getByText('Software Engineering, Elevated by Intelligence.')).toBeInTheDocument();

    // 3D Architecture Preview badges
    expect(screen.getByText('Autonomous Code Synthesis')).toBeInTheDocument();
    expect(screen.getByText('● Verified')).toBeInTheDocument();
    expect(screen.getByText('Isolated Container Runtime')).toBeInTheDocument();
    expect(screen.getByText('● Port 8001')).toBeInTheDocument();
    expect(screen.getByText('Version Concurrency & Rollback')).toBeInTheDocument();
    expect(screen.getByText('v1 → v2')).toBeInTheDocument();

    // Trust & Sandboxing badges
    expect(screen.getByText('Fullstack Sandboxing')).toBeInTheDocument();
    expect(screen.getByText('Live App Refinement')).toBeInTheDocument();
  });

  it('2. Enforces registration validation with live password checklist and matching verification', async () => {
    renderWithAuth(<LoginView initialMode="register" />);

    expect(screen.getByRole('heading', { name: /create your account/i })).toBeInTheDocument();
    expect(screen.getByText('8+ characters')).toBeInTheDocument();
    expect(screen.getByText('1+ number')).toBeInTheDocument();
    expect(screen.getByText('1+ letter')).toBeInTheDocument();
    expect(screen.getByText('Passwords match')).toBeInTheDocument();

    // Attempt submitting without entering name
    fireEvent.change(screen.getByLabelText(/email address/i), { target: { value: 'dev@test.com' } });
    fireEvent.change(screen.getByLabelText(/^password \*/i), { target: { value: 'short' } });
    fireEvent.click(screen.getByRole('button', { name: /create account & continue/i }));

    expect(await screen.findByText('Please enter your full name.')).toBeInTheDocument();

    // Enter name, but short password
    fireEvent.change(screen.getByLabelText(/full name/i), { target: { value: 'Dev Engineer' } });
    fireEvent.click(screen.getByRole('button', { name: /create account & continue/i }));

    expect(await screen.findByText('Password must be at least 8 characters long.')).toBeInTheDocument();

    // Enter 8 characters without number
    fireEvent.change(screen.getByLabelText(/^password \*/i), { target: { value: 'abcdefgh' } });
    fireEvent.click(screen.getByRole('button', { name: /create account & continue/i }));

    expect(await screen.findByText('Password must contain at least one number.')).toBeInTheDocument();

    // Enter password without letters
    fireEvent.change(screen.getByLabelText(/^password \*/i), { target: { value: '12345678' } });
    fireEvent.click(screen.getByRole('button', { name: /create account & continue/i }));

    expect(await screen.findByText('Password must contain at least one letter.')).toBeInTheDocument();

    // Valid password but mismatched confirmation
    fireEvent.change(screen.getByLabelText(/^password \*/i), { target: { value: 'Pass1234' } });
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'PassDifferent' } });
    fireEvent.click(screen.getByRole('button', { name: /create account & continue/i }));

    expect(await screen.findByText('Passwords do not match.')).toBeInTheDocument();
  });

  it('3. Successful signup calls register API, stores token, and triggers completion callback', async () => {
    const registerSpy = vi.spyOn(authApi, 'register').mockResolvedValue({
      access_token: 'signup-jwt-token-verified',
      token_type: 'bearer',
      user: mockUser,
    });

    const handleSuccess = vi.fn();
    renderWithAuth(<LoginView initialMode="register" onSuccess={handleSuccess} />);

    fireEvent.change(screen.getByLabelText(/full name/i), { target: { value: 'Dev Engineer' } });
    fireEvent.change(screen.getByLabelText(/email address/i), { target: { value: 'dev@example.com' } });
    fireEvent.change(screen.getByLabelText(/^password \*/i), { target: { value: 'SecurePass99' } });
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'SecurePass99' } });

    fireEvent.click(screen.getByRole('button', { name: /create account & continue/i }));

    await waitFor(() => {
      expect(registerSpy).toHaveBeenCalledWith({
        name: 'Dev Engineer',
        email: 'dev@example.com',
        password: 'SecurePass99',
        confirm_password: 'SecurePass99',
      });
      expect(handleSuccess).toHaveBeenCalled();
      expect(localStorage.getItem('se_auth_token')).toBe('signup-jwt-token-verified');
    });
  });

  it('4. AuthModal renders with modal styling, supports mode switching and password toggles', () => {
    const handleClose = vi.fn();
    renderWithAuth(<AuthModal isOpen={true} onClose={handleClose} initialMode="login" />);

    expect(screen.getByRole('heading', { name: /sign in to se intelliplatform/i })).toBeInTheDocument();

    // Mode switch to create account in modal
    const registerTab = screen.getByRole('button', { name: /create account/i });
    fireEvent.click(registerTab);

    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    expect(screen.getByText('8+ characters')).toBeInTheDocument();

    // Toggle confirm password visibility
    const confirmInput = screen.getByLabelText(/confirm password/i);
    expect(confirmInput).toHaveAttribute('type', 'password');

    const toggleConfirmBtn = document.getElementById('btn-toggle-confirm-password')!;
    fireEvent.click(toggleConfirmBtn);
    expect(confirmInput).toHaveAttribute('type', 'text');
  });

  it('5. Handles backend authentication failure with accessible role="alert" message', async () => {
    vi.spyOn(authApi, 'login').mockRejectedValue(new Error('Invalid email or password.'));

    renderWithAuth(<LoginView initialMode="login" />);

    fireEvent.change(screen.getByLabelText(/email address/i), { target: { value: 'wrong@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'WrongPassword123' } });

    fireEvent.click(screen.getByRole('button', { name: /sign in to workspace/i }));

    const alertBox = await screen.findByRole('alert');
    expect(alertBox).toBeInTheDocument();
    expect(alertBox).toHaveTextContent('Invalid email or password.');
  });
});

