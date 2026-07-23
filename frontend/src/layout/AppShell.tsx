import { ReactNode } from 'react';
import TopNav from './TopNav';
import SystemStatusBar from './SystemStatusBar';

interface AppShellProps {
  sidebar?: ReactNode;
  rightPanel?: ReactNode;
  children: ReactNode;
  fullWidth?: boolean;
}

export default function AppShell({ sidebar, rightPanel, children, fullWidth }: AppShellProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <TopNav />
      <SystemStatusBar />

      {fullWidth ? (
        <main style={{ flex: 1, overflow: 'auto' }}>{children}</main>
      ) : (
        <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          {sidebar && (
            <aside
              style={{
                width: 240,
                borderRight: '1px solid var(--border-subtle)',
                overflow: 'auto',
                background: 'var(--bg-surface)',
              }}
            >
              {sidebar}
            </aside>
          )}

          <main style={{ flex: 1, overflow: 'auto', padding: 16 }}>
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
