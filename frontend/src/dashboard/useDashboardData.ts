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
  mps: MpSummary[];
  status: StatusData;
}

interface DashboardDataState {
  data: DashboardData | null;
  error: boolean;
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
      .then(([contributions, mps, status]) => setData({ contributions, mps, status }))
      .catch(() => setError(true));
  }, []);

  return { data, error };
}
