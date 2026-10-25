import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Briefcase,
  BookOpen,
  Users,
  CheckSquare,
  FileText,
  Clock,
  ArrowRight,
  PlusCircle,
  Award,
} from 'lucide-react';
import { api } from '../../services/api';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';

export const FacultyDashboardPage: React.FC = () => {
  const [data, setData] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api.dashboard.faculty()
      .then(setData)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return <LoadingSpinner label="Loading faculty academic management dashboard..." />;
  }

  if (!data) {
    return <div style={{ color: 'var(--text-muted)' }}>Could not load faculty dashboard.</div>;
  }

  const {
    faculty_profile,
    assigned_courses = [],
    total_students,
    pending_grading_count,
    recent_attendance_count,
    upcoming_deadlines = [],
    recent_announcements = [],
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
            <span className="badge badge-purple">{faculty_profile.employee_id}</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {faculty_profile.designation}
            </span>
          </div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, color: '#ffffff', marginBottom: '0.35rem' }}>
            {faculty_profile.full_name}
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Department of {faculty_profile.department_name} • Office: {faculty_profile.office_room || 'Main Hall'}
          </p>
        </div>

        {/* Quick Actions */}
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <Link to="/attendance" className="btn btn-primary btn-sm">
            <CheckSquare size={15} />
            <span>Mark Attendance</span>
          </Link>
          <Link to="/assignments" className="btn btn-secondary btn-sm">
            <FileText size={15} />
            <span>Assignments & Grading</span>
          </Link>
          <Link to="/examinations" className="btn btn-outline btn-sm">
            <Award size={15} />
            <span>Exam Results Entry</span>
          </Link>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.5rem' }}>
            <BookOpen size={18} color="var(--accent-primary)" />
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Assigned Courses</span>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#ffffff' }}>{assigned_courses.length}</div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.5rem' }}>
            <Users size={18} color="var(--accent-indigo)" />
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Total Students Enrolled</span>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#ffffff' }}>{total_students}</div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.5rem' }}>
            <FileText size={18} color="var(--accent-amber)" />
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Submissions Pending Review</span>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-amber)' }}>{pending_grading_count}</div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.5rem' }}>
            <CheckSquare size={18} color="var(--accent-emerald)" />
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Attendance Records</span>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>{recent_attendance_count}</div>
        </div>
      </div>

      {/* 2-Column Course & Grading Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '2rem' }}>
        {/* Assigned Courses List */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff' }}>My Teaching Courses</h3>
            <Link to="/courses" style={{ fontSize: '0.8rem', color: 'var(--accent-primary)', fontWeight: 600 }}>
              All Courses →
            </Link>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            {assigned_courses.map((c: any) => (
              <div
                key={c.id}
                style={{
                  padding: '1rem',
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span className="badge badge-info">{c.code}</span>
                    <strong style={{ fontSize: '0.95rem', color: '#ffffff' }}>{c.title}</strong>
                  </div>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>{c.enrolled_count} Students</span>
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)', marginBottom: '0.85rem' }}>
                  Schedule: {c.schedule} • {c.semester}
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <Link to={`/courses/${c.id}`} className="btn btn-outline btn-sm">
                    Syllabus
                  </Link>
                  <Link to={`/attendance`} className="btn btn-secondary btn-sm">
                    Attendance
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Upcoming Deadlines & Grading */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff' }}>Upcoming Assignment Deadlines</h3>
            <Link to="/assignments" style={{ fontSize: '0.8rem', color: 'var(--accent-primary)', fontWeight: 600 }}>
              Assignments Studio →
            </Link>
          </div>

          {upcoming_deadlines.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>No upcoming assignment deadlines scheduled.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {upcoming_deadlines.map((a: any) => (
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
                    <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#ffffff' }}>{a.title}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.2rem' }}>
                      {a.course_code} • Due: {new Date(a.due_date).toLocaleDateString()}
                    </div>
                  </div>
                  <Link to={`/assignments/${a.id}`} className="btn btn-primary btn-sm">
                    Review ({a.submission_count})
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
