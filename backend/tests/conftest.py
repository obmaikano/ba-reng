"""Shared pytest fixtures for API tests."""

from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from backend.db import migrate as migrate_module
from backend.db.connection import get_connection
from backend.main import app


@dataclass
class SeededApi:
    """A TestClient plus the actual row ids inserted into its backing test DB."""

    client: TestClient
    mp_ids: dict[str, int]
    contribution_ids: list[int]


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    """Build a fresh migrated SQLite DB with fixture data and return a SeededApi."""
    db_path = tmp_path / 'test.db'
    monkeypatch.setenv('DATABASE_PATH', str(db_path))

    migrate_module.migrate()

    conn = get_connection()
    try:
        conn.executemany(
            'INSERT INTO mps (name, constituency, party) VALUES (?, ?, ?)',
            [
                ('Jane Motswana', 'Gaborone Central', 'BDP'),
                ('John Kgosi', 'Francistown East', 'UDC'),
            ],
        )
        mp_ids = {
            row['name']: row['id']
            for row in conn.execute('SELECT id, name FROM mps').fetchall()
        }

        conn.execute(
            'INSERT INTO documents (source_url, title, doc_type, raw_text_hash) '
            'VALUES (?, ?, ?, ?)',
            (
                'https://example.org/notice-paper-1',
                'Notice Paper 1',
                'notice_paper',
                'hash-1',
            ),
        )
        document_id = conn.execute(
            "SELECT id FROM documents WHERE raw_text_hash = 'hash-1'",
        ).fetchone()['id']

        conn.executemany(
            'INSERT INTO contributions '
            '(document_id, mp_id, contribution_type, subject_text, ministry_addressed, '
            'date, raw_match_name, raw_constituency, source_url) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            [
                (
                    document_id, mp_ids['Jane Motswana'], 'question',
                    'When will the Mohembo bridge be repaired', 'Transport',
                    '2026-07-01', 'MS. J. MOTSWANA, MP.', 'GABORONE CENTRAL',
                    'https://example.org/notice-paper-1',
                ),
                (
                    document_id, mp_ids['Jane Motswana'], 'motion',
                    'Motion on rural water supply', 'Water Affairs',
                    '2026-07-02', 'MS. J. MOTSWANA, MP.', 'GABORONE CENTRAL',
                    'https://example.org/notice-paper-1',
                ),
                (
                    document_id, mp_ids['John Kgosi'], 'question',
                    'On school infrastructure funding', 'Education',
                    '2026-07-03', 'MR. J. KGOSI, MP.', 'FRANCISTOWN EAST',
                    'https://example.org/notice-paper-1',
                ),
            ],
        )
        contribution_ids = [
            row['id']
            for row in conn.execute('SELECT id FROM contributions ORDER BY id').fetchall()
        ]

        conn.execute(
            'INSERT INTO crawl_runs (started_at, finished_at, source, status, new_documents) '
            'VALUES (?, ?, ?, ?, ?)',
            (
                '2026-07-01 10:00:00', '2026-07-01 10:05:00',
                'botswanaspeaks.gov.bw', 'SUCCESS', 1,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return SeededApi(
        client=TestClient(app),
        mp_ids=mp_ids,
        contribution_ids=contribution_ids,
    )
