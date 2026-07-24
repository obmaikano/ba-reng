import { Routes, Route, Navigate } from 'react-router-dom';
import { useCallback, useState } from 'react';
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
import FilterSidebar, { DEFAULT_FILTERS, FilterState } from './feed/FilterSidebar';
import FeedRightPanel from './feed/FeedRightPanel';
import FindMpPage from './findmp/FindMpPage';
import MpProfilePage from './mp/MpProfilePage';
import ComparePage from './compare/ComparePage';
import RankingsPage from './rankings/RankingsPage';
import BillTrackerPage from './bills/BillTrackerPage';
import SearchPage from './search/SearchPage';

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

function MpProfile() {
  const { data } = useFeedData(DEFAULT_FILTERS);
  const mps = data?.mps ?? [];
  const unresolvedCount = data?.unresolvedCount ?? 0;

  return (
    <AppShell
      sidebar={<FilterSidebar ministries={[]} filters={DEFAULT_FILTERS} onChange={() => {}} />}
      rightPanel={<FeedRightPanel mps={mps} unresolvedCount={unresolvedCount} />}
    >
      <MpProfilePage />
    </AppShell>
  );
}

function Compare() {
  const { data } = useFeedData(DEFAULT_FILTERS);
  const mps = data?.mps ?? [];
  const unresolvedCount = data?.unresolvedCount ?? 0;

  return (
    <AppShell
      sidebar={<FilterSidebar ministries={[]} filters={DEFAULT_FILTERS} onChange={() => {}} />}
      rightPanel={<FeedRightPanel mps={mps} unresolvedCount={unresolvedCount} />}
    >
      <ComparePage />
    </AppShell>
  );
}

function Feed() {
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);
  const { data, error } = useFeedData(filters);
  const handleFilterChange = useCallback((next: FilterState) => {
    setFilters(next);
  }, []);

  if (error) {
    return (
      <AppShell>
        <span style={{ color: 'var(--accent-red)', fontFamily: 'var(--font-mono)', fontSize: 12, padding: 24, display: 'block' }}>
          Could not load feed data. Is the API running?
        </span>
      </AppShell>
    );
  }

  if (!data) {
    return (
      <AppShell>
        <span style={{ color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontSize: 12, padding: 24, display: 'block' }}>
          Loading…
        </span>
      </AppShell>
    );
  }

  const ministryNames = Array.from(
    new Set(data.contributions.map((c) => c.ministry_addressed).filter((m): m is string => Boolean(m))),
  ).sort();

  const ministryCounts: Record<string, number> = {};
  for (const c of data.contributions) {
    if (c.ministry_addressed) {
      ministryCounts[c.ministry_addressed] = (ministryCounts[c.ministry_addressed] ?? 0) + 1;
    }
  }

  return (
    <AppShell
      sidebar={<FilterSidebar ministries={ministryNames} filters={filters} onChange={handleFilterChange} ministryCounts={ministryCounts} />}
      rightPanel={<FeedRightPanel mps={data.mps} unresolvedCount={data.unresolvedCount} />}
    >
      <FeedPage contributions={data.contributions} totalCount={data.totalCount} />
    </AppShell>
  );
}

function FindMp() {
  return (
    <AppShell
      sidebar={<FilterSidebar ministries={[]} filters={DEFAULT_FILTERS} onChange={() => {}} />}
    >
      <FindMpPage />
    </AppShell>
  );
}

function Rankings() {
  const { data } = useFeedData(DEFAULT_FILTERS);
  const mps = data?.mps ?? [];
  const unresolvedCount = data?.unresolvedCount ?? 0;

  return (
    <AppShell
      sidebar={<FilterSidebar ministries={[]} filters={DEFAULT_FILTERS} onChange={() => {}} />}
      rightPanel={<FeedRightPanel mps={mps} unresolvedCount={unresolvedCount} />}
    >
      <RankingsPage />
    </AppShell>
  );
}

function Bills() {
  const { data } = useFeedData(DEFAULT_FILTERS);
  const mps = data?.mps ?? [];
  const unresolvedCount = data?.unresolvedCount ?? 0;

  return (
    <AppShell
      sidebar={<FilterSidebar ministries={[]} filters={DEFAULT_FILTERS} onChange={() => {}} />}
      rightPanel={<FeedRightPanel mps={mps} unresolvedCount={unresolvedCount} />}
    >
      <BillTrackerPage />
    </AppShell>
  );
}

function Search() {
  const { data } = useFeedData(DEFAULT_FILTERS);
  const mps = data?.mps ?? [];
  const unresolvedCount = data?.unresolvedCount ?? 0;

  return (
    <AppShell
      sidebar={<FilterSidebar ministries={[]} filters={DEFAULT_FILTERS} onChange={() => {}} />}
      rightPanel={<FeedRightPanel mps={mps} unresolvedCount={unresolvedCount} />}
    >
      <SearchPage />
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
        <Route path="/bills" element={<Bills />} />
        <Route path="/search" element={<Search />} />
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/admin/*"
          element={
            <ProtectedRoute requiredRoles={["editor"]}>
              <AdminLayout />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
