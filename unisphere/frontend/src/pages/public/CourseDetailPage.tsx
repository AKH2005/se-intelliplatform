import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  BookOpen,
  Calendar,
  Clock,
  Users,
  FileText,
  UserCheck,
  CheckCircle,
  Download,
  ArrowLeft,
  GraduationCap,
} from 'lucide-react';
import { api } from '../../services/api';
import { Navbar } from '../../components/layout/Navbar';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { Breadcrumbs } from '../../components/common/Breadcrumbs';
import { useAuth } from '../../context/AuthContext';
import { Toast } from '../../components/common/Toast';

export const CourseDetailPage: React.FC = () => {
  const { courseId } = useParams<{ courseId: string }>();
  const { user, isStudent } = useAuth();
  const navigate = useNavigate();

  const [data, setData] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [isEnrolling, setIsEnrolling] = useState(false);

  const fetchCourse = async () => {
    if (!courseId) return;
    setIsLoading(true);
    try {
      const res = await api.courses.get(Number(courseId));
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Course not found.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCourse();
  }, [courseId]);

  const handleEnroll = async () => {
    if (!user) {
      navigate('/login');
      return;
    }
    if (!courseId) return;
    setIsEnrolling(true);
    try {
      await api.courses.enroll(Number(courseId));
      setToast({ type: 'success', message: 'Successfully enrolled in course!' });
      fetchCourse();
    } catch (err: any) {
      setToast({ type: 'error', message: err.message || 'Enrollment failed.' });
    } finally {
      setIsEnrolling(false);
    }
  };

  if (isLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <Navbar />
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <LoadingSpinner label="Loading course syllabus..." />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <Navbar />
        <div className="container" style={{ padding: '4rem 1.5rem', textAlign: 'center' }}>
          <h2 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#ffffff', marginBottom: '0.75rem' }}>
            Course Not Found
          </h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
            {error || 'The requested course ID does not exist in the UniSphere database.'}
          </p>
          <Link to="/courses" className="btn btn-primary">
            <ArrowLeft size={16} />
            <span>Return to Course Catalogue</span>
          </Link>
        </div>
      </div>
    );
  }

  const { course, instructor, enrolled_students = [], assignments = [], materials = [] } = data;
  const isAlreadyEnrolled = user && enrolled_students.some((st: any) => st.student_id === user.student_profile_id);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />

      <div className="container" style={{ padding: '2rem 1.5rem', flex: 1 }}>
        <Breadcrumbs
          items={[
            { label: 'Courses Catalogue', href: '/courses' },
            { label: course.code },
          ]}
        />

        {/* Hero Banner */}
        <div
          className="card"
          style={{
            marginBottom: '2rem',
            padding: '2.25rem',
            background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.95))',
            border: '1px solid var(--border-strong)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1.5rem' }}>
            <div style={{ maxWidth: 760 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                <span className="badge badge-info">{course.code}</span>
                <span className="badge badge-purple">{course.department_name}</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{course.semester}</span>
              </div>
              <h1 style={{ fontSize: '2.4rem', fontWeight: 800, color: '#ffffff', marginBottom: '0.85rem' }}>
                {course.title}
              </h1>
              <p style={{ fontSize: '1rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
                {course.description}
              </p>
            </div>

            {/* Quick Meta Card */}
            <div
              style={{
                background: 'rgba(0, 0, 0, 0.25)',
                padding: '1.25rem 1.5rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                minWidth: '240px',
              }}
            >
              <div style={{ marginBottom: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.65rem', fontSize: '0.875rem' }}>
                <Calendar size={16} color="var(--accent-primary)" />
                <span>{course.schedule}</span>
              </div>
              <div style={{ marginBottom: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.65rem', fontSize: '0.875rem' }}>
                <GraduationCap size={16} color="var(--accent-indigo)" />
                <span>{course.credits} Academic Credits</span>
              </div>
              <div style={{ marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.65rem', fontSize: '0.875rem' }}>
                <Users size={16} color="var(--accent-emerald)" />
                <span>{enrolled_students.length} / {course.max_capacity} Enrolled</span>
              </div>

              {isStudent && (
                isAlreadyEnrolled ? (
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.45rem',
                      color: 'var(--accent-emerald)',
                      fontSize: '0.875rem',
                      fontWeight: 700,
                      padding: '0.5rem',
                      background: 'rgba(16, 185, 129, 0.1)',
                      borderRadius: 'var(--radius-sm)',
                      justifyContent: 'center',
                    }}
                  >
                    <CheckCircle size={16} />
                    <span>Enrolled in Course</span>
                  </div>
                ) : (
                  <button
                    type="button"
                    className="btn btn-primary"
                    style={{ width: '100%' }}
                    onClick={handleEnroll}
                    disabled={isEnrolling}
                  >
                    <UserCheck size={16} />
                    <span>{isEnrolling ? 'Enrolling...' : 'Enroll in Course'}</span>
                  </button>
                )
              )}
            </div>
          </div>
        </div>

        {/* 2-Column Details Layout */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '2rem' }}>
          {/* Left Column: Instructor, Materials, Assignments */}
          <div>
            {/* Instructor Box */}
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff', marginBottom: '1rem' }}>
                Course Instructor
              </h3>
              {instructor ? (
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                  <div
                    style={{
                      width: 48,
                      height: 48,
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #0284c7, #38bdf8)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 800,
                      fontSize: '1.1rem',
                      color: '#ffffff',
                    }}
                  >
                    {instructor.name.charAt(0)}
                  </div>
                  <div>
                    <Link
                      to={instructor.id ? `/faculty/${instructor.id}` : '#'}
                      style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--accent-primary)' }}
                    >
                      {instructor.name}
                    </Link>
                    <div style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>{instructor.designation}</div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>Office: {instructor.office_room || 'Faculty Hall'}</div>
                  </div>
                </div>
              ) : (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Instructor will be assigned shortly.</p>
              )}
            </div>

            {/* Course Materials */}
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff', marginBottom: '1rem' }}>
                Course Materials & Syllabus
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {materials.map((m: any) => (
                  <div
                    key={m.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '0.75rem 1rem',
                      background: 'rgba(255, 255, 255, 0.02)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                      <FileText size={18} color="var(--accent-primary)" />
                      <div>
                        <div style={{ fontSize: '0.875rem', fontWeight: 600, color: '#ffffff' }}>{m.title}</div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>{m.type} • Uploaded {m.uploaded_at}</div>
                      </div>
                    </div>
                    <button
                      type="button"
                      className="btn btn-outline btn-sm"
                      onClick={() => alert(`Downloading ${m.title}...`)}
                    >
                      <Download size={13} />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Active Assignments */}
            <div className="card">
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff', marginBottom: '1rem' }}>
                Course Assignments
              </h3>
              {assignments.length === 0 ? (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>No assignments posted yet.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {assignments.map((a: any) => (
                    <div
                      key={a.id}
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
                        <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#ffffff' }}>{a.title}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                          Due: {new Date(a.due_date).toLocaleDateString()} • Max: {a.max_marks} pts
                        </div>
                      </div>
                      <Link to={`/assignments/${a.id}`} className="btn btn-outline btn-sm">
                        View
                      </Link>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Enrolled Students (Required for Journey A) */}
          <div>
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff' }}>
                  Enrolled Students ({enrolled_students.length})
                </h3>
                <span className="badge badge-info">{course.max_capacity - enrolled_students.length} spots left</span>
              </div>

              {enrolled_students.length === 0 ? (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>No students currently enrolled in this course.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                  {enrolled_students.map((st: any) => (
                    <div
                      key={st.student_id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '0.75rem 1rem',
                        background: 'rgba(255, 255, 255, 0.02)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-sm)',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div
                          style={{
                            width: 32,
                            height: 32,
                            borderRadius: '50%',
                            background: 'var(--bg-surface)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'var(--accent-primary)',
                            fontWeight: 700,
                            fontSize: '0.8rem',
                          }}
                        >
                          {st.full_name?.charAt(0) || 'S'}
                        </div>
                        <div>
                          {/* CLICKABLE LINK TO STUDENT DETAILS (Required by Journey A) */}
                          <Link
                            to={`/students/${st.student_id}`}
                            style={{
                              fontSize: '0.9rem',
                              fontWeight: 700,
                              color: 'var(--accent-primary)',
                              display: 'block',
                            }}
                          >
                            {st.full_name}
                          </Link>
                          <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                            ID: {st.student_id_number} • Year {st.year}
                          </div>
                        </div>
                      </div>

                      <Link to={`/students/${st.student_id}`} className="btn btn-outline btn-sm" style={{ fontSize: '0.75rem' }}>
                        Dossier
                      </Link>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {toast && <Toast type={toast.type} message={toast.message} onClose={() => setToast(null)} />}
    </div>
  );
};
