import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  GraduationCap,
  BookOpen,
  CalendarCheck,
  FileText,
  Clock,
  Award,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  Users,
} from 'lucide-react';
import { api } from '../../services/api';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';

export const StudentDashboardPage: React.FC = () => {
  const [data, setData] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api.dashboard.student()
      .then(setData)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return <LoadingSpinner label="Fetching your academic dashboard..." />;
  }

  if (!data) {
    return <div style={{ color: 'var(--text-muted)' }}>Could not load student dashboard.</div>;
  }

  const {
    student_profile,
    enrolled_courses = [],
    attendance_summary,
    upcoming_examinations = [],
    pending_assignments = [],
    recent_announcements = [],
    recent_results = [],
    overall_gpa,
  } = data;

  return (
    <div>
      {/* Welcome Banner */}
      <div
        className="card"
        style={{
          padding: '2rem',
          marginBottom: '2rem',
          background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.95))',
          border: '1px solid var(--border-strong)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1.5rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.5rem' }}>
            <span className="badge badge-info">{student_profile.student_id_number}</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Year {student_profile.year} • Semester {student_profile.semester}
            </span>
          </div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, color: '#ffffff', marginBottom: '0.35rem' }}>
            Welcome Back, {student_profile.full_name}
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Department of {student_profile.department_name} • Academic Year 2026/2027
          </p>
        </div>

        {/* GPA & Attendance Badges */}
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div
            style={{
              padding: '1rem 1.25rem',
              background: 'rgba(0, 0, 0, 0.3)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--accent-primary)' }}>
              {overall_gpa.toFixed(2)}
            </div>
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Cumulative GPA
            </div>
          </div>

          <div
            style={{
              padding: '1rem 1.25rem',
              background: 'rgba(0, 0, 0, 0.3)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>
              {attendance_summary.attendance_percentage}%
            </div>
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Attendance Rate
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Left Courses & Assignments, Right Exams & Results */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '2rem' }}>
        {/* Left Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Enrolled Courses */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <BookOpen size={18} color="var(--accent-primary)" />
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff' }}>Enrolled Courses</h3>
              </div>
              <Link to="/courses" style={{ fontSize: '0.8rem', color: 'var(--accent-primary)', fontWeight: 600 }}>
                Explore More →
              </Link>
            </div>

            {enrolled_courses.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>You are not enrolled in any courses yet.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {enrolled_courses.map((c: any) => (
                  <div
                    key={c.id}
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
                        <span className="badge badge-info">{c.code}</span>
                        <strong style={{ fontSize: '0.9rem', color: '#ffffff' }}>{c.title}</strong>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                        Instructor: {c.instructor_name} • {c.credits} Credits • {c.schedule}
                      </div>
                    </div>
                    <Link to={`/courses/${c.id}`} className="btn btn-outline btn-sm">
                      Details
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Pending Assignments */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <FileText size={18} color="var(--accent-amber)" />
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff' }}>Pending Assignments</h3>
              </div>
              <Link to="/assignments" style={{ fontSize: '0.8rem', color: 'var(--accent-primary)', fontWeight: 600 }}>
                All Assignments →
              </Link>
            </div>

            {pending_assignments.length === 0 ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-emerald)', fontSize: '0.875rem' }}>
                <CheckCircle2 size={16} />
                <span>All assignments are completed and up to date!</span>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {pending_assignments.map((a: any) => (
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
                      <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#ffffff', marginBottom: '0.2rem' }}>
                        {a.title}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                        <Clock size={12} />
                        <span>Due: {new Date(a.due_date).toLocaleDateString()} • {a.course_code}</span>
                      </div>
                    </div>
                    <Link to={`/assignments/${a.id}`} className="btn btn-primary btn-sm">
                      Submit Work
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Upcoming Examinations */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CalendarCheck size={18} color="var(--accent-rose)" />
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff' }}>Upcoming Examinations</h3>
              </div>
              <Link to="/examinations" style={{ fontSize: '0.8rem', color: 'var(--accent-primary)', fontWeight: 600 }}>
                Timetable →
              </Link>
            </div>

            {upcoming_examinations.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>No upcoming examinations scheduled.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {upcoming_examinations.map((ex: any) => (
                  <div
                    key={ex.id}
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
                      <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#ffffff' }}>{ex.title}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                        {ex.course_code} • {ex.exam_date} at {ex.start_time} • Room {ex.room_number}
                      </div>
                    </div>
                    <span className="badge badge-warning">{ex.exam_type}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recent Examination Results */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
              <Award size={18} color="var(--accent-emerald)" />
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff' }}>Recent Examination Results</h3>
            </div>

            {recent_results.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>No exam results posted yet.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {recent_results.map((r: any) => (
                  <div
                    key={r.id}
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
                      <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#ffffff' }}>{r.exam_title}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                        {r.course_code} • Remarks: {r.remarks || 'Standard evaluation'}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span className="badge badge-success" style={{ fontSize: '0.85rem' }}>{r.grade}</span>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.2rem' }}>
                        {r.marks_obtained}/{r.max_marks} pts
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Campus Announcements */}
          <div className="card">
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff', marginBottom: '1rem' }}>
              Campus Announcements
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
              {recent_announcements.map((a: any) => (
                <div key={a.id} style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.65rem' }}>
                  <Link to={`/announcements/${a.id}`} style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--accent-primary)', display: 'block', marginBottom: '0.2rem' }}>
                    {a.title}
                  </Link>
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-dim)', lineHeight: 1.4 }}>
                    {a.content?.slice(0, 95)}...
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
