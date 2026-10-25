import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  BookOpen,
  Users,
  Briefcase,
  CheckSquare,
  FileText,
  CalendarCheck,
  Bell,
  Settings,
  GraduationCap,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Sidebar: React.FC = () => {
  const { user } = useAuth();

  const getDashboardRoute = () => {
    if (user?.role === 'STUDENT') return '/student/dashboard';
    if (user?.role === 'FACULTY') return '/faculty/dashboard';
    return '/admin/dashboard';
  };

  const navGroups = [
    {
      group: 'PORTAL',
      items: [
        { label: 'My Dashboard', href: getDashboardRoute(), icon: LayoutDashboard },
      ],
    },
    {
      group: 'ACADEMICS',
      items: [
        { label: 'Courses Catalogue', href: '/courses', icon: BookOpen },
        { label: 'Students Directory', href: '/students', icon: Users },
        { label: 'Faculty Directory', href: '/faculty', icon: Briefcase },
      ],
    },
    {
      group: 'COURSE WORK',
      items: [
        { label: 'Attendance', href: '/attendance', icon: CheckSquare },
        { label: 'Assignments', href: '/assignments', icon: FileText },
        { label: 'Examinations', href: '/examinations', icon: CalendarCheck },
      ],
    },
    {
      group: 'CAMPUS',
      items: [
        { label: 'Announcements', href: '/announcements', icon: Bell },
        { label: 'Account Settings', href: '/settings', icon: Settings },
      ],
    },
  ];

  return (
    <aside
      style={{
        width: '260px',
        background: 'var(--bg-card)',
        borderRight: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        flexShrink: 0,
        height: '100vh',
        position: 'sticky',
        top: 0,
      }}
    >
      <div>
        {/* Brand Header */}
        <div
          style={{
            height: '68px',
            display: 'flex',
            alignItems: 'center',
            gap: '0.65rem',
            padding: '0 1.5rem',
            borderBottom: '1px solid var(--border-subtle)',
          }}
        >
          <div
            style={{
              width: 34,
              height: 34,
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #0284c7, #38bdf8)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <GraduationCap size={20} color="#ffffff" />
          </div>
          <div>
            <span style={{ fontSize: '1.05rem', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.02em', display: 'block', lineHeight: 1.1 }}>
              UniSphere
            </span>
            <span style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--accent-primary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              {user?.role || 'PORTAL'}
            </span>
          </div>
        </div>

        {/* Navigation list */}
        <nav style={{ padding: '1.25rem 0.85rem', overflowY: 'auto', maxHeight: 'calc(100vh - 160px)' }}>
          {navGroups.map((grp, gIdx) => (
            <div key={gIdx} style={{ marginBottom: '1.25rem' }}>
              <div
                style={{
                  fontSize: '0.65rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  color: 'var(--text-dim)',
                  padding: '0.2rem 0.75rem 0.4rem 0.75rem',
                }}
              >
                {grp.group}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                {grp.items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.href}
                      to={item.href}
                      style={({ isActive }) => ({
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.65rem',
                        padding: '0.55rem 0.75rem',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '0.85rem',
                        fontWeight: isActive ? 700 : 500,
                        color: isActive ? '#ffffff' : 'var(--text-muted)',
                        background: isActive ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
                        borderLeft: isActive ? '3px solid var(--accent-primary)' : '3px solid transparent',
                        transition: 'all 0.15s ease',
                      })}
                    >
                      <Icon size={17} color={item.href.includes('dashboard') ? 'var(--accent-primary)' : 'currentColor'} />
                      <span>{item.label}</span>
                    </NavLink>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </div>

      {/* User profile footer */}
      <div
        style={{
          padding: '1rem 1.25rem',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          background: 'rgba(0, 0, 0, 0.15)',
        }}
      >
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #6366f1, #38bdf8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#ffffff',
            fontWeight: 700,
            fontSize: '0.85rem',
          }}
        >
          {user?.full_name?.charAt(0) || 'U'}
        </div>
        <div style={{ overflow: 'hidden', flex: 1 }}>
          <div style={{ fontSize: '0.825rem', fontWeight: 700, color: '#ffffff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {user?.full_name}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {user?.email}
          </div>
        </div>
      </div>
    </aside>
  );
};
