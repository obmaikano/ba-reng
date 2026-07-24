import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Button, Classes } from '@blueprintjs/core';
import { useAuth } from '../auth/AuthContext';

const NAV_ITEMS = [
  { path: "/admin", label: "Dashboard" },
  { path: '/admin/ministry-mappings', label: 'Ministry Mappings' },
  { path: '/admin/entity-review', label: 'Entity Review' },
  { path: '/admin/users', label: 'User Management' },
];

export default function AdminLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className={Classes.DARK} style={{
      minHeight: '100vh', display: 'flex',
      background: 'var(--bg-canvas, #0B0E14)',
    }}>
      <nav style={{
        width: 220, borderRight: '1px solid #1F242E',
        padding: '1rem', display: 'flex', flexDirection: 'column',
      }}>
        <div style={{ marginBottom: '2rem' }}>
          <div style={{ fontFamily: 'var(--font-mono, monospace)', color: '#BDC1C9', fontSize: '0.85rem' }}>
            Ba Reng? Admin
          </div>
          <div style={{ color: '#738091', fontSize: '0.75rem', marginTop: '0.25rem' }}>
            {user?.display_name} ({user?.role})
          </div>
        </div>

        {NAV_ITEMS.map((item) => (
          <Button
            key={item.path}
            minimal
            alignText="left"
            active={location.pathname === item.path}
            onClick={() => navigate(item.path)}
            style={{ marginBottom: '0.25rem', color: location.pathname === item.path ? '#2B95D6' : '#BDC1C9' }}
          >
            {item.label}
          </Button>
        ))}

        <div style={{ marginTop: 'auto' }}>
          <Button minimal alignText="left" onClick={handleLogout} style={{ color: '#738091' }}>
            Sign out
          </Button>
        </div>
      </nav>

      <main style={{ flex: 1, padding: '1.5rem', overflowY: 'auto' }}>
        <Outlet />
      </main>
    </div>
  );
}
