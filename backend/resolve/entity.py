"""Entity resolution: match parsed contribution names to canonical MPs."""

import re
import sqlite3

from backend.db.connection import get_connection
from backend.resolve.nearest_match import resolve_nearest

# Honorifics to strip when extracting surname
HONORIFICS_RE = re.compile(
    r'^(?:mr|ms|mrs|miss|hon|dr|prof|rev|adv|sen|rep)s?\.?\s*',
    re.IGNORECASE,
)

# Suffixes to strip
SUFFIX_RE = re.compile(r',?\s*mp\.?\s*$', re.IGNORECASE)
PAREN_RE = re.compile(r'\([^)]*\)')


def _normalize_constituency(name: str) -> str:
    """Normalize a constituency name for matching."""
    name = name.lower().strip()
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip()


def _extract_surname(raw_name: str) -> str:
    """Extract the surname from a raw parliamentary name.

    Examples:
        'MR. J. DOE, MP.' -> 'DOE'
        'Mr. A. B. Person, MP.' -> 'Person'
        'Ms. C. D. Leader' -> 'Leader'
    """
    name = raw_name.strip()
    name = SUFFIX_RE.sub('', name)
    name = HONORIFICS_RE.sub('', name)
    name = name.strip()
    parts = name.split()
    if parts:
        candidate = parts[-1].strip('.,;:()[]')
        return candidate
    return raw_name


def resolve_contribution(
    cursor: sqlite3.Cursor,
    raw_match_name: str,
    raw_constituency: str | None,
) -> int | None:
    """Resolve a contribution to an mp_id.

    Strategy: constituency-first, surname fallback.
    Returns mp_id or None if no match found.

    Delegates to the scalable implementation with on-the-fly maps.
    """
    constituency_map = _build_constituency_map(cursor)
    token_map = _build_token_map(cursor)
    return resolve_contribution_scalable(
        cursor, raw_match_name, raw_constituency,
        constituency_map, token_map,
    )


def _build_constituency_map(cursor: sqlite3.Cursor) -> dict[str, int]:
    """Build a map of normalized constituency -> mp_id."""
    rows = cursor.execute('SELECT id, constituency FROM mps').fetchall()
    mapping: dict[str, int] = {}
    for row in rows:
        key = _normalize_constituency(row['constituency'])
        if key:
            mapping[key] = row['id']
    return mapping


def _build_token_map(cursor: sqlite3.Cursor) -> dict[str, list[int]]:
    """Build a map of every name token -> [mp_id, ...] for surname matching.

    Maps every word in an MP's full name (not just the last word) so that
    both first-name and last-name extraction from raw_match_name can resolve.
    Uses sets internally to avoid duplicates when an MP has the same token twice
    (e.g. 'Motsamai Motsamai').
    """
    rows = cursor.execute('SELECT id, name FROM mps').fetchall()
    mapping: dict[str, set[int]] = {}
    for row in rows:
        tokens = row['name'].strip().upper().split()
        for token in tokens:
            mapping.setdefault(token, set()).add(row['id'])
    return {k: list(v) for k, v in mapping.items()}


def _build_ministry_map(cursor: sqlite3.Cursor) -> dict[str, int]:
    """Build a map of normalized ministry title -> mp_id from the ministry_mapping table."""
    rows = cursor.execute(
        'SELECT normalized_title, mp_id FROM ministry_mapping',
    ).fetchall()
    return {row['normalized_title']: row['mp_id'] for row in rows}


def resolve_contribution_scalable(
    cursor: sqlite3.Cursor,
    raw_match_name: str,
    raw_constituency: str | None,
    constituency_map: dict[str, int] | None = None,
    token_map: dict[str, list[int]] | None = None,
    ministry_map: dict[str, int] | None = None,
) -> int | None:
    """Resolve a contribution to an mp_id using pre-built maps."""
    if constituency_map is None:
        constituency_map = _build_constituency_map(cursor)
    if token_map is None:
        token_map = _build_token_map(cursor)
    if ministry_map is None:
        ministry_map = _build_ministry_map(cursor)

    normalized_raw_constituency = _normalize_constituency(raw_constituency or '')

    if normalized_raw_constituency and normalized_raw_constituency in constituency_map:
        return constituency_map[normalized_raw_constituency]

    surname = _extract_surname(raw_match_name)
    if surname:
        candidates = token_map.get(surname.upper(), [])
        if len(candidates) == 1:
            return candidates[0]

    lookup_key = _normalize_constituency(raw_match_name)
    if lookup_key in ministry_map:
        return ministry_map[lookup_key]

    # Fourth fallback: Levenshtein + Jaccard token similarity nearest-match
    if token_map:
        mp_names = [
            (mid, row['name'].upper())
            for mids in token_map.values()
            for mid in mids
            if (row := cursor.execute(
                'SELECT name FROM mps WHERE id = ?', (mid,),
            ).fetchone()) is not None
        ]
        mp_names = list(set(mp_names))  # deduplicate
        nearest_id, _score = resolve_nearest(raw_match_name, mp_names)
        if nearest_id is not None:
            return nearest_id

    return None


if __name__ == '__main__':
    conn = get_connection()
    cursor = conn.cursor()
    unresolved = cursor.execute(
        "SELECT raw_match_name, raw_constituency, id "
        "FROM entity_review_queue WHERE status='UNRESOLVED'",
    ).fetchall()
    constituency_map = _build_constituency_map(cursor)
    token_map = _build_token_map(cursor)
    ministry_map = _build_ministry_map(cursor)
    resolved = 0
    for row in unresolved:
        mp_id = resolve_contribution_scalable(
            cursor, row['raw_match_name'], row['raw_constituency'],
            constituency_map, token_map, ministry_map,
        )
        if mp_id:
            resolved += 1
            print(f'  RESOLVED: [{row["raw_match_name"]}] -> mp_id={mp_id}')
        else:
            rc = row['raw_constituency']
            print(f'  UNRESOLVED: [{row["raw_match_name"]}] (constituency={rc!r})')
    print(f'\nResolved: {resolved}/{len(unresolved)}')
    conn.close()
