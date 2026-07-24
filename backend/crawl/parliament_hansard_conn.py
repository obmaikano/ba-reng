"""Parliament of Botswana Hansard connector — fetches Daily Hansard PDFs from parliament.gov.bw."""

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
HANSARD_URL = f'{BASE_URL}/index.php?option=com_documents&view=files&catid=87&Itemid=438'
HANSARD_BASE = f'{BASE_URL}/index.php?option=com_documents&view=files&catid=87'
PDF_DIR = Path(__file__).resolve().parent.parent.parent / 'data' / 'pdfs'

HEADERS = {
    'User-Agent': 'BaReng/0.1 (Botswana Parliament MP Monitor; research)',
}

DATE_IN_TITLE = re.compile(
    r'(\d{1,2})(?:ST|ND|RD|TH)?\s+(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|'
    r'JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s*,?\s*(\d{4})',
    re.IGNORECASE,
)

DATE_ISO = re.compile(r'(\d{4})-(\d{2})-(\d{2})')


def _parse_hansard_date(title: str, fallback_date: str = '') -> str:
    m = DATE_IN_TITLE.search(title)
    if m:
        try:
            dt = datetime.strptime(f'{m.group(1)} {m.group(2)} {m.group(3)}', '%d %B %Y')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass

    iso = DATE_ISO.search(fallback_date)
    if iso:
        return f'{iso.group(1)}-{iso.group(2)}-{iso.group(3)}'

    return fallback_date


def _extract_hansard_number(title: str) -> int | None:
    m = re.search(r'HANSARD\s*(?:NO[:\s]*)?\s*(\d+)', title, re.IGNORECASE)
    if m:
        return int(m.group(1))

    day = re.search(r'(\d{1,2})(?:ST|ND|RD|TH)?\s', title, re.IGNORECASE)
    if day:
        return int(day.group(1))
    return None


def _fetch_page(offset: int = 0, limit: int = 100) -> str:
    """Fetch one page of Hansard listings with pagination."""
    url = f'{HANSARD_BASE}&limitstart={offset}&limit={limit}'
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def _extract_pdf_links(html: str) -> list[tuple[str, str, str]]:
    """Parse PDF links, titles, and dates from a listing page."""
    soup = BeautifulSoup(html, 'html.parser')
    pdf_links: list[tuple[str, str, str]] = []

    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        if not href.lower().endswith('.pdf'):
            continue

        full_url = href if href.startswith('http') else f'{BASE_URL}{href}'
        title = a.get_text(strip=True)

        row = a.find_parent('tr')
        date_str = ''
        if row:
            cells = row.find_all('td')
            for cell in cells:
                text = cell.get_text(strip=True)
                iso = DATE_ISO.search(text)
                if iso:
                    date_str = text
                    break

        if not title:
            title = Path(href).stem.replace('-', ' ').replace('_', ' ')

        parsed_date = _parse_hansard_date(title, date_str)
        pdf_links.append((full_url, title, parsed_date))

    return pdf_links


def _count_total_pages(html: str) -> int:
    """Count total pages from Joomla pagination."""
    soup = BeautifulSoup(html, 'html.parser')
    pagination = soup.find('ul', class_='pagination')
    if not pagination:
        return 1
    pages = pagination.find_all('li')
    nums = []
    for p in pages:
        text = p.get_text(strip=True)
        if text.isdigit():
            nums.append(int(text))
    return max(nums) if nums else 1


def crawl(conn: sqlite3.Connection | None = None) -> dict:
    """Fetch Hansard listings from parliament.gov.bw and download new PDFs."""
    close_conn = conn is None
    if conn is None:
        conn = get_connection()

    PDF_DIR.mkdir(parents=True, exist_ok=True)
    cursor = conn.cursor()

    try:
        html = _fetch_page(0, 100)
        total_pages = _count_total_pages(html)
        pdf_links = _extract_pdf_links(html)

        for page in range(1, total_pages):
            try:
                page_html = _fetch_page(page * 100, 100)
                pdf_links.extend(_extract_pdf_links(page_html))
            except Exception:
                continue

    except Exception as e:
        return {'source': 'parliament_hansard', 'status': 'FAILED', 'error': str(e),
                'new_documents': 0, 'skipped': 0}

    new_count = 0
    skipped_count = 0

    for pdf_url, title, date_str in pdf_links:
        pdf_bytes = b''
        try:
            r = requests.get(pdf_url, headers=HEADERS, timeout=60)
            r.raise_for_status()
            pdf_bytes = r.content
        except Exception:
            continue

        content_hash = hashlib.sha256(pdf_bytes).hexdigest()

        existing = cursor.execute(
            'SELECT id FROM documents WHERE raw_text_hash = ?', (content_hash,),
        ).fetchone()
        if existing:
            skipped_count += 1
            continue

        filename = f'parliament_hansard_{date_str}_{content_hash[:12]}.pdf'
        file_path = PDF_DIR / filename
        file_path.write_bytes(pdf_bytes)

        cursor.execute(
            """INSERT INTO documents (title, doc_type, file_path, source_url, raw_text_hash, published_date)
               VALUES (?, 'hansard', ?, ?, ?, ?)""",
            (title, str(file_path), pdf_url, content_hash, date_str),
        )
        new_count += 1

    cursor.execute(
        """INSERT INTO crawl_runs (source, status, new_documents, errors, started_at, finished_at)
           VALUES ('parliament_hansard', 'SUCCESS', ?, 0, datetime('now'), datetime('now'))""",
        (new_count,),
    )
    conn.commit()

    if close_conn:
        conn.close()

    return {
        'source': 'parliament_hansard',
        'status': 'SUCCESS',
        'new_documents': new_count,
        'skipped': skipped_count,
        'total_listed': len(pdf_links),
    }


register('parliament_hansard_conn')
