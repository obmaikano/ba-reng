"""Botswana Speaks connector — fetches listing pages and downloads new PDFs."""

import hashlib
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from backend.crawl import register
from backend.db.connection import get_connection

BASE_URL = 'https://botswanaspeaks.gov.bw'
LISTING_URL = f'{BASE_URL}/category/4/parliament'
PDF_DIR = Path(__file__).resolve().parent.parent.parent / 'data' / 'pdfs'

HEADERS = {
    'User-Agent': 'BaReng/0.1 (Botswana Parliament MP Monitor; research)',
}

DOC_TYPE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r'notice\s*paper', re.IGNORECASE), 'notice_paper'),
    (re.compile(r'order\s*paper', re.IGNORECASE), 'order_paper'),
    (re.compile(r'\bbill\b', re.IGNORECASE), 'bill'),
    (re.compile(r'motion', re.IGNORECASE), 'motion'),
    (re.compile(r'committee\s*of\s*supply', re.IGNORECASE), 'committee_of_supply'),
    (re.compile(r'hansard', re.IGNORECASE), 'hansard'),
    (re.compile(r'addendum', re.IGNORECASE), 'addendum'),
    (re.compile(r'corrigendum', re.IGNORECASE), 'corrigendum'),
]


def infer_doc_type(title: str) -> str:
    """Map a document title to a normalized doc_type."""
    for pattern, doc_type in DOC_TYPE_PATTERNS:
        if pattern.search(title):
            return doc_type
    return 'other'


def parse_date_from_article(soup: BeautifulSoup) -> str | None:
    """Extract published date from article page HTML."""
    date_el = soup.select_one('.post-date .day')
    month_el = soup.select_one('.post-date .month')
    if date_el and month_el:
        try:
            day = date_el.get_text(strip=True)
            month_year = month_el.get_text(strip=True)
            dt = datetime.strptime(f'{day} {month_year}', '%d %b %Y')
            return dt.strftime('%Y-%m-%d')
        except (ValueError, IndexError):
            pass
    return None


def get_pdf_links(soup: BeautifulSoup) -> list[str]:
    """Extract PDF download URLs from an article page."""
    links: list[str] = []
    for a in soup.select('a[href]'):
        href = a['href']
        if href.lower().endswith('.pdf'):
            if href.startswith('/'):
                links.append(BASE_URL + href)
            elif href.startswith('http'):
                links.append(href)
    return links


def fetch_article_links(
    listing_soup: BeautifulSoup,
) -> list[tuple[str, str]]:
    """Extract article URLs and titles from the category listing page."""
    articles: list[tuple[str, str]] = []
    seen = set()
    for a in listing_soup.select('article a[href]'):
        href = a['href']
        if href.startswith('/article/') and href not in seen:
            seen.add(href)
            articles.append((href, a.get_text(strip=True)))
    return articles


def download_pdf(pdf_url: str) -> bytes | None:
    """Download a PDF from the given URL and return its raw bytes."""
    try:
        resp = requests.get(pdf_url, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        return resp.content
    except requests.RequestException:
        return None


def compute_hash(content: bytes) -> str:
    """Compute SHA-256 hex digest of byte content."""
    return hashlib.sha256(content).hexdigest()


def crawl(conn: sqlite3.Connection | None = None) -> dict:
    """Run the Botswana Speaks crawl: fetch listing, download new PDFs."""
    close_conn = conn is None
    if conn is None:
        conn = get_connection()

    cursor = conn.cursor()
    crawl_id = _start_run(cursor, 'botswanaspeaks.gov.bw')

    try:
        listing_resp = requests.get(LISTING_URL, headers=HEADERS, timeout=60)
        listing_resp.raise_for_status()
    except requests.RequestException as exc:
        _finish_run(cursor, crawl_id, 'ERROR', errors=1)
        if close_conn:
            conn.close()
        return {'status': 'ERROR', 'error': str(exc), 'new_documents': 0}

    listing_soup = BeautifulSoup(listing_resp.text, 'html.parser')
    article_links = fetch_article_links(listing_soup)

    new_count = 0
    error_count = 0
    skip_count = 0
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    for rel_path, _ in article_links:
        try:
            article_url = BASE_URL + rel_path

            article_resp = requests.get(article_url, headers=HEADERS, timeout=60)
            article_resp.raise_for_status()
            article_soup = BeautifulSoup(article_resp.text, 'html.parser')

            title_tag = article_soup.select_one('h1')
            title = title_tag.get_text(strip=True) if title_tag else 'Untitled'
            published_date = parse_date_from_article(article_soup)

            pdf_urls = get_pdf_links(article_soup)
            if not pdf_urls:
                skip_count += 1
                continue

            pdf_url = pdf_urls[0]
            pdf_content = download_pdf(pdf_url)
            if pdf_content is None:
                error_count += 1
                continue

            content_hash = compute_hash(pdf_content)

            existing = cursor.execute(
                'SELECT id FROM documents WHERE raw_text_hash = ?',
                (content_hash,),
            ).fetchone()
            if existing is not None:
                skip_count += 1
                continue

            doc_type = infer_doc_type(title)
            pdf_filename = f'{content_hash[:16]}.pdf'
            pdf_path = PDF_DIR / pdf_filename
            pdf_path.write_bytes(pdf_content)

            cols = '(source_url, title, doc_type, published_date, raw_text_hash, file_path)'
            vals = 'VALUES (?, ?, ?, ?, ?, ?)'
            cursor.execute(
                f'INSERT INTO documents {cols} {vals}',
                (article_url, title, doc_type, published_date, content_hash, str(pdf_path)),
            )
            new_count += 1
        except requests.RequestException:
            error_count += 1
            continue

    _finish_run(cursor, crawl_id, 'SUCCESS', new_count, error_count)

    if close_conn:
        conn.close()

    return {
        'status': 'SUCCESS',
        'new_documents': new_count,
        'skipped': skip_count,
        'errors': error_count,
    }


def _start_run(cursor: sqlite3.Cursor, source: str) -> int:
    """Create a new crawl_runs record and return its ID."""
    cursor.execute(
        """INSERT INTO crawl_runs (source, started_at, status)
           VALUES (?, datetime('now'), 'RUNNING')""",
        (source,),
    )
    return cursor.lastrowid


def _finish_run(
    cursor: sqlite3.Cursor,
    run_id: int,
    status: str,
    new_documents: int = 0,
    errors: int = 0,
) -> None:
    """Finalize a crawl_runs record with completion status and counts."""
    cursor.execute(
        """UPDATE crawl_runs
           SET finished_at = datetime('now'), status = ?,
               new_documents = ?, errors = ?
           WHERE id = ?""",
        (status, new_documents, errors, run_id),
    )
    cursor.connection.commit()


register('botswanaspeaks_conn')

if __name__ == '__main__':
    result = crawl()
    print(f'Result: {result}')
