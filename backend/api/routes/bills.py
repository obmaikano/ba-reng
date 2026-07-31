"""Bill endpoints — grouped by bill name/number with lifecycle stages."""

import re
from fastapi import APIRouter, Query

from backend.db.connection import get_connection

router = APIRouter(prefix='/api/v1/bills', tags=['bills'])

# Extract bill number: "Bill No. 8 of 2026" or "Bill No. 31 of 2025"
BILL_NO_RE = re.compile(r'Bill\s+No\.?\s*(\d+)\s+of\s+(\d{4})', re.IGNORECASE)

# Bill stage ordering for timeline
STAGE_ORDER = {
    'bill_presentation': 0,
    'bill_1st': 0,
    'bill_reading': 1,
    'bill_2nd': 2,
    'second_reading': 2,
    'committee_stage': 3,
    'bill_amendment': 4,
    'amendment': 4,
    'bill_3rd': 5,
    'third_reading': 5,
}


def _bill_key(subject: str) -> str | None:
    """Extract a stable grouping key from a bill subject line.

    Returns None for fragments that are clearly not real bill names.
    """
    m = BILL_NO_RE.search(subject or '')
    if m:
        return f'Bill No. {m.group(1)} of {m.group(2)}'
    # Fallback: use first 60 chars, cleaned
    clean = re.sub(r'\s+', ' ', (subject or '').strip().strip('\u201c\u201d\u2018\u2019"'))
    # If it's too short or clearly a fragment, skip
    if len(clean) < 15:
        return None
    return clean[:60]


def _bill_name(subject: str) -> str:
    """Extract a human-readable bill name from a contribution subject line.

    Tries to find "X Bill, YYYY" or "X Act, YYYY" patterns first,
    then falls back to stripping the "(Bill No. X of YYYY)" suffix.
    """
    s = (subject or '').strip()
    # Try to find "Name Bill, 2026" or "Name Act, 2026" pattern — this is the
    # real bill title embedded in longer subject lines like Gazette headings
    m = re.search(
        r'([\w\s\-().,/]+(?:Bill|Act)[\w\s\-().,/#]*?),\s*\d{4}',
        s, re.IGNORECASE,
    )
    if m:
        candidate = m.group(1).strip()
        # Skip if it's just boilerplate
        if 'Government Gazette' not in candidate and 'printed by' not in candidate.lower():
            # Clean trailing bill-no suffix from the candidate too
            candidate = re.sub(
                r'\s*\(?Bill\s+No\.?\s*\d+\s+of\s+\d{4}\)?\s*$', '',
                candidate, flags=re.IGNORECASE,
            ).strip()
            if len(candidate) > 5:
                return candidate

    # Fallback: remove "(Bill No. X of YYYY)" wherever it appears
    name = re.sub(
        r'\s*\(?Bill\s+No\.?\s*\d+\s+of\s+\d{4}\)?\s*', '',
        s, flags=re.IGNORECASE,
    ).strip()
    # Strip Gazette boilerplate prefix
    name = re.sub(
        r'^The\s+Botswana\s+Government\s+Gazette\s+is\s+printed\s+by\s+Department\s+of\s+Government\s+Printing\s+and\s+Publishing\s+Services,\s*',
        '', name, flags=re.IGNORECASE,
    ).strip()
    return name


# Primary bill types — always real bills, include unconditionally.
# Secondary types (bill_reading, bill_amendment, etc.) — require "Bill No."
# in subject_text to exclude motions, SONA responses, and committee-of-supply
# fragments that the parser sometimes classifies as bill_reading.
_BILL_TYPES_PRIMARY = (
    'bill_presentation', 'bill_1st', 'bill_2nd',
    'second_reading', 'bill_3rd', 'third_reading',
)
_BILL_TYPES_SECONDARY = (
    'bill_reading', 'bill_amendment', 'committee_stage', 'amendment',
)
_BILL_PLACEHOLDERS_PRIMARY = ','.join('?' * len(_BILL_TYPES_PRIMARY))
_BILL_PLACEHOLDERS_SECONDARY = ','.join('?' * len(_BILL_TYPES_SECONDARY))
_BILL_ALL_TYPES = (*_BILL_TYPES_PRIMARY, *_BILL_TYPES_SECONDARY)

_BILL_LIST_QUERY = f"""SELECT id, subject_text, contribution_type, date, ministry_addressed,
                           mp_id, raw_match_name
                    FROM contributions
                    WHERE (
                        contribution_type IN ({_BILL_PLACEHOLDERS_PRIMARY})
                        OR (
                            contribution_type IN ({_BILL_PLACEHOLDERS_SECONDARY})
                            AND subject_text LIKE '%Bill No.%'
                        )
                    )
                    ORDER BY date DESC"""

_BILL_DETAIL_QUERY = f"""SELECT c.*, m.name AS mp_name, m.party, m.constituency,
                      d.source_url AS doc_source_url
               FROM contributions c
               LEFT JOIN mps m ON m.id = c.mp_id
               LEFT JOIN documents d ON d.id = c.document_id
               WHERE (
                   c.contribution_type IN ({_BILL_PLACEHOLDERS_PRIMARY})
                   OR (
                       c.contribution_type IN ({_BILL_PLACEHOLDERS_SECONDARY})
                       AND c.subject_text LIKE '%Bill No.%'
                   )
               )
               ORDER BY c.date"""


