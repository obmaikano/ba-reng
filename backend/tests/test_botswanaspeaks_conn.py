"""Tests for the Botswana Speaks crawl connector."""

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests
from bs4 import BeautifulSoup

from backend.crawl import REGISTRY
from backend.crawl.botswanaspeaks_conn import (
    compute_hash,
    crawl,
    download_pdf,
    fetch_article_links,
    get_pdf_links,
    infer_doc_type,
    parse_date_from_article,
)

SAMPLE_LISTING_HTML = """
<html><body>
<article>
  <div class="post-date"><span class="day">23 Jul</span><span class="month">2026</span></div>
  <h2><a href="/article/396/notice-paper">NOTICE PAPER (FOR FRIDAY 24 JULY, 2026)</a></h2>
</article>
<article>
  <div class="post-date"><span class="day">23 Jul</span><span class="month">2026</span></div>
  <h2><a href="/article/395/order-paper">ORDER PAPER (THURSDAY 23 JULY 2026)</a></h2>
</article>
</body></html>
"""

SAMPLE_ARTICLE_HTML = """
<html><body>
<h1>NOTICE PAPER (FOR FRIDAY 24 JULY, 2026)</h1>
<div class="post-date"><span class="day">24 Jul</span><span class="month">2026</span></div>
File: <a href="/media/NOTPAP-24-07-26.pdf">NOTPAP-24-07-26.pdf</a>
</body></html>
"""


class TestInferDocType:
    def test_notice_paper(self) -> None:
        assert infer_doc_type('NOTICE PAPER (FOR FRIDAY 24 JULY)') == 'notice_paper'

    def test_order_paper(self) -> None:
        assert infer_doc_type('ORDER PAPER (THURSDAY 23 JULY)') == 'order_paper'

    def test_bill(self) -> None:
        assert infer_doc_type('Tax Administration Bill, 2025') == 'bill'

    def test_motion(self) -> None:
        assert infer_doc_type('NOTPAP - MOTIONS - 24-07-26') == 'motion'

    def test_other(self) -> None:
        assert infer_doc_type('Some random document') == 'other'

    @staticmethod
    def _bold_unicode(text: str) -> str:
        """Map ASCII letters/digits to their mathematical bold forms."""
        out: list[str] = []
        for ch in text:
            if 'A' <= ch <= 'Z':
                out.append(chr(ord(ch) - ord('A') + 0x1D400))
            elif '0' <= ch <= '9':
                out.append(chr(ord(ch) - ord('0') + 0x1D7CE))
            else:
                out.append(ch)
        return ''.join(out)

    def test_bold_unicode_order_paper(self) -> None:
        title = self._bold_unicode(
            'BOTSWANA NATIONAL ASSEMBLY ORDER PAPER (THURSDAY 24TH JULY, 2026)',
        )
        assert infer_doc_type(title) == 'order_paper'

    def test_spaced_letters_order_paper(self) -> None:
        title = 'BOTSWANA NATIONAL ASSEMBLY O R D E R P A P E R (TUESDAY 14TH APRIL)'
        assert infer_doc_type(title) == 'order_paper'

    def test_spaced_letters_addendum_notice_paper(self) -> None:
        title = 'A D D E N D U M BOTSWANA NATIONAL ASSEMBLY N O T I C E P A P E R (THURSDAY)'
        assert infer_doc_type(title) == 'notice_paper'

    def test_order_paper_addendum(self) -> None:
        assert infer_doc_type('ORDER PAPER-ADDENDUM (MONDAY 27TH JULY, 2026)') == 'order_paper'

    def test_notice_of_tabling(self) -> None:
        title = 'NOTICE OF TABLING OF A PAPER (FOR TUESDAY 14TH APRIL, 2026)'
        assert infer_doc_type(title) == 'notice_paper'

    def test_notice_of_questions(self) -> None:
        title = 'NOTICE OF QUESTIONS (FOR ORAL ANSWER ON MONDAY 13TH APRIL, 2026)'
        assert infer_doc_type(title) == 'notice_paper'

    def test_ministerial_status_update(self) -> None:
        title = ('MINISTRY OF MINERALS AND ENERGY FUEL SUPPLY STATUS UPDATE BY '
                 'HONOURABLE MINISTER')
        assert infer_doc_type(title) == 'ministerial_statement'


