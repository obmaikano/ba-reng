"""Tests for MP roster fetching and entity resolution."""

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

from backend.db.connection import _sha256_hex
from backend.resolve.entity import (
    _build_constituency_map,
    _build_token_map,
    _extract_surname,
    _normalize_constituency,
    resolve_contribution,
    resolve_contribution_scalable,
)
from backend.resolve.run import resolve_all
from backend.roster.wikipedia import (
    _clean_wiki_name,
    fetch_roster,
    store_roster,
)

MIGRATIONS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / 'backend' / 'db' / 'migrations'
)
SCHEMA_SQL = ''.join(
    p.read_text() for p in sorted(MIGRATIONS_DIR.glob('*.sql'))
)


def _in_memory_db() -> sqlite3.Connection:
    conn = sqlite3.connect(':memory:')
    conn.execute('PRAGMA foreign_keys=ON')
    conn.row_factory = sqlite3.Row
    conn.create_function('SHA256_HEX', 1, _sha256_hex, deterministic=True)
    conn.executescript(SCHEMA_SQL)
    return conn


_TR = (
    '<tr><td>1</td><td>Chobe</td>'
    '<td>Simasiku Mapulanga</td><td></td><td>BCP</td>'
    '<td>2,853</td><td>63.31</td><td>34.49</td></tr>'
)
_TR1 = (
    '<tr><td>2</td><td>Maun North</td>'
    '<td>Dumelang Saleshando</td><td></td><td>BCP</td>'
    '<td>5,707</td><td>64.08</td><td>43.65</td></tr>'
)
_TR8 = (
    '<tr><td>8</td><td>Tati East</td>'
    '<td>Thabologo Furniture</td><td></td><td>BCP</td>'
    '<td>418</td><td>33.47</td><td>3.12</td></tr>'
)
_TR55 = (
    '<tr><td>55</td><td>Kanye West</td>'
    '<td>Victor Phologolo</td><td></td><td>UDC</td>'
    '<td>2,335</td><td>53.32</td><td>14.68</td></tr>'
)
_TR61 = (
    '<tr><td>61</td><td>Charleshill</td>'
    '<td>Motsamai Motsamai</td><td></td><td>UDC</td>'
    '<td>295</td><td>41.07</td><td>3.73</td></tr>'
)

_THEAD = (
    '<thead><tr>'
    '<th>No.</th><th>Constituency</th><th>Name</th><th>Party</th>'
    '<th>Majority</th><th>% of total votes</th>'
    '<th>Margin (% points)</th>'
    '</tr></thead>'
)

SIXTY_MP_HTML: list[str] = [
    f'<tr><td>{i}</td><td>Const {i}</td><td>Name {i}</td>'
    f'<td></td><td>BCP</td><td>100</td><td>50</td><td>10</td></tr>'
    for i in range(1, 61)
]
SIXTY_MP_HTML_BODY = (
    '<html><body><table class="wikitable">'
    + _THEAD + '<tbody>' + ''.join(SIXTY_MP_HTML) + '</tbody></table></body></html>'
)

SAMPLE_HTML = f"""
<html><body>
<table class="wikitable">
{_THEAD}
<tbody>
{_TR}
{_TR1}
{_TR8}
{_TR55}
{_TR61}
</tbody>
</table>
<table class="wikitable">
</table>
</body></html>
"""

_TR62 = (
    '<tr><td>62</td>'
    '<td>Pius Mokgware</td><td></td><td>UDC</td>'
    '<td></td><td></td><td></td></tr>'
)
_TR63 = (
    '<tr><td>63</td>'
    '<td>Bogolo Kenewendo</td><td></td><td>Ind.</td>'
    '<td></td><td></td><td></td></tr>'
)
_TR68 = (
    '<tr><td>68</td>'
    '<td>Duma Boko</td><td></td><td>UDC</td>'
    '<td></td><td></td><td></td></tr>'
)
_TR69 = (
    '<tr><td>69</td>'
    '<td>Dithapelo Keorapetse</td><td></td><td>Spkr.</td>'
    '<td></td><td></td><td></td></tr>'
)

