import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { Navbar } from '../../components/layout/Navbar';
import { useAuth } from '../../context/AuthContext';
import { Lock, Mail, Eye, EyeOff, LogIn, AlertCircle, Sparkles, GraduationCap } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Preserve original destination from state
  const from = (location.state as any)?.from?.pathname || null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const user = await login({ email: email.trim(), password });
      // Redirect to from or role dashboard
      if (from) {
        navigate(from, { replace: true });
      } else if (user.role === 'STUDENT') {
        navigate('/student/dashboard', { replace: true });
      } else if (user.role === 'FACULTY') {
        navigate('/faculty/dashboard', { replace: true });
      } else {
        navigate('/admin/dashboard', { replace: true });
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const setDemoCredentials = (e: string, p: string) => {
    setEmail(e);
    setPassword(p);
    setError(null);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />

      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '3rem 1.5rem' }}>
        <div style={{ width: '100%', maxWidth: '440px' }}>
          {/* Card */}
          <div className="card" style={{ padding: '2.5rem', boxShadow: 'var(--shadow-lg)', border: '1px solid var(--border-strong)' }}>
            <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: '12px',
                  background: 'linear-gradient(135deg, #0284c7, #38bdf8)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '1rem',
                  boxShadow: '0 4px 15px rgba(56, 189, 248, 0.35)',
                }}
              >
                <GraduationCap size={26} color="#ffffff" />
              </div>
              <h1 style={{ fontSize: '1.65rem', fontWeight: 800, color: '#ffffff', marginBottom: '0.35rem' }}>
                Sign In to UniSphere
              </h1>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                Access courses, grades, attendance, and campus workspaces.
              </p>
            </div>

            {error && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.65rem',
                  padding: '0.85rem 1rem',
                  background: 'rgba(244, 63, 94, 0.15)',
                  border: '1px solid rgba(244, 63, 94, 0.3)',
                  borderRadius: 'var(--radius-sm)',
                  color: '#fda4af',
                  fontSize: '0.85rem',
                  marginBottom: '1.5rem',
                }}
              >
                <AlertCircle size={18} style={{ flexShrink: 0 }} />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">University Email Address</label>
                <div style={{ position: 'relative' }}>
                  <Mail size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
                  <input
                    type="email"
                    className="form-input"
                    placeholder="e.g. student.alex@unisphere.edu"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    style={{ paddingLeft: '2.25rem' }}
                  />
                </div>
              </div>

              <div className="form-group">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <label className="form-label">Password</label>
                  <Link to="/forgot-password" style={{ fontSize: '0.78rem', color: 'var(--accent-primary)' }}>
                    Forgot password?
                  </Link>
                </div>
                <div style={{ position: 'relative' }}>
                  <Lock size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    className="form-input"
                    placeholder="Enter account password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    style={{ paddingLeft: '2.25rem', paddingRight: '2.25rem' }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{
                      position: 'absolute',
                      right: 12,
                      top: '50%',
                      transform: 'translateY(-50%)',
                      background: 'none',
                      border: 'none',
                      color: 'var(--text-dim)',
                      cursor: 'pointer',
                      padding: 0,
                    }}
                    title={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                className="btn btn-primary"
                style={{ width: '100%', marginTop: '0.75rem', padding: '0.75rem' }}
                disabled={isLoading}
              >
                <LogIn size={16} />
                <span>{isLoading ? 'Authenticating...' : 'Sign In to Portal'}</span>
              </button>
            </form>

            {/* Quick Demo Fill Buttons */}
            <div style={{ marginTop: '2rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '1.25rem' }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-dim)', textAlign: 'center', marginBottom: '0.75rem' }}>
                Fast Login Demo Accounts
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.45rem' }}>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  style={{ fontSize: '0.72rem', padding: '0.4rem 0.2rem' }}
                  onClick={() => setDemoCredentials('student.alex@unisphere.edu', 'StudentPass123!')}
                >
                  Student
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  style={{ fontSize: '0.72rem', padding: '0.4rem 0.2rem' }}
                  onClick={() => setDemoCredentials('prof.smith@unisphere.edu', 'FacultyPass123!')}
                >
                  Faculty
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  style={{ fontSize: '0.72rem', padding: '0.4rem 0.2rem' }}
                  onClick={() => setDemoCredentials('admin@unisphere.edu', 'AdminPass123!')}
                >
                  Admin
                </button>
              </div>
            </div>

            <div style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              New to UniSphere?{' '}
              <Link to="/register" style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>
                Create Student Account
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
