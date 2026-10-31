import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/common/Button';
import { Modal } from '../../components/common/Modal';
import {
  Eye,
  EyeOff,
  Lock,
  Mail,
  User as UserIcon,
  ShieldCheck,
  AlertCircle,
  Check,
  Code2,
} from 'lucide-react';

export interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialMode?: 'login' | 'register';
  onSuccess?: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  initialMode = 'login',
  onSuccess,
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
  };

  // Password validation helpers for Register mode
  const hasMinLength = password.length >= 8;
  const hasNumber = /\d/.test(password);
  const hasLetter = /[A-Za-z]/.test(password);
  const passwordsMatch = password.length > 0 && password === confirmPassword;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    const cleanEmail = email.trim();
    if (!cleanEmail || !password) {
      setLocalError('Please fill in all required fields.');
      return;
    }

    if (mode === 'register') {
      if (!name.trim()) {
        setLocalError('Please enter your full name.');
        return;
      }
      if (!hasMinLength) {
        setLocalError('Password must be at least 8 characters long.');
        return;
      }
      if (!hasNumber) {
        setLocalError('Password must contain at least one number.');
        return;
      }
      if (!hasLetter) {
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
      setName('');
      setEmail('');
      setPassword('');
      setConfirmPassword('');
      onClose();
      if (onSuccess) onSuccess();
    } catch (err: any) {
      setLocalError(err?.message || 'Authentication failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeError = localError || error;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={mode === 'login' ? 'Sign In to SE IntelliPlatform' : 'Create Your Account'}
      subtitle={
        mode === 'login'
          ? 'Enter your credentials to access your workspaces and live previews.'
          : 'Join to synthesize, build, and verify software with AI.'
      }
      icon={<Code2 size={18} />}
      size="default"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* Segmented Mode Toggle Tabs */}
        <div
          style={{
            display: 'flex',
            borderRadius: 'var(--radius-md, 10px)',
            background: 'rgba(8, 11, 18, 0.65)',
            padding: '0.25rem',
            border: '1px solid var(--border-medium, rgba(255, 255, 255, 0.12))',
            boxShadow: 'inset 0 1px 3px rgba(0, 0, 0, 0.4)',
          }}
        >
          <button
            type="button"
            id="tab-sign-in"
            onClick={() => switchMode('login')}
            style={{
              flex: 1,
              padding: '0.5rem 0.75rem',
              borderRadius: 'var(--radius-sm, 6px)',
              border: 'none',
              background:
                mode === 'login'
                  ? 'var(--accent-gradient, linear-gradient(135deg, #7c3aed, #6366f1))'
                  : 'transparent',
              color: mode === 'login' ? '#ffffff' : 'var(--text-muted, #94a3b8)',
              fontWeight: mode === 'login' ? 650 : 500,
              fontSize: '0.85rem',
              cursor: 'pointer',
              transition: 'all var(--transition-fast, 150ms ease)',
              boxShadow: mode === 'login' ? 'var(--shadow-sm), 0 0 12px rgba(124, 58, 237, 0.35)' : 'none',
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            id="tab-create-account"
            onClick={() => switchMode('register')}
            style={{
              flex: 1,
              padding: '0.5rem 0.75rem',
              borderRadius: 'var(--radius-sm, 6px)',
              border: 'none',
              background:
                mode === 'register'
                  ? 'var(--accent-gradient, linear-gradient(135deg, #7c3aed, #6366f1))'
                  : 'transparent',
              color: mode === 'register' ? '#ffffff' : 'var(--text-muted, #94a3b8)',
              fontWeight: mode === 'register' ? 650 : 500,
              fontSize: '0.85rem',
              cursor: 'pointer',
              transition: 'all var(--transition-fast, 150ms ease)',
              boxShadow: mode === 'register' ? 'var(--shadow-sm), 0 0 12px rgba(124, 58, 237, 0.35)' : 'none',
            }}
          >
            Create Account
          </button>
        </div>

        {/* Error Alert Box */}
        {activeError && (
          <div
            role="alert"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.65rem 0.85rem',
              background: 'linear-gradient(180deg, rgba(239, 68, 68, 0.14) 0%, rgba(239, 68, 68, 0.08) 100%)',
              border: '1px solid rgba(239, 68, 68, 0.35)',
              color: '#f87171',
              borderRadius: 'var(--radius-sm, 6px)',
              fontSize: '0.825rem',
              lineHeight: 1.45,
            }}
          >
            <AlertCircle size={16} style={{ flexShrink: 0 }} />
            <span style={{ flex: 1 }}>{activeError}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {mode === 'register' && (
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label
                className="form-label"
                htmlFor="auth-name"
                style={{ fontWeight: 600, fontSize: '0.825rem', color: '#e2e8f0', marginBottom: '0.35rem', display: 'block' }}
              >
                Full Name *
              </label>
              <div style={{ position: 'relative' }}>
                <UserIcon
                  size={16}
                  style={{
                    position: 'absolute',
                    left: '0.75rem',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'var(--text-muted, #64748b)',
                    pointerEvents: 'none',
                  }}
                />
                <input
                  id="auth-name"
                  type="text"
                  className="form-input"
                  style={{
                    paddingLeft: '2.3rem',
                    background: 'var(--bg-surface-subtle, #0d121f)',
                    border: '1px solid var(--border-medium, rgba(255, 255, 255, 0.12))',
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
              htmlFor="auth-email"
              style={{ fontWeight: 600, fontSize: '0.825rem', color: '#e2e8f0', marginBottom: '0.35rem', display: 'block' }}
            >
              Email Address *
            </label>
            <div style={{ position: 'relative' }}>
              <Mail
                size={16}
                style={{
                  position: 'absolute',
                  left: '0.75rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-muted, #64748b)',
                  pointerEvents: 'none',
                }}
              />
              <input
                id="auth-email"
                type="email"
                className="form-input"
                style={{
                  paddingLeft: '2.3rem',
                  background: 'var(--bg-surface-subtle, #0d121f)',
                  border: '1px solid var(--border-medium, rgba(255, 255, 255, 0.12))',
                }}
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label
              className="form-label"
              htmlFor="auth-password"
              style={{ fontWeight: 600, fontSize: '0.825rem', color: '#e2e8f0', marginBottom: '0.35rem', display: 'block' }}
            >
              Password *
            </label>
            <div style={{ position: 'relative' }}>
              <Lock
                size={16}
                style={{
                  position: 'absolute',
                  left: '0.75rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-muted, #64748b)',
                  pointerEvents: 'none',
                }}
              />
              <input
                id="auth-password"
                type={showPassword ? 'text' : 'password'}
                className="form-input"
                style={{
                  paddingLeft: '2.3rem',
                  paddingRight: '2.5rem',
                  background: 'var(--bg-surface-subtle, #0d121f)',
                  border: '1px solid var(--border-medium, rgba(255, 255, 255, 0.12))',
                }}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <button
                type="button"
                id="btn-toggle-password"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '0.75rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-muted, #94a3b8)',
                  cursor: 'pointer',
                  padding: '0.2rem',
                  display: 'flex',
                  alignItems: 'center',
                  borderRadius: '4px',
                }}
                title={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {mode === 'register' && (
            <>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label
                  className="form-label"
                  htmlFor="auth-confirm-password"
                  style={{ fontWeight: 600, fontSize: '0.825rem', color: '#e2e8f0', marginBottom: '0.35rem', display: 'block' }}
                >
                  Confirm Password *
                </label>
                <div style={{ position: 'relative' }}>
                  <Lock
                    size={16}
                    style={{
                      position: 'absolute',
                      left: '0.75rem',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      color: 'var(--text-muted, #64748b)',
                      pointerEvents: 'none',
                    }}
                  />
                  <input
                    id="auth-confirm-password"
                    type={showConfirmPassword ? 'text' : 'password'}
                    className="form-input"
                    style={{
                      paddingLeft: '2.3rem',
                      paddingRight: '2.5rem',
                      background: 'var(--bg-surface-subtle, #0d121f)',
                      border: '1px solid var(--border-medium, rgba(255, 255, 255, 0.12))',
                    }}
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                  />
                  <button
                    type="button"
                    id="btn-toggle-confirm-password"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    style={{
                      position: 'absolute',
                      right: '0.75rem',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--text-muted, #94a3b8)',
                      cursor: 'pointer',
                      padding: '0.2rem',
                      display: 'flex',
                      alignItems: 'center',
                      borderRadius: '4px',
                    }}
                    title={showConfirmPassword ? 'Hide password' : 'Show password'}
                  >
                    {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              {/* Password Requirements Checklist */}
              <div
                style={{
                  background: 'rgba(0, 0, 0, 0.25)',
                  border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
                  borderRadius: 'var(--radius-sm, 6px)',
                  padding: '0.5rem 0.65rem',
                  fontSize: '0.725rem',
                  display: 'grid',
                  gridTemplateColumns: 'repeat(2, 1fr)',
                  gap: '0.3rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: hasMinLength ? '#34d399' : '#64748b' }}>
                  <Check size={11} strokeWidth={hasMinLength ? 3 : 2} />
                  <span>8+ characters</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: hasNumber ? '#34d399' : '#64748b' }}>
                  <Check size={11} strokeWidth={hasNumber ? 3 : 2} />
                  <span>1+ number</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: hasLetter ? '#34d399' : '#64748b' }}>
                  <Check size={11} strokeWidth={hasLetter ? 3 : 2} />
                  <span>1+ letter</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: passwordsMatch ? '#34d399' : '#64748b' }}>
                  <Check size={11} strokeWidth={passwordsMatch ? 3 : 2} />
                  <span>Passwords match</span>
                </div>
              </div>
            </>
          )}

          <Button
            type="submit"
            variant="primary"
            isLoading={isSubmitting}
            id={mode === 'login' ? 'btn-auth-login-submit' : 'btn-auth-register-submit'}
            style={{
              marginTop: '0.35rem',
              padding: '0.65rem',
              fontWeight: 650,
              fontSize: '0.9rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.45rem',
              boxShadow: 'var(--shadow-sm), 0 0 16px -2px rgba(124, 58, 237, 0.4)',
            }}
            icon={<ShieldCheck size={16} />}
          >
            <span>{mode === 'login' ? 'Sign In to Workspace' : 'Create Account & Continue'}</span>
          </Button>
        </form>

        <div style={{ textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-muted, #94a3b8)' }}>
          {mode === 'login' ? (
            <span>
              Don't have an account?{' '}
              <button
                type="button"
                onClick={() => switchMode('register')}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--accent-violet-light, #a78bfa)',
                  fontWeight: 650,
                  cursor: 'pointer',
                  padding: 0,
                  textDecoration: 'underline',
                  textUnderlineOffset: '2px',
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
                onClick={() => switchMode('login')}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--accent-violet-light, #a78bfa)',
                  fontWeight: 650,
                  cursor: 'pointer',
                  padding: 0,
                  textDecoration: 'underline',
                  textUnderlineOffset: '2px',
                }}
              >
                Sign in
              </button>
            </span>
          )}
        </div>
      </div>
    </Modal>
  );
};