SAMPLE_HTML_WITH_SPECIAL = f"""
<html><body>
<table class="wikitable">
{_THEAD}
<tbody>
{_TR}
<tr><td colspan="7">Specially-elected MPs</td></tr>
{_TR62}
{_TR63}
<tr><td colspan="7">President</td></tr>
{_TR68}
<tr><td colspan="7">Presiding officer</td></tr>
{_TR69}
</tbody>
</table>
</body></html>
"""

_TR62_5 = '<tr><td>62</td><td>Pius Mokgware</td><td></td><td>UDC</td><td></td></tr>'
_TR63_5 = '<tr><td>63</td><td>Bogolo Kenewendo</td><td></td><td>Ind.</td><td></td></tr>'
_TR68_5 = '<tr><td>68</td><td>Duma Boko</td><td></td><td>UDC</td><td></td></tr>'
_TR69_5 = '<tr><td>69</td><td>Dithapelo Keorapetse</td><td></td><td>Spkr.</td><td></td></tr>'

SAMPLE_HTML_ACTUAL_5COLS = f"""
<html><body>
<table class="wikitable">
{_THEAD}
<tbody>
{_TR}
<tr><th colspan="7">Specially-elected MPs</th></tr>
{_TR62_5}
{_TR63_5}
<tr><th colspan="7">President</th></tr>
{_TR68_5}
<tr><th colspan="7">Presiding officer</th></tr>
{_TR69_5}
</tbody>
</table>
</body></html>
"""


# ---------------------------------------------------------------------------
# Roster
# ---------------------------------------------------------------------------


def _mock_wiki_response(html: str) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.text = html
    mock_resp.raise_for_status.return_value = None
    return mock_resp


class TestFetchRoster:
    def test_fetches_elected_mps(self) -> None:
        with patch('backend.roster.wikipedia.requests.get') as mock_get:
            mock_get.return_value = _mock_wiki_response(SAMPLE_HTML)
            mps = fetch_roster()

        assert len(mps) == 5
        assert mps[0] == {'name': 'Simasiku Mapulanga', 'constituency': 'Chobe', 'party': 'BCP'}
        assert mps[1] == {
            'name': 'Dumelang Saleshando', 'constituency': 'Maun North', 'party': 'BCP',
        }
        assert mps[2] == {
            'name': 'Thabologo Furniture', 'constituency': 'Tati East', 'party': 'BCP',
        }
        assert mps[3] == {'name': 'Victor Phologolo', 'constituency': 'Kanye West', 'party': 'UDC'}

    def test_includes_specially_elected(self) -> None:
        with patch('backend.roster.wikipedia.requests.get') as mock_get:
            mock_get.return_value = _mock_wiki_response(SAMPLE_HTML_WITH_SPECIAL)
            mps = fetch_roster()

        assert len(mps) == 1
        assert mps[0] == {'name': 'Simasiku Mapulanga', 'constituency': 'Chobe', 'party': 'BCP'}

    def test_specially_elected_5cols(self) -> None:
        with patch('backend.roster.wikipedia.requests.get') as mock_get:
            mock_get.return_value = _mock_wiki_response(SAMPLE_HTML_ACTUAL_5COLS)
            mps = fetch_roster()

        assert len(mps) == 5
        assert mps[0] == {'name': 'Simasiku Mapulanga', 'constituency': 'Chobe', 'party': 'BCP'}
        assert mps[1] == {
            'name': 'Pius Mokgware',
            'constituency': 'Specially-elected (Pius Mokgware)',
            'party': 'UDC',
        }
        assert mps[2] == {
            'name': 'Bogolo Kenewendo',
            'constituency': 'Specially-elected (Bogolo Kenewendo)',
            'party': 'Independent',
        }
        assert mps[3] == {'name': 'Duma Boko', 'constituency': 'President', 'party': 'UDC'}
        assert mps[4] == {
            'name': 'Dithapelo Keorapetse', 'constituency': 'Speaker', 'party': 'Speaker',
        }

    def test_no_table_returns_empty(self) -> None:
        with patch('backend.roster.wikipedia.requests.get') as mock_get:
            mock_get.return_value = _mock_wiki_response(
                '<html><body>No table here</body></html>'
            )
            mps = fetch_roster()
        assert mps == []

    def test_skips_empty_rows(self) -> None:
        """Live Wikipedia can emit a trailing <tr> with no cells; it must not crash."""
        html = (
            '<html><body><table class="wikitable">'
            + _THEAD
            + '<tbody>'
            + _TR
            + '<tr></tr>'
            + _TR1
            + '<tr>  </tr>'
            + '</tbody></table></body></html>'
        )
        with patch('backend.roster.wikipedia.requests.get') as mock_get:
            mock_get.return_value = _mock_wiki_response(html)
            mps = fetch_roster()

        assert len(mps) == 2
        assert mps[0]['name'] == 'Simasiku Mapulanga'
        assert mps[1]['name'] == 'Dumelang Saleshando'

    def test_handles_network_error(self) -> None:
        with patch('backend.roster.wikipedia.requests.get') as mock_get:
            mock_get.side_effect = ConnectionError('Network error')
            try:
                fetch_roster()
                assert False, 'Should have raised'
            except ConnectionError:
                pass


