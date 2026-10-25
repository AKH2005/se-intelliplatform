import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Users,
  Briefcase,
  BookOpen,
  Landmark,
  ShieldCheck,
  CheckCircle2,
  TrendingUp,
  UserPlus,
  ArrowRight,
} from 'lucide-react';
import { api } from '../../services/api';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';

export const AdminDashboardPage: React.FC = () => {
  const [data, setData] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api.dashboard.admin()
      .then(setData)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return <LoadingSpinner label="Calculating university statistics..." />;
  }

  if (!data) {
    return <div style={{ color: 'var(--text-muted)' }}>Could not load administrator dashboard.</div>;
  }

  const {
    total_students,
    total_faculty,
    total_courses,
    total_departments,
    overall_attendance_rate,
    department_stats = [],
    recent_registrations = [],
  } = data;

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <span className="badge badge-purple" style={{ marginBottom: '0.4rem' }}>Governance Portal</span>
          <h1 style={{ fontSize: '2.25rem', fontWeight: 800, color: '#ffffff' }}>University Administration</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Executive metrics, institutional capacity, enrollment telemetry, and department operations.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <Link to="/students" className="btn btn-primary btn-sm">
            <UserPlus size={15} />
            <span>Manage Students</span>
          </Link>
          <Link to="/faculty" className="btn btn-secondary btn-sm">
            <Briefcase size={15} />
            <span>Manage Faculty</span>
          </Link>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '1.25rem', marginBottom: '2.5rem' }}>
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.5rem' }}>
            <Users size={18} color="var(--accent-primary)" />
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Total Enrolled Students</span>
          </div>
          <div style={{ fontSize: '2.25rem', fontWeight: 800, color: '#ffffff' }}>{total_students}</div>
          <Link to="/students" style={{ fontSize: '0.75rem', color: 'var(--accent-primary)', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.25rem', marginTop: '0.5rem' }}>
            <span>Directory</span> →
          </Link>
        </div>

        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.5rem' }}>
            <Briefcase size={18} color="var(--accent-indigo)" />
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Accredited Faculty</span>
          </div>
          <div style={{ fontSize: '2.25rem', fontWeight: 800, color: '#ffffff' }}>{total_faculty}</div>
          <Link to="/faculty" style={{ fontSize: '0.75rem', color: 'var(--accent-indigo)', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.25rem', marginTop: '0.5rem' }}>
            <span>Faculty List</span> →
          </Link>
        </div>

        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.5rem' }}>
            <BookOpen size={18} color="var(--accent-emerald)" />
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Active Courses</span>
          </div>
          <div style={{ fontSize: '2.25rem', fontWeight: 800, color: '#ffffff' }}>{total_courses}</div>
          <Link to="/courses" style={{ fontSize: '0.75rem', color: 'var(--accent-emerald)', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.25rem', marginTop: '0.5rem' }}>
            <span>Catalogue</span> →
          </Link>
        </div>

        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.5rem' }}>
            <TrendingUp size={18} color="var(--accent-amber)" />
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Campus Attendance Rate</span>
          </div>
          <div style={{ fontSize: '2.25rem', fontWeight: 800, color: 'var(--accent-amber)' }}>{overall_attendance_rate}%</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.5rem' }}>
            Institution Target: 90%
          </div>
        </div>
      </div>

      {/* 2-Column: Department Breakdown & Recent Student Registrations */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '2rem' }}>
        {/* Department Operations Table */}
        <div className="card">
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#ffffff', marginBottom: '1.25rem' }}>
            Departmental Breakdown
          </h3>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Department Name</th>
                  <th>Students</th>
                  <th>Faculty</th>
                  <th>Courses</th>
                </tr>
              </thead>
              <tbody>
                {department_stats.map((dept: any) => (
                  <tr key={dept.department_id}>
                    <td><span className="badge badge-info">{dept.code}</span></td>
                    <td style={{ fontWeight: 600 }}>{dept.name}</td>
                    <td>{dept.students}</td>
                    <td>{dept.faculty}</td>
                    <td>{dept.courses}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Recent Registrations Table */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#ffffff' }}>
              Recent Student Registrations
            </h3>
            <Link to="/students" style={{ fontSize: '0.8rem', color: 'var(--accent-primary)', fontWeight: 600 }}>
              All Students →
            </Link>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {recent_registrations.map((st: any) => (
              <div
                key={st.id}
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
                  <Link
                    to={`/students/${st.id}`}
                    style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--accent-primary)', display: 'block' }}
                  >
                    {st.full_name}
                  </Link>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                    ID: {st.student_id_number} • Dept: {st.department_name}
                  </div>
                </div>
                <Link to={`/students/${st.id}`} className="btn btn-outline btn-sm">
                  View Record
                </Link>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
