import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Users,
  GraduationCap,
  Calendar,
  BookOpen,
  Award,
  FileText,
  CheckSquare,
  Edit,
  Phone,
  MapPin,
  Shield,
  ArrowLeft,
} from 'lucide-react';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { Breadcrumbs } from '../../components/common/Breadcrumbs';
import { Modal } from '../../components/common/Modal';
import { Toast } from '../../components/common/Toast';

export const StudentDetailPage: React.FC = () => {
  const { studentId } = useParams<{ studentId: string }>();
  const { user, isAdmin, isFaculty } = useAuth();

  const [data, setData] = useState<any | null>(null);
  const [departments, setDepartments] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Edit student modal (Journey B)
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [editName, setEditName] = useState('');
  const [editGpa, setEditGpa] = useState<number>(3.5);
  const [editYear, setEditYear] = useState<number>(1);
  const [editPhone, setEditPhone] = useState('');
  const [editAddress, setEditAddress] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchStudent = async () => {
    if (!studentId) return;
    setIsLoading(true);
    try {
      const [res, dList] = await Promise.all([
        api.students.get(Number(studentId)),
        api.departments.list(),
      ]);
      setData(res);
      setDepartments(dList);

      // Pre-fill edit fields
      setEditName(res.student.full_name);
      setEditGpa(res.student.gpa);
      setEditYear(res.student.year);
      setEditPhone(res.personal_info.phone || '');
      setEditAddress(res.personal_info.address || '');
    } catch (err: any) {
      setError(err.message || 'Student record not found.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStudent();
  }, [studentId]);

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!studentId) return;
    setIsSaving(true);
    try {
      const updated = await api.students.update(Number(studentId), {
        full_name: editName.trim(),
        gpa: Number(editGpa),
        year: Number(editYear),
        phone: editPhone.trim(),
        address: editAddress.trim(),
      });
      setIsEditOpen(false);
      setToast({ type: 'success', message: `Student profile for ${updated.full_name} updated successfully!` });
      fetchStudent();
    } catch (err: any) {
      setToast({ type: 'error', message: err.message || 'Failed to update student profile.' });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return <LoadingSpinner label="Loading student academic dossier..." />;
  }

  if (error || !data) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem 1rem' }}>
        <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#ffffff', marginBottom: '0.75rem' }}>
          Student Record Not Found
        </h2>
        <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
          {error || 'The requested student ID is not valid or was removed.'}
        </p>
        <Link to="/students" className="btn btn-primary">
          <ArrowLeft size={16} />
          <span>Return to Students Directory</span>
        </Link>
      </div>
    );
  }

  const { student, personal_info, enrolled_courses = [], attendance, exam_results = [], submissions = [], can_edit } = data;

  return (
    <div>
      <Breadcrumbs
        items={[
          { label: 'Students Directory', href: '/students' },
          { label: student.full_name },
        ]}
      />

      {/* Header Profile Card */}
      <div
        className="card"
        style={{
          padding: '2rem',
          marginBottom: '2rem',
          background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.95))',
          border: '1px solid var(--border-strong)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1.5rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <div
            style={{
              width: 58,
              height: 58,
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #0284c7, #38bdf8)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 800,
              fontSize: '1.4rem',
              color: '#ffffff',
              boxShadow: '0 4px 15px rgba(56, 189, 248, 0.3)',
            }}
          >
            {student.full_name.charAt(0)}
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.35rem' }}>
              <span className="badge badge-info">{student.student_id_number}</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Department of {student.department_name}
              </span>
            </div>
            <h1 style={{ fontSize: '2rem', fontWeight: 800, color: '#ffffff', marginBottom: '0.2rem' }}>
              {student.full_name}
            </h1>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Class Standing: Year {student.year} • Semester {student.semester}
            </div>
          </div>
        </div>

        {/* Action Controls & GPA */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <div
            style={{
              padding: '0.85rem 1.25rem',
              background: 'rgba(0, 0, 0, 0.3)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--accent-primary)' }}>
              {student.gpa.toFixed(2)}
            </div>
            <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Cumulative GPA
            </div>
          </div>

          {(isAdmin || isFaculty) && (
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={() => setIsEditOpen(true)}
            >
              <Edit size={14} />
              <span>Edit Student Dossier</span>
            </button>
          )}
        </div>
      </div>

      {/* 2-Column Content Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '2rem' }}>
        {/* Left Column: Personal Info & Enrolled Courses */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Personal Information */}
          <div className="card">
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff', marginBottom: '1.25rem' }}>
              Personal & Contact Information
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              <div>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)', display: 'block' }}>Email Address</span>
                <span style={{ fontSize: '0.9rem', color: '#ffffff', fontWeight: 600 }}>{personal_info.email}</span>
              </div>
              <div>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)', display: 'block' }}>Primary Telephone</span>
                <span style={{ fontSize: '0.9rem', color: '#ffffff' }}>{personal_info.phone || 'None provided'}</span>
              </div>
              <div>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)', display: 'block' }}>Campus Residence</span>
                <span style={{ fontSize: '0.9rem', color: '#ffffff' }}>{personal_info.address || 'None provided'}</span>
              </div>
              <div>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)', display: 'block' }}>Emergency Contact</span>
                <span style={{ fontSize: '0.9rem', color: '#ffffff' }}>{personal_info.emergency_contact || 'None provided'}</span>
              </div>
            </div>
          </div>

          {/* Enrolled Courses */}
          <div className="card">
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff', marginBottom: '1.25rem' }}>
              Active Enrolled Courses ({enrolled_courses.length})
            </h3>
            {enrolled_courses.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No active course enrollments.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {enrolled_courses.map((c: any) => (
                  <div
                    key={c.enrollment_id}
                    style={{
                      padding: '0.85rem 1rem',
                      background: 'rgba(255, 255, 255, 0.02)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
                        <span className="badge badge-info">{c.course_code}</span>
                        <strong style={{ fontSize: '0.9rem', color: '#ffffff' }}>{c.title}</strong>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                        Instructor: {c.instructor} • {c.schedule}
                      </div>
                    </div>
                    <Link to={`/courses/${c.course_id}`} className="btn btn-outline btn-sm">
                      Course
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Attendance & Results & Submissions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Attendance History */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff' }}>Attendance Telemetry</h3>
              <span className="badge badge-success">{attendance.percentage}% Present</span>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.25rem', textAlign: 'center' }}>
              <div style={{ flex: 1, padding: '0.5rem', background: 'rgba(255, 255, 255, 0.02)', borderRadius: 'var(--radius-sm)' }}>
                <div style={{ fontWeight: 800, color: 'var(--accent-emerald)' }}>{attendance.present}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Present</div>
              </div>
              <div style={{ flex: 1, padding: '0.5rem', background: 'rgba(255, 255, 255, 0.02)', borderRadius: 'var(--radius-sm)' }}>
                <div style={{ fontWeight: 800, color: 'var(--accent-amber)' }}>{attendance.late}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Late</div>
              </div>
              <div style={{ flex: 1, padding: '0.5rem', background: 'rgba(255, 255, 255, 0.02)', borderRadius: 'var(--radius-sm)' }}>
                <div style={{ fontWeight: 800, color: 'var(--accent-rose)' }}>{attendance.absent}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Absent</div>
              </div>
            </div>

            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Recent sessions:
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem', marginTop: '0.5rem' }}>
              {attendance.history.slice(0, 5).map((h: any) => (
                <div
                  key={h.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontSize: '0.78rem',
                    padding: '0.35rem 0',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                  }}
                >
                  <span>{h.date} — {h.course_code}</span>
                  <span className={`badge ${h.status === 'PRESENT' ? 'badge-success' : h.status === 'LATE' ? 'badge-warning' : 'badge-danger'}`} style={{ fontSize: '0.65rem' }}>
                    {h.status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Exam Results */}
          <div className="card">
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff', marginBottom: '1.25rem' }}>
              Academic Examination Results
            </h3>
            {exam_results.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No examination results recorded yet.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                {exam_results.map((r: any) => (
                  <div
                    key={r.id}
                    style={{
                      padding: '0.75rem 1rem',
                      background: 'rgba(255, 255, 255, 0.02)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#ffffff' }}>{r.exam_title}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                        {r.course_code} • {r.date}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span className="badge badge-success">{r.grade}</span>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                        {r.marks_obtained}/{r.max_marks} pts
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Edit Student Modal (Journey B) */}
      <Modal
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        title="Edit Student Information (Admin / Faculty)"
        footer={
          <>
            <button type="button" className="btn btn-secondary" onClick={() => setIsEditOpen(false)}>
              Cancel
            </button>
            <button type="submit" form="edit-student-form" className="btn btn-primary" disabled={isSaving}>
              {isSaving ? 'Saving Changes...' : 'Save Updated Information'}
            </button>
          </>
        }
      >
        <form id="edit-student-form" onSubmit={handleEditSubmit}>
          <div className="form-group">
            <label className="form-label">Full Name *</label>
            <input
              type="text"
              className="form-input"
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              required
            />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Cumulative GPA</label>
              <input
                type="number"
                step="0.01"
                min={0}
                max={4.0}
                className="form-input"
                value={editGpa}
                onChange={(e) => setEditGpa(Number(e.target.value))}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Class Year</label>
              <input
                type="number"
                min={1}
                max={4}
                className="form-input"
                value={editYear}
                onChange={(e) => setEditYear(Number(e.target.value))}
                required
              />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Telephone</label>
            <input
              type="text"
              className="form-input"
              value={editPhone}
              onChange={(e) => setEditPhone(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Campus Residence / Address</label>
            <input
              type="text"
              className="form-input"
              value={editAddress}
              onChange={(e) => setEditAddress(e.target.value)}
            />
          </div>
        </form>
      </Modal>

      {toast && <Toast type={toast.type} message={toast.message} onClose={() => setToast(null)} />}
    </div>
  );
};
