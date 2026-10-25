import React from 'react';
import { Navbar } from '../../components/layout/Navbar';
import { Award, Compass, Shield, Users, Landmark, BookOpen } from 'lucide-react';
import { Link } from 'react-router-dom';

export const AboutPage: React.FC = () => {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />

      <section style={{ padding: '4rem 0 3rem 0', background: 'radial-gradient(ellipse 60% 50% at 50% 0%, rgba(56, 189, 248, 0.1), transparent)', borderBottom: '1px solid var(--border-subtle)' }}>
        <div className="container" style={{ maxWidth: 860, textAlign: 'center' }}>
          <span className="badge badge-info" style={{ marginBottom: '1rem' }}>Our Heritage</span>
          <h1 style={{ fontSize: '2.75rem', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.02em', marginBottom: '1rem' }}>
            About UniSphere University
          </h1>
          <p style={{ fontSize: '1.1rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
            Founded with a commitment to interdisciplinary research and technological innovation, UniSphere prepares students to solve global challenges through rigorous academics, modern laboratories, and collaborative leadership.
          </p>
        </div>
      </section>

      <div className="container" style={{ padding: '4rem 1.5rem', maxWidth: 1000 }}>
        {/* Core Pillars */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem', marginBottom: '4rem' }}>
          <div className="card">
            <Compass size={28} color="var(--accent-primary)" style={{ marginBottom: '1rem' }} />
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#ffffff', marginBottom: '0.5rem' }}>Our Mission</h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
              To deliver world-class technical education, foster groundbreaking discovery, and empower ethically driven professionals dedicated to community impact.
            </p>
          </div>
          <div className="card">
            <Shield size={28} color="var(--accent-emerald)" style={{ marginBottom: '1rem' }} />
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#ffffff', marginBottom: '0.5rem' }}>Global Accreditation</h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
              UniSphere holds premier ABET, AACSB, and regional higher education accreditations across all undergraduate and postgraduate engineering programs.
            </p>
          </div>
          <div className="card">
            <Award size={28} color="var(--accent-amber)" style={{ marginBottom: '1rem' }} />
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#ffffff', marginBottom: '0.5rem' }}>Research Impact</h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
              Over 40 state-of-the-art laboratories dedicated to machine intelligence, sustainable energy, embedded robotics, and cybersecurity.
            </p>
          </div>
        </div>

        {/* Leadership & Faculty */}
        <div style={{ marginBottom: '4rem' }}>
          <h2 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#ffffff', marginBottom: '1.5rem' }}>University Leadership</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
            <div className="card">
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff' }}>Chancellor Victoria Sterling</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--accent-primary)', marginBottom: '0.75rem' }}>Office of the Chancellor</div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                Oversees university institutional strategy, national accreditation partnerships, and long-term research endowment expansion.
              </p>
            </div>
            <div className="card">
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff' }}>Dr. Alan Smith</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--accent-primary)', marginBottom: '0.75rem' }}>Dean of Computing & Applied Science</div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                Directs the engineering curriculum, faculty appointments, industry capstone partnerships, and computing laboratories.
              </p>
            </div>
          </div>
        </div>

        {/* Action banner */}
        <div className="card" style={{ background: 'linear-gradient(135deg, rgba(2, 132, 199, 0.2), rgba(99, 102, 241, 0.2))', border: '1px solid var(--border-strong)', textAlign: 'center', padding: '3rem 2rem' }}>
          <h3 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#ffffff', marginBottom: '0.75rem' }}>Ready to Begin Your Academic Journey?</h3>
          <p style={{ color: 'var(--text-muted)', maxWidth: 550, margin: '0 auto 1.75rem auto', fontSize: '0.95rem' }}>
            Discover our accredited degree programs or get in touch with our admissions counsellors today.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem' }}>
            <Link to="/courses" className="btn btn-primary">Browse Courses</Link>
            <Link to="/contact" className="btn btn-secondary">Contact Admissions</Link>
          </div>
        </div>
      </div>
    </div>
  );
};