class TestStoreRoster:
    def _mock_60_mps(self) -> MagicMock:
        mock_resp = MagicMock()
        mock_resp.text = SIXTY_MP_HTML_BODY
        mock_resp.raise_for_status.return_value = None
        return mock_resp

    def test_stores_mps(self) -> None:
        conn = _in_memory_db()
        with patch('backend.roster.wikipedia.requests.get') as mock_get:
            mock_get.return_value = self._mock_60_mps()
            result = store_roster(conn)

        assert result['total'] == 60
        assert result['inserted'] == 60
        assert result['skipped'] == 0

    def test_store_is_idempotent(self) -> None:
        conn = _in_memory_db()
        with patch('backend.roster.wikipedia.requests.get') as mock_get:
            mock_get.return_value = self._mock_60_mps()
            store_roster(conn)
            result = store_roster(conn)

        assert result['inserted'] == 0
        assert result['skipped'] == 60

    def test_party_mapping(self) -> None:
        assert _clean_wiki_name('Simasiku Mapulanga[1]') == 'Simasiku Mapulanga'
        assert _clean_wiki_name('Name[12][34]') == 'Name'
        assert _clean_wiki_name('Plain Name') == 'Plain Name'


# ---------------------------------------------------------------------------
# Entity Resolution — _normalize_constituency
# ---------------------------------------------------------------------------


class TestNormalizeConstituency:
    def test_lowercases(self) -> None:
        assert _normalize_constituency('Maun North') == 'maun north'

    def test_strips_punctuation(self) -> None:
        assert _normalize_constituency("Moshupa-Manyana") == 'moshupamanyana'

    def test_collapses_whitespace(self) -> None:
        assert _normalize_constituency('  Tati   East  ') == 'tati east'

    def test_empty_string(self) -> None:
        assert _normalize_constituency('') == ''


# ---------------------------------------------------------------------------
# Entity Resolution — _extract_surname
# ---------------------------------------------------------------------------


class TestExtractSurname:
    def test_standard_mp_format(self) -> None:
        assert _extract_surname('MR. S. O. MAPULANGA, MP.') == 'MAPULANGA'

    def test_mixed_case(self) -> None:
        assert _extract_surname('Mr. A. B. Person, MP.') == 'Person'

    def test_no_mp_suffix(self) -> None:
        assert _extract_surname('Dr. K. Gobotswang') == 'Gobotswang'

    def test_single_word_name(self) -> None:
        assert _extract_surname('Dumelang') == 'Dumelang'

    def test_honorific_only(self) -> None:
        assert _extract_surname('HON. C, MP.') == 'C'

    def test_empty_string(self) -> None:
        assert _extract_surname('') == ''


# ---------------------------------------------------------------------------
# Entity Resolution — resolve_contribution
# ---------------------------------------------------------------------------


