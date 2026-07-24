"""Tests for social draft generator."""

import pytest

from backend.db import migrate as migrate_module
from backend.db.connection import get_connection
from backend.social import draft_generator as dg


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """Return path to a fresh migrated DB with test contributions."""
    db = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db))
    migrate_module.migrate()

    conn = get_connection()
    try:
        conn.executemany(
            "INSERT INTO mps (name, constituency, party) VALUES (?, ?, ?)",
            [("Jane Motswana", "Gaborone Central", "BDP")],
        )
        conn.execute(
            "INSERT INTO documents (source_url, title, doc_type, raw_text_hash) "
            "VALUES (?, ?, ?, ?)",
            ("https://example.org/doc", "Test Doc", "notice_paper", "hash-zz"),
        )
        doc_id = conn.execute(
            "SELECT id FROM documents WHERE raw_text_hash = 'hash-zz'"
        ).fetchone()["id"]
        mp_id = conn.execute(
            "SELECT id FROM mps WHERE name = 'Jane Motswana'"
        ).fetchone()["id"]
        conn.execute(
            "INSERT INTO contributions "
            "(document_id, mp_id, contribution_type, subject_text, ministry_addressed, date, "
            "raw_match_name, raw_constituency, source_url) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                doc_id, mp_id, "question",
                "When will the Mohembo bridge be repaired?",
                "Transport", "2026-07-01", "MS. MOTSWANA", "GABORONE",
                "https://example.org/doc",
            ),
        )
        conn.execute(
            "INSERT INTO contributions "
            "(document_id, mp_id, contribution_type, subject_text, ministry_addressed, date, "
            "raw_match_name, raw_constituency, source_url) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                doc_id, mp_id, "motion",
                "Motion on improving rural water supply infrastructure",
                "Water Affairs", "2026-07-02", "MS. MOTSWANA", "GABORONE",
                "https://example.org/doc",
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return str(db)


class TestGenerateDrafts:
    def test_generates_drafts_for_new_contributions(self, db_path):
        drafts = dg.generate_drafts()
        assert len(drafts) == 2
        texts = {d["contribution_type"]: d["draft_text"] for d in drafts}
        assert "Mohembo bridge" in texts["question"]
        assert "Motion on improving" in texts["motion"]

    def test_second_run_produces_no_duplicates(self, db_path):
        first = dg.generate_drafts()
        assert len(first) == 2
        second = dg.generate_drafts()
        assert len(second) == 0

    def test_draft_has_hashtags(self, db_path):
        drafts = dg.generate_drafts()
        for d in drafts:
            assert "#Botswana" in d["draft_text"]
            assert "#Parliament" in d["draft_text"]

    def test_draft_truncates_long_subjects(self, db_path):
        drafts = dg.generate_drafts()
        for d in drafts:
            assert len(d["draft_text"]) <= 320


class TestReviewQueue:
    def test_list_pending_drafts(self, db_path):
        dg.generate_drafts()
        pending = dg.list_drafts("PENDING")
        assert len(pending) == 2

    def test_approve_draft(self, db_path):
        dg.generate_drafts()
        pending = dg.list_drafts("PENDING")
        draft_id = pending[0]["id"]
        result = dg.approve_draft(draft_id, "test-admin")
        assert result["detail"] == "Approved"
        still_pending = dg.list_drafts("PENDING")
        assert draft_id not in {d["id"] for d in still_pending}

    def test_reject_draft(self, db_path):
        dg.generate_drafts()
        pending = dg.list_drafts("PENDING")
        draft_id = pending[0]["id"]
        result = dg.reject_draft(draft_id, "test-admin")
        assert result["detail"] == "Rejected"

    def test_approve_nonexistent_draft(self, db_path):
        dg.generate_drafts()  # ensure tables exist
        result = dg.approve_draft(99999)
        assert "not found" in result["detail"]

    def test_approve_twice(self, db_path):
        dg.generate_drafts()
        pending = dg.list_drafts("PENDING")
        draft_id = pending[0]["id"]
        dg.approve_draft(draft_id)
        result2 = dg.approve_draft(draft_id)
        assert "not found" in result2["detail"]
