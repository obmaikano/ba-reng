# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Ba Reng? ("What did they say?") — Botswana Parliament MP Monitor. Scrapes public parliamentary
sources (Botswana Speaks, Wikipedia MP roster, Hansard PDFs), parses them into structured
contributions, resolves speakers to MPs, and serves a read-mostly React dashboard over a FastAPI
backend backed by SQLite.

## Workflow contract — read this first

This repo runs on a project-local workflow defined in `AGENTS.md`, with live state in `.vibe/`.
**Read `AGENTS.md` then `.vibe/STATE.md` then `.vibe/SPRINT.md` then `.vibe/PLAN.md` before starting
work** — they are the authoritative source for what checkpoint is active and what "done" means here,
and take precedence over assumptions (though current chat instructions win over all of it). Key rules
from `AGENTS.md` worth internalizing:

- Work one checkpoint at a time, on a feature branch named `checkpoint/<id>-<slug>`, never on `main`.
- A checkpoint isn't done until: lint/typecheck/tests pass, an adversarial review pass has been done,
  and for frontend checkpoints the rendered output has been compared against
  `docs/mockups/combined.html` (screen-by-screen) for layout, section titles, spacing, and live data.
- Commit messages are prefixed with the checkpoint ID (e.g. `3.8: Add Full-Text Search screen`).

## Commands

```bash
# Docker (primary dev workflow)
docker compose up --build      # backend :8000, frontend :5173

# Native fallback
make install       # venv + backend deps + frontend npm install
make dev-backend   # uvicorn backend.main:app --reload --port 8000
make dev-frontend  # vite dev server

make lint          # ruff check backend/ + eslint frontend/src
make typecheck     # tsc --noEmit (frontend)
make test          # pytest (backend)
make build         # vite build (runs tsc --noEmit first)
```

Single test / targeted runs:

```bash
.venv/bin/pytest backend/tests/test_api.py::test_name -v
.venv/bin/pytest backend/tests/test_roster_and_resolve.py
cd frontend && npx tsc --noEmit          # type errors only
cd frontend && npx eslint src/path/to/File.tsx
```

Data pipeline (run manually, not on every request):

```bash
python -m backend.parse.run       # parse pending documents into contributions/utterances
python -m backend.resolve.run     # resolve raw_match_name+constituency -> mp_id
python -m backend.db.migrate      # apply pending SQL migrations in backend/db/migrations/
```

## Architecture

### Pipeline (backend, batch — not part of request handling)

```
Source connectors (backend/crawl/)
  -> raw documents (HTML/PDF), deduped via raw_text_hash on `documents`
  -> Parsers, dispatched by doc_type (backend/parse/run.py `_PARSERS` registry):
       notice_paper | order_paper | committee_of_supply | bill | motion
       | ministerial_speech | hansard
  -> Entity resolution (backend/resolve/): constituency match -> fuzzy constituency
       -> surname match -> unresolved -> entity_review_queue
  -> Hansard-only branch: offline spaCy NLP (backend/parse/nlp_extract.py) +
       language tagging (backend/parse/language_tagger.py) for English/Setswana
       code-switched speech turns
  -> SQLite (data/bareng.db): mps, documents, contributions, hansard_sessions,
       agenda_items, utterances, entity_review_queue, crawl_runs
```

`backend/parse/run.py` is the orchestration entry point — it dispatches by `doc_type` to the
per-format parser, hashes `subject_text` for dedup on insert, and queues unresolved names into
`entity_review_queue` rather than silently dropping them. New document types are added by writing a
`parse_pdf(...)` function and registering it in `_PARSERS`.

### Backend layout (`backend/`)

- `api/routes/` — read-mostly FastAPI routers (mps, contributions, constituencies, hansard,
  analytics, narrative, search, status), mounted in `backend/main.py`.
- `api/auth/`, `api/admin/`, `api/middleware/auth.py` — JWT auth (python-jose + passlib/bcrypt),
  role-gated admin endpoints (`admin|editor|viewer`).
- `api/metrics/participation_index.py` — the "Participation Index" scoring; always returns
  `is_proxy: True` and a caveat string — this is enforced by convention, not by the DB, so any new
  metric surfaced in the UI must carry the same caveat.
- `crawl/` — source connectors (e.g. `botswanaspeaks_conn.py`), hash-based dedup against `documents`.
- `parse/` — one module per document format; `run.py` is the dispatcher.
- `resolve/` — `entity.py` (constituency/surname resolution), `nearest_match.py`, `run.py` (batch
  resolution pass).
- `roster/wikipedia.py` — canonical MP list scraped from Wikipedia (constituency, party).
- `narrative/` — higher-level derived analysis: ministry inference, rhetorical/persona
  classification, deferral scorecards — built on top of parsed contributions/utterances, not part of
  the core parse/resolve pipeline.
- `db/connection.py` — single `get_connection()` helper (WAL mode, foreign keys on, row_factory=Row);
  DB path from `DATABASE_PATH` env var, defaults to `data/bareng.db`.
- `db/migrations/*.sql` — plain numbered SQL files, applied in order by `db/migrate.py`. No ORM.

### Frontend layout (`frontend/src/`)

React 19 + Vite + Blueprint.js v6 + Tailwind v4 + react-router-dom v7. Organized by feature/screen:
`dashboard/` (default landing — narrative weekly digest, not a raw feed), `feed/` (raw Live Record
Stream), `mp/`, `compare/`, `bills/`, `rankings/`, `search/`, `findmp/`, `admin/` (RBAC-gated),
`auth/` (JWT context + `ProtectedRoute`), `layout/` (`AppShell`, `TopNav`, `SystemStatusBar`).

- `api.ts` — single fetch client for the FastAPI backend.
- Each screen owns its own `use*Data.ts` hook for fetching + shaping API responses (see
  `dashboard/useDashboardData.ts`, `feed/useFeedData.ts`) rather than a shared global store.

### Design system (hard constraints, not just style preference)

Palantir-inspired terminal aesthetic — deviating from these breaks visual QA against
`docs/mockups/combined.html`:

- Canvas `#0B0E14`, radius `0` everywhere, 1px hairline borders only (`#1F242E`/`#2A313D`).
- Color is functional only: blue = data/metrics, amber = warnings/unresolved/proxy caveats,
  green = system health, red = destructive only. Never decorative.
- `--font-mono` (JetBrains Mono) for all timestamps, IDs, constituency/party codes, table data;
  `--font-ui` (Inter) for names/prose. No serif, no gradients, no drop shadows, no imagery.
- Section titles are UPPERCASE with SVG icons (see `dashboard/` components for the pattern).
- Full spec: `docs/ARCHITECTURE.md` (data model, API surface, token reference) and
  `docs/mockups/combined.html` (11 screens, source of truth for pixel-level layout).

### Data integrity conventions

- Every API response that surfaces a document-derived fact includes `source_url` back to the
  original PDF/page.
- Any "proxy metric" (e.g. Participation Index) must be labeled as such in both API payload
  (`is_proxy`) and UI — this is a project-wide constraint, not a per-feature decision.
- Unresolved entity matches go to `entity_review_queue` and are surfaced in the admin UI, never
  silently guessed or dropped.
