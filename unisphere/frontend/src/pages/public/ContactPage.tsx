import React, { useState } from 'react';
import { Navbar } from '../../components/layout/Navbar';
import { Mail, Phone, MapPin, Send, CheckCircle2, AlertCircle } from 'lucide-react';
import { api } from '../../services/api';

export const ContactPage: React.FC = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{ success: boolean; message: string } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFeedback(null);

    // Validation
    if (name.trim().length < 2) {
      setFeedback({ success: false, message: 'Please provide a valid name (at least 2 characters).' });
      return;
    }
    if (!email.includes('@') || !email.includes('.')) {
      setFeedback({ success: false, message: 'Please provide a valid email address.' });
      return;
    }
    if (subject.trim().length < 3) {
      setFeedback({ success: false, message: 'Subject must be at least 3 characters long.' });
      return;
    }
    if (message.trim().length < 10) {
      setFeedback({ success: false, message: 'Message must be at least 10 characters long.' });
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await api.contact.submit({
        name: name.trim(),
        email: email.trim(),
        subject: subject.trim(),
        message: message.trim(),
      });
      setFeedback({
        success: true,
        message: `Thank you, ${res.name}. Your inquiry #${res.id} has been registered with UniSphere Admissions. We will contact you at ${res.email}.`,
      });
      setName('');
      setEmail('');
      setSubject('');
      setMessage('');
    } catch (err: any) {
      setFeedback({
        success: false,
        message: err.message || 'Failed to submit contact message. Please try again.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />

      <section style={{ padding: '3.5rem 0 2rem 0', background: 'radial-gradient(ellipse 60% 50% at 50% 0%, rgba(56, 189, 248, 0.08), transparent)', borderBottom: '1px solid var(--border-subtle)' }}>
        <div className="container" style={{ textAlign: 'center', maxWidth: 700 }}>
          <span className="badge badge-info" style={{ marginBottom: '0.75rem' }}>Admissions & Inquiries</span>
          <h1 style={{ fontSize: '2.5rem', fontWeight: 800, color: '#ffffff', marginBottom: '0.75rem' }}>
            Contact UniSphere University
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            Have questions about programs, campus tours, or university partnerships? Submit an inquiry and our admissions team will respond promptly.
          </p>
        </div>
      </section>

      <div className="container" style={{ padding: '3.5rem 1.5rem', maxWidth: 1000, flex: 1 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2.5rem' }}>
          {/* Contact Details Card */}
          <div>
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#ffffff', marginBottom: '1.25rem' }}>
                University Campus
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.15rem' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.85rem' }}>
                  <MapPin size={20} color="var(--accent-primary)" style={{ flexShrink: 0, marginTop: '2px' }} />
                  <div>
                    <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#ffffff' }}>Main University Campus</div>
                    <div style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                      100 Innovation Boulevard, Tech District<br />Cambridge, MA 02138
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.85rem' }}>
                  <Mail size={20} color="var(--accent-indigo)" style={{ flexShrink: 0, marginTop: '2px' }} />
                  <div>
                    <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#ffffff' }}>General Inquiries</div>
                    <div style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>admissions@unisphere.edu</div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.85rem' }}>
                  <Phone size={20} color="var(--accent-emerald)" style={{ flexShrink: 0, marginTop: '2px' }} />
                  <div>
                    <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#ffffff' }}>Telephone Desk</div>
                    <div style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>+1 (555) 019-8000 (Mon - Fri, 8am - 5pm)</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="card" style={{ background: 'rgba(56, 189, 248, 0.05)', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
              <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#ffffff', marginBottom: '0.35rem' }}>
                Looking for Portal Access?
              </div>
              <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)', marginBottom: '0.85rem' }}>
                Current students and faculty members can directly sign in to their dedicated workspaces.
              </p>
              <a href="/login" style={{ fontSize: '0.825rem', fontWeight: 700, color: 'var(--accent-primary)' }}>
                Go to Portal Sign In →
              </a>
            </div>
          </div>

          {/* Contact Form */}
          <div className="card">
            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#ffffff', marginBottom: '1.25rem' }}>
              Send an Inquiry
            </h3>

            {feedback && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '0.75rem',
                  padding: '1rem',
                  borderRadius: 'var(--radius-sm)',
                  marginBottom: '1.25rem',
                  background: feedback.success ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
                  border: `1px solid ${feedback.success ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
                  color: feedback.success ? '#6ee7b7' : '#fda4af',
                  fontSize: '0.875rem',
                  fontWeight: 500,
                }}
              >
                {feedback.success ? <CheckCircle2 size={18} style={{ flexShrink: 0, marginTop: '2px' }} /> : <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />}
                <span>{feedback.message}</span>
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Full Name *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Elena Rostova"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Email Address *</label>
                <input
                  type="email"
                  className="form-input"
                  placeholder="e.g. elena@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Subject *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Fall 2026 Admissions Query"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Inquiry Message *</label>
                <textarea
                  className="form-textarea"
                  placeholder="Tell us about your background and what programs you are interested in..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  required
                />
              </div>

              <button
                type="submit"
                className="btn btn-primary"
                style={{ width: '100%', marginTop: '0.5rem' }}
                disabled={isSubmitting}
              >
                <Send size={16} />
                <span>{isSubmitting ? 'Sending Message...' : 'Submit Inquiry'}</span>
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
