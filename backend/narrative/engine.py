"""Narrative Synthesis Engine — deterministic story generation for parliamentary data."""

import sqlite3
from collections import Counter
from collections.abc import Iterable
from datetime import date, timedelta
from typing import Any

from backend.db.connection import get_connection
from backend.narrative.deferral_scorecard import deferral_alert, deferral_scorecard
from backend.narrative.ministerial_inference import dynamic_infer_ministry
from backend.narrative.persona_classifier import classify_persona
from backend.narrative.rhetorical_classifier import DBIntentClassifier
from backend.narrative.rhetorical_harvester import RhetoricalHarvester


def _week_bounds() -> tuple[str, str]:
    """Return (monday_iso, sunday_iso) for the most recent complete week.

    If today is Monday–Sunday, returns the previous Monday–Sunday.
    """
    today = date.today()
    monday = today - timedelta(days=today.weekday() + 7)
    sunday = monday + timedelta(days=6)
    return monday.isoformat(), sunday.isoformat()


def _group_by(values: Iterable[dict], key: str) -> dict[str, list[dict]]:
    buckets: dict[str, list[dict]] = {}
    for v in values:
        k = str(v.get(key, '') or '')
        buckets.setdefault(k, []).append(v)
    return buckets


def _generate_mp_focus_narrative(rows_bucket: list[dict]) -> dict:
    """Build a single MP focus block."""
    mp_name = rows_bucket[0].get('mp_name') or rows_bucket[0].get('raw_match_name') or 'Unresolved MP'
    constituency = rows_bucket[0].get('constituency') or ''
    party = rows_bucket[0].get('party') or ''
    total = len(rows_bucket)
    topics = [r['inferred_ministry'] for r in rows_bucket if r.get('inferred_ministry')]
    top_topic = Counter(topics).most_common(1)
    topic_label = top_topic[0][0] if top_topic else 'General Matters'

    return {
        'mp_name': mp_name,
        'constituency': constituency,
        'party': party,
        'total_contributions': total,
        'top_topic': topic_label,
        'narrative': f'{mp_name} ({constituency}) concentrated {total} intervention{"s" if total != 1 else ""} primarily on {topic_label}.',
    }


