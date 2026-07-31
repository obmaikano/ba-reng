"""Tests for the system-learning module (backend/learn)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.db import migrate as migrate_module
from backend.db.connection import get_connection
from backend.learn import config as learn_config
from backend.learn.collector import SystemCollector
from backend.learn.connection import LearnConnection
from backend.learn.decision import DecisionLog
from backend.learn.export import KnowledgeExporter
from backend.learn.memory import Memory
from backend.learn.pipeline import LearningPipeline


@pytest.fixture
def learn_env(tmp_path, monkeypatch):
    """Point the learn module at a fresh migrated DB with seed data."""
    db_path = tmp_path / 'learn.db'
    monkeypatch.setenv('DATABASE_PATH', str(db_path))
    learn_config.get_config.cache_clear()
    LearnConnection.close()

    migrate_module.migrate()

    conn = get_connection()
    try:
        conn.execute(
            'INSERT INTO mps (name, constituency, party) VALUES (?, ?, ?)',
            ('Jane Motswana', 'Gaborone Central', 'BDP'),
        )
        mp_id = conn.execute(
            "SELECT id FROM mps WHERE name = 'Jane Motswana'",
        ).fetchone()['id']

        conn.execute(
            """
            INSERT INTO entity_review_queue
                (raw_match_name, status, resolved_mp_id, created_at)
            VALUES (?, ?, ?, ?)
            """,
            ('MS. J. MOTSWANA, MP.', 'RESOLVED', mp_id, '2026-07-01'),
        )

        conn.execute(
            """
            INSERT INTO parliamentary_glossary (term_setswana, term_english)
            VALUES (?, ?)
            """,
            ('Temothuo', 'Agriculture'),
        )

        conn.execute(
            'INSERT INTO documents (source_url, title, doc_type, raw_text_hash) '
            "VALUES ('https://x.test/1', 'Doc 1', 'notice_paper', 'h1')",
        )
        conn.execute(
            """
            INSERT INTO contributions
                (document_id, mp_id, contribution_type, subject_text,
                 raw_match_name, raw_constituency, date, source_url)
            VALUES (1, ?, 'question', 'Water supply',
                    'MS. J. MOTSWANA, MP.', 'GABORONE CENTRAL', '2026-07-01',
                    'https://x.test/1')
            """,
            (mp_id,),
        )
        conn.commit()
    finally:
        conn.close()

    return db_path


def test_collector_harvests_all_sources(learn_env) -> None:
    collector = SystemCollector()
    counts = collector.collect_all()

    assert counts['entity_resolutions'] == 1
    assert counts['ministry_keywords'] >= 1
    assert counts['glossary'] == 1
    assert counts['data_quality'] == 4

    memory = Memory()
    assert memory.retrieve('entity:MS. J. MOTSWANA, MP.') is not None
    assert memory.retrieve('ministry_keyword:hospital') is not None
    assert memory.retrieve('glossary:Temothuo') is not None
    assert memory.retrieve('dqs:documents_total') is not None
    LearnConnection.close()


def test_pipeline_run_exports_artifacts(learn_env, tmp_path) -> None:
    learn_config.get_config().markdown_path = str(tmp_path / 'LEARNED.md')
    learn_config.get_config().json_path = str(tmp_path / 'learned.json')

    pipeline = LearningPipeline()
    result = pipeline.run()

    assert result['collected']['entity_resolutions'] >= 1
    markdown = Path(result['exports']['markdown'])
    json_out = Path(result['exports']['json'])
    assert markdown.exists()
    assert json_out.exists()

    text = markdown.read_text(encoding='utf-8')
    assert 'MS. J. MOTSWANA, MP.' in text
    assert 'Learned System Knowledge' in text

    payload = json.loads(json_out.read_text(encoding='utf-8'))
    assert payload['memories']
    pipeline.close()


def test_decision_log_creates_memory_on_success(learn_env) -> None:
    log = DecisionLog()
    decision_id = log.record(
        'Fix ministry lookup',
        'Prefer static seeds before auto-harvested keywords',
        files_read=['backend/parse/base.py'],
        constraints_checked=['pytest backend/tests -q'],
    )
    log.mark_outcome(decision_id, 'success', 'All tests pass')

    memory = Memory()
    decisions = memory.search(category='decision')
    assert any('Fix ministry lookup' in d['value'] for d in decisions)
    LearnConnection.close()


def test_exporter_handles_empty_db(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / 'empty.db'
    monkeypatch.setenv('DATABASE_PATH', str(db_path))
    learn_config.get_config.cache_clear()
    LearnConnection.close()
    migrate_module.migrate()

    exporter = KnowledgeExporter()
    markdown = exporter.export_markdown()
    text = markdown.read_text(encoding='utf-8')
    assert 'No knowledge recorded yet' in text
    LearnConnection.close()
