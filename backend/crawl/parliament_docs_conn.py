"""Parliament of Botswana document connector.

Fetches Order Paper and Notice Paper PDFs from parliament.gov.bw. Order Paper
PDFs also carry the bill and motion listings for a sitting, so this one
category covers PLAN.md 1.8's "order papers, bills, and motions" objective
without a separate category (there is no distinct Bills or Motions listing
on the site).
"""

import hashlib
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from backend.crawl import register
from backend.db.connection import get_connection

BASE_URL = 'https://www.parliament.gov.bw'
PDF_DIR = Path(__file__).resolve().parent.parent.parent / 'data' / 'pdfs'
SHORT_YEAR_CENTURY_PREFIX = '20'
MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024

HEADERS = {
    'User-Agent': 'BaReng/0.1 (Botswana Parliament MP Monitor; research)',
}

# (source name, doc_type, catid, itemid) - discovered from the site's own
# category nav (index.php?option=com_documents&view=categories). Order Paper
# PDFs carry the bill/motion listings for a sitting; there is no separate
# Bills or Motions category on the site.
CATEGORIES = (
    ('parliament_order_paper', 'order_paper', 85, 433),
    ('parliament_notice_paper', 'notice_paper', 86, 578),
)


def _parse_pdf_date(title: str) -> str:
    """Parse a document date out of a PDF title/filename.

    Filenames embed a DD-MM-YY upload timestamp and a DD-MM-YYYY document
    date (e.g. "...24_07_26_01_43_20_24_07_2026"); the full 4-digit year
    match is preferred since it is the more reliable of the two.
    """
    full_year = re.search(r'(\d{1,2})[-_\s](\d{1,2})[-_\s](\d{4})\b', title)
    m = full_year or re.search(r'(\d{1,2})[-_\s](\d{1,2})[-_\s](\d{2})\b', title)
    if not m:
        return ''
    day, month, year = m.group(1), m.group(2), m.group(3)
    if len(year) == len(SHORT_YEAR_CENTURY_PREFIX):
        year = f'{SHORT_YEAR_CENTURY_PREFIX}{year}'
    try:
        parsed = datetime(year=int(year), month=int(month), day=int(day))
    except ValueError:
        return ''
    return parsed.strftime('%Y-%m-%d')


def _fetch_page(catid: int, offset: int = 0, limit: int = 100) -> str:
    url = (
        f'{BASE_URL}/index.php?option=com_documents&view=files'
        f'&catid={catid}&limitstart={offset}&limit={limit}'
    )
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def _extract_pdf_links(html: str) -> list[tuple[str, str]]:
    """Parse (pdf_url, title) pairs from a listing page."""
    soup = BeautifulSoup(html, 'html.parser')
    pdf_links: list[tuple[str, str]] = []

    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        if not href.lower().endswith('.pdf'):
            continue

        full_url = href if href.startswith('http') else f'{BASE_URL}{href}'
        title = a.get_text(strip=True) or Path(href).stem.replace('-', ' ').replace('_', ' ')
        pdf_links.append((full_url, title))

    return pdf_links


def _count_total_pages(html: str) -> int:
    soup = BeautifulSoup(html, 'html.parser')
    pagination = soup.find('ul', class_='pagination')
    if not pagination:
        return 1
    nums = [int(li.get_text(strip=True)) for li in pagination.find_all('li')
            if li.get_text(strip=True).isdigit()]
    return max(nums) if nums else 1


