"""Ba Reng? — System-Learning Program

This file is the instruction set for the system-learning pipeline. The
pipeline is deterministic: it harvests durable knowledge from the live
database and exports it to plain files any model can read. No model is
trained, fine-tuned, or called.

=== What the system learns ===

1. Entity resolutions — raw_match_name -> resolved MP, from the
   entity_review_queue. These are the ground-truth corrections humans
   and agents made during review.

2. Ministry keyword mappings — canonical ministry names for each
   static-seed keyword, from ministry_keywords where source_type =
   'static_seed'.

3. Glossary terms — Setswana -> English parliamentary glossary entries.

4. Data quality snapshot — document counts, contribution counts, and
   entity-review queue resolution state.

=== How knowledge is consumed ===

The pipeline writes:
  - docs/LEARNED.md — a markdown digest, committed to the repo.
  - data/knowledge/learned.json — a structured export, runtime only.

Any model working on this codebase may read docs/LEARNED.md as context.
The file is model-agnostic: plain text, no embeddings, no API calls.

=== Commands ===

  - Run the full loop:  python -m backend.learn.run
  - Re-export only:     python -m backend.learn.run --export-only
  - Tests:              pytest backend/tests/test_learn.py -q

=== Constraints ===

- No LLM calls. No fine-tuning. No vector database.
- All changes must pass `pytest backend/tests/` with 0 failures.
- Backend must pass `ruff check backend/` with 0 new findings.
- SQLite schema changes must have migration scripts.
"""
