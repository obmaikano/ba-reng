import { ReactNode } from 'react';
import TopNav from './TopNav';
import SystemStatusBar from './SystemStatusBar';
import Breadcrumbs from './Breadcrumbs';

interface AppShellProps {
  sidebar?: ReactNode;
  rightPanel?: ReactNode;
  children: ReactNode;
  fullWidth?: boolean;
}

const RESPONSIVE_CSS = `
  @media (max-width: 768px) {
    .appshell-grid { grid-template-columns: 1fr !important; }
    .appshell-grid > aside { display: none; }
    .appshell-flex > aside { display: none; }
    .appshell-flex > main { width: 100% !important; }
    .appshell-status { font-size: 9px !important; padding: 0 8px !important; }
    .appshell-status span { gap: 8px !important; }
  }
`;

export default function AppShell({ sidebar, rightPanel, children, fullWidth }: AppShellProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <style>{RESPONSIVE_CSS}</style>
      <TopNav />
      <Breadcrumbs />
      <div className="appshell-status">
        <SystemStatusBar />
      </div>

      {fullWidth ? (
        <main style={{ flex: 1, overflow: 'auto' }}>{children}</main>
      ) : rightPanel && !sidebar ? (
        <div
          className="appshell-grid"
          style={{
            display: 'grid',
            gridTemplateColumns: '9fr 3fr',
            gap: 1,
            flex: 1,
            overflow: 'hidden',
            background: 'var(--border-subtle)',
          }}
        >
          <section style={{ overflow: 'auto', background: 'var(--bg-canvas)', padding: 20 }}>
            {children}
          </section>
          <aside
            style={{
              overflow: 'auto',
              background: 'var(--bg-surface)',
              borderLeft: '1px solid var(--border-subtle)',
              padding: 16,
            }}
          >
            {rightPanel}
          </aside>
        </div>
      ) : (
        <div className="appshell-flex" style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          {sidebar && (
            <aside
              style={{
                width: 240,
                borderRight: '1px solid var(--border-subtle)',
                overflow: 'auto',
                background: 'var(--bg-surface)',
                padding: 16,
              }}
            >
              {sidebar}
            </aside>
          )}

          <main style={{ flex: 1, overflow: 'auto' }}>
            {children}
          </main>

          {rightPanel && (
            <aside
              style={{
                width: 280,
                borderLeft: '1px solid var(--border-subtle)',
                overflow: 'auto',
                background: 'var(--bg-surface)',
              }}
            >
              {rightPanel}
            </aside>
          )}
        </div>
      )}
    </div>
  );
}
