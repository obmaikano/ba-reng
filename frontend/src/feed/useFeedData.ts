import { useEffect, useState } from 'react';
import { get } from '../api';
import { Contribution, MpSummary } from '../dashboard/types';

export interface FeedData {
  contributions: Contribution[];
  mps: MpSummary[];
  totalCount: number;
  unresolvedCount: number;
}

interface FeedDataState {
  data: FeedData | null;
  error: boolean;
}

export function useFeedData(): FeedDataState {
  const [data, setData] = useState<FeedData | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    Promise.all([
      get<Contribution[]>('/api/v1/contributions?limit=100'),
      get<MpSummary[]>('/api/v1/mps'),
      get<{ contribution_count: number; unresolved_entity_count: number }>('/api/v1/status'),
    ])
      .then(([contributions, mps, status]) => {
        setData({
          contributions,
          mps,
          totalCount: status.contribution_count,
          unresolvedCount: status.unresolved_entity_count,
        });
      })
      .catch(() => setError(true));
  }, []);

  return { data, error };
}
