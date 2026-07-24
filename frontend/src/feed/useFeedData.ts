import { useCallback, useEffect, useState } from 'react';
import { get } from '../api';
import { Contribution, MpSummary } from '../dashboard/types';
import { FilterState } from './FilterSidebar';

export interface FeedData {
  contributions: Contribution[];
  mps: MpSummary[];
  totalCount: number;
  unresolvedCount: number;
}

interface FeedDataState {
  data: FeedData | null;
  error: boolean;
  refetch: () => void;
}

interface FeedResponse {
  data: Contribution[];
  total_records: number;
  returned_records: number;
}

function buildQuery(params: FilterState): string {
  const qs: string[] = [];
  if (params.type && params.type !== 'All Types') qs.push(`type=${encodeURIComponent(params.type)}`);
  if (params.party && params.party !== 'All Parties') qs.push(`party=${encodeURIComponent(params.party)}`);
  if (params.ministry && params.ministry !== 'All Ministries') qs.push(`ministry=${encodeURIComponent(params.ministry)}`);
  if (params.constituency) qs.push(`constituency=${encodeURIComponent(params.constituency)}`);
  if (params.startDate) qs.push(`start_date=${encodeURIComponent(params.startDate)}`);
  if (params.endDate) qs.push(`end_date=${encodeURIComponent(params.endDate)}`);
  qs.push('limit=100');
  return qs.length > 0 ? `?${qs.join('&')}` : '?limit=100';
}

export function useFeedData(currentFilters: FilterState): FeedDataState {
  const [data, setData] = useState<FeedData | null>(null);
  const [error, setError] = useState(false);

  const fetchData = useCallback(() => {
    Promise.all([
      get<FeedResponse>(`/api/v1/contributions${buildQuery(currentFilters)}`),
      get<MpSummary[]>('/api/v1/mps'),
      get<{ contribution_count: number; unresolved_entity_count: number }>('/api/v1/status'),
    ])
      .then(([feedResp, mps, status]) => {
        setData({
          contributions: feedResp.data,
          mps,
          totalCount: feedResp.total_records,
          unresolvedCount: status.unresolved_entity_count,
        });
        setError(false);
      })
      .catch(() => setError(true));
  }, [currentFilters]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, error, refetch: fetchData };
}