class TestParseDateFromArticle:
    def test_valid_date(self) -> None:
        soup = BeautifulSoup(SAMPLE_ARTICLE_HTML, 'html.parser')
        assert parse_date_from_article(soup) == '2026-07-24'

    def test_no_date(self) -> None:
        soup = BeautifulSoup('<html></html>', 'html.parser')
        assert parse_date_from_article(soup) is None


class TestGetPdfLinks:
    def test_finds_pdf_links(self) -> None:
        soup = BeautifulSoup(SAMPLE_ARTICLE_HTML, 'html.parser')
        links = get_pdf_links(soup)
        assert len(links) == 1
        assert links[0].endswith('/media/NOTPAP-24-07-26.pdf')

    def test_no_pdf_links(self) -> None:
        soup = BeautifulSoup('<html><a href="/about">About</a></html>', 'html.parser')
        assert get_pdf_links(soup) == []


class TestFetchArticleLinks:
    def test_fetches_article_links(self) -> None:
        soup = BeautifulSoup(SAMPLE_LISTING_HTML, 'html.parser')
        links = fetch_article_links(soup)
        assert len(links) == 2
        assert links[0] == '/article/396/notice-paper'

    def test_deduplicates(self) -> None:
        html = SAMPLE_LISTING_HTML + (
            '<article><a href="/article/396/notice-paper">Duplicate</a></article>'
        )
        soup = BeautifulSoup(html, 'html.parser')
        links = fetch_article_links(soup)
        assert len(links) == 2


class TestComputeHash:
    def test_sha256_hash(self) -> None:
        content = b'test pdf content'
        expected = 'd2524f66e1af3706b65c13e8d1dc70366f68b2ff7d02a8004e20981fad902e6f'
        assert compute_hash(content) == expected


class TestCrawlRegistry:
    def test_connector_is_registered(self) -> None:
        assert 'botswanaspeaks_conn' in REGISTRY


class TestCrawlIntegration:
    @patch('backend.crawl.botswanaspeaks_conn.requests')
    def test_crawl_success(self, mock_requests: MagicMock) -> None:
        mock_listing_resp = MagicMock()
        mock_listing_resp.text = SAMPLE_LISTING_HTML
        mock_listing_resp.raise_for_status = MagicMock()

        mock_article_resp = MagicMock()
        mock_article_resp.text = SAMPLE_ARTICLE_HTML
        mock_article_resp.raise_for_status = MagicMock()

        mock_requests.get.side_effect = [
            mock_listing_resp,
            mock_article_resp,
            mock_article_resp,
        ]

        conn = sqlite3.connect(':memory:')
        conn.execute('PRAGMA foreign_keys=ON')
        conn.row_factory = sqlite3.Row
        schema_path = (
            Path(__file__).resolve().parent.parent.parent
            / 'backend' / 'db' / 'migrations' / '001_initial.sql'
        )
        conn.executescript(schema_path.read_text())

        with (
            patch(
                'backend.crawl.botswanaspeaks_conn.download_pdf',
                return_value=b'fake pdf content',
            ),
            patch('backend.crawl.botswanaspeaks_conn.Path.write_bytes'),
            patch('backend.crawl.botswanaspeaks_conn.Path.mkdir'),
        ):
            result = crawl(conn)

        assert result['status'] == 'SUCCESS'


class TestDownloadPdf:
    @patch('backend.crawl.botswanaspeaks_conn.requests.get')
    def test_download_success(self, mock_get: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.content = b'pdf data'
        mock_resp.headers = {'Content-Type': 'application/pdf'}
        mock_get.return_value = mock_resp

        result = download_pdf('https://example.com/test.pdf')
        assert result == b'pdf data'

    @patch('backend.crawl.botswanaspeaks_conn.requests.get')
    def test_download_failure(self, mock_get: MagicMock) -> None:
        mock_get.side_effect = requests.RequestException('Connection error')
        result = download_pdf('https://example.com/test.pdf')
        assert result is None

    @patch('backend.crawl.botswanaspeaks_conn.requests.get')
    def test_rejects_wrong_content_type(self, mock_get: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.content = b'<html>fake</html>'
        mock_resp.headers = {'Content-Type': 'text/html'}
        mock_get.return_value = mock_resp

        result = download_pdf('https://example.com/not-a-pdf')
        assert result is None

    @patch('backend.crawl.botswanaspeaks_conn.requests.get')
    def test_rejects_oversized(self, mock_get: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.content = b'x' * (50 * 1024 * 1024 + 1)
        mock_resp.headers = {'Content-Type': 'application/pdf'}
        mock_get.return_value = mock_resp

        result = download_pdf('https://example.com/huge.pdf')
        assert result is None
