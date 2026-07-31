import { useNavigate, useLocation } from 'react-router-dom';

interface Crumb {
  label: string;
  path?: string;
}

function breadcrumbsForPath(pathname: string): Crumb[] {
  const crumbs: Crumb[] = [{ label: 'Week', path: '/' }];

  if (pathname.startsWith('/hansard/session/')) {
    crumbs.push({ label: 'Hansard', path: '/hansard' });
    crumbs.push({ label: 'Session' });
  } else if (pathname.startsWith('/hansard')) {
    crumbs.push({ label: 'Hansard' });
  } else if (pathname.startsWith('/contribution/')) {
    crumbs.push({ label: 'Feed', path: '/feed' });
    crumbs.push({ label: 'Contribution' });
  } else if (pathname.startsWith('/ministry/')) {
    crumbs.push({ label: 'Feed', path: '/feed' });
    crumbs.push({ label: 'Ministry' });
  } else if (pathname.startsWith('/constituency/')) {
    crumbs.push({ label: 'Feed', path: '/feed' });
    crumbs.push({ label: 'Constituency' });
  } else if (pathname.startsWith('/mp/')) {
    crumbs.push({ label: 'Find MP', path: '/find' });
    crumbs.push({ label: 'MP Profile' });
  } else if (pathname.startsWith('/compare')) {
    crumbs.push({ label: 'Compare MPs' });
  } else if (pathname.startsWith('/rankings')) {
    crumbs.push({ label: 'Participation Index' });
  } else if (pathname.startsWith('/bills/')) {
    crumbs.push({ label: 'Bill Tracker', path: '/bills' });
    crumbs.push({ label: 'Bill Detail' });
  } else if (pathname.startsWith('/bills')) {
    crumbs.push({ label: 'Bill Tracker' });
  } else if (pathname.startsWith('/feed')) {
    crumbs.push({ label: 'Live Feed' });
  } else if (pathname.startsWith('/find')) {
    crumbs.push({ label: 'Find MP' });
  } else if (pathname.startsWith('/search')) {
    crumbs.push({ label: 'Search' });
  } else if (pathname.startsWith('/analytics')) {
    crumbs.push({ label: 'Analytics' });
  } else if (pathname.startsWith('/about')) {
    crumbs.push({ label: 'About' });
  } else if (pathname.startsWith('/admin/entity-review')) {
    crumbs.push({ label: 'Admin', path: '/admin' });
    crumbs.push({ label: 'Entity Review' });
  } else if (pathname.startsWith('/admin/users')) {
    crumbs.push({ label: 'Admin', path: '/admin' });
    crumbs.push({ label: 'User Management' });
  } else if (pathname.startsWith('/admin/ministry-mappings')) {
    crumbs.push({ label: 'Admin', path: '/admin' });
    crumbs.push({ label: 'Ministry Mappings' });
  } else if (pathname.startsWith('/admin')) {
    crumbs.push({ label: 'Admin' });
  }

  return crumbs;
}

export default function Breadcrumbs() {
  const navigate = useNavigate();
  const location = useLocation();
  const crumbs = breadcrumbsForPath(location.pathname);

  if (crumbs.length <= 1) return null;

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      padding: '8px 24px',
      borderBottom: '1px solid var(--border-subtle)',
      fontFamily: 'var(--font-mono)',
      fontSize: 10,
    }}>
      {crumbs.map((crumb, i) => (
        <span key={i} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {crumb.path ? (
            <span
              onClick={() => navigate(crumb.path!)}
              style={{ color: 'var(--accent-blue)', cursor: 'pointer' }}
            >
              {crumb.label}
            </span>
          ) : (
            <span style={{ color: 'var(--text-tertiary)' }}>{crumb.label}</span>
          )}
          {i < crumbs.length - 1 && (
            <span style={{ color: 'var(--text-tertiary)' }}>/</span>
          )}
        </span>
      ))}
    </div>
  );
}
