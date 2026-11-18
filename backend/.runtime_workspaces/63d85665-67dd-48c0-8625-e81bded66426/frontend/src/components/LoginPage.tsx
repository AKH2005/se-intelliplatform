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
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleQuickFill = () => {
    setEmail('player@carrommaster.local');
    setPassword('CarromMaster2026!');
    setName('Master Striker');
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
        role: 'Pro Striker',
      };
      onLoginSuccess(profile);
    } catch (err: any) {
      setError(err?.message || 'Authentication failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-modal-overlay" onClick={onClose} style={{ position: 'fixed', inset: 0, zIndex: 10000, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(3,7,18,0.75)', backdropFilter: 'blur(8px)' }}>
      <div className="auth-card" onClick={e => e.stopPropagation()} style={{ background: '#0f172a', border: '1px solid rgba(99,102,241,0.3)', borderRadius: '16px', width: '90%', maxWidth: '420px', padding: '1.75rem', color: '#f8fafc' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', gap: '0.5rem', background: 'rgba(30,41,59,0.6)', padding: '0.25rem', borderRadius: '8px' }}>
            <button type="button" style={{ background: !isSignUp ? '#6366f1' : 'transparent', border: 'none', color: '#fff', padding: '0.4rem 0.85rem', borderRadius: '6px', cursor: 'pointer', fontWeight: 600 }} onClick={() => { setIsSignUp(false); setError(null); }}>Sign In</button>
            <button type="button" style={{ background: isSignUp ? '#6366f1' : 'transparent', border: 'none', color: '#fff', padding: '0.4rem 0.85rem', borderRadius: '6px', cursor: 'pointer', fontWeight: 600 }} onClick={() => { setIsSignUp(true); setError(null); }}>Register</button>
          </div>
          <button type="button" style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1.2rem', cursor: 'pointer' }} onClick={onClose}>✕</button>
        </div>

        <form onSubmit={handleSubmit}>
          {error && <div style={{ background: 'rgba(239,68,68,0.2)', border: '1px solid #ef4444', color: '#fca5a5', padding: '0.5rem', borderRadius: '6px', marginBottom: '0.75rem', fontSize: '0.85rem' }}>{error}</div>}

          {isSignUp && (
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '0.35rem' }}>Player Nickname</label>
              <input type="text" placeholder="Master Striker" value={name} onChange={e => setName(e.target.value)} style={{ width: '100%', background: 'rgba(30,41,59,0.7)', border: '1px solid rgba(99,102,241,0.25)', borderRadius: '8px', padding: '0.65rem', color: '#fff', boxSizing: 'border-box' }} required={isSignUp} />
            </div>
          )}

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '0.35rem' }}>Email Address</label>
            <input type="email" placeholder="player@carrommaster.local" value={email} onChange={e => setEmail(e.target.value)} style={{ width: '100%', background: 'rgba(30,41,59,0.7)', border: '1px solid rgba(99,102,241,0.25)', borderRadius: '8px', padding: '0.65rem', color: '#fff', boxSizing: 'border-box' }} required />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '0.35rem' }}>Password</label>
            <input type="password" placeholder="••••••••••••" value={password} onChange={e => setPassword(e.target.value)} style={{ width: '100%', background: 'rgba(30,41,59,0.7)', border: '1px solid rgba(99,102,241,0.25)', borderRadius: '8px', padding: '0.65rem', color: '#fff', boxSizing: 'border-box' }} required />
          </div>

          <div style={{ marginBottom: '1.25rem', fontSize: '0.85rem', color: '#94a3b8' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', cursor: 'pointer' }}>
              <input type="checkbox" checked={rememberMe} onChange={e => setRememberMe(e.target.checked)} /> Remember me
            </label>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
            <button type="submit" disabled={isLoading} style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', border: 'none', color: '#fff', padding: '0.75rem', borderRadius: '8px', fontWeight: 700, cursor: 'pointer' }}>
              {isLoading ? 'Authenticating...' : (isSignUp ? 'Create Player Account' : 'Sign In to Carrom Master')}
            </button>
            <button type="button" onClick={handleQuickFill} style={{ background: 'rgba(30,41,59,0.7)', border: '1px dashed rgba(99,102,241,0.4)', color: '#a5b4fc', padding: '0.6rem', borderRadius: '8px', fontWeight: 600, cursor: 'pointer', fontSize: '0.85rem' }}>
              👤 Quick Fill Carrom Player
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
