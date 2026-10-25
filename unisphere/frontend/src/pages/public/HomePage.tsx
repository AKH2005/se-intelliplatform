import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  GraduationCap,
  BookOpen,
  Award,
  Users,
  ArrowRight,
  Sparkles,
  ShieldCheck,
  Calendar,
  Building,
} from 'lucide-react';
import { api } from '../../services/api';
import { Navbar } from '../../components/layout/Navbar';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';

export const HomePage: React.FC = () => {
  const [courses, setCourses] = useState<any[]>([]);
  const [announcements, setAnnouncements] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [cList, aList] = await Promise.all([
          api.courses.list(),
          api.announcements.list(),
        ]);
        setCourses(cList.slice(0, 3));
        setAnnouncements(aList.slice(0, 3));
      } catch (err) {
        console.error('Failed to load homepage data:', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />

      {/* Hero Section */}
      <section
        style={{
          padding: '6rem 0 4rem 0',
          background: 'radial-gradient(ellipse 80% 50% at 50% -20%, rgba(56, 189, 248, 0.15), transparent)',
          borderBottom: '1px solid var(--border-subtle)',
          textAlign: 'center',
        }}
      >
        <div className="container" style={{ maxWidth: 860 }}>
          <div
            className="badge badge-info"
            style={{ marginBottom: '1.25rem', padding: '0.35rem 0.85rem' }}
          >
            <Sparkles size={14} />
            <span>Empowering Next-Generation Innovators</span>
          </div>
          <h1
            style={{
              fontSize: '3.25rem',
              fontWeight: 800,
              letterSpacing: '-0.03em',
              lineHeight: 1.15,
              marginBottom: '1.25rem',
              color: '#ffffff',
            }}
          >
            A Unified Platform for Modern Academic Excellence
          </h1>
          <p
            style={{
              fontSize: '1.15rem',
              color: 'var(--text-muted)',
              lineHeight: 1.6,
              marginBottom: '2.5rem',
              maxWidth: 720,
              margin: '0 auto 2.5rem auto',
            }}
          >
            UniSphere combines admissions, intelligent course registration, real-time attendance, grading workflows, and student telemetry into one seamless university portal.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <Link to="/courses" className="btn btn-primary btn-lg">
              <BookOpen size={18} />
              <span>Explore Course Catalogue</span>
            </Link>
            <Link to="/login" className="btn btn-outline btn-lg">
              <span>Access Student & Faculty Portal</span>
              <ArrowRight size={18} />
            </Link>
          </div>
        </div>
      </section>

      {/* University Key Metrics */}
      <section style={{ padding: '3.5rem 0', borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-card)' }}>
        <div className="container">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.5rem', textAlign: 'center' }}>
            <div>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--accent-primary)', marginBottom: '0.25rem' }}>4,800+</div>
              <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-muted)' }}>Enrolled Students</div>
            </div>
            <div>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--accent-indigo)', marginBottom: '0.25rem' }}>140+</div>
              <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-muted)' }}>Accredited Faculty</div>
            </div>
            <div>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--accent-emerald)', marginBottom: '0.25rem' }}>98.4%</div>
              <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-muted)' }}>Graduation Placement</div>
            </div>
            <div>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--accent-amber)', marginBottom: '0.25rem' }}>$42M</div>
              <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-muted)' }}>Annual Research Grants</div>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Courses Section */}
      <section style={{ padding: '4.5rem 0', borderBottom: '1px solid var(--border-subtle)' }}>
        <div className="container">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '2.5rem', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <span className="badge badge-purple" style={{ marginBottom: '0.5rem' }}>Academics</span>
              <h2 style={{ fontSize: '2rem', fontWeight: 800, color: '#ffffff' }}>Featured University Courses</h2>
            </div>
            <Link to="/courses" style={{ color: 'var(--accent-primary)', fontWeight: 600, fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span>View All Courses</span>
              <ArrowRight size={16} />
            </Link>
          </div>

          {isLoading ? (
            <LoadingSpinner label="Loading catalogue courses..." />
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
              {courses.map((c) => (
                <div key={c.id} className="card card-hover" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem' }}>
                      <span className="badge badge-info">{c.code}</span>
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)', fontWeight: 600 }}>{c.credits} Credits</span>
                    </div>
                    <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff', marginBottom: '0.5rem' }}>
                      {c.title}
                    </h3>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '1.25rem' }}>
                      {c.description?.slice(0, 110)}...
                    </p>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.75rem', marginBottom: '1rem' }}>
                      Instructor: <strong style={{ color: 'var(--text-main)' }}>{c.instructor_name}</strong>
                    </div>
                    <Link to={`/courses/${c.id}`} className="btn btn-outline btn-sm" style={{ width: '100%' }}>
                      <span>View Course Syllabus</span>
                      <ArrowRight size={14} />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Announcements & News Section */}
      <section style={{ padding: '4.5rem 0', background: 'var(--bg-card)' }}>
        <div className="container">
          <div style={{ marginBottom: '2.5rem' }}>
            <span className="badge badge-warning" style={{ marginBottom: '0.5rem' }}>Campus News</span>
            <h2 style={{ fontSize: '2rem', fontWeight: 800, color: '#ffffff' }}>Latest University Announcements</h2>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
            {announcements.map((a) => (
              <div key={a.id} className="card card-hover">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <span className="badge badge-success">{a.category}</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                    {new Date(a.published_at).toLocaleDateString()}
                  </span>
                </div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff', marginBottom: '0.65rem' }}>
                  {a.title}
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '1.25rem' }}>
                  {a.content?.slice(0, 120)}...
                </p>
                <Link to={`/announcements/${a.id}`} style={{ fontSize: '0.825rem', fontWeight: 600, color: 'var(--accent-primary)', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
                  <span>Read Full Notice</span>
                  <ArrowRight size={13} />
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer style={{ marginTop: 'auto', borderTop: '1px solid var(--border-subtle)', padding: '2.5rem 0', background: '#070a12', fontSize: '0.85rem', color: 'var(--text-dim)', textAlign: 'center' }}>
        <div className="container">
          <p>© 2026 UniSphere University Management System. All rights reserved.</p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '1.5rem', marginTop: '0.75rem' }}>
            <Link to="/about" style={{ color: 'var(--text-muted)' }}>About University</Link>
            <Link to="/courses" style={{ color: 'var(--text-muted)' }}>Courses</Link>
            <Link to="/contact" style={{ color: 'var(--text-muted)' }}>Admissions Contact</Link>
            <Link to="/login" style={{ color: 'var(--text-muted)' }}>Portal Sign In</Link>
          </div>
        </div>
      </footer>
    </div>
  );
};
