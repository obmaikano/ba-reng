import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import LoginPage from './auth/LoginPage';
import ProtectedRoute from './auth/ProtectedRoute';
import AdminLayout from './admin/AdminLayout';
import AppShell from './layout/AppShell';

function Home() {
  return (
    <AppShell fullWidth>
      <div style={{ padding: '2rem' }}>
        <h1 style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', fontSize: 24, margin: 0 }}>
          This Week in Parliament
        </h1>
        <p style={{ color: 'var(--text-tertiary)', marginTop: 8 }}>
          Ba Reng? — Botswana Parliament MP Monitor
        </p>
      </div>
    </AppShell>
  );
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
