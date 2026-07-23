import { Routes, Route, Navigate, useParams } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import LoginPage from './auth/LoginPage';
import ProtectedRoute from './auth/ProtectedRoute';
import AdminLayout from './admin/AdminLayout';
import AppShell from './layout/AppShell';
import DashboardMain from './dashboard/DashboardMain';
import DashboardSidebar from './dashboard/DashboardSidebar';
import { useDashboardData } from './dashboard/useDashboardData';

function Home() {
  const { data, error } = useDashboardData();

  if (error) {
    return (
      <AppShell>
        <span style={{ color: 'var(--accent-red)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          Could not load dashboard data. Is the API running?
        </span>
      </AppShell>
    );
  }

  if (!data) {
    return (
      <AppShell>
        <span style={{ color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          Loading this week in parliament…
        </span>
      </AppShell>
    );
  }

  return (
    <AppShell rightPanel={<DashboardSidebar data={data} />}>
      <DashboardMain data={data} />
    </AppShell>
  );
}

function ComingSoon({ title }: { title: string }) {
  return (
    <AppShell>
      <span style={{ color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
        {title} — coming soon
      </span>
    </AppShell>
  );
}

function MpProfileStub() {
  const { mpId } = useParams();
  return <ComingSoon title={`MP Profile #${mpId}`} />;
}

function Feed() {
  return (
    <AppShell
      sidebar={<div style={{ padding: 12, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>Filters</div>}
    >
      <span style={{ color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>Live Record Stream</span>
    </AppShell>
  );
}

function FindMp() {
  return (
    <AppShell
      sidebar={<div style={{ padding: 12, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>Browse Constituencies</div>}
    >
      <span style={{ color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>Find My MP</span>
    </AppShell>
  );
}

function Rankings() {
  return (
    <AppShell
      sidebar={<div style={{ padding: 12, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>Party Filter</div>}
      rightPanel={
        <div style={{ padding: 12 }}>
          <div style={{
            border: '1px solid var(--accent-amber)',
            background: 'rgba(245, 166, 35, 0.08)',
            padding: 8,
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            color: 'var(--accent-amber)',
          }}>
            Proxy metric — based on recorded contributions only. Not attendance data.
          </div>
        </div>
      }
    >
      <span style={{ color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
        Participation Index Leaderboard
      </span>
    </AppShell>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/feed" element={<Feed />} />
        <Route path="/find" element={<FindMp />} />
        <Route path="/rankings" element={<Rankings />} />
        <Route path="/mp/:mpId" element={<MpProfileStub />} />
        <Route path="/compare" element={<ComingSoon title="Compare MPs" />} />
        <Route path="/bills" element={<ComingSoon title="Bill Tracker" />} />
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/admin/*"
          element={
            <ProtectedRoute>
              <AdminLayout />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
