import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { get } from '../api';
import { sectionTitle, mono, surface, narrativeSection } from '../dashboard/styles';

interface HansardSession {
  session_id: number;
  document_id: number;
  hansard_no: number;
  session_date: string;
  meeting_description: string;
  sitting_time: string | null;
  document_title: string | null;
  source_url: string | null;
}

interface UtteranceStats {
  total_records: number;
  data: { mp_id: number | null }[];
}

export default function HansardSessionsPage() {
  const [sessions, setSessions] = useState<HansardSession[]>([]);
  const [sessionStats, setSessionStats] = useState<Record<number, { turns: number; speakers: number }>>({});
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    let cancelled = false;

    get<HansardSession[]>('/api/v1/hansard/sessions')
      .then(async (sessionsData) => {
        if (cancelled) return;
        setSessions(sessionsData);

        // Fetch utterance stats per session
        const statsMap: Record<number, { turns: number; speakers: number }> = {};
        const statsPromises = sessionsData.map(async (s) => {
          try {
            const resp = await get<UtteranceStats>(`/api/v1/hansard/utterances?session_id=${s.session_id}&limit=1`);
            const speakerIds = new Set(resp.data.map((u: { mp_id: number | null }) => u.mp_id).filter(Boolean));
            statsMap[s.session_id] = { turns: resp.total_records, speakers: speakerIds.size };
          } catch {
            statsMap[s.session_id] = { turns: 0, speakers: 0 };
          }
        });

        await Promise.all(statsPromises);
        if (!cancelled) {
          setSessionStats(statsMap);
          setLoading(false);
        }
      })
      .catch(() => { if (!cancelled) setLoading(false); });

    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div style={{ padding: 24 }}>
        <span style={{ color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          Loading hansard sessions…
        </span>
      </div>
    );
  }

  const sorted = [...sessions].sort((a, b) => {
    if (a.session_date !== b.session_date) return b.session_date.localeCompare(a.session_date);
    return b.hansard_no - a.hansard_no;
  });

  return (
    <div style={{ padding: 24 }}>
      <div style={{ ...narrativeSection, display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <span style={{ ...sectionTitle, marginBottom: 4 }}>HANSARD</span>
          <h1 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', margin: '4px 0 2px 0' }}>
            Parliamentary Debates
          </h1>
          <p style={{ ...mono, fontSize: 11, color: 'var(--text-tertiary)', margin: 0 }}>
            Browse verbatim transcripts of parliamentary proceedings
          </p>
        </div>
      </div>

      {sorted.length === 0 ? (
        <div style={{ ...surface, padding: 24, textAlign: 'center' }}>
          <span style={{ ...mono, fontSize: 12, color: 'var(--text-tertiary)' }}>
            No hansard sessions found. Run the crawler to import debate transcripts.
          </span>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {sorted.map((s) => {
            const stats = sessionStats[s.session_id] || { turns: 0, speakers: 0 };
            const dateStr = new Date(s.session_date).toLocaleDateString('en-GB', {
              day: 'numeric', month: 'short', year: 'numeric',
            });

            return (
              <div
                key={s.session_id}
                onClick={() => navigate(`/hansard/session/${s.session_id}`)}
                style={{
                  ...surface,
                  padding: '14px 16px',
                  borderLeft: '3px solid var(--accent-blue)',
                  cursor: 'pointer',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 6 }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span style={{
                        ...mono, fontSize: 9, textTransform: 'uppercase', padding: '2px 6px',
                        color: 'var(--accent-blue)', border: '1px solid var(--accent-blue)',
                      }}>
                        HANSARD #{s.hansard_no}
                      </span>
                      <span style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)' }}>
                        {dateStr}
                      </span>
                      {s.sitting_time && (
                        <span style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)' }}>
                          {s.sitting_time}
                        </span>
                      )}
                    </div>
                    <h3 style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', margin: '4px 0 2px 0' }}>
                      {s.meeting_description}
                    </h3>
                    {s.document_title && (
                      <p style={{ fontSize: 11, color: 'var(--text-tertiary)', margin: '2px 0 0 0' }}>
                        {s.document_title}
                      </p>
                    )}
                  </div>

                  {/* Stats */}
                  <div style={{ display: 'flex', gap: 16, flexShrink: 0, marginLeft: 16 }}>
                    <div style={{ textAlign: 'center' }}>
                      <span style={{ ...mono, fontSize: 16, fontWeight: 700, color: 'var(--accent-blue)', display: 'block' }}>
                        {stats.turns}
                      </span>
                      <span style={{ ...mono, fontSize: 8, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Turns
                      </span>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <span style={{ ...mono, fontSize: 16, fontWeight: 700, color: 'var(--accent-blue)', display: 'block' }}>
                        {stats.speakers}
                      </span>
                      <span style={{ ...mono, fontSize: 8, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Speakers
                      </span>
                    </div>
                  </div>
                </div>

                {s.source_url && (
                  <div style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)', marginTop: 4 }}>
                    Source: {s.source_url.length > 80 ? s.source_url.slice(0, 80) + '…' : s.source_url}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
