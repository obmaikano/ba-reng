import { Routes, Route, Navigate } from 'react-router-dom';
import { useCallback, useState } from 'react';
import { AuthProvider } from './auth/AuthContext';
import LoginPage from './auth/LoginPage';
import ProtectedRoute from './auth/ProtectedRoute';
import AdminLayout from './admin/AdminLayout';
import AdminDashboardPage from './admin/AdminDashboardPage';
import MinistryMappingPage from './admin/MinistryMappingPage';
import EntityReviewPage from './admin/EntityReviewPage';
import UserManagementPage from './admin/UserManagementPage';
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
import AboutPage from './about/AboutPage';
import AnalyticsOverview from './analytics/AnalyticsOverview';
import ContributionDetailPage from './detail/ContributionDetailPage';
import MinistryDetailPage from './detail/MinistryDetailPage';
import ConstituencyDetailPage from './detail/ConstituencyDetailPage';
import HansardSessionDetailPage from './detail/HansardSessionDetailPage';

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

  const partyNames = Array.from(
    new Set(data.mps.map((m) => m.party).filter((p): p is string => Boolean(p))),
  ).sort();

  const ministryCounts: Record<string, number> = {};
  for (const c of data.contributions) {
    if (c.ministry_addressed) {
      ministryCounts[c.ministry_addressed] = (ministryCounts[c.ministry_addressed] ?? 0) + 1;
    }
  }

  return (
    <AppShell
      sidebar={<FilterSidebar ministries={ministryNames} parties={partyNames} filters={filters} onChange={handleFilterChange} ministryCounts={ministryCounts} />}
      rightPanel={<FeedRightPanel mps={data.mps} unresolvedCount={data.unresolvedCount} />}
    >
      <FeedPage contributions={data.contributions} totalCount={data.totalCount} />
    </AppShell>
  );
}

function FindMp() {
  return (
    <AppShell>
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
      rightPanel={<FeedRightPanel mps={mps} unresolvedCount={unresolvedCount} />}
    >
      <RankingsPage />
    </AppShell>
  );
}

function About() {
  return (
    <AppShell>
      <AboutPage />
    </AppShell>
  );
}

function Analytics() {
  return (
    <AppShell>
      <div style={{ padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h2 style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', margin: 0 }}>
            Parliamentary Analytics
          </h2>
        </div>
        <AnalyticsOverview />
      </div>
    </AppShell>
  );
}


function ContributionDetail() {
  const { data } = useFeedData(DEFAULT_FILTERS);
  const mps = data?.mps ?? [];
  const unresolvedCount = data?.unresolvedCount ?? 0;

  return (
    <AppShell
      rightPanel={<FeedRightPanel mps={mps} unresolvedCount={unresolvedCount} />}
    >
      <ContributionDetailPage />
    </AppShell>
  );
}


function MinistryDetail() {
  const { data } = useFeedData(DEFAULT_FILTERS);
  const mps = data?.mps ?? [];
  const unresolvedCount = data?.unresolvedCount ?? 0;

  return (
    <AppShell
      rightPanel={<FeedRightPanel mps={mps} unresolvedCount={unresolvedCount} />}
    >
      <MinistryDetailPage />
    </AppShell>
  );
}

function ConstituencyDetail() {
  const { data } = useFeedData(DEFAULT_FILTERS);
  const mps = data?.mps ?? [];
  const unresolvedCount = data?.unresolvedCount ?? 0;

  return (
    <AppShell
      rightPanel={<FeedRightPanel mps={mps} unresolvedCount={unresolvedCount} />}
    >
      <ConstituencyDetailPage />
    </AppShell>
  );
}


function HansardSessionDetail() {
  const { data } = useFeedData(DEFAULT_FILTERS);
  const mps = data?.mps ?? [];
  const unresolvedCount = data?.unresolvedCount ?? 0;

  return (
    <AppShell
      rightPanel={<FeedRightPanel mps={mps} unresolvedCount={unresolvedCount} />}
    >
      <HansardSessionDetailPage />
    </AppShell>
  );
}

function Bills() {
  const { data } = useFeedData(DEFAULT_FILTERS);
  const mps = data?.mps ?? [];
  const unresolvedCount = data?.unresolvedCount ?? 0;

  return (
    <AppShell
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
        <Route path="/about" element={<About />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/admin"
          element={
            <ProtectedRoute requiredRoles={["editor"]}>
              <AdminLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<AdminDashboardPage />} />
          <Route path="ministry-mappings" element={<MinistryMappingPage />} />
          <Route path="entity-review" element={<EntityReviewPage />} />
          <Route path="users" element={<UserManagementPage />} />
        </Route>
        <Route path="/contribution/:id" element={<ContributionDetail />} />
        <Route path="/ministry/:name" element={<MinistryDetail />} />
        <Route path="/constituency/:name" element={<ConstituencyDetail />} />
        <Route path="/hansard/session/:id" element={<HansardSessionDetail />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
