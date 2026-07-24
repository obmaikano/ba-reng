import { Navigate } from 'react-router-dom';
import { Spinner, Classes } from '@blueprintjs/core';
import { useAuth } from './AuthContext';

interface Props {
  children: React.ReactNode;
  requiredRoles?: string[];
}

export default function ProtectedRoute({ children, requiredRoles }: Props) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className={Classes.DARK} style={{
        minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'var(--bg-canvas, #0B0E14)',
      }}>
        <Spinner />
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;
  // Admin bypasses all role checks.
  if (requiredRoles && user.role !== 'admin' && !requiredRoles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}