@router.get('')
def list_bills(
    limit: int = Query(50, ge=1, le=200),
) -> dict:
    """List bills grouped by bill number/name with stage counts and latest date."""
    conn = get_connection()
    try:
        rows = conn.execute(_BILL_LIST_QUERY, _BILL_ALL_TYPES).fetchall()

        # Group by bill key
        groups: dict[str, dict] = {}
        for r in rows:
            key = _bill_key(r['subject_text'])
            if key is None:
                continue  # skip fragments without a valid bill key
            if key not in groups:
                groups[key] = {
                    'bill_key': key,
                    'bill_name': _bill_name(r['subject_text']),
                    'contributions': [],
                    'stages': set(),
                    'latest_date': r['date'],
                    'ministry_addressed': r['ministry_addressed'],
                    'sponsor_mp_id': None,
                    'sponsor_name': None,
                }
            else:
                # Update bill_name if current contribution has a better name
                # (prefer names with "Bill" or "Act" over gazette headings)
                current_name = _bill_name(r['subject_text'])
                existing = groups[key]['bill_name']
                has_keyword = lambda n: bool(re.search(r'(Bill|Act)\b', n, re.IGNORECASE))
                if has_keyword(current_name) and not has_keyword(existing):
                    groups[key]['bill_name'] = current_name
            group = groups[key]
            group['contributions'].append(dict(r))
            group['stages'].add(r['contribution_type'])
            if r['date'] > group['latest_date']:
                group['latest_date'] = r['date']
            # First non-null ministry wins
            if not group['ministry_addressed'] and r['ministry_addressed']:
                group['ministry_addressed'] = r['ministry_addressed']
            # First non-null MP wins (sponsor)
            if not group['sponsor_mp_id'] and r['mp_id']:
                group['sponsor_mp_id'] = r['mp_id']

        # Sort by latest date descending
        sorted_groups = sorted(groups.values(), key=lambda g: g['latest_date'], reverse=True)

        # Enrich sponsor names
        mp_ids = [g['sponsor_mp_id'] for g in sorted_groups if g['sponsor_mp_id']]
        if mp_ids:
            placeholders = ','.join('?' * len(mp_ids))
            mp_rows = conn.execute(
                f'SELECT id, name FROM mps WHERE id IN ({placeholders})', mp_ids,
            ).fetchall()
            mp_map = {r['id']: r['name'] for r in mp_rows}
            for g in sorted_groups:
                if g['sponsor_mp_id']:
                    g['sponsor_name'] = mp_map.get(g['sponsor_mp_id'])

        # Paginate
        total = len(sorted_groups)
        paged = sorted_groups[:limit]

        # Clean up: remove raw contributions list, replace with counts
        result = []
        for g in paged:
            contribs = g.pop('contributions')
            stages_list = sorted(g.pop('stages'), key=lambda s: STAGE_ORDER.get(s, 99))
            result.append({
                **g,
                'contribution_count': len(contribs),
                'stages': stages_list,
                'latest_stage': stages_list[-1] if stages_list else None,
            })

        return {
            'total_records': total,
            'returned_records': len(result),
            'data': result,
        }
    finally:
        conn.close()


@router.get('/{bill_key:path}')
def get_bill(bill_key: str) -> dict:
    """Get a single bill's full lifecycle — all contributions across all stages."""
    conn = get_connection()
    try:
        rows = conn.execute(_BILL_DETAIL_QUERY, _BILL_ALL_TYPES).fetchall()

        # Filter to matching bill key
        matching = [dict(r) for r in rows if _bill_key(r['subject_text']) == bill_key]
        if not matching:
            return {'error': 'Bill not found', 'bill_key': bill_key}

        # Sort by stage order then date
        matching.sort(key=lambda c: (
            STAGE_ORDER.get(c['contribution_type'], 99),
            c['date'],
        ))

        # Pick best bill name: prefer non-empty names with "Bill" or "Act" keywords
        bill_name = ''
        for c in matching:
            candidate = _bill_name(c['subject_text'])
            if candidate and len(candidate) > len(bill_name):
                bill_name = candidate
            if bill_name and re.search(r'(Bill|Act)\b', bill_name, re.IGNORECASE):
                break  # good enough
        if not bill_name:
            bill_name = _bill_name(matching[0]['subject_text'])
        ministry = next((c['ministry_addressed'] for c in matching if c['ministry_addressed']), None)
        sponsor_mp_id = next((c['mp_id'] for c in matching if c['mp_id']), None)

        # Stage timeline
        stages_seen: dict[str, list[dict]] = {}
        for c in matching:
            stage = c['contribution_type']
            stages_seen.setdefault(stage, []).append(c)

        timeline = []
        for stage, items in sorted(stages_seen.items(), key=lambda x: STAGE_ORDER.get(x[0], 99)):
            timeline.append({
                'stage': stage,
                'count': len(items),
                'first_date': items[0]['date'],
                'last_date': items[-1]['date'],
                'items': items,
            })

        return {
            'bill_key': bill_key,
            'bill_name': bill_name,
            'ministry_addressed': ministry,
            'sponsor_mp_id': sponsor_mp_id,
            'total_contributions': len(matching),
            'timeline': timeline,
        }
    finally:
        conn.close()
