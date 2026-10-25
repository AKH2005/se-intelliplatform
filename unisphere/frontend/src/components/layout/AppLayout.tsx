import React from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { useAuth } from '../../context/AuthContext';
import { LogOut, Bell, Shield, User as UserIcon } from 'lucide-react';

export const AppLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-main)' }}>
      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Main Content Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* Top Header Bar */}
        <header
          style={{
            height: '68px',
            borderBottom: '1px solid var(--border-subtle)',
            background: 'rgba(17, 24, 39, 0.75)',
            backdropFilter: 'blur(10px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 2rem',
            position: 'sticky',
            top: 0,
            zIndex: 90,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Current Role:</span>
            <span className="badge badge-info">{user?.role}</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {/* Quick public site link */}
            <Link to="/" className="btn btn-outline btn-sm" style={{ fontSize: '0.78rem' }}>
              Public Site
            </Link>

            {/* Notifications */}
            <Link
              to="/announcements"
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.45rem',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
              title="Campus Announcements"
            >
              <Bell size={16} />
            </Link>

            {/* Settings */}
            <Link
              to="/settings"
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.45rem',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
              title="Account Settings"
            >
              <UserIcon size={16} />
            </Link>

            {/* Sign Out Button */}
            <button
              type="button"
              onClick={logout}
              className="btn btn-danger btn-sm"
              style={{ fontSize: '0.78rem' }}
            >
              <LogOut size={13} />
              <span>Sign Out</span>
            </button>
          </div>
        </header>

        {/* Page Content Body */}
        <main style={{ flex: 1, padding: '2rem', overflowY: 'auto' }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
};
