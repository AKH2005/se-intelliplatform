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
  Check,
  Terminal,
  Layers,
  Cpu,
} from 'lucide-react';

export interface LoginViewProps {
  initialMode?: 'login' | 'register';
  onSuccess?: () => void;
  redirectPath?: string;
}

export const LoginView: React.FC<LoginViewProps> = ({
  initialMode = 'login',
  onSuccess,
  redirectPath = '/select-mode',
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

  // Password checklist helpers for Register mode
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
      setLocalError('Please enter both your email address and password.');
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
      if (typeof window !== 'undefined') {
        window.history.pushState({}, '', redirectPath || '/select-mode');
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
        background: 'radial-gradient(ellipse at 50% 10%, rgba(124, 58, 237, 0.15) 0%, rgba(10, 13, 20, 1) 75%)',
        padding: '2rem 1.25rem',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Background Decorative Tech Grid */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
          pointerEvents: 'none',
        }}
      />

      {/* Ambient Glow Orbs */}
      <div
        style={{
          position: 'absolute',
          top: '15%',
          left: '10%',
          width: '320px',
          height: '320px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(139, 92, 246, 0.12) 0%, transparent 70%)',
          filter: 'blur(40px)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: '10%',
          right: '12%',
          width: '380px',
          height: '380px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(99, 102, 241, 0.10) 0%, transparent 70%)',
          filter: 'blur(50px)',
          pointerEvents: 'none',
        }}
      />

      {/* Split-Screen Main Auth Container */}
      <div
        style={{
          width: '100%',
          maxWidth: '1040px',
          background: 'rgba(18, 24, 40, 0.75)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '1px solid var(--border-glass-bright, rgba(255, 255, 255, 0.15))',
          borderRadius: 'var(--radius-xl, 18px)',
          boxShadow: 'var(--shadow-xl), 0 0 50px -10px rgba(124, 58, 237, 0.2), var(--shadow-inner-rim)',
          display: 'flex',
          flexDirection: 'row',
          overflow: 'hidden',
          position: 'relative',
          zIndex: 1,
        }}
        className="auth-split-container"
      >
        {/* ================================================================= */}
        {/* 1. Brand Showcase Panel (Left on Desktop, Clean Header on Mobile)  */}
        {/* ================================================================= */}
        <div
          style={{
            flex: '1.05',
            padding: '3rem 2.75rem',
            background: 'linear-gradient(145deg, rgba(20, 26, 44, 0.95) 0%, rgba(11, 15, 26, 0.95) 100%)',
            borderRight: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            position: 'relative',
          }}
          className="auth-brand-panel"
        >
          {/* Top Brand Identity */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '2rem' }}>
              <div
                style={{
                  width: 42,
                  height: 42,
                  borderRadius: 'var(--radius-md, 10px)',
                  background: 'var(--accent-gradient, linear-gradient(135deg, #7c3aed, #6366f1))',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 4px 16px rgba(124, 58, 237, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.25)',
                }}
              >
                <Code2 size={22} color="#ffffff" />
              </div>
              <div>
                <span
                  style={{
                    fontSize: '1.15rem',
                    fontWeight: 750,
                    color: '#ffffff',
                    letterSpacing: '-0.02em',
                    display: 'block',
                    lineHeight: 1.2,
                  }}
                >
                  SE IntelliPlatform
                </span>
                <span
                  style={{
                    fontSize: '0.7rem',
                    fontWeight: 650,
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    color: 'var(--accent-violet-light, #a78bfa)',
                  }}
                >
                  Autonomous AI Engineering
                </span>
              </div>
            </div>

            <h2
              style={{
                fontSize: '1.75rem',
                fontWeight: 750,
                color: '#ffffff',
                letterSpacing: '-0.03em',
                lineHeight: 1.25,
                marginBottom: '0.85rem',
              }}
            >
              Software Engineering, Elevated by Intelligence.
            </h2>

            <p
              style={{
                fontSize: '0.9rem',
                color: 'var(--text-secondary, #cbd5e1)',
                lineHeight: 1.6,
                marginBottom: '2rem',
              }}
            >
              Synthesize full-stack applications from requirements, run isolated preview containers, and continuously refine software through natural conversation.
            </p>

            {/* Abstract 3D-Perspective Architecture Graphic */}
            <div
              style={{
                position: 'relative',
                padding: '1.25rem',
                borderRadius: 'var(--radius-lg, 14px)',
                background: 'rgba(9, 12, 21, 0.75)',
                border: '1px solid var(--border-medium, rgba(255, 255, 255, 0.12))',
                boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.08), 0 12px 28px -4px rgba(0, 0, 0, 0.55)',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem',
                marginBottom: '2rem',
              }}
              className="auth-architecture-preview"
            >
              {/* Stack Layer 1: Code Generation */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.55rem 0.85rem',
                  borderRadius: 'var(--radius-sm, 6px)',
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid rgba(255, 255, 255, 0.07)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
                  <Terminal size={14} color="#a78bfa" />
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#f8fafc' }}>
                    Autonomous Code Synthesis
                  </span>
                </div>
                <span
                  style={{
                    fontSize: '0.68rem',
                    fontWeight: 650,
                    color: '#34d399',
                    background: 'rgba(16, 185, 129, 0.12)',
                    padding: '0.15rem 0.45rem',
                    borderRadius: '9999px',
                    border: '1px solid rgba(16, 185, 129, 0.25)',
                  }}
                >
                  ● Verified
                </span>
              </div>

              {/* Stack Layer 2: Docker Runtime */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.55rem 0.85rem',
                  borderRadius: 'var(--radius-sm, 6px)',
                  background: 'rgba(124, 58, 237, 0.08)',
                  border: '1px solid rgba(139, 92, 246, 0.25)',
                  boxShadow: '0 0 16px -2px rgba(124, 58, 237, 0.15)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
                  <Cpu size={14} color="#818cf8" />
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#f8fafc' }}>
                    Isolated Container Runtime
                  </span>
                </div>
                <span
                  style={{
                    fontSize: '0.68rem',
                    fontWeight: 650,
                    color: '#38bdf8',
                    background: 'rgba(56, 189, 248, 0.12)',
                    padding: '0.15rem 0.45rem',
                    borderRadius: '9999px',
                    border: '1px solid rgba(56, 189, 248, 0.25)',
                  }}
                >
                  ● Port 8001
                </span>
              </div>

              {/* Stack Layer 3: Versioning & Rollback */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.55rem 0.85rem',
                  borderRadius: 'var(--radius-sm, 6px)',
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid rgba(255, 255, 255, 0.07)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
                  <Layers size={14} color="#38bdf8" />
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#f8fafc' }}>
                    Version Concurrency & Rollback
                  </span>
                </div>
                <span
                  style={{
                    fontSize: '0.68rem',
                    fontWeight: 650,
                    color: '#c4b5fd',
                    background: 'rgba(139, 92, 246, 0.12)',
                    padding: '0.15rem 0.45rem',
                    borderRadius: '9999px',
                    border: '1px solid rgba(139, 92, 246, 0.25)',
                  }}
                >
                  v1 → v2
                </span>
              </div>
            </div>
          </div>

          {/* Bottom Capability Tags */}
          <div
            style={{
              display: 'flex',
              gap: '1rem',
              alignItems: 'center',
              flexWrap: 'wrap',
              fontSize: '0.75rem',
              color: 'var(--text-muted, #94a3b8)',
              borderTop: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.07))',
              paddingTop: '1.25rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <ShieldCheck size={14} color="#10b981" />
              <span>Fullstack Sandboxing</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <Sparkles size={14} color="#8b5cf6" />
              <span>Live App Refinement</span>
            </div>
          </div>
        </div>

        {/* ================================================================= */}
        {/* 2. Authentication Form Panel (Right on Desktop, Full on Mobile)   */}
        {/* ================================================================= */}
        <div
          style={{
            flex: '1',
            padding: '3rem 2.75rem',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            background: 'var(--bg-glass-card, rgba(20, 26, 44, 0.65))',
          }}
          className="auth-form-panel"
        >
          {/* Segmented Mode Toggle Tabs */}
          <div
            style={{
              display: 'flex',
              borderRadius: 'var(--radius-md, 10px)',
              background: 'rgba(8, 11, 18, 0.6)',
              padding: '0.25rem',
              border: '1px solid var(--border-medium, rgba(255, 255, 255, 0.12))',
              marginBottom: '1.75rem',
              boxShadow: 'inset 0 1px 3px rgba(0, 0, 0, 0.4)',
            }}
          >
            <button
              type="button"
              id="btn-tab-login"
              onClick={() => switchMode('login')}
              style={{
                flex: 1,
                padding: '0.55rem 0.85rem',
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
                boxShadow: mode === 'login' ? 'var(--shadow-sm), 0 0 14px rgba(124, 58, 237, 0.35)' : 'none',
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
                padding: '0.55rem 0.85rem',
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
                boxShadow: mode === 'register' ? 'var(--shadow-sm), 0 0 14px rgba(124, 58, 237, 0.35)' : 'none',
              }}
            >
              Register
            </button>
          </div>

          {/* Form Header */}
          <div style={{ marginBottom: '1.5rem' }}>
            <h1
              style={{
                fontSize: '1.55rem',
                fontWeight: 750,
                color: '#ffffff',
                letterSpacing: '-0.025em',
                marginBottom: '0.35rem',
              }}
            >
              {mode === 'login' ? 'Welcome Back' : 'Create Your Account'}
            </h1>
            <p
              style={{
                fontSize: '0.85rem',
                color: 'var(--text-muted, #94a3b8)',
                lineHeight: 1.5,
                margin: 0,
              }}
            >
              {mode === 'login'
                ? 'Sign in to access your projects, specifications, and AI workspaces.'
                : 'Join SE IntelliPlatform to build, verify, and preview software with AI.'}
            </p>
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
                background: 'linear-gradient(180deg, rgba(239, 68, 68, 0.14) 0%, rgba(239, 68, 68, 0.08) 100%)',
                border: '1px solid rgba(239, 68, 68, 0.35)',
                color: '#f87171',
                borderRadius: 'var(--radius-md, 10px)',
                fontSize: '0.85rem',
                marginBottom: '1.25rem',
                lineHeight: 1.45,
                boxShadow: 'var(--shadow-xs)',
              }}
            >
              <AlertCircle size={17} style={{ flexShrink: 0, marginTop: '0.1rem' }} />
              <span style={{ flex: 1 }}>{activeError}</span>
            </div>
          )}

          {/* Authentication Form */}
          <form onSubmit={handleSubmit} noValidate style={{ display: 'flex', flexDirection: 'column', gap: '1.15rem' }}>
            {/* Full Name Field (Register Mode Only) */}
            {mode === 'register' && (
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label
                  className="form-label"
                  htmlFor="login-name"
                  style={{
                    fontWeight: 600,
                    fontSize: '0.825rem',
                    color: '#e2e8f0',
                    marginBottom: '0.35rem',
                    display: 'block',
                  }}
                >
                  Full Name *
                </label>
                <div style={{ position: 'relative' }}>
                  <UserIcon
                    size={16}
                    style={{
                      position: 'absolute',
                      left: '0.85rem',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      color: 'var(--text-muted, #64748b)',
                      pointerEvents: 'none',
                    }}
                  />
                  <input
                    id="login-name"
                    type="text"
                    className="form-input"
                    style={{
                      paddingLeft: '2.4rem',
                      width: '100%',
                      background: 'var(--bg-surface-subtle, #0d121f)',
                      border: '1px solid var(--border-medium, rgba(255, 255, 255, 0.12))',
                      fontSize: '0.875rem',
                      borderRadius: 'var(--radius-sm, 6px)',
                      color: '#ffffff',
                      paddingTop: '0.6rem',
                      paddingBottom: '0.6rem',
                    }}
                    placeholder="e.g. Alex Morgan"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>
              </div>
            )}

            {/* Email Address Field */}
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label
                className="form-label"
                htmlFor="login-email"
                style={{
                  fontWeight: 600,
                  fontSize: '0.825rem',
                  color: '#e2e8f0',
                  marginBottom: '0.35rem',
                  display: 'block',
                }}
              >
                Email Address *
              </label>
              <div style={{ position: 'relative' }}>
                <Mail
                  size={16}
                  style={{
                    position: 'absolute',
                    left: '0.85rem',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'var(--text-muted, #64748b)',
                    pointerEvents: 'none',
                  }}
                />
                <input
                  id="login-email"
                  type="email"
                  className="form-input"
                  style={{
                    paddingLeft: '2.4rem',
                    width: '100%',
                    background: 'var(--bg-surface-subtle, #0d121f)',
                    border: '1px solid var(--border-medium, rgba(255, 255, 255, 0.12))',
                    fontSize: '0.875rem',
                    borderRadius: 'var(--radius-sm, 6px)',
                    color: '#ffffff',
                    paddingTop: '0.6rem',
                    paddingBottom: '0.6rem',
                  }}
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="form-group" style={{ marginBottom: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
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
                  style={{
                    position: 'absolute',
                    left: '0.85rem',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'var(--text-muted, #64748b)',
                    pointerEvents: 'none',
                  }}
                />
                <input
                  id="login-password"
                  type={showPassword ? 'text' : 'password'}
                  className="form-input"
                  style={{
                    paddingLeft: '2.4rem',
                    paddingRight: '2.5rem',
                    width: '100%',
                    background: 'var(--bg-surface-subtle, #0d121f)',
                    border: '1px solid var(--border-medium, rgba(255, 255, 255, 0.12))',
                    fontSize: '0.875rem',
                    borderRadius: 'var(--radius-sm, 6px)',
                    color: '#ffffff',
                    paddingTop: '0.6rem',
                    paddingBottom: '0.6rem',
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

            {/* Confirm Password Field (Register Mode Only) */}
            {mode === 'register' && (
              <>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label
                    className="form-label"
                    htmlFor="login-confirm-password"
                    style={{
                      fontWeight: 600,
                      fontSize: '0.825rem',
                      color: '#e2e8f0',
                      marginBottom: '0.35rem',
                      display: 'block',
                    }}
                  >
                    Confirm Password *
                  </label>
                  <div style={{ position: 'relative' }}>
                    <Lock
                      size={16}
                      style={{
                        position: 'absolute',
                        left: '0.85rem',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        color: 'var(--text-muted, #64748b)',
                        pointerEvents: 'none',
                      }}
                    />
                    <input
                      id="login-confirm-password"
                      type={showConfirmPassword ? 'text' : 'password'}
                      className="form-input"
                      style={{
                        paddingLeft: '2.4rem',
                        paddingRight: '2.5rem',
                        width: '100%',
                        background: 'var(--bg-surface-subtle, #0d121f)',
                        border: '1px solid var(--border-medium, rgba(255, 255, 255, 0.12))',
                        fontSize: '0.875rem',
                        borderRadius: 'var(--radius-sm, 6px)',
                        color: '#ffffff',
                        paddingTop: '0.6rem',
                        paddingBottom: '0.6rem',
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

                {/* Password Strength / Requirement Live Feedback */}
                <div
                  style={{
                    background: 'rgba(0, 0, 0, 0.25)',
                    border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
                    borderRadius: 'var(--radius-sm, 6px)',
                    padding: '0.55rem 0.75rem',
                    fontSize: '0.75rem',
                    display: 'grid',
                    gridTemplateColumns: 'repeat(2, 1fr)',
                    gap: '0.35rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: hasMinLength ? '#34d399' : '#64748b' }}>
                    <Check size={12} strokeWidth={hasMinLength ? 3 : 2} />
                    <span>8+ characters</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: hasNumber ? '#34d399' : '#64748b' }}>
                    <Check size={12} strokeWidth={hasNumber ? 3 : 2} />
                    <span>1+ number</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: hasLetter ? '#34d399' : '#64748b' }}>
                    <Check size={12} strokeWidth={hasLetter ? 3 : 2} />
                    <span>1+ letter</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: passwordsMatch ? '#34d399' : '#64748b' }}>
                    <Check size={12} strokeWidth={passwordsMatch ? 3 : 2} />
                    <span>Passwords match</span>
                  </div>
                </div>
              </>
            )}

            {/* Submit Action Button */}
            <Button
              type="submit"
              variant="primary"
              size="lg"
              isLoading={isSubmitting}
              id={mode === 'login' ? 'btn-login-submit' : 'btn-register-submit'}
              style={{
                marginTop: '0.5rem',
                fontWeight: 650,
                fontSize: '0.925rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                boxShadow: 'var(--shadow-sm), 0 0 20px -2px rgba(124, 58, 237, 0.45)',
              }}
              icon={<ShieldCheck size={18} />}
            >
              <span>{mode === 'login' ? 'Sign In to Workspace' : 'Create Account & Continue'}</span>
            </Button>
          </form>

          {/* Footer Switcher */}
          <div
            style={{
              textAlign: 'center',
              marginTop: '1.75rem',
              fontSize: '0.85rem',
              color: 'var(--text-muted, #94a3b8)',
            }}
          >
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
                  id="btn-switch-to-login"
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
      </div>

      {/* Feature Highlights Footer Bar */}
      <div
        style={{
          marginTop: '2.5rem',
          display: 'flex',
          gap: '2.5rem',
          alignItems: 'center',
          flexWrap: 'wrap',
          justifyContent: 'center',
          color: 'var(--text-muted, #94a3b8)',
          fontSize: '0.825rem',
          position: 'relative',
          zIndex: 1,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
          <FolderKanban size={15} color="var(--accent-primary, #6366f1)" />
          <span>Isolated Project Workspaces</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
          <Bot size={15} color="var(--accent-violet, #8b5cf6)" />
          <span>Requirements-Driven AI Generation</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
          <Sparkles size={15} color="#10b981" />
          <span>Project-Specific Live Previews</span>
        </div>
      </div>

      {/* Responsive Styles for Split-Screen */}
      <style>{`
        @media (max-width: 900px) {
          .auth-split-container {
            flex-direction: column !important;
            max-width: 480px !important;
          }
          .auth-brand-panel {
            padding: 2rem 1.5rem !important;
            border-right: none !important;
            border-bottom: 1px solid var(--border-subtle, rgba(255, 255, 255, 0.08)) !important;
          }
          .auth-form-panel {
            padding: 2rem 1.5rem !important;
          }
          .auth-architecture-preview {
            display: none !important;
          }
        }
      `}</style>
    </div>
  );
};