class TestResolveContribution:
    def test_constituency_first(self) -> None:
        conn = _in_memory_db()
        conn.execute("INSERT INTO mps (name, constituency, party) VALUES (?, ?, ?)",
                     ('Simasiku Mapulanga', 'Chobe', 'BCP'))
        conn.execute("INSERT INTO mps (name, constituency, party) VALUES (?, ?, ?)",
                     ('Thabologo Furniture', 'Tati East', 'BCP'))
        conn.commit()

        mp_id = resolve_contribution(
            conn.cursor(),
            'MR. S. O. MAPULANGA, MP.',
            'Chobe',
        )
        assert mp_id == 1

    def test_surname_fallback(self) -> None:
        conn = _in_memory_db()
        conn.execute("INSERT INTO mps (name, constituency, party) VALUES (?, ?, ?)",
                     ('Simasiku Mapulanga', 'Chobe', 'BCP'))
        conn.execute("INSERT INTO mps (name, constituency, party) VALUES (?, ?, ?)",
                     ('Thabologo Furniture', 'Tati East', 'BCP'))
        conn.commit()

        mp_id = resolve_contribution(
            conn.cursor(),
            'MR. S. O. MAPULANGA, MP.',
            None,
        )
        assert mp_id == 1

    def test_surname_fallback_no_constituency(self) -> None:
        conn = _in_memory_db()
        conn.execute("INSERT INTO mps (name, constituency, party) VALUES (?, ?, ?)",
                     ('Simasiku Mapulanga', 'Chobe', 'BCP'))
        conn.commit()

        mp_id = resolve_contribution(
            conn.cursor(),
            'Mr. S. O. Mapulanga',
            '',
        )
        assert mp_id == 1

    def test_surname_fallback_mixed_case(self) -> None:
        conn = _in_memory_db()
        conn.execute("INSERT INTO mps (name, constituency, party) VALUES (?, ?, ?)",
                     ('Thabologo Furniture', 'Tati East', 'BCP'))
        conn.commit()

        mp_id = resolve_contribution(
            conn.cursor(),
            'MR. T. FURNITURE, MP.',
            None,
        )
        assert mp_id == 1

    def test_no_match_returns_none(self) -> None:
        conn = _in_memory_db()
        conn.execute("INSERT INTO mps (name, constituency, party) VALUES (?, ?, ?)",
                     ('Simasiku Mapulanga', 'Chobe', 'BCP'))
        conn.commit()

        mp_id = resolve_contribution(
            conn.cursor(),
            'MR. Z. ZEBRA, MP.',
            None,
        )
        assert mp_id is None


class TestResolveContributionScalable:
    def test_uses_prebuilt_maps(self) -> None:
        conn = _in_memory_db()
        conn.execute("INSERT INTO mps (name, constituency, party) VALUES (?, ?, ?)",
                     ('Simasiku Mapulanga', 'Chobe', 'BCP'))
        conn.execute("INSERT INTO mps (name, constituency, party) VALUES (?, ?, ?)",
                     ('Thabologo Furniture', 'Tati East', 'BCP'))
        conn.commit()

        cursor = conn.cursor()

        cmap = _build_constituency_map(cursor)
        smap = _build_token_map(cursor)

        got = resolve_contribution_scalable(
            cursor, 'MR. S. O. MAPULANGA, MP.', 'Chobe', cmap, smap,
        )
        assert got == 1

        got = resolve_contribution_scalable(
            cursor, 'MR. T. FURNITURE, MP.', None, cmap, smap,
        )
        assert got == 2

        got = resolve_contribution_scalable(
            cursor, 'MR. Z. ZEBRA, MP.', None, cmap, smap,
        )
        assert got is None


# ---------------------------------------------------------------------------
# Resolve run.py
# ---------------------------------------------------------------------------


