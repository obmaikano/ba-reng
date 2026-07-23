export interface ParticipationIndex {
  participation_index: number;
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
}

export interface Contribution {
  id: number;
  contribution_type: string;
  subject_text: string;
  ministry_addressed: string | null;
  date: string;
  source_url: string;
  mp_id: number | null;
  mp_name: string | null;
  party: string | null;
  constituency: string | null;
}
