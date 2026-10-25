import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Navbar } from '../../components/layout/Navbar';
import { api } from '../../services/api';
import { KeyRound, Mail, Lock, CheckCircle2, AlertCircle, ArrowLeft } from 'lucide-react';

export const ForgotPasswordPage: React.FC = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState<'request' | 'reset'>('request');
  const [email, setEmail] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');

  const [isLoading, setIsLoading] = useState(false);
  const [feedback, setFeedback] = useState<{ success: boolean; message: string } | null>(null);

  const handleRequestToken = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setFeedback(null);
    try {
      const res = await api.auth.forgotPassword(email.trim());
      if (res.reset_token) {
        setResetToken(res.reset_token);
        setStep('reset');
        setFeedback({
          success: true,
          message: 'Development Mode: Recovery token generated below. Please enter your new password.',
        });
      } else {
        setFeedback({
          success: true,
          message: res.message,
        });
      }
    } catch (err: any) {
      setFeedback({ success: false, message: err.message || 'Failed to request password reset.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 6) {
      setFeedback({ success: false, message: 'New password must be at least 6 characters long.' });
      return;
    }
    setIsLoading(true);
    try {
      const res = await api.auth.resetPassword({
        reset_token: resetToken,
        new_password: newPassword,
      });
      alert(res.message);
      navigate('/login');
    } catch (err: any) {
      setFeedback({ success: false, message: err.message || 'Failed to reset password.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />

      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '3rem 1.5rem' }}>
        <div style={{ width: '100%', maxWidth: '440px' }}>
          <div className="card" style={{ padding: '2.5rem', boxShadow: 'var(--shadow-lg)' }}>
            <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: '12px',
                  background: 'rgba(56, 189, 248, 0.1)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '1rem',
                  color: 'var(--accent-primary)',
                }}
              >
                <KeyRound size={24} />
              </div>
              <h1 style={{ fontSize: '1.65rem', fontWeight: 800, color: '#ffffff', marginBottom: '0.35rem' }}>
                Account Recovery
              </h1>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                {step === 'request'
                  ? 'Enter your university email to receive recovery instructions.'
                  : 'Enter your new account password to complete recovery.'}
              </p>
            </div>

            {feedback && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '0.65rem',
                  padding: '0.85rem',
                  borderRadius: 'var(--radius-sm)',
                  marginBottom: '1.5rem',
                  background: feedback.success ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
                  border: `1px solid ${feedback.success ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
                  color: feedback.success ? '#6ee7b7' : '#fda4af',
                  fontSize: '0.85rem',
                }}
              >
                {feedback.success ? <CheckCircle2 size={18} style={{ flexShrink: 0, marginTop: '2px' }} /> : <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />}
                <span>{feedback.message}</span>
              </div>
            )}

            {step === 'request' ? (
              <form onSubmit={handleRequestToken}>
                <div className="form-group">
                  <label className="form-label">University Email</label>
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

                <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '0.5rem' }} disabled={isLoading}>
                  {isLoading ? 'Generating Recovery Token...' : 'Send Recovery Token'}
                </button>
              </form>
            ) : (
              <form onSubmit={handleResetPassword}>
                <div className="form-group">
                  <label className="form-label">Recovery Token</label>
                  <input
                    type="text"
                    className="form-input"
                    value={resetToken}
                    onChange={(e) => setResetToken(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">New Password (Min 6 characters)</label>
                  <div style={{ position: 'relative' }}>
                    <Lock size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
                    <input
                      type="password"
                      className="form-input"
                      placeholder="Enter new password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      required
                      style={{ paddingLeft: '2.25rem' }}
                    />
                  </div>
                </div>

                <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '0.5rem' }} disabled={isLoading}>
                  {isLoading ? 'Updating Password...' : 'Save New Password'}
                </button>
              </form>
            )}

            <div style={{ textAlign: 'center', marginTop: '1.75rem' }}>
              <Link to="/login" style={{ color: 'var(--text-muted)', fontSize: '0.85rem', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
                <ArrowLeft size={14} />
                <span>Return to Sign In</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