def _dedupe_by_url(pdf_links: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Drop duplicate PDF URLs within one crawl run.

    Joomla listing rows commonly render two anchors (title + download icon)
    pointing at the same PDF; without this, the same URL/content hash can be
    processed twice within one run, colliding with the UNIQUE raw_text_hash
    constraint on a row this same run already inserted.
    """
    seen: set[str] = set()
    deduped: list[tuple[str, str]] = []
    for url, title in pdf_links:
        if url in seen:
            continue
        seen.add(url)
        deduped.append((url, title))
    return deduped


def _fetch_all_listings(catid: int, max_documents: int | None) -> list[tuple[str, str]]:
    html = _fetch_page(catid, 0, 100)
    total_pages = _count_total_pages(html)
    pdf_links = _extract_pdf_links(html)

    for page in range(1, total_pages):
        if max_documents is not None and len(pdf_links) >= max_documents:
            break
        try:
            page_html = _fetch_page(catid, page * 100, 100)
        except requests.RequestException:
            continue
        pdf_links.extend(_extract_pdf_links(page_html))

    return _dedupe_by_url(pdf_links)


def _download_pdf(pdf_url: str) -> bytes | None:
    try:
        r = requests.get(pdf_url, headers=HEADERS, timeout=60)
        r.raise_for_status()
    except requests.RequestException:
        return None
    content_type = r.headers.get('Content-Type', '')
    if 'application/pdf' not in content_type:
        return None
    if len(r.content) > MAX_DOWNLOAD_BYTES:
        return None
    return r.content


def _download_new_documents(
    cursor: sqlite3.Cursor,
    source: str,
    doc_type: str,
    pdf_links: list[tuple[str, str]],
) -> tuple[int, int, int]:
    new_count = 0
    skipped_count = 0
    error_count = 0

    for pdf_url, title in pdf_links:
        pdf_bytes = _download_pdf(pdf_url)
        if pdf_bytes is None:
            error_count += 1
            continue

        content_hash = hashlib.sha256(pdf_bytes).hexdigest()

        existing = cursor.execute(
            'SELECT id FROM documents WHERE raw_text_hash = ?', (content_hash,),
        ).fetchone()
        if existing:
            skipped_count += 1
            continue

        date_str = _parse_pdf_date(title)
        filename = f'{source}_{content_hash[:12]}.pdf'
        file_path = PDF_DIR / filename

        try:
            file_path.write_bytes(pdf_bytes)
            cursor.execute(
                'INSERT INTO documents '
                '(title, doc_type, file_path, source_url, raw_text_hash, published_date) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                (title, doc_type, str(file_path), pdf_url, content_hash, date_str),
            )
        except (OSError, sqlite3.Error):
            error_count += 1
            continue

        new_count += 1

    return new_count, skipped_count, error_count


def _crawl_category(
    conn: sqlite3.Connection,
    source: str,
    doc_type: str,
    catid: int,
    max_documents: int | None,
) -> dict:
    cursor = conn.cursor()

    try:
        pdf_links = _fetch_all_listings(catid, max_documents)
    except requests.RequestException as e:
        return {'source': source, 'status': 'FAILED', 'error': str(e),
                'new_documents': 0, 'skipped': 0, 'errors': 0}

    if max_documents is not None:
        pdf_links = pdf_links[:max_documents]

    new_count, skipped_count, error_count = _download_new_documents(
        cursor, source, doc_type, pdf_links,
    )
    conn.commit()

    return {
        'source': source,
        'status': 'SUCCESS',
        'new_documents': new_count,
        'skipped': skipped_count,
        'errors': error_count,
        'total_listed': len(pdf_links),
    }


def crawl(
    conn: sqlite3.Connection | None = None,
    max_documents_per_category: int | None = None,
) -> dict:
    """Fetch Order Paper and Notice Paper listings from parliament.gov.bw.

    Downloads new PDFs, hash-deduped against `documents.raw_text_hash`.
    """
    close_conn = conn is None
    if conn is None:
        conn = get_connection()

    PDF_DIR.mkdir(parents=True, exist_ok=True)
    cursor = conn.cursor()

    results: dict[str, dict] = {}
    for source, doc_type, catid, _itemid in CATEGORIES:
        result = _crawl_category(conn, source, doc_type, catid, max_documents_per_category)
        results[source] = result

        cursor.execute(
            'INSERT INTO crawl_runs '
            '(source, status, new_documents, errors, started_at, finished_at) '
            "VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))",
            (
                source,
                result['status'],
                result['new_documents'],
                result['errors'] if result['status'] == 'SUCCESS' else 1,
            ),
        )
        conn.commit()

    if close_conn:
        conn.close()

    all_succeeded = all(r['status'] == 'SUCCESS' for r in results.values())
    return {
        'source': 'parliament_docs',
        'status': 'SUCCESS' if all_succeeded else 'PARTIAL',
        'categories': results,
    }


register('parliament_docs_conn')
