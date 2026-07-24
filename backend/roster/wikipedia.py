"""Fetch canonical MP roster from Wikipedia 13th Parliament page."""

import re
import sqlite3

import requests
from bs4 import BeautifulSoup

from backend.db.connection import get_connection

WIKIPEDIA_URL = 'https://en.wikipedia.org/wiki/13th_Parliament_of_Botswana'
MIN_EXPECTED_MPS = 60

HEADERS = {
    'User-Agent': 'BaReng/0.1 (Botswana Parliament MP Monitor; research)',
}

# Common party abbreviations found in Wikipedia tables — used only as fallback
# when the raw text is a short abbreviation with no other context.
_PARTY_FALLBACK: dict[str, str] = {
    'BCP': 'BCP',
    'UDC': 'UDC',
    'BDP': 'BDP',
    'BPF': 'BPF',
}


def _normalize_party(raw: str) -> str:
    """Normalize a party name from the Wikipedia table cell.

    Prefer the full name as-is from the cell text.
    Only use the fallback map for single-word abbreviations.
    """
    party = raw.strip()
    if party in _PARTY_FALLBACK:
        return _PARTY_FALLBACK[party]
    if party in ('Ind.', 'Ind'):
        return 'Independent'
    if party in ('Spkr.',):
        return 'Speaker'
    return party


def _detect_special_row(no: int, cells: list) -> str | None:
    """Detect if a row represents the President or Speaker from cell text.

    Returns the descriptive label, or None if this is a regular MP row.
    """
    all_text = ' '.join(c.get_text(strip=True).lower() for c in cells)
    if 'president' in all_text and 'speaker' not in all_text:
        return 'President'
    if 'speaker' in all_text:
        return 'Speaker'
    return None


def _detect_from_section(section: str | None) -> str | None:
    """Detect President/Speaker from a preceding section header row.

    Section headers like 'President' or 'Presiding officer' appear
    as interleaved rows before the actual MP data row.
    """
    if not section:
        return None
    s = section.lower()
    if 'president' in s and 'presiding' not in s:
        return 'President'
    if 'presiding officer' in s or 'speaker' in s:
        return 'Speaker'
    return None


def _normalize_constituency(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip()


def _clean_wiki_name(name: str) -> str:
    name = re.sub(r'\[\d+\]', '', name)
    name = re.sub(r'\[edit\]', '', name)
    return name.strip()


def fetch_roster() -> list[dict]:
    """Fetch the MP roster from Wikipedia.

    Returns list of dicts with keys: name, constituency, party.
    Specially-elected MPs and ex-officio members (President, Speaker)
    use a descriptive constituency label that satisfies UNIQUE.
    Party names are detected from the Wikipedia table cell content.
    """
    resp = requests.get(WIKIPEDIA_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    table = _find_mp_table(soup)
    if table is None:
        return []

    rows = table.find_all('tr')
    mps: list[dict] = []
    current_section: str | None = None
    for row in rows:
        cells = row.find_all(['td', 'th'])
        ncols = len(cells)

        first_text = cells[0].get_text(strip=True)

        # Track section headers (e.g. "President", "Specially-elected MPs")
        # Must run BEFORE the ncols<2 guard — section headers with colspan
        # have only one cell and would otherwise be skipped.
        if not first_text.isdigit():
            all_text = ' '.join(c.get_text(strip=True).lower() for c in cells)
            if any(s in all_text for s in ('president', 'speaker', 'presiding officer', 'specially-elected')):
                current_section = all_text
            continue

        if ncols < 2:
            continue

        no = int(first_text)

        # Wikitable column layout:
        #   8-col: [0]No [1]Constituency [2]Name [3]portrait [4]Party [5]Majority [6]% [7]Margin
        #   5-col: [0]No [1]Name         [2]portrait [3]Party [4]blank
        if ncols == 5:
            name = _clean_wiki_name(cells[1].get_text(strip=True))
            party_text = cells[3].get_text(strip=True) if len(cells) > 3 else ''
            party = _normalize_party(party_text)

            if party == 'Speaker':
                constituency = 'Speaker'
            else:
                special = _detect_special_row(no, cells) or _detect_from_section(current_section)
                if special:
                    constituency = special
                else:
                    constituency = f'Specially-elected ({name})'
        elif ncols == 8:
            constituency = cells[1].get_text(strip=True)
            name = _clean_wiki_name(cells[2].get_text(strip=True))
            party_text = cells[4].get_text(strip=True) if len(cells) > 4 else ''
            party = _normalize_party(party_text)

            special = _detect_special_row(no, cells)
            if special:
                constituency = special
        else:
            continue

        if not name:
            continue

        mps.append({
            'name': name,
            'constituency': constituency,
            'party': party,
        })

    return mps


def _find_mp_table(soup: BeautifulSoup) -> BeautifulSoup | None:
    """Find the wikitable containing MP data."""
    for table in soup.find_all('table', class_='wikitable'):
        headers = table.find_all('th')
        header_texts = [h.get_text(strip=True).lower() for h in headers]
        if 'constituency' in header_texts:
            return table
    return None


def store_roster(conn: sqlite3.Connection | None = None) -> dict:
    """Fetch MP roster from Wikipedia and store in the mps table."""
    close_conn = conn is None
    if conn is None:
        conn = get_connection()

    cursor = conn.cursor()
    mps = fetch_roster()
    if len(mps) < MIN_EXPECTED_MPS:
        raise ValueError(
            f'Expected at least {MIN_EXPECTED_MPS} MPs, got {len(mps)}. '
            'Wikipedia table format may have changed.'
        )

    inserted = 0
    skipped = 0
    for mp in mps:
        try:
            cursor.execute(
                """INSERT INTO mps (name, constituency, party)
                   VALUES (?, ?, ?)""",
                (mp['name'], mp['constituency'], mp['party']),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            skipped += 1

    conn.commit()

    if close_conn:
        conn.close()

    return {
        'total': len(mps),
        'inserted': inserted,
        'skipped': skipped,
    }


if __name__ == '__main__':
    result = store_roster()
    print(f'Result: {result}')
