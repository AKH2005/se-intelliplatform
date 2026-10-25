import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/common/Button';
import {
  Code2,
  Lock,
  Mail,
  User as UserIcon,
  Eye,
  EyeOff,
  ShieldCheck,
  AlertCircle,
  Sparkles,
  Bot,
  FolderKanban,
} from 'lucide-react';

interface LoginViewProps {
  initialMode?: 'login' | 'register';
  onSuccess?: () => void;
  redirectPath?: string;
}

export const LoginView: React.FC<LoginViewProps> = ({
  initialMode = 'login',
  onSuccess,
  redirectPath = '/projects',
}) => {
  const { login, register, error, clearError } = useAuth();
  const [mode, setMode] = useState<'login' | 'register'>(initialMode);

  // Form states
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const switchMode = (newMode: 'login' | 'register') => {
    setMode(newMode);
    clearError();
    setLocalError(null);
    if (typeof window !== 'undefined') {
      window.history.replaceState({}, '', newMode === 'register' ? '/register' : '/login');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    const cleanEmail = email.trim();
    if (!cleanEmail || !password) {
      setLocalError('Please enter both your email address and password.');
      return;
    }

    if (mode === 'register') {
      if (!name.trim()) {
        setLocalError('Please enter your full name.');
        return;
      }
      if (password.length < 8) {
        setLocalError('Password must be at least 8 characters long.');
        return;
      }
      if (!/\d/.test(password)) {
        setLocalError('Password must contain at least one number.');
        return;
      }
      if (!/[A-Za-z]/.test(password)) {
        setLocalError('Password must contain at least one letter.');
        return;
      }
      if (password !== confirmPassword) {
        setLocalError('Passwords do not match.');
        return;
      }
    }

    setIsSubmitting(true);
    try {
      if (mode === 'login') {
        await login({ email: cleanEmail, password });
      } else {
        await register({
          name: name.trim(),
          email: cleanEmail,
          password,
          confirm_password: confirmPassword,
        });
      }
      if (typeof window !== 'undefined') {
        window.history.pushState({}, '', redirectPath || '/projects');
      }
      if (onSuccess) onSuccess();
    } catch (err: any) {
      setLocalError(err?.message || 'Authentication failed. Please verify your credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeError = localError || error;

  return (
    <div
      style={{
        minHeight: '100vh',
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'radial-gradient(ellipse at 50% 20%, rgba(99, 102, 241, 0.15) 0%, rgba(10, 14, 26, 1) 75%)',
        padding: '2rem 1rem',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Background Decorative Grid */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
          pointerEvents: 'none',
        }}
      />

      {/* Main Auth Container Card */}
      <div
        style={{
          width: '100%',
          maxWidth: '440px',
          background: 'rgba(18, 24, 38, 0.85)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: 'var(--radius-lg, 16px)',
          padding: '2.5rem 2.25rem',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.5), 0 0 40px rgba(99, 102, 241, 0.15)',
          position: 'relative',
          zIndex: 1,
        }}
      >
        {/* Logo and Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 54,
              height: 54,
              borderRadius: '14px',
              background: 'linear-gradient(135deg, var(--accent-primary, #6366f1), var(--accent-cyan, #06b6d4))',
              boxShadow: '0 8px 24px rgba(99, 102, 241, 0.35)',
              marginBottom: '1rem',
            }}
          >
            <Code2 size={28} color="#ffffff" />
          </div>

          <div
            style={{
              fontSize: '0.72rem',
              fontWeight: 700,
              letterSpacing: '0.12em',
              textTransform: 'uppercase',
              color: 'var(--accent-cyan, #06b6d4)',
              marginBottom: '0.35rem',
            }}
          >
            SE IntelliPlatform
          </div>

          <h1
            style={{
              fontSize: '1.65rem',
              fontWeight: 800,
              color: '#ffffff',
              letterSpacing: '-0.025em',
              margin: '0 0 0.5rem 0',
            }}
          >
            {mode === 'login' ? 'Welcome Back' : 'Create Your Account'}
          </h1>

          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary, #94a3b8)', margin: 0, lineHeight: 1.45 }}>
            {mode === 'login'
              ? 'Sign in to access your projects, specifications, and AI workspaces.'
              : 'Join SE IntelliPlatform to build, verify, and preview software with AI.'}
          </p>
        </div>

        {/* Mode Toggle Tabs */}
        <div
          style={{
            display: 'flex',
            borderRadius: 'var(--radius-md, 8px)',
            background: 'rgba(0, 0, 0, 0.25)',
            padding: '0.25rem',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            marginBottom: '1.5rem',
          }}
        >
          <button
            type="button"
            id="btn-tab-login"
            onClick={() => switchMode('login')}
            style={{
              flex: 1,
              padding: '0.55rem',
              borderRadius: 'var(--radius-sm, 6px)',
              border: 'none',
              background: mode === 'login' ? 'var(--accent-primary, #6366f1)' : 'transparent',
              color: mode === 'login' ? '#ffffff' : 'var(--text-muted, #64748b)',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            id="btn-tab-register"
            onClick={() => switchMode('register')}
            style={{
              flex: 1,
              padding: '0.55rem',
              borderRadius: 'var(--radius-sm, 6px)',
              border: 'none',
              background: mode === 'register' ? 'var(--accent-primary, #6366f1)' : 'transparent',
              color: mode === 'register' ? '#ffffff' : 'var(--text-muted, #64748b)',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            Register
          </button>
        </div>

        {/* Error Alert Box */}
        {activeError && (
          <div
            role="alert"
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.65rem',
              padding: '0.75rem 1rem',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.35)',
              color: '#f87171',
              borderRadius: 'var(--radius-md, 8px)',
              fontSize: '0.85rem',
              marginBottom: '1.25rem',
              lineHeight: 1.4,
            }}
          >
            <AlertCircle size={17} style={{ flexShrink: 0, marginTop: '0.1rem' }} />
            <span>{activeError}</span>
          </div>
        )}

        {/* Auth Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.15rem' }}>
          {mode === 'register' && (
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label
                className="form-label"
                htmlFor="login-name"
                style={{ fontWeight: 600, fontSize: '0.825rem', color: '#e2e8f0', marginBottom: '0.4rem', display: 'block' }}
              >
                Full Name *
              </label>
              <div style={{ position: 'relative' }}>
                <UserIcon
                  size={16}
                  style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted, #64748b)' }}
                />
                <input
                  id="login-name"
                  type="text"
                  className="form-input"
                  style={{
                    paddingLeft: '2.4rem',
                    width: '100%',
                    background: 'rgba(0, 0, 0, 0.3)',
                    border: '1px solid rgba(255, 255, 255, 0.12)',
                    fontSize: '0.9rem',
                    borderRadius: '8px',
                    color: '#ffffff',
                    padding: '0.65rem 0.85rem 0.65rem 2.4rem',
                  }}
                  placeholder="e.g. Alex Morgan"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>
            </div>
          )}

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label
              className="form-label"
              htmlFor="login-email"
              style={{ fontWeight: 600, fontSize: '0.825rem', color: '#e2e8f0', marginBottom: '0.4rem', display: 'block' }}
            >
              Email Address *
            </label>
            <div style={{ position: 'relative' }}>
              <Mail
                size={16}
                style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted, #64748b)' }}
              />
              <input
                id="login-email"
                type="email"
                className="form-input"
                style={{
                  paddingLeft: '2.4rem',
                  width: '100%',
                  background: 'rgba(0, 0, 0, 0.3)',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                  fontSize: '0.9rem',
                  borderRadius: '8px',
                  color: '#ffffff',
                  padding: '0.65rem 0.85rem 0.65rem 2.4rem',
                }}
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
              <label
                className="form-label"
                htmlFor="login-password"
                style={{ fontWeight: 600, fontSize: '0.825rem', color: '#e2e8f0', margin: 0 }}
              >
                Password *
              </label>
            </div>
            <div style={{ position: 'relative' }}>
              <Lock
                size={16}
                style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted, #64748b)' }}
              />
              <input
                id="login-password"
                type={showPassword ? 'text' : 'password'}
                className="form-input"
                style={{
                  paddingLeft: '2.4rem',
                  paddingRight: '2.5rem',
                  width: '100%',
                  background: 'rgba(0, 0, 0, 0.3)',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                  fontSize: '0.9rem',
                  borderRadius: '8px',
                  color: '#ffffff',
                  padding: '0.65rem 2.5rem 0.65rem 2.4rem',
                }}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <button
                type="button"
                id="btn-login-toggle-password"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '0.85rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-muted, #64748b)',
                  cursor: 'pointer',
                  padding: 0,
                  display: 'flex',
                  alignItems: 'center',
                }}
                title={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {mode === 'register' && (
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label
                className="form-label"
                htmlFor="login-confirm-password"
                style={{ fontWeight: 600, fontSize: '0.825rem', color: '#e2e8f0', marginBottom: '0.4rem', display: 'block' }}
              >
                Confirm Password *
              </label>
              <div style={{ position: 'relative' }}>
                <Lock
                  size={16}
                  style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted, #64748b)' }}
                />
                <input
                  id="login-confirm-password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  className="form-input"
                  style={{
                    paddingLeft: '2.4rem',
                    paddingRight: '2.5rem',
                    width: '100%',
                    background: 'rgba(0, 0, 0, 0.3)',
                    border: '1px solid rgba(255, 255, 255, 0.12)',
                    fontSize: '0.9rem',
                    borderRadius: '8px',
                    color: '#ffffff',
                    padding: '0.65rem 2.5rem 0.65rem 2.4rem',
                  }}
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  id="btn-login-toggle-confirm-password"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  style={{
                    position: 'absolute',
                    right: '0.85rem',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-muted, #64748b)',
                    cursor: 'pointer',
                    padding: 0,
                    display: 'flex',
                    alignItems: 'center',
                  }}
                  title={showConfirmPassword ? 'Hide password' : 'Show password'}
                >
                  {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
          )}

          <Button
            type="submit"
            variant="primary"
            isLoading={isSubmitting}
            id={mode === 'login' ? 'btn-login-submit' : 'btn-register-submit'}
            style={{
              marginTop: '0.5rem',
              padding: '0.75rem',
              fontWeight: 700,
              fontSize: '0.925rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              background: 'linear-gradient(135deg, var(--accent-primary, #6366f1), var(--accent-cyan, #06b6d4))',
              boxShadow: '0 4px 14px rgba(99, 102, 241, 0.3)',
            }}
          >
            <ShieldCheck size={17} />
            <span>{mode === 'login' ? 'Sign In to Workspace' : 'Create Account & Continue'}</span>
          </Button>
        </form>

        {/* Footer Mode Switcher */}
        <div style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.85rem', color: 'var(--text-muted, #64748b)' }}>
          {mode === 'login' ? (
            <span>
              Don't have an account?{' '}
              <button
                type="button"
                id="btn-switch-to-register"
                onClick={() => switchMode('register')}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--accent-primary, #6366f1)',
                  fontWeight: 600,
                  cursor: 'pointer',
                  padding: 0,
                  textDecoration: 'underline',
                }}
              >
                Sign up
              </button>
            </span>
          ) : (
            <span>
              Already have an account?{' '}
              <button
                type="button"
                id="btn-switch-to-login"
                onClick={() => switchMode('login')}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--accent-primary, #6366f1)',
                  fontWeight: 600,
                  cursor: 'pointer',
                  padding: 0,
                  textDecoration: 'underline',
                }}
              >
                Sign in
              </button>
            </span>
          )}
        </div>
      </div>

      {/* Feature Highlights Footer */}
      <div
        style={{
          marginTop: '2.5rem',
          display: 'flex',
          gap: '2rem',
          alignItems: 'center',
          flexWrap: 'wrap',
          justifyContent: 'center',
          color: 'var(--text-muted, #64748b)',
          fontSize: '0.8rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <FolderKanban size={15} color="var(--accent-primary, #6366f1)" />
          <span>Isolated Project Workspaces</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <Bot size={15} color="var(--accent-cyan, #06b6d4)" />
          <span>Requirements-Driven AI Generation</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <Sparkles size={15} color="#10b981" />
          <span>Project-Specific Live Previews</span>
        </div>
      </div>
    </div>
  );
};
