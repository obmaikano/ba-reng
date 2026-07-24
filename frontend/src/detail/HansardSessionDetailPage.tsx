import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { get } from '../api';

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

interface UtteranceItem {
  utterance_id: number;
  agenda_id: number;
  mp_id: number | null;
  speaker_name: string;
  speech_type: string;
  speech_text: string;
  language: string;
  evidence_type: string | null;
  word_count: number | null;
  sequence_order: number;
  mp_name: string | null;
  party: string | null;
  constituency: string | null;
  agenda_title: string;
  agenda_category: string;
}

interface UtterancesResponse {
  total_records: number;
  returned_records: number;
  data: UtteranceItem[];
}

export default function HansardSessionDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState<HansardSession | null>(null);
  const [utterances, setUtterances] = useState<UtteranceItem[]>([]);
  const [totalUtterances, setTotalUtterances] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);

    Promise.all([
      get<HansardSession[]>('/api/v1/hansard/sessions'),
      get<UtterancesResponse>(`/api/v1/hansard/utterances?session_id=${id}&limit=200`),
    ])
      .then(([sessions, utteranceResp]) => {
        const sess = sessions.find((s) => s.session_id === Number(id));
        if (!sess) {
          setError('Session not found.');
          setLoading(false);
          return;
        }
        setSession(sess);
        setUtterances(utteranceResp.data || []);
        setTotalUtterances(utteranceResp.total_records);
        setError(null);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to load session data');
        setLoading(false);
      });
  }, [id]);

  if (loading) {
    return (
      <div style={{ padding: 24 }}>
        <span style={{ color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          Loading session data…
        </span>
      </div>
    );
  }

  if (error || !session) {
    return (
      <div style={{ padding: 24 }}>
        <span style={{ color: 'var(--accent-red)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          {error || 'Session not found.'}
        </span>
        <div style={{ marginTop: 12 }}>
          <span onClick={() => navigate('/')} style={{ color: 'var(--accent-blue)', cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 11 }}>
            ← Home
          </span>
        </div>
      </div>
    );
  }

  // Group utterances by agenda item
  const agendaMap = new Map<number, { title: string; category: string; items: UtteranceItem[] }>();
  for (const u of utterances) {
    const existing = agendaMap.get(u.agenda_id);
    if (existing) {
      existing.items.push(u);
    } else {
      agendaMap.set(u.agenda_id, {
        title: u.agenda_title,
        category: u.agenda_category,
        items: [u],
      });
    }
  }

  // Unique speakers
  const speakers = new Map<string, { mp_id: number | null; party: string | null; count: number }>();
  for (const u of utterances) {
    const key = u.mp_name || u.speaker_name;
    const existing = speakers.get(key);
    if (existing) {
      existing.count++;
    } else {
      speakers.set(key, { mp_id: u.mp_id, party: u.party, count: 1 });
    }
  }
  const speakerList = Array.from(speakers.entries()).sort((a, b) => b[1].count - a[1].count);

  const evidenceColors: Record<string, string> = {
    EMPIRICAL: 'var(--accent-green)',
    STATUTORY: 'var(--accent-blue)',
    ANECDOTAL: 'var(--accent-amber)',
    NORMATIVE: 'var(--text-secondary)',
  };

  const speechTypeColors: Record<string, string> = {
    minister_answer: 'var(--accent-green)',
    question: 'var(--accent-blue)',
    supplementary_question: 'var(--accent-blue)',
    point_of_procedure: 'var(--accent-amber)',
    member_statement: 'var(--text-secondary)',
  };

  return (
    <div style={{ padding: 24 }}>
      {/* Breadcrumb */}
      <div style={{ marginBottom: 16, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)' }}>
        <span onClick={() => navigate('/')} style={{ cursor: 'pointer', color: 'var(--accent-blue)' }}>Home</span>
        <span style={{ margin: '0 6px' }}>→</span>
        <span>Hansard</span>
        <span style={{ margin: '0 6px' }}>→</span>
        <span>Session #{session.hansard_no}</span>
      </div>

      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <span style={{
          fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)',
          textTransform: 'uppercase', letterSpacing: '0.08em',
        }}>
          HANSARD SESSION
        </span>
        <h1 style={{ fontSize: 20, fontWeight: 600, color: 'var(--text-primary)', margin: '4px 0 2px 0' }}>
          Hansard No. {session.hansard_no}
        </h1>
        <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)', margin: 0 }}>
          {session.session_date} · {session.meeting_description}
          {session.sitting_time && ` · ${session.sitting_time}`}
        </p>
      </div>

      {/* Session metadata + source */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16, marginBottom: 20 }}>
        <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', padding: 14 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
            <MiniStat label="Turns" value={String(totalUtterances)} />
            <MiniStat label="Speakers" value={String(speakerList.length)} />
            <MiniStat label="Agenda Items" value={String(agendaMap.size)} />
          </div>
        </div>
        <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', padding: 14, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>
            Speakers
          </span>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {speakerList.slice(0, 8).map(([name, info]) => (
              <span
                key={name}
                onClick={() => info.mp_id && navigate(`/mp/${info.mp_id}`)}
                style={{
                  fontFamily: 'var(--font-mono)', fontSize: 9, padding: '2px 6px',
                  border: '1px solid var(--border-subtle)', color: info.mp_id ? 'var(--accent-blue)' : 'var(--text-tertiary)',
                  cursor: info.mp_id ? 'pointer' : 'default',
                }}
              >
                {name.split(/\s+/).slice(0, 2).map((w: string) => w[0]).join('')} ({info.count})
              </span>
            ))}
            {speakerList.length > 8 && (
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)' }}>
                +{speakerList.length - 8} more
              </span>
            )}
          </div>
        </div>
      </div>

      {session.source_url && (
        <div style={{
          marginBottom: 20, padding: 12,
          background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)',
          borderLeft: '3px solid var(--accent-blue)',
        }}>
          <a href={session.source_url} target="_blank" rel="noreferrer" style={{
            fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-blue)', textDecoration: 'none',
          }}>
            View source PDF →
          </a>
        </div>
      )}

      {/* Utterances grouped by agenda item */}
      {Array.from(agendaMap.entries()).map(([agendaId, agenda]) => (
        <div key={agendaId} style={{ marginBottom: 24 }}>
          <div style={{
            padding: '10px 14px', marginBottom: 0,
            background: 'var(--bg-surface)', border: '1px solid var(--border-default)',
            borderBottom: 'none',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{
                fontFamily: 'var(--font-mono)', fontSize: 9, textTransform: 'uppercase',
                color: 'var(--accent-amber)', border: '1px solid var(--accent-amber)',
                padding: '1px 6px',
              }}>
                {agenda.category}
              </span>
              <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)' }}>
                {agenda.title}
              </span>
              <span style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)' }}>
                {agenda.items.length} turn{agenda.items.length === 1 ? '' : 's'}
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {agenda.items.map((u) => {
              const tagColor = evidenceColors[u.evidence_type || ''] || speechTypeColors[u.speech_type] || 'var(--text-tertiary)';
              const tagLabel = u.evidence_type || u.speech_type;
              const speakerInitials = (u.mp_name || u.speaker_name).split(/\s+/).slice(0, 2).map((w: string) => w[0]).join('').toUpperCase();

              return (
                <div
                  key={u.utterance_id}
                  style={{
                    background: 'var(--bg-elevated)', border: '1px solid var(--border-default)',
                    borderTop: 'none', padding: '10px 14px',
                    display: 'flex', alignItems: 'flex-start', gap: 10,
                  }}
                >
                  {/* Speaker avatar */}
                  <div
                    onClick={() => u.mp_id && navigate(`/mp/${u.mp_id}`)}
                    style={{
                      width: 26, height: 26, display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontFamily: 'var(--font-mono)', fontSize: 9, fontWeight: 600,
                      color: u.mp_id ? 'var(--accent-blue)' : 'var(--text-tertiary)',
                      border: `1px solid ${u.mp_id ? 'var(--accent-blue)' : 'var(--border-subtle)'}`,
                      background: 'var(--bg-surface)', flexShrink: 0, cursor: u.mp_id ? 'pointer' : 'default',
                    }}
                  >
                    {speakerInitials}
                  </div>

                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span
                        onClick={() => u.mp_id && navigate(`/mp/${u.mp_id}`)}
                        style={{
                          fontSize: 11, fontWeight: 600, color: u.mp_id ? 'var(--accent-blue)' : 'var(--text-primary)',
                          cursor: u.mp_id ? 'pointer' : 'default',
                        }}
                      >
                        {u.mp_name || u.speaker_name}
                      </span>
                      {u.party && (
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)' }}>
                          {u.party}
                        </span>
                      )}
                      {u.constituency && (
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)' }}>
                          {u.constituency}
                        </span>
                      )}
                      <span style={{
                        fontFamily: 'var(--font-mono)', fontSize: 8, textTransform: 'uppercase',
                        padding: '1px 4px', border: `1px solid ${tagColor}`,
                        color: tagColor, marginLeft: 'auto',
                      }}>
                        {tagLabel}
                      </span>
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                      {u.speech_text.length > 500
                        ? u.speech_text.slice(0, 500) + '…'
                        : u.speech_text}
                    </div>
                    {u.language && u.language !== 'en' && (
                      <div style={{ marginTop: 4, fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)' }}>
                        Language: {u.language.toUpperCase()}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}

      {utterances.length === 0 && (
        <div style={{ padding: 16, textAlign: 'center', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)', border: '1px solid var(--border-subtle)' }}>
          No utterances recorded for this session.
        </div>
      )}
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
        {label}
      </span>
      <span style={{ display: 'block', fontFamily: 'var(--font-mono)', fontSize: 16, fontWeight: 700, color: 'var(--accent-blue)', marginTop: 2 }}>
        {value}
      </span>
    </div>
  );
}
