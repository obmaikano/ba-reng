import { useEffect, useState } from 'react';
import { get } from '../api';
import { Contribution, MpSummary } from './types';

export interface StatusData {
  mp_count: number;
  contribution_count: number;
  document_count: number;
  unresolved_entity_count: number;
  last_crawl: { started_at: string; status: string; new_documents: number } | null;
}

export interface DashboardData {
  contributions: Contribution[];
  weekContributions: Contribution[];
  weekStart: string | null;
  weekEnd: string | null;
  sittingDays: number;
  mps: MpSummary[];
  status: StatusData;
}

interface DashboardDataState {
  data: DashboardData | null;
  error: boolean;
}

const WEEK_WINDOW_DAYS = 7;

function scopeToLatestWeek(contributions: Contribution[]): {
  weekContributions: Contribution[];
  weekStart: string | null;
  weekEnd: string | null;
  sittingDays: number;
} {
  if (contributions.length === 0) {
    return { weekContributions: [], weekStart: null, weekEnd: null, sittingDays: 0 };
  }

  const latestDate = contributions.reduce((max, c) => (c.date > max ? c.date : max), contributions[0].date);
  const windowStart = new Date(latestDate);
  windowStart.setDate(windowStart.getDate() - (WEEK_WINDOW_DAYS - 1));
  const weekStart = windowStart.toISOString().slice(0, 10);

  const weekContributions = contributions.filter((c) => c.date >= weekStart && c.date <= latestDate);
  const sittingDays = new Set(weekContributions.map((c) => c.date)).size;

  return { weekContributions, weekStart, weekEnd: latestDate, sittingDays };
}

export function useDashboardData(): DashboardDataState {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    Promise.all([
      get<Contribution[]>('/api/v1/contributions?limit=200'),
      get<MpSummary[]>('/api/v1/mps'),
      get<StatusData>('/api/v1/status'),
    ])
      .then(([contributions, mps, status]) => {
        const { weekContributions, weekStart, weekEnd, sittingDays } = scopeToLatestWeek(contributions);
        setData({ contributions, weekContributions, weekStart, weekEnd, sittingDays, mps, status });
      })
      .catch(() => setError(true));
  }, []);

  return { data, error };
}
