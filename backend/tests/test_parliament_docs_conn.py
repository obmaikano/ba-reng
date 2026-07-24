"""Tests for the parliament.gov.bw Order Paper / Notice Paper connector."""

import hashlib
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

from backend.crawl import REGISTRY
from backend.crawl.parliament_docs_conn import (
    _count_total_pages,
    _extract_pdf_links,
    _parse_pdf_date,
    crawl,
)
from backend.db.connection import _sha256_hex

MIGRATIONS_DIR = (
    Path(__file__).resolve().parent.parent.parent / 'backend' / 'db' / 'migrations'
)
SCHEMA_SQL = ''.join(p.read_text() for p in sorted(MIGRATIONS_DIR.glob('*.sql')))


def _in_memory_db() -> sqlite3.Connection:
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.create_function('SHA256_HEX', 1, _sha256_hex, deterministic=True)
    conn.executescript(SCHEMA_SQL)
    return conn


LISTING_HTML = """
<html><body>
<table>
<tr><td>ORDPAP</td><td><a href="/documents/ORDPAP---24-07-26_01_43_20_24_07_2026.pdf">
Order Paper 24 07 2026</a></td></tr>
</table>
</body></html>
"""

PAGINATED_HTML = LISTING_HTML.replace(
    '</body>', '<ul class="pagination"><li>1</li><li>2</li></ul></body>',
)


class TestParsePdfDate:
    def test_prefers_full_four_digit_year(self) -> None:
        assert _parse_pdf_date('ORDPAP 02 09 24 02 40 05 01 09 2024') == '2024-09-01'

    def test_handles_hyphen_separated_title(self) -> None:
        assert _parse_pdf_date('ORDPAP---24-07-26_01_43_20_24_07_2026') == '2026-07-24'

    def test_returns_empty_string_when_no_date_found(self) -> None:
        assert _parse_pdf_date('no date here') == ''


class TestExtractPdfLinks:
    def test_extracts_url_and_title(self) -> None:
        links = _extract_pdf_links(LISTING_HTML)
        assert len(links) == 1
        url, title = links[0]
        assert url == 'https://www.parliament.gov.bw/documents/ORDPAP---24-07-26_01_43_20_24_07_2026.pdf'
        assert title == 'Order Paper 24 07 2026'

    def test_ignores_non_pdf_links(self) -> None:
        html = '<a href="/documents/notes.txt">Notes</a>'
        assert _extract_pdf_links(html) == []


class TestCountTotalPages:
    def test_no_pagination_returns_one(self) -> None:
        assert _count_total_pages(LISTING_HTML) == 1

    def test_reads_max_page_number(self) -> None:
        assert _count_total_pages(PAGINATED_HTML) == 2


