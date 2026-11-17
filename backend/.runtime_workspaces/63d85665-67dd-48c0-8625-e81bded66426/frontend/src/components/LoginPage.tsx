import React, { useState } from 'react';

export interface UserProfile {
  email: string;
  name: string;
  level?: number;
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
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const getPasswordStrength = (pwd: string): { label: string; score: number; color: string } => {
    if (!pwd) return { label: 'None', score: 0, color: '#64748b' };
    if (pwd.length < 6) return { label: 'Weak', score: 25, color: '#ef4444' };
    if (pwd.length < 10) return { label: 'Medium', score: 60, color: '#eab308' };
    if (/[A-Z]/.test(pwd) && /[0-9]/.test(pwd) && /[^A-Za-z0-9]/.test(pwd)) {
      return { label: 'Legendary', score: 100, color: '#a855f7' };
    }
    return { label: 'Strong', score: 85, color: '#22c55e' };
  };

  const strength = getPasswordStrength(password);

  const handleQuickFill = () => {
    setEmail('ninja@shadowduel.com');
    setPassword('ShadowMaster2026!');
    setName('Master Shadow');
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!email || !password) {
      setError('Please provide email and password.');
      return;
    }
    setIsLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 350));
      const profile: UserProfile = {
        email,
        name: name || email.split('@')[0],
        level: 12,
        role: 'Grandmaster',
      };
      onLoginSuccess(profile);
    } catch (err: any) {
      setError(err?.message || 'Authentication failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-modal-overlay glass-backdrop" onClick={onClose}>
      <div className="auth-card modern-glass-card glow-border" onClick={e => e.stopPropagation()}>
        <div className="auth-card-header">
          <div className="auth-badge-pill">🔒 ENCRYPTED ARENA PORTAL</div>
          <div className="auth-tabs modern-tabs">
            <button
              type="button"
              className={`auth-tab ${!isSignUp ? 'active' : ''}`}
              onClick={() => { setIsSignUp(false); setError(null); }}
            >
              Sign In
            </button>
            <button
              type="button"
              className={`auth-tab ${isSignUp ? 'active' : ''}`}
              onClick={() => { setIsSignUp(true); setError(null); }}
            >
              Register
            </button>
          </div>
          <button type="button" className="auth-close-btn" onClick={onClose}>✕</button>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {error && <div className="auth-error-banner animate-shake">{error}</div>}

          {isSignUp && (
            <div className="auth-field">
              <label>Warrior Nickname</label>
              <input
                type="text"
                className="input-modern"
                placeholder="Shadow Slayer"
                value={name}
                onChange={e => setName(e.target.value)}
                required={isSignUp}
              />
            </div>
          )}

          <div className="auth-field">
            <label>Email Address</label>
            <input
              type="email"
              className="input-modern"
              placeholder="warrior@shadowduel.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="auth-field">
            <label>Master Password</label>
            <input
              type="password"
              className="input-modern"
              placeholder="••••••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
            {password && (
              <div className="strength-meter-wrapper">
                <div className="strength-bar-track">
                  <div
                    className="strength-bar-fill"
                    style={{ width: `${strength.score}%`, backgroundColor: strength.color }}
                  />
                </div>
                <span className="strength-text" style={{ color: strength.color }}>
                  {strength.label} Security
                </span>
              </div>
            )}
          </div>

          <div className="social-login-grid">
            <button type="button" className="btn-social google" onClick={handleQuickFill}>
              <span>G</span> Google SSO
            </button>
            <button type="button" className="btn-social github" onClick={handleQuickFill}>
              <span>⌨</span> GitHub
            </button>
          </div>

          <div className="auth-options">
            <label className="auth-remember">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={e => setRememberMe(e.target.checked)}
              />
              <span>Keep session alive for 30 days</span>
            </label>
          </div>

          <div className="auth-actions">
            <button type="submit" className="btn-primary auth-submit-btn modern-gradient" disabled={isLoading}>
              {isLoading ? 'Decrypting Credentials...' : (isSignUp ? 'Create Warrior Account' : 'Sign In to Arena')}
            </button>
            <button type="button" className="btn-secondary auth-demo-btn neon-subtle" onClick={handleQuickFill}>
              ⚡ Quick Fill Demo Ninja
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
