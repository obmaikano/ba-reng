"""Shared parsing utilities for Botswana Parliament document parsers."""

import re
from datetime import datetime

import pdfplumber

from backend.db.connection import get_connection

DATE_PATTERN = re.compile(
    r'(?:FOR\s+)?'
    r'(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)'
    r'\s+\d{1,2}(?:ST|ND|RD|TH)?\s+'
    r'(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|'
    r'OCTOBER|NOVEMBER|DECEMBER),?\s+\d{4}',
    re.IGNORECASE,
)

# Fallback: dates without weekday prefix (Committee of Supply speeches, motions)
DATE_WITHOUT_WEEKDAY = re.compile(
    r'(?:ON\s+|DELIVERED\s+(?:TO\s+THE\s+NATIONAL\s+ASSEMBLY\s+)?ON\s+)?'
    r'(\d{1,2})(?:ST|ND|RD|TH)?\s+(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER),?\s+(\d{4})',
    re.IGNORECASE,
)

MINISTRY_NORMALISE_RE = re.compile(
    r'^(?:(?:THE\s+)?(?:HONOURABLE|HON\.?)?\s*)?'
    r'(?:Minister\s+(?:of|for)(?:\s+State)?\s+)?\s*',
    re.IGNORECASE,
)

MINISTRY_CLEANUP_RE = re.compile(
    r'\s*:\s*\(?[ivx]+\)?\s*$',
)

MINISTRY_TRAILING = re.compile(r'[:,\s]+$')

MINISTRY_ARTIFACTS = re.compile(
    r'\s*(?:\b\d{4}(?:/\d{4})?\b|'
    r'\b(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|'
    r'JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)'
    r'\s+\d{4}\b|'
    r'DELIVERED TO THE NATIONAL ASSEMBLY|'
    r'Page\s+\d+\s+of\s+\d+|'
    r'I\.\s+INTRODUCTION|'
    r'(?:HRS/MINS|COMMITTEE OF SUPPLY).*$)',
    re.IGNORECASE,
)

MINISTRY_LEAKED_SUBJECT = re.compile(
    r'\s+(?:if|whether|when|why|how|to\s+state|to\s+update|to\s+apprise|'
    r'to\s+explain|to\s+clarify|to\s+give|to\s+indicate|'
    r'to\s+confirm|to\s+provide|to\s+brief|to\s+inform|to\s+establish|'
    r'what\s+plans|what\s+steps|what\s+action|what\s+the)\b.*$',
    re.IGNORECASE,
)

MINISTRY_BARE_ROMAN = re.compile(r'\s+\(?[ivx]+\)?\s*$', re.IGNORECASE)

def _get_canonical_ministry(name: str) -> str:
    """Look up a canonical ministry name from the database.

    The lookup is deterministic. It tries, in order:
      1. Exact canonical-name match on the ministries table.
      2. Keyword match preferring static-seed rows, then highest weight.

    Returns:
        The canonical ministry name, or empty string if no match.
    """
    conn = get_connection()
    try:
        cleaned = name.lower().strip().rstrip('.').rstrip(',')
        row = conn.execute(
            'SELECT canonical_name FROM ministries WHERE LOWER(canonical_name) = ?',
            (cleaned,),
        ).fetchone()
        if row:
            return row['canonical_name']
        row = conn.execute(
            """
            SELECT m.canonical_name
            FROM ministry_keywords k
            JOIN ministries m ON m.id = k.ministry_id
            WHERE k.keyword = ?
            ORDER BY CASE WHEN k.source_type = 'static_seed' THEN 0 ELSE 1 END,
                     k.weight DESC,
                     m.id ASC
            LIMIT 1
            """,
            (cleaned,),
        ).fetchone()
        if row:
            return row['canonical_name']
        return ''
    finally:
        conn.close()


MOTION_SIGNATURE = re.compile(
    r'\(((?:MR|MS|MRS|DR|HON|BRIGADIER)\.?\s+.+?),\s+MP\.\s*[-\u2013]\s*(.+?)\)',
    re.IGNORECASE,
)

# Real Notice/Order Paper motion lists are almost always closed with a curly
# opening quote, but at least one real document used a straight quote for one
# motion in an otherwise-curly-quoted list -- a genuine inconsistency in the
# source PDF, not a formatting choice we control.
MOTION_LINE = re.compile(r'^\s*(\d+)\.\s*["“](.+)', re.DOTALL)

# Single-motion Notice Papers (e.g. "NOTICE OF A MOTION" for one motion) start
# the quoted motion text with a bullet instead of a number.
BULLET_MOTION_LINE = re.compile(r'^\s*[\u2022\u25AA]\s*["“](.+)', re.DOTALL)


