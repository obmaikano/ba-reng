import { useEffect, useState } from 'react';
import { get } from '../api';
import { Contribution, MpSummary, NarrativeData } from './types';

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
  prevWeekCount: number;
  mps: MpSummary[];
  status: StatusData;
  narrative: NarrativeData | null;
}

interface DashboardDataState {
  data: DashboardData | null;
  error: boolean;
}

interface ContributionsResponse {
  data: Contribution[];
  total_records: number;
  returned_records: number;
}

const WEEK_WINDOW_DAYS = 7;

function shiftDate(date: string, days: number): string {
  const shifted = new Date(date);
  shifted.setDate(shifted.getDate() + days);
  return shifted.toISOString().slice(0, 10);
}

function scopeToLatestWeek(contributions: Contribution[]): {
  weekContributions: Contribution[];
  weekStart: string | null;
  weekEnd: string | null;
  sittingDays: number;
  prevWeekCount: number;
} {
  if (contributions.length === 0) {
    return { weekContributions: [], weekStart: null, weekEnd: null, sittingDays: 0, prevWeekCount: 0 };
  }

  const latestDate = contributions.reduce((max, c) => (c.date > max ? c.date : max), contributions[0].date);
  const weekStart = shiftDate(latestDate, -(WEEK_WINDOW_DAYS - 1));

  const weekContributions = contributions.filter((c) => c.date >= weekStart && c.date <= latestDate);
  const sittingDays = new Set(weekContributions.map((c) => c.date)).size;

  const prevWeekStart = shiftDate(weekStart, -WEEK_WINDOW_DAYS);
  const prevWeekEnd = shiftDate(weekStart, -1);
  const prevWeekCount = contributions.filter((c) => c.date >= prevWeekStart && c.date <= prevWeekEnd).length;

  return { weekContributions, weekStart, weekEnd: latestDate, sittingDays, prevWeekCount };
}

export function useDashboardData(): DashboardDataState {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    Promise.all([
      get<ContributionsResponse>('/api/v1/contributions?limit=200'),
      get<MpSummary[]>('/api/v1/mps'),
      get<StatusData>('/api/v1/status'),
      get<NarrativeData>('/api/v1/narrative/weekly'),
    ])
      .then(([contributionsResp, mps, status, narrative]) => {
        const contributions = contributionsResp.data;
        const scoped = scopeToLatestWeek(contributions);
        setData({ contributions, ...scoped, mps, status, narrative });
      })
      .catch(() => setError(true));
  }, []);

  return { data, error };
}
