import { useEffect, useState, useCallback } from 'react';
import { Button, Spinner, Intent, HTMLSelect } from "@blueprintjs/core";
import { get, post } from '../api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface MP {
  id: number;
  name: string;
  constituency: string;
  party: string;
}

interface Entity {
  id: number;
  raw_match_name: string;
  status: string;
  resolved_mp_id: number | null;
  document_title: string | null;
  source_url: string | null;
  suggestions: MP[];
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const CARD: React.CSSProperties = {
  border: '1px solid #1F242E',
  background: '#12161C',
  padding: '14px 20px',
  marginBottom: 8,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  gap: 16,
};

const MONO_SM: React.CSSProperties = {
  fontFamily: 'var(--font-mono)', fontSize: 12, color: '#BDC1C9',
};

const MONO_XS: React.CSSProperties = {
  fontFamily: 'var(--font-mono)', fontSize: 10, color: '#738091',
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function EntityReviewPage() {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedMp, setSelectedMp] = useState<Record<number, number>>({});
  const [actionMsg, setActionMsg] = useState('');

  const fetchEntities = useCallback(async () => {
    try {
      const data = await get<Entity[]>('/api/v1/admin/entity-review');
      setEntities(data);
      setError('');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load entities');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEntities();
  }, [fetchEntities]);

  const handleResolve = async (entityId: number) => {
    const mpId = selectedMp[entityId];
    if (!mpId) return;
    setActionMsg('');
    try {
      const res = await post<{ detail: string; mp_name: string }>(
        `/api/v1/admin/entity-review/${entityId}/resolve`,
        { mp_id: mpId },
      );
      setActionMsg(`Resolved to ${res.mp_name}`);
      setEntities((prev) => prev.filter((e) => e.id !== entityId));
    } catch (err: unknown) {
      setActionMsg(err instanceof Error ? err.message : 'Resolve failed');
    }
  };

  const handleSkip = async (entityId: number) => {
    setActionMsg('');
    try {
      await post(`/api/v1/admin/entity-review/${entityId}/skip`, {});
      setActionMsg('Skipped');
      setEntities((prev) => prev.filter((e) => e.id !== entityId));
    } catch (err: unknown) {
      setActionMsg(err instanceof Error ? err.message : 'Skip failed');
    }
  };

  // -----------------------------------------------------------------------
  // States
  // -----------------------------------------------------------------------

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 200 }}>
        <Spinner size={24} />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ color: '#F55656', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
        {error}
        <Button minimal small intent={Intent.PRIMARY} onClick={fetchEntities} style={{ marginLeft: 12 }}>
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 900 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <h1 style={{
          fontFamily: 'var(--font-mono)', fontSize: 16, fontWeight: 600,
          color: '#E8EDF2', margin: 0,
        }}>
          Entity Review Queue
          <span style={{ color: '#738091', fontSize: 13, fontWeight: 400, marginLeft: 10 }}>
            {entities.length} unresolved
          </span>
        </h1>
        <div style={{ display: 'flex', gap: 8 }}>
          {actionMsg && (
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#15B371', alignSelf: 'center' }}>
              {actionMsg}
            </span>
          )}
          <Button minimal small icon="refresh" onClick={fetchEntities}>
            Refresh
          </Button>
        </div>
      </div>

      {/* Empty state */}
      {entities.length === 0 && (
        <div style={{ ...CARD, justifyContent: 'center', padding: 40 }}>
          <span style={{ ...MONO_XS, fontSize: 12 }}>No unresolved entities. Queue is clear.</span>
        </div>
      )}

      {/* Entity list */}
      {entities.map((entity) => (
        <div key={entity.id} style={CARD}>
          {/* Left: entity info */}
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ ...MONO_SM, fontWeight: 600, marginBottom: 2 }}>
              {entity.raw_match_name}
            </div>
            <div style={MONO_XS}>
              {entity.document_title || 'Unknown document'}
              {entity.source_url && (
                <> &middot; <a href={entity.source_url} target="_blank" rel="noreferrer"
                  style={{ color: '#2B95D6', textDecoration: 'none' }}>
                  View source
                </a></>
              )}
            </div>
          </div>

          {/* Right: resolve controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
            {entity.suggestions.length > 0 ? (
              <HTMLSelect
                minimal
                style={{
                  fontFamily: 'var(--font-mono)', fontSize: 11, color: '#BDC1C9',
                  background: '#0F1319', border: '1px solid #1F242E', padding: '2px 8px',
                  minWidth: 200,
                }}
                value={selectedMp[entity.id] ?? ''}
                onChange={(e) => setSelectedMp((prev) => ({
                  ...prev,
                  [entity.id]: Number(e.target.value),
                }))}
              >
                <option value="">Select MP…</option>
                {entity.suggestions.map((mp) => (
                  <option key={mp.id} value={mp.id}>
                    {mp.name} ({mp.constituency}, {mp.party})
                  </option>
                ))}
              </HTMLSelect>
            ) : (
              <span style={MONO_XS}>No suggestions</span>
            )}
            <Button
              small
              intent={Intent.PRIMARY}
              disabled={!selectedMp[entity.id]}
              onClick={() => handleResolve(entity.id)}
            >
              Resolve
            </Button>
            <Button small minimal onClick={() => handleSkip(entity.id)}>
              Skip
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}