class TestResolveAll:
    def test_resolves_unresolved_entities(self) -> None:
        conn = _in_memory_db()

        conn.execute(
            "INSERT INTO documents (id, title, doc_type, file_path, source_url) "
            "VALUES (?, ?, ?, ?, ?)",
            (1, 'Test', 'notice_paper', '/fake.pdf', 'https://x.com'),
        )
        conn.execute(
            "INSERT INTO contributions (id, document_id, contribution_type, subject_text, "
            "date, raw_match_name, raw_constituency, source_url) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (1, 1, 'question', 'Subject?', '2026-07-24', 'MR. S. O. MAPULANGA, MP.', 'Chobe', ''),
        )
        conn.execute(
            "INSERT INTO contributions (id, document_id, contribution_type, subject_text, "
            "date, raw_match_name, raw_constituency, source_url) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (2, 1, 'motion', 'Motion subject', '2026-07-24', 'MR. Z. ZEBRA, MP.', 'Nowhere', ''),
        )
        conn.execute(
            "INSERT INTO contributions (id, document_id, contribution_type, subject_text, "
            "date, raw_match_name, raw_constituency, source_url) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                3, 1, 'question', 'Same speaker?', '2026-07-24',
                'MR. S. O. MAPULANGA, MP.', 'Chobe', '',
            ),
        )
        conn.execute(
            "INSERT INTO mps (name, constituency, party) VALUES (?, ?, ?)",
            ('Simasiku Mapulanga', 'Chobe', 'BCP'),
        )

        conn.execute(
            "INSERT INTO entity_review_queue (raw_match_name, contribution_id, status) "
            "VALUES (?, ?, 'UNRESOLVED')",
            ('MR. S. O. MAPULANGA, MP.', 1),
        )
        conn.execute(
            "INSERT INTO entity_review_queue (raw_match_name, contribution_id, status) "
            "VALUES (?, ?, 'UNRESOLVED')",
            ('MR. Z. ZEBRA, MP.', 2),
        )
        conn.commit()

        result = resolve_all(conn)

        assert result['total'] == 2
        assert result['resolved'] == 1
        assert result['unresolved'] == 1
        assert 49.0 < result['rate'] < 51.0

        mp_id = conn.execute("SELECT mp_id FROM contributions WHERE id=1").fetchone()[0]
        assert mp_id == 1

        mp_id = conn.execute("SELECT mp_id FROM contributions WHERE id=2").fetchone()[0]
        assert mp_id is None

        mp_id_3 = conn.execute("SELECT mp_id FROM contributions WHERE id=3").fetchone()[0]
        assert mp_id_3 is None

    def test_no_unresolved(self) -> None:
        conn = _in_memory_db()
        result = resolve_all(conn)
        assert result['total'] == 0
        assert result['resolved'] == 0
        assert result['rate'] == 0.0

    def test_ministry_fallback(self) -> None:
        conn = _in_memory_db()
        conn.execute(
            "INSERT INTO mps (id, name, constituency, party) VALUES (?, ?, ?, ?)",
            (1, 'Tina Finance', 'City Centre', 'BDP'),
        )
        conn.execute(
            "INSERT INTO ministry_mapping (normalized_title, mp_id) "
            "VALUES (?, ?)",
            ('minister of finance', 1),
        )
        conn.execute(
            "INSERT INTO documents (id, title, doc_type, file_path, source_url) "
            "VALUES (?, ?, ?, ?, ?)",
            (1, 'Test', 'notice_paper', '/fake.pdf', 'https://x.com'),
        )
        conn.execute(
            "INSERT INTO contributions (id, document_id, contribution_type, "
            "subject_text, date, raw_match_name, raw_constituency, source_url) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (1, 1, 'bill', 'Appropriation Bill', '2026-07-24',
             'Minister of Finance', '', ''),
        )
        conn.execute(
            "INSERT INTO entity_review_queue (raw_match_name, contribution_id, status) "
            "VALUES (?, ?, 'UNRESOLVED')",
            ('Minister of Finance', 1),
        )
        conn.commit()

        result = resolve_all(conn)

        assert result['total'] == 1
        assert result['resolved'] == 1
        assert result['rate'] == 100.0
        mp_id = conn.execute("SELECT mp_id FROM contributions WHERE id=1").fetchone()[0]
        assert mp_id == 1
