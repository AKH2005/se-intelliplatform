import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth, UserRole } from '../../context/AuthContext';
import { LoadingSpinner } from './LoadingSpinner';

interface ProtectedRouteProps {
  children: React.ReactElement;
  allowedRoles?: UserRole[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div style={{ minHeight: '80vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <LoadingSpinner label="Authenticating session..." />
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    // Preserve intended destination in state
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    // If user's role is not allowed, redirect to their permitted dashboard
    const defaultDashboard =
      user.role === 'STUDENT'
        ? '/student/dashboard'
        : user.role === 'FACULTY'
        ? '/faculty/dashboard'
        : '/admin/dashboard';
    return <Navigate to={defaultDashboard} replace />;
  }

  return children;
};