def parse_numbered_motions(text: str, date: str | None) -> list[dict]:
    """Parse a numbered "(Mover, MP. - Constituency)"-signed motion list."""
    contributions: list[dict] = []
    lines = text.split('\n')

    current_motion_lines: list[str] = []
    in_motion = False
    prev_line = ''

    def finalize_unsigned() -> None:
        full_text = ' '.join(current_motion_lines).strip()
        contributions.append({
            'contribution_type': 'motion',
            'raw_match_name': '',
            'raw_constituency': '',
            'ministry_addressed': '',
            'subject_text': full_text,
            'date': date or '',
        })

    for line in lines:
        ls = line.strip()
        if not ls:
            continue

        motion_match = MOTION_LINE.match(ls) or BULLET_MOTION_LINE.match(ls)
        if motion_match:
            if in_motion and current_motion_lines:
                finalize_unsigned()
            group = motion_match.lastindex or 1
            start_text = motion_match.group(group)
            if BULLET_MOTION_LINE.match(ls):
                # A standalone bullet motion often carries its title on the
                # line above the quoted text (e.g. "DECRIMINALISATION OF SEX
                # WORK" then the motion). Keep that title in the subject.
                title = prev_line.strip()
                if title and not title.startswith('('):
                    current_motion_lines = [f'{title}: {start_text}']
                else:
                    current_motion_lines = [start_text]
            else:
                current_motion_lines = [start_text]
            in_motion = True
        elif in_motion:
            sig_match = MOTION_SIGNATURE.search(ls)
            if sig_match:
                current_motion_lines.append(ls[:sig_match.start()].strip())
                full_text = ' '.join(current_motion_lines).strip()
                contributions.append({
                    'contribution_type': 'motion',
                    'raw_match_name': sig_match.group(1).strip(),
                    'raw_constituency': sig_match.group(2).strip(),
                    'ministry_addressed': '',
                    'subject_text': full_text,
                    'date': date or '',
                })
                in_motion = False
                current_motion_lines = []
            else:
                current_motion_lines.append(ls)
        prev_line = ls

    if in_motion and current_motion_lines:
        finalize_unsigned()

    return contributions


def extract_text(pdf_path: str) -> str:
    """Extract and concatenate text from all PDF pages."""
    with pdfplumber.open(pdf_path) as pdf:
        lines: list[str] = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines.append(text)
    return '\n'.join(lines)


def _extract_date_from_header(text: str) -> str | None:
    """Extract a date from document text.

    Tries weekday-prefixed format first, then falls back to bare date
    format (common in Committee of Supply speeches).
    """
    match = DATE_PATTERN.search(text)
    if match:
        raw = match.group(0).strip().upper()
        raw = raw.removeprefix('FOR ')
        raw = re.sub(r'\b(\d+)(ST|ND|RD|TH)\b', r'', raw)
        raw = raw.replace(',', '').strip()
        try:
            dt = datetime.strptime(raw, '%A %d %B %Y')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass

    # Fallback: dates without weekday (e.g. "24 MARCH 2026", "23rd MARCH, 2026")
    match = DATE_WITHOUT_WEEKDAY.search(text)
    if match:
        try:
            dt = datetime.strptime(
                f'{match.group(1)} {match.group(2)} {match.group(3)}',
                '%d %B %Y',
            )
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass

    return None

def normalise_ministry(raw: str) -> str:
    """Normalise ministry name: strip prefixes, artifacts, subject leaks."""
    name = raw.strip()
    name = MINISTRY_NORMALISE_RE.sub('', name)
    name = MINISTRY_CLEANUP_RE.sub('', name).strip()
    name = MINISTRY_BARE_ROMAN.sub('', name).strip()
    name = MINISTRY_TRAILING.sub('', name).strip()

    name = re.sub(r'[\[\]\(\)]', '', name)
    name = re.sub(r'\s+for the\s*$', '', name, flags=re.IGNORECASE).strip()
    name = re.sub(r'\s+and$', '', name, flags=re.IGNORECASE).strip()
    name = re.sub(r'\s+&$', '', name).strip()
    name = re.sub(r'\s*&\s*', ' and ', name)

    name = re.sub(r'\b2O(\d)', r'20\1', name)

    name = MINISTRY_ARTIFACTS.sub('', name).strip()
    name = MINISTRY_LEAKED_SUBJECT.sub('', name).strip()
    name = re.sub(r'\s*:\s*\(?[ivx]+\)?\s*', ' ', name).strip()
    name = MINISTRY_LEAKED_SUBJECT.sub('', name).strip()
    name = re.sub(r'\s*:\s*\(?[ivx]+\)?\s*$', '', name, flags=re.IGNORECASE).strip()
    name = re.sub(r'\s+\b(?:on|at|in|by|for the)\s*$', '', name, flags=re.IGNORECASE).strip()
    name = re.sub(r'([a-z])(if|whether|when|why|how|to\s+)', r'\1 \2', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+:\s*$', '', name)
    name = MINISTRY_BARE_ROMAN.sub('', name).strip()
    name = re.sub(r'\s+:\s*$', '', name)
    name = re.sub(r'[:\s]+$', '', name)

    name = re.sub(r'.*?\bMINISTER\s+(?:OF|FOR)(?:\s+STATE)?\s*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\bMINISTER\s+(?:OF|FOR)(?:\s+STATE)?\s*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'^MINISTER\b\s*', '', name, flags=re.IGNORECASE)

    name = re.sub(r'\s{2,}', ' ', name).strip()

    if not name:
        return ''

    result = _get_canonical_ministry(name)
    if result:
        return result

    return name.title() if name.isupper() else name
