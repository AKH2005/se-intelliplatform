import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { GraduationCap, LogIn, UserPlus, BookOpen, Info, Mail, LayoutDashboard } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Navbar: React.FC = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const location = useLocation();

  const getDashboardLink = () => {
    if (!user) return '/login';
    if (user.role === 'STUDENT') return '/student/dashboard';
    if (user.role === 'FACULTY') return '/faculty/dashboard';
    return '/admin/dashboard';
  };

  const navLinks = [
    { label: 'Home', href: '/' },
    { label: 'About', href: '/about' },
    { label: 'Courses', href: '/courses' },
    { label: 'Contact', href: '/contact' },
  ];

  return (
    <header
      style={{
        height: '68px',
        borderBottom: '1px solid var(--border-subtle)',
        background: 'rgba(11, 15, 25, 0.85)',
        backdropFilter: 'blur(12px)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
      }}
    >
      <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        {/* Brand Logo */}
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div
            style={{
              width: 38,
              height: 38,
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #0284c7, #38bdf8)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 2px 10px rgba(56, 189, 248, 0.35)',
            }}
          >
            <GraduationCap size={22} color="#ffffff" />
          </div>
          <div>
            <span style={{ fontSize: '1.15rem', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.02em', display: 'block', lineHeight: 1.1 }}>
              UniSphere
            </span>
            <span style={{ fontSize: '0.68rem', fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.04em' }}>
              UNIVERSITY SYSTEM
            </span>
          </div>
        </Link>

        {/* Public Navigation Links */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '1.75rem' }}>
          {navLinks.map((link) => {
            const isActive = location.pathname === link.href;
            return (
              <Link
                key={link.href}
                to={link.href}
                style={{
                  fontSize: '0.9rem',
                  fontWeight: 600,
                  color: isActive ? 'var(--accent-primary)' : 'var(--text-muted)',
                  transition: 'color 0.15s ease',
                  borderBottom: isActive ? '2px solid var(--accent-primary)' : '2px solid transparent',
                  padding: '0.4rem 0',
                }}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* Auth CTA Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {isAuthenticated && user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <Link to={getDashboardLink()} className="btn btn-primary btn-sm">
                <LayoutDashboard size={14} />
                <span>My Dashboard</span>
              </Link>
              <button
                type="button"
                onClick={logout}
                className="btn btn-outline btn-sm"
                title="Sign out of UniSphere"
              >
                Sign Out
              </button>
            </div>
          ) : (
            <>
              <Link to="/login" className="btn btn-outline btn-sm">
                <LogIn size={14} />
                <span>Sign In</span>
              </Link>
              <Link to="/register" className="btn btn-primary btn-sm">
                <UserPlus size={14} />
                <span>Register</span>
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
};
