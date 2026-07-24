export interface BreakdownItem {
  contribution_type: string;
  count: number;
  weight: number;
  weighted_score: number;
}

export interface ParticipationIndex {
  participation_index: number;
  breakdown: BreakdownItem[];
  is_proxy: boolean;
  caveat: string;
}

export interface MpSummary {
  id: number;
  name: string;
  constituency: string;
  party: string;
  photo_url: string | null;
  contribution_count: number;
  participation_index: ParticipationIndex;
  participation_rank?: number;
  participation_rank_of?: number;
}

export interface Contribution {
  id: number;
  contribution_type: string;
  subject_text: string;
  ministry_addressed: string | null;
  date: string;
  source_url: string;
  doc_source_url?: string;
  mp_id: number | null;
  mp_name: string | null;
  raw_match_name?: string;
  party: string | null;
  constituency: string | null;
}

export interface TopStoryNarrative {
  mp_name: string;
  constituency: string;
  contribution_type: string;
  date: string;
  ministry: string;
  subject: string;
  action: string;
  context: string;
  impact: string;
  source_url: string;
}

export interface MpFocusNarrative {
  mp_name: string;
  constituency: string;
  party: string;
  total_contributions: number;
  top_topic: string;
  narrative: string;
  persona?: string;
  persona_description?: string;
}

export interface HotTopicNarrative {
  ministry: string;
  count: number;
  pct: number;
}

export interface NarrativeData {
  period: { start: string; end: string };
  status: string;
  message?: string;
  summary_metrics: {
    total_contributions: number;
    sitting_days: number;
    active_mps_count: number;
    top_addressed_ministry: string;
    top_ministry_count: number;
    top_ministry_pct: number;
    ministry_breakdown: Record<string, number>;
  };
  narrative_highlights: {
    headline_story: string;
    oversight_gap: string | null;
    deferral_alert: string | null;
    persona_breakdown: Record<string, number>;
    intent_breakdown: Record<string, number>;
  };
  top_story: TopStoryNarrative | null;
  mp_focus: MpFocusNarrative[];
  hot_topics: HotTopicNarrative[];
  deferral_scorecard: DeferralScorecardEntry[];
}

export interface DeferralScorecardEntry {
  ministry: string;
  deferred_count: number;
  total_questions: number;
  deferral_rate_pct: number;
  backlog_count: number;
}
