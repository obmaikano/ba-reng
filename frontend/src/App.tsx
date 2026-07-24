import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import LoginPage from './auth/LoginPage';
import ProtectedRoute from './auth/ProtectedRoute';
import AdminLayout from './admin/AdminLayout';
import AppShell from './layout/AppShell';
import DashboardMain from './dashboard/DashboardMain';
import DashboardSidebar from './dashboard/DashboardSidebar';
import { useDashboardData } from './dashboard/useDashboardData';
import { useFeedData } from './feed/useFeedData';
import FeedPage from './feed/FeedPage';
import FilterSidebar from './feed/FilterSidebar';
import FeedRightPanel from './feed/FeedRightPanel';
import FindMpPage from './findmp/FindMpPage';
import MpProfilePage from './mp/MpProfilePage';
import ComparePage from './compare/ComparePage';
import RankingsPage from './rankings/RankingsPage';

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

function MpProfile() {
  const { data } = useFeedData();
  const mps = data?.mps ?? [];
  const unresolvedCount = data?.unresolvedCount ?? 0;

  return (
    <AppShell
      sidebar={<FilterSidebar ministries={[]} />}
      rightPanel={<FeedRightPanel mps={mps} unresolvedCount={unresolvedCount} />}
    >
      <MpProfilePage />
    </AppShell>
  );
}

function Compare() {
  const { data } = useFeedData();
  const mps = data?.mps ?? [];
  const unresolvedCount = data?.unresolvedCount ?? 0;

  return (
    <AppShell
      sidebar={<FilterSidebar ministries={[]} />}
      rightPanel={<FeedRightPanel mps={mps} unresolvedCount={unresolvedCount} />}
    >
      <ComparePage />
    </AppShell>
  );
}

function Feed() {
  const { data, error } = useFeedData();

  if (error) {
    return (
      <AppShell>
        <span style={{ color: 'var(--accent-red)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          Could not load feed data. Is the API running?
        </span>
      </AppShell>
    );
  }

  if (!data) {
    return (
      <AppShell>
        <span style={{ color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          Loading…
        </span>
      </AppShell>
    );
  }

  const ministryNames = Array.from(
    new Set(data.contributions.map((c) => c.ministry_addressed).filter((m): m is string => Boolean(m))),
  ).sort();

  return (
    <AppShell
      sidebar={<FilterSidebar ministries={ministryNames} />}
      rightPanel={<FeedRightPanel mps={data.mps} unresolvedCount={data.unresolvedCount} />}
    >
      <FeedPage contributions={data.contributions} totalCount={data.totalCount} />
    </AppShell>
  );
}

function FindMp() {
  return (
    <AppShell
      sidebar={<FilterSidebar ministries={[]} />}
    >
      <FindMpPage />
    </AppShell>
  );
}

function Rankings() {
  return (
    <AppShell>
      <RankingsPage />
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
        <Route path="/mp/:mpId" element={<MpProfile />} />
        <Route path="/compare" element={<Compare />} />
        <Route path="/bills" element={<ComingSoon title="Bill Tracker" />} />
        <Route path="/search" element={<ComingSoon title="Search" />} />
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
