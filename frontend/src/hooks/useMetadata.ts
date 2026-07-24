import { useEffect, useState } from 'react';
import { get } from '../api';

export interface PartyMeta {
  short: string;
  color: string;
}

export interface ContributionTypeMeta {
  type: string;
  label: string;
  color: string;
}

interface MetadataState {
  parties: Record<string, PartyMeta> | null;
  contributionTypes: Record<string, ContributionTypeMeta> | null;
  loading: boolean;
  error: string | null;
}

let cached: MetadataState | null = null;
let fetchPromise: Promise<MetadataState> | null = null;

async function fetchMetadata(): Promise<MetadataState> {
  if (cached) return cached;
  if (fetchPromise) return fetchPromise;

  fetchPromise = (async () => {
    try {
      const [parties, contributionTypes] = await Promise.all([
        get<Record<string, PartyMeta>>('/api/v1/metadata/parties'),
        get<Record<string, ContributionTypeMeta>>('/api/v1/metadata/contribution-types'),
      ]);
      cached = { parties, contributionTypes, loading: false, error: null };
      return cached;
    } catch (err) {
      const error = err instanceof Error ? err.message : 'Failed to load metadata';
      cached = { parties: null, contributionTypes: null, loading: false, error };
      return cached;
    }
  })();

  return fetchPromise;
}

export function usePartyMeta(partyName: string): PartyMeta {
  const [meta, setMeta] = useState<MetadataState | null>(cached);

  useEffect(() => {
    if (cached) return;
    let cancelled = false;
    fetchMetadata().then((m) => { if (!cancelled) setMeta(m); });
    return () => { cancelled = true; };
  }, []);

  if (meta?.parties?.[partyName]) {
    return meta.parties[partyName];
  }

  // Fallback: deterministic short name + color from palette.
  const PALETTE = [
    'var(--accent-blue)', 'var(--accent-amber)', 'var(--accent-green)', 'var(--accent-red)',
    '#8B5CF6', '#EC4899', '#06B6D4', '#F97316', '#84CC16', '#6366F1',
  ];
  const hash = partyName.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);
  const short = partyName.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 5);
  return { short, color: PALETTE[hash % PALETTE.length] };
}

export function useTypeMeta(contributionType: string): ContributionTypeMeta {
  const [meta, setMeta] = useState<MetadataState | null>(cached);

  useEffect(() => {
    if (cached) return;
    let cancelled = false;
    fetchMetadata().then((m) => { if (!cancelled) setMeta(m); });
    return () => { cancelled = true; };
  }, []);

  if (meta?.contributionTypes?.[contributionType]) {
    return meta.contributionTypes[contributionType];
  }

  // Fallback: generate label and color from type name.
  const label = contributionType.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  return { type: contributionType, label, color: 'var(--text-secondary)' };
}
