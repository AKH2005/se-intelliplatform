import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/common/Button';
import { Modal } from '../../components/common/Modal';
import { Eye, EyeOff, Lock, Mail, User as UserIcon, ShieldCheck, AlertCircle } from 'lucide-react';

interface AuthModalProps {
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    if (!email.trim() || !password) {
      setLocalError('Please fill in all required fields.');
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
        await login({ email: email.trim(), password });
      } else {
        await register({
          name: name.trim(),
          email: email.trim(),
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
      title={mode === 'login' ? 'Sign In to SE IntelliPlatform' : 'Create Account'}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* Mode Toggle Tabs */}
        <div
          style={{
            display: 'flex',
            borderRadius: 'var(--radius-md)',
            background: 'var(--bg-surface-subtle)',
            padding: '0.25rem',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <button
            type="button"
            id="tab-sign-in"
            onClick={() => switchMode('login')}
            style={{
              flex: 1,
              padding: '0.5rem',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              background: mode === 'login' ? 'var(--accent-primary)' : 'transparent',
              color: mode === 'login' ? '#ffffff' : 'var(--text-muted)',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              transition: 'all 0.2s',
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
              padding: '0.5rem',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              background: mode === 'register' ? 'var(--accent-primary)' : 'transparent',
              color: mode === 'register' ? '#ffffff' : 'var(--text-muted)',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            Create Account
          </button>
        </div>

        {/* Error Alert */}
        {activeError && (
          <div
            role="alert"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.65rem 0.85rem',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#f87171',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.82rem',
            }}
          >
            <AlertCircle size={16} style={{ flexShrink: 0 }} />
            <span>{activeError}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {mode === 'register' && (
            <div className="form-group">
              <label className="form-label" htmlFor="auth-name" style={{ fontWeight: 600, fontSize: '0.82rem' }}>
                Full Name *
              </label>
              <div style={{ position: 'relative' }}>
                <UserIcon
                  size={16}
                  style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}
                />
                <input
                  id="auth-name"
                  type="text"
                  className="form-input"
                  style={{ paddingLeft: '2.3rem' }}
                  placeholder="e.g. Alex Morgan"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>
            </div>
          )}

          <div className="form-group">
            <label className="form-label" htmlFor="auth-email" style={{ fontWeight: 600, fontSize: '0.82rem' }}>
              Email Address *
            </label>
            <div style={{ position: 'relative' }}>
              <Mail
                size={16}
                style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}
              />
              <input
                id="auth-email"
                type="email"
                className="form-input"
                style={{ paddingLeft: '2.3rem' }}
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="auth-password" style={{ fontWeight: 600, fontSize: '0.82rem' }}>
              Password *
            </label>
            <div style={{ position: 'relative' }}>
              <Lock
                size={16}
                style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}
              />
              <input
                id="auth-password"
                type={showPassword ? 'text' : 'password'}
                className="form-input"
                style={{ paddingLeft: '2.3rem', paddingRight: '2.3rem' }}
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
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  padding: 0,
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {mode === 'register' && (
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                Must be at least 8 characters with at least one letter and one number.
              </div>
            )}
          </div>

          {mode === 'register' && (
            <div className="form-group">
              <label className="form-label" htmlFor="auth-confirm-password" style={{ fontWeight: 600, fontSize: '0.82rem' }}>
                Confirm Password *
              </label>
              <div style={{ position: 'relative' }}>
                <Lock
                  size={16}
                  style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}
                />
                <input
                  id="auth-confirm-password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  className="form-input"
                  style={{ paddingLeft: '2.3rem', paddingRight: '2.3rem' }}
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
                    color: 'var(--text-muted)',
                    cursor: 'pointer',
                    padding: 0,
                    display: 'flex',
                    alignItems: 'center',
                  }}
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
            id={mode === 'login' ? 'btn-auth-login-submit' : 'btn-auth-register-submit'}
            style={{
              marginTop: '0.5rem',
              padding: '0.65rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.4rem',
            }}
          >
            <ShieldCheck size={16} />
            <span>{mode === 'login' ? 'Sign In' : 'Create Account'}</span>
          </Button>
        </form>

        <div style={{ textAlign: 'center', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
          {mode === 'login' ? (
            <span>
              Don't have an account?{' '}
              <button
                type="button"
                onClick={() => switchMode('register')}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--accent-primary)',
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
                onClick={() => switchMode('login')}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--accent-primary)',
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
    </Modal>
  );
};
