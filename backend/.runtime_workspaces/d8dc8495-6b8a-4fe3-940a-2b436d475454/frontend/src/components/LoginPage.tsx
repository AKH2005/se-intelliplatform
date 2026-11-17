import React, { useState } from 'react';

export interface UserProfile {
  email: string;
  name: string;
  role?: string;
}

interface LoginPageProps {
  isOpen: boolean;
  onClose: () => void;
  onLoginSuccess: (user: UserProfile) => void;
}

export default function LoginPage({ isOpen, onClose, onLoginSuccess }: LoginPageProps) {
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleQuickFill = () => {
    setEmail('executive@acmecorp.com');
    setPassword('ExecutiveSecure2026!');
    setName('Sarah Connor (VP)');
    setError(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please provide email and password.');
      return;
    }
    setError(null);
    const profile: UserProfile = {
      email,
      name: name || email.split('@')[0],
      role: 'Executive',
    };
    onLoginSuccess(profile);
  };

  return (
    <div
      id="auth-modal-overlay"
      className="auth-modal-overlay"
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 100000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(8px)',
      }}
      onClick={onClose}
    >
      <div
        className="auth-card"
        style={{
          maxWidth: '440px',
          width: '92%',
          backgroundColor: '#111726',
          border: '1px solid rgba(99, 102, 241, 0.4)',
          borderRadius: '14px',
          padding: '1.5rem',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6)',
          color: '#f8fafc',
        }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              type="button"
              id="tab-login"
              style={{
                padding: '0.4rem 0.8rem',
                borderRadius: '6px',
                border: 'none',
                background: !isSignUp ? '#6366f1' : 'transparent',
                color: '#fff',
                fontWeight: 700,
                cursor: 'pointer',
              }}
              onClick={() => { setIsSignUp(false); setError(null); }}
            >
              Sign In
            </button>
            <button
              type="button"
              id="tab-register"
              style={{
                padding: '0.4rem 0.8rem',
                borderRadius: '6px',
                border: 'none',
                background: isSignUp ? '#6366f1' : 'transparent',
                color: '#fff',
                fontWeight: 700,
                cursor: 'pointer',
              }}
              onClick={() => { setIsSignUp(true); setError(null); }}
            >
              Register
            </button>
          </div>
          <button
            type="button"
            id="btn-close-modal"
            style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1.2rem', cursor: 'pointer' }}
            onClick={onClose}
          >
            ✕
          </button>
        </div>

        {error && (
          <div id="auth-error-msg" style={{ background: 'rgba(239, 68, 68, 0.2)', border: '1px solid #ef4444', color: '#fca5a5', padding: '0.5rem', borderRadius: '6px', marginBottom: '0.75rem', fontSize: '0.85rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {isSignUp && (
            <div style={{ marginBottom: '0.85rem' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Executive Name</label>
              <input
                type="text"
                id="auth-name-input"
                style={{ width: '100%', padding: '0.55rem 0.85rem', background: '#0a0d14', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '8px', color: '#fff', boxSizing: 'border-box' }}
                placeholder="e.g. Sarah Connor"
                value={name}
                onChange={e => setName(e.target.value)}
              />
            </div>
          )}

          <div style={{ marginBottom: '0.85rem' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Work Email</label>
            <input
              type="email"
              id="auth-email-input"
              style={{ width: '100%', padding: '0.55rem 0.85rem', background: '#0a0d14', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '8px', color: '#fff', boxSizing: 'border-box' }}
              placeholder="executive@acmecorp.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
            />
          </div>

          <div style={{ marginBottom: '0.85rem' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', marginBottom: '0.25rem', color: '#94a3b8' }}>Password</label>
            <input
              type="password"
              id="auth-pwd-input"
              style={{ width: '100%', padding: '0.55rem 0.85rem', background: '#0a0d14', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '8px', color: '#fff', boxSizing: 'border-box' }}
              placeholder="••••••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', fontSize: '0.8rem', color: '#94a3b8' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', cursor: 'pointer' }}>
              <input type="checkbox" checked={rememberMe} onChange={e => setRememberMe(e.target.checked)} /> Remember me
            </label>
            <button
              type="button"
              id="link-forgot-password"
              style={{ background: 'transparent', border: 'none', color: '#6366f1', cursor: 'pointer', textDecoration: 'underline' }}
              onClick={() => alert('✓ Password recovery link has been dispatched to ' + (email || 'executive@acmecorp.com'))}
            >
              Forgot password?
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <button
              type="submit"
              id="btn-submit-auth"
              style={{ width: '100%', padding: '0.65rem', background: '#6366f1', border: 'none', borderRadius: '8px', color: '#fff', fontWeight: 700, cursor: 'pointer' }}
            >
              {isSignUp ? 'Create Executive Account' : 'Sign In to Dashboard'}
            </button>
            <button
              type="button"
              id="btn-quick-fill"
              style={{ width: '100%', padding: '0.55rem', background: 'rgba(255, 255, 255, 0.05)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '8px', color: '#94a3b8', fontSize: '0.8rem', cursor: 'pointer' }}
              onClick={handleQuickFill}
            >
              👤 Quick Fill Executive Demo
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
