import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

interface NavItem {
  label: string;
  path: string;
  admin?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { label: '01 Week', path: '/' },
  { label: '02 Feed', path: '/feed' },
  { label: '03 Find MP', path: '/find' },
  { label: '04 Profile', path: '/find' },
  { label: '05 Compare', path: '/compare' },
  { label: '06 Index', path: '/rankings' },
  { label: '07 Bills', path: '/bills' },
  { label: '08 Search', path: '/search' },
  { label: 'Analytics', path: '/analytics' },
];

const ADMIN_ITEMS: NavItem[] = [
  { label: '09 Admin', path: '/admin', admin: true },
  { label: '10 Entities', path: '/admin/entity-review', admin: true },
  { label: '11 Users', path: '/admin/users', admin: true },
];

function navBtnStyle(active: boolean, admin: boolean) {
  if (active) {
    return admin
      ? {
          background: 'rgba(245,166,35,0.1)',
          color: 'var(--accent-amber)',
          borderColor: 'rgba(245,166,35,0.3)',
        }
      : { background: 'var(--bg-elevated)', color: 'var(--accent-blue)', borderColor: 'var(--accent-blue)' };
  }
  return { background: 'transparent', color: admin ? 'var(--accent-amber)' : 'var(--text-secondary)', borderColor: 'var(--border-subtle)' };
}

export default function TopNav() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  const renderButton = (item: NavItem) => {
    const active = item.path === '/' ? location.pathname === '/' : location.pathname.startsWith(item.path);
    return (
      <button
        key={item.label}
        onClick={() => navigate(item.path)}
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 10,
          padding: '4px 10px',
          border: '1px solid',
          cursor: 'pointer',
          ...navBtnStyle(active, Boolean(item.admin)),
        }}
      >
        {item.label}
      </button>
    );
  };

  return (
    <nav
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: 44,
        padding: '0 20px',
        borderBottom: '1px solid var(--border-default)',
        background: 'var(--bg-canvas)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div
          onClick={() => navigate('/')}
          style={{
            width: 18,
            height: 18,
            background: 'var(--text-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            flexShrink: 0,
          }}
        >
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, fontWeight: 700, color: 'var(--bg-canvas)' }}>
            BR
          </span>
        </div>
        <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)' }}>Ba Reng?</span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)' }}>v0.1.0</span>
        <span style={{ color: 'var(--text-tertiary)', fontSize: 10 }}>·</span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-amber)' }}>
          WEEKLY_DIGEST
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap' }}>
        {NAV_ITEMS.map(renderButton)}
        <span style={{ color: 'var(--text-tertiary)', margin: '0 4px' }}>|</span>
        {ADMIN_ITEMS.map(renderButton)}
        <span style={{ margin: '0 4px' }} />
        {user ? (
          <>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-secondary)' }}>
              {user.display_name} ({user.role})
            </span>
            <button
              onClick={logout}
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                padding: '4px 10px',
                border: '1px solid var(--border-subtle)',
                background: 'transparent',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
              }}
            >
              Logout
            </button>
          </>
        ) : (
          <button
            onClick={() => navigate('/login')}
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 10,
              padding: '4px 10px',
              border: '1px solid var(--border-subtle)',
              background: 'transparent',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
            }}
          >
            Login
          </button>
        )}
      </div>
    </nav>
  );
}