class TestCrawl:
    def test_downloads_and_inserts_new_documents(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr('backend.crawl.parliament_docs_conn.PDF_DIR', tmp_path)

        conn = _in_memory_db()

        def _listing_html_for(catid_marker: str) -> str:
            return LISTING_HTML.replace(
                'ORDPAP---24-07-26_01_43_20_24_07_2026.pdf',
                f'{catid_marker}_24-07-26_01_43_20_24_07_2026.pdf',
            )

        def fake_get(url: str, **kwargs):
            if url.endswith('.pdf'):
                pdf_resp = MagicMock(
                    content=f'%PDF-1.4 {url}'.encode(),
                    headers={'Content-Type': 'application/pdf'},
                )
                pdf_resp.raise_for_status = MagicMock()
                return pdf_resp
            catid_marker = 'ORDPAP' if 'catid=85' in url else 'NOTPAP'
            listing_resp = MagicMock(text=_listing_html_for(catid_marker))
            listing_resp.raise_for_status = MagicMock()
            return listing_resp

        with patch('backend.crawl.parliament_docs_conn.requests.get', side_effect=fake_get):
            result = crawl(conn=conn)

        assert result['status'] == 'SUCCESS'
        assert result['categories']['parliament_order_paper']['new_documents'] == 1
        assert result['categories']['parliament_notice_paper']['new_documents'] == 1

        documents = conn.execute(
            'SELECT doc_type, published_date, file_path, source_url FROM documents ORDER BY id',
        ).fetchall()
        assert len(documents) == 2
        assert {d['doc_type'] for d in documents} == {'order_paper', 'notice_paper'}
        for doc in documents:
            assert doc['published_date'] == '2026-07-24'
            assert Path(doc['file_path']).exists()
            assert doc['source_url'].startswith('https://www.parliament.gov.bw/documents/')

        crawl_runs = conn.execute(
            'SELECT source, status, new_documents FROM crawl_runs ORDER BY id',
        ).fetchall()
        assert len(crawl_runs) == 2
        assert {r['source'] for r in crawl_runs} == {
            'parliament_order_paper', 'parliament_notice_paper',
        }
        assert all(r['status'] == 'SUCCESS' for r in crawl_runs)

    def test_dedups_against_existing_hash(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr('backend.crawl.parliament_docs_conn.PDF_DIR', tmp_path)

        conn = _in_memory_db()
        content_hash = hashlib.sha256(b'%PDF-1.4 fake content').hexdigest()
        conn.execute(
            """INSERT INTO documents (title, doc_type, source_url, raw_text_hash)
               VALUES ('existing', 'order_paper', 'https://x.com/existing.pdf', ?)""",
            (content_hash,),
        )
        conn.commit()

        mock_listing_resp = MagicMock(text=LISTING_HTML)
        mock_listing_resp.raise_for_status = MagicMock()

        mock_pdf_resp = MagicMock(
            content=b'%PDF-1.4 fake content',
            headers={'Content-Type': 'application/pdf'},
        )
        mock_pdf_resp.raise_for_status = MagicMock()

        def fake_get(url: str, **kwargs):
            if url.endswith('.pdf'):
                return mock_pdf_resp
            return mock_listing_resp

        with patch('backend.crawl.parliament_docs_conn.requests.get', side_effect=fake_get):
            result = crawl(conn=conn)

        assert result['categories']['parliament_order_paper']['skipped'] == 1
        assert result['categories']['parliament_order_paper']['new_documents'] == 0

    def test_dedupes_duplicate_pdf_url_within_same_listing_page(
        self, tmp_path, monkeypatch,
    ) -> None:
        """Joomla listing rows can render two anchors (title + download icon)
        pointing at the same PDF URL. Without intra-run dedup, the second
        occurrence would try to INSERT a row with a raw_text_hash the first
        occurrence already committed, raising sqlite3.IntegrityError."""
        monkeypatch.setattr('backend.crawl.parliament_docs_conn.PDF_DIR', tmp_path)

        duplicate_html = (
            '<html><body><table>'
            '<tr><td><a href="/documents/ORDPAP-24-07-26.pdf">Order Paper</a>'
            '<a href="/documents/ORDPAP-24-07-26.pdf">(download)</a></td></tr>'
            '</table></body></html>'
        )

        conn = _in_memory_db()

        mock_listing_resp = MagicMock(text=duplicate_html)
        mock_listing_resp.raise_for_status = MagicMock()

        mock_pdf_resp = MagicMock(
            content=b'%PDF-1.4 fake content',
            headers={'Content-Type': 'application/pdf'},
        )
        mock_pdf_resp.raise_for_status = MagicMock()

        def fake_get(url: str, **kwargs):
            if url.endswith('.pdf'):
                return mock_pdf_resp
            return mock_listing_resp

        with patch('backend.crawl.parliament_docs_conn.requests.get', side_effect=fake_get):
            result = crawl(conn=conn)

        assert result['status'] == 'SUCCESS'
        assert result['categories']['parliament_order_paper']['new_documents'] == 1
        assert result['categories']['parliament_order_paper']['total_listed'] == 1

    def test_per_document_download_failure_is_counted_and_run_continues(
        self, tmp_path, monkeypatch,
    ) -> None:
        monkeypatch.setattr('backend.crawl.parliament_docs_conn.PDF_DIR', tmp_path)

        conn = _in_memory_db()

        mock_listing_resp = MagicMock(text=LISTING_HTML)
        mock_listing_resp.raise_for_status = MagicMock()

        def fake_get(url: str, **kwargs):
            if url.endswith('.pdf'):
                raise requests.exceptions.ConnectionError('pdf host unreachable')
            return mock_listing_resp

        with patch('backend.crawl.parliament_docs_conn.requests.get', side_effect=fake_get):
            result = crawl(conn=conn)

        assert result['status'] == 'SUCCESS'
        assert result['categories']['parliament_order_paper']['new_documents'] == 0
        assert result['categories']['parliament_order_paper']['errors'] == 1

        crawl_runs = conn.execute(
            "SELECT errors FROM crawl_runs WHERE source = 'parliament_order_paper'",
        ).fetchone()
        assert crawl_runs['errors'] == 1

    def test_category_failure_reported_as_failed_status(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr('backend.crawl.parliament_docs_conn.PDF_DIR', tmp_path)

        conn = _in_memory_db()

        with patch(
            'backend.crawl.parliament_docs_conn.requests.get',
            side_effect=requests.exceptions.ConnectionError('unreachable'),
        ):
            result = crawl(conn=conn)

        assert result['status'] == 'PARTIAL'
        for category_result in result['categories'].values():
            assert category_result['status'] == 'FAILED'


def test_registers_in_crawl_registry() -> None:
    assert 'parliament_docs_conn' in REGISTRY
