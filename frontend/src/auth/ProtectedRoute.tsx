import { Navigate } from 'react-router-dom';
import { Spinner, Classes } from '@blueprintjs/core';
import { useAuth } from './AuthContext';

interface Props {
  children: React.ReactNode;
  requiredRole?: string;
}

export default function ProtectedRoute({ children, requiredRole }: Props) {
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
  if (requiredRole && user.role !== requiredRole && user.role !== 'admin') {
    return <Navigate to="/admin" replace />;
  }
  return <>{children}</>;
}
