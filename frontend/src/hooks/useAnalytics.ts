import { useEffect, useState } from 'react';
import { get } from '../api';

export interface MinisterialDodgeItem {
  ministry: string;
  total_questions: number;
  deferred_count: number;
  deferral_rate_pct: number;
  avg_response_lag_days: number;
}

export interface VelocityRadarItem {
  keyword: string;
  current_frequency: number;
  prior_avg_frequency: number;
  velocity_delta_pct: number;
}

export interface CLAIMetric {
  mp_id: number;
  name: string;
  constituency: string;
  total_contributions: number;
  local_mentions: number;
  clai_score_pct: number;
}

export function useAnalytics(mpId?: number) {
  const [dodgeData, setDodgeData] = useState<MinisterialDodgeItem[]>([]);
  const [velocityData, setVelocityData] = useState<VelocityRadarItem[]>([]);
  const [claiData, setClaiData] = useState<CLAIMetric | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    const fetchAll = async () => {
      try {
        const [dodgeJson, velocityJson] = await Promise.all([
          get<MinisterialDodgeItem[]>('/api/v1/analytics/ministerial-dodge'),
          get<VelocityRadarItem[]>('/api/v1/analytics/topic-velocity'),
        ]);

        const claiJson = mpId
          ? await get<CLAIMetric>(`/api/v1/analytics/constituency-alignment/${mpId}`)
          : null;

        if (!cancelled) {
          setDodgeData(dodgeJson);
          setVelocityData(velocityJson);
          setClaiData(claiJson);
          setLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to fetch analytics');
          setLoading(false);
        }
      }
    };

    fetchAll();
    return () => { cancelled = true; };
  }, [mpId]);

  return { dodgeData, velocityData, claiData, loading, error };
}