class NarrativeEngine:
    """Produces weekly-digest narrative payloads from the contributions table."""

    def __init__(self, conn: sqlite3.Connection | None = None):
        self._conn = conn or get_connection()
        self._own_conn = conn is None

    def close(self) -> None:
        if self._own_conn:
            self._conn.close()

    def weekly_digest(self, start_date: str | None = None, end_date: str | None = None) -> dict[str, Any]:
        """Build a narrative digest for the given date range.

        Defaults to the most recently completed week if no range is supplied.
        """
        start = start_date or _week_bounds()[0]
        end = end_date or _week_bounds()[1]

        cursor = self._conn.cursor()

        cursor.execute(
            """SELECT c.*, m.name AS mp_name, m.party, m.constituency
               FROM contributions c
               LEFT JOIN mps m ON c.mp_id = m.id
               WHERE c.date BETWEEN ? AND ?
               ORDER BY c.date""",
            (start, end),
        )
        rows = [dict(r) for r in cursor.fetchall()]

        if not rows:
            return {
                'period': {'start': start, 'end': end},
                'status': 'NO_DATA',
                'message': 'No parliament sittings recorded for this period.',
            }

        for r in rows:
            r['inferred_ministry'] = dynamic_infer_ministry(
                r.get('subject_text', ''),
                r.get('ministry_addressed'),
                conn=self._conn,
            )

        rh = RhetoricalHarvester(self._conn)
        dbc = DBIntentClassifier(self._conn)
        intent_counts: Counter[str] = Counter()
        for r in rows:
            text = r.get('subject_text', '') or r.get('speech_text', '')
            if text:
                rh.harvest(text)
                intent = dbc.classify(text)
                r['primary_intent'] = intent['primary_intent']
                r['constructiveness_ratio'] = intent['constructiveness_ratio']
                intent_counts[intent['primary_intent']] += 1

        ministry_counts = Counter(r['inferred_ministry'] for r in rows)
        top_ministry, top_count = ministry_counts.most_common(1)[0]
        total_pct = round(top_count / len(rows) * 100)

        mp_buckets = _group_by(rows, 'mp_id')
        mp_focus_list = [_generate_mp_focus_narrative(b) for b in mp_buckets.values() if b[0].get('mp_id')]
        mp_focus_list.sort(key=lambda m: m['total_contributions'], reverse=True)

        sitting_days = len({r['date'] for r in rows})
        active_mp_count = len(mp_buckets)

        # Persona + deferral analytics
        persona_counts: Counter[str] = Counter()
        for mp_focus in mp_focus_list:
            mp_rows = [r for r in rows if r.get('mp_name') == mp_focus['mp_name']]
            types = [r.get('contribution_type', '') for r in mp_rows]
            persona = classify_persona(types)
            mp_focus['persona'] = persona['persona']
            mp_focus['persona_description'] = persona['description']
            persona_counts[persona['persona']] += 1

        scorecard = deferral_scorecard(self._conn)
        deferral_warning = deferral_alert(scorecard)

        unanswered = [r for r in rows if r.get('contribution_type') == 'question_deferral']

        return {
            'period': {'start': start, 'end': end},
            'status': 'OK',
            'summary_metrics': {
                'total_contributions': len(rows),
                'sitting_days': sitting_days,
                'active_mps_count': active_mp_count,
                'top_addressed_ministry': top_ministry,
                'top_ministry_count': top_count,
                'top_ministry_pct': total_pct,
                'ministry_breakdown': dict(ministry_counts.most_common()),
            },
            'narrative_highlights': {
                'headline_story': (
                    f'Parliament focused heavily on {top_ministry}, '
                    f'accounting for {top_count} of {len(rows)} recorded interventions '
                    f'({total_pct}%).'
                ),
                'oversight_gap': (
                    f'{len(unanswered)} question{"s" if len(unanswered) != 1 else ""} deferred to a Later Date'
                    if unanswered
                    else None
                ),
                'deferral_alert': deferral_warning,
                'persona_breakdown': dict(persona_counts.most_common()),
                'intent_breakdown': dict(intent_counts.most_common()),
            },
            'deferral_scorecard': scorecard[:5],
            'top_story': _build_top_story(rows[0]) if rows else None,
            'mp_focus': mp_focus_list[:5],
            'hot_topics': [
                {'ministry': m, 'count': c, 'pct': round(c / len(rows) * 100)}
                for m, c in ministry_counts.most_common(5)
            ],
        }


def _build_top_story(contribution: dict) -> dict:
    """Construct a 3-part micro-narrative: Action → Context → Impact."""
    mp_name = contribution.get('mp_name') or contribution.get('raw_match_name') or 'Unresolved MP'
    constituency = contribution.get('constituency') or ''
    subject = contribution.get('subject_text', '')
    ctype = contribution.get('contribution_type', '')
    ministry = contribution.get('inferred_ministry') or contribution.get('ministry_addressed') or ''

    action = f'{mp_name} ({constituency}) introduced a {ctype.replace("_", " ")}.'
    if len(subject) < 100:
        action = f'{mp_name} ({constituency}): {subject}'

    return {
        'mp_name': mp_name,
        'constituency': constituency,
        'contribution_type': ctype,
        'date': contribution.get('date', ''),
        'ministry': ministry,
        'subject': subject,
        'action': action,
        'context': f'The intervention targets {ministry or "General Parliamentary Business"}, addressing issues raised during the current session.',
        'impact': f'If resolved, this could affect policy decisions within {ministry or "the relevant portfolio"}.',
        'source_url': contribution.get('source_url', ''),
    }
