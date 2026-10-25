import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Navbar } from '../../components/layout/Navbar';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import { UserPlus, Mail, Lock, User, Hash, AlertCircle } from 'lucide-react';

export const RegisterPage: React.FC = () => {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [studentIdNumber, setStudentIdNumber] = useState('');
  const [departmentId, setDepartmentId] = useState<number>(1);
  const [departments, setDepartments] = useState<any[]>([]);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.departments.list().then(setDepartments).catch(console.error);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    setIsLoading(true);
    try {
      await register({
        full_name: fullName.trim(),
        email: email.trim().toLowerCase(),
        password,
        student_id_number: studentIdNumber.trim().toUpperCase(),
        department_id: Number(departmentId),
        year: 1,
        semester: 1,
      });
      navigate('/student/dashboard', { replace: true });
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />

      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '3rem 1.5rem' }}>
        <div style={{ width: '100%', maxWidth: '480px' }}>
          <div className="card" style={{ padding: '2.5rem', boxShadow: 'var(--shadow-lg)' }}>
            <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
              <h1 style={{ fontSize: '1.65rem', fontWeight: 800, color: '#ffffff', marginBottom: '0.35rem' }}>
                Student Registration
              </h1>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                Create your verified UniSphere student portal account.
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
                <label className="form-label">Full Name *</label>
                <div style={{ position: 'relative' }}>
                  <User size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Maya Lin"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                    style={{ paddingLeft: '2.25rem' }}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">University Email *</label>
                <div style={{ position: 'relative' }}>
                  <Mail size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
                  <input
                    type="email"
                    className="form-input"
                    placeholder="e.g. maya.lin@unisphere.edu"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    style={{ paddingLeft: '2.25rem' }}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Student ID Number *</label>
                <div style={{ position: 'relative' }}>
                  <Hash size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. CS-2026-108"
                    value={studentIdNumber}
                    onChange={(e) => setStudentIdNumber(e.target.value)}
                    required
                    style={{ paddingLeft: '2.25rem' }}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Academic Department *</label>
                <select
                  className="form-select"
                  value={departmentId}
                  onChange={(e) => setDepartmentId(Number(e.target.value))}
                >
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.code})
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Password * (Minimum 6 characters)</label>
                <div style={{ position: 'relative' }}>
                  <Lock size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
                  <input
                    type="password"
                    className="form-input"
                    placeholder="Create a secure password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    style={{ paddingLeft: '2.25rem' }}
                  />
                </div>
              </div>

              <button
                type="submit"
                className="btn btn-primary"
                style={{ width: '100%', marginTop: '0.75rem', padding: '0.75rem' }}
                disabled={isLoading}
              >
                <UserPlus size={16} />
                <span>{isLoading ? 'Creating Account...' : 'Complete Registration'}</span>
              </button>
            </form>

            <div style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Already registered?{' '}
              <Link to="/login" style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>
                Sign In
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
