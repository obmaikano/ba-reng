# CONTEXT — Ba Reng? (Botswana Parliament MP Monitor)

## Architecture (high-level system shape)

- **Data Pipeline**: Python 3.12 — requests, pdfplumber, PyMuPDF, BeautifulSoup
  - Connectors: botswanaspeaks_conn.py, parliament_docs_conn.py, roster_conn.py
  - Parsers: notice_paper, order_paper, committee_of_supply, bill, motion, hansard
  - Entity resolution: constituency-first, surname fallback, unmatched → `entity_review_queue`
- **API**: FastAPI (async, auto-docs, lightweight) — 9 read-only endpoints + 6 admin endpoints
- **Frontend**: React 19 + Vite + Blueprint.js (v5) + Tailwind CSS (utility only)
- **Database**: SQLite (single file, WAL mode, git-versioned) — `mps`, `documents`, `contributions`, `crawl_runs`, `entity_review_queue`, `sit_calendar`, `users`, `sessions`
- **Auth**: email+password, bcrypt, JWT httpOnly cookies, RBAC (Admin/Editor/Viewer), FastAPI dependency injection
- **Deploy**: GitHub Actions — daily crawl → parse → resolve → build → deploy (GitHub Pages / Vercel)

## Visual direction

- Canvas: `#0B0E14` (cold slate, not warm dark)
- Type: Inter (UI) + JetBrains Mono (metadata, data, tags, timestamps)
- Radius: zero everywhere
- Borders: 1px hairline — `#1F242E` subtle, `#2A313D` default
- Color: functional only — blue=data, amber=warning/constraint, green=health, red=destructive
- Imagery: none. Data is the visual. MP photos = uniform ratio + monogram fallback
- Elevation: Blueprint BP7 `box-shadow` tokens
- Reference lock: Palantir Foundry/AIP via Blueprint.js BP7 tokens

## Key decisions

- Blueprint.js (not shadcn/Radix) — Palantir's own toolkit, built for data-dense interfaces, has Table2 virtualized table, native dark mode via BP7 tokens
- Participation Index is a proxy metric — always labeled as such, never called "most/least active"
- No attendance data exists from Botswana Parliament — enforced at component level, not left to developer
- Unresolved entity names stored in `entity_review_queue` — never silently guessed
- Narrative-first design: home page is weekly digest, not raw feed. Raw feed preserved as Screen 02.
- SPA architecture: Screens 02-11 render inside feed column (col-7) of persistent 3-column layout. Screen 01 uses full width.

## 11 screens

| # | Screen | Type | Description |
|---|---|---|---|
| 01 | This Week in Parliament | Public | Narrative dashboard (default home) |
| 02 | Live Record Stream | Public | Raw filtered feed |
| 03 | Find My MP | Public | Constituency search |
| 04 | MP Profile | Public | Stats + session focus narrative |
| 05 | MP Compare | Public | Side-by-side with comparison story |
| 06 | Participation Index | Public | Leaderboard with caveat |
| 07 | Bill Tracker | Public | Legislative progress |
| 08 | Search | Public | Full-text search |
| 09 | Admin Dashboard | Admin | Pipeline health, data quality, crawl log |
| 10 | Entity Review Queue | Admin | Resolve unmatched names |
| 11 | User Management | Admin | CRUD users + RBAC matrix |

## Gotchas

- **No attendance register exists** for Botswana Parliament. Participation Index is explicitly a proxy metric. Any view displaying it must show the caveat. This is enforced in the component, not left to the developer.
- MP roster from Wikipedia — must handle by-elections, deaths, resignations. Refresh periodically.
- Botswana Speaks listing page may return full history on one page — hash dedup is critical (skip unchanged PDFs via `raw_text_hash`).
- Entity resolution is constituency-first, surname fallback. Constituency normalization: lowercase, strip punctuation, collapse whitespace.
- Admin operators provisioned CLI-only initially (no HTTP signup).
- `Go is not installed` — this project uses Python. Run Python tests via `pytest`.
- `.vibe/` is **gitignored** — STATE/PLAN/CONTEXT/HISTORY/SPRINT are runtime, never committed.

## Hot files

- `BA_RENG_ARCHITECTURE_AND_DESIGN.md` — canonical architecture spec (10 sections)
- `BA_RENG_USER_JOURNEY_MAP.md` — all 146 touchpoints mapped
- `ba-reng-combined.html` — merged 11-screen mockup (no build step)
- `PLAN.md` — original architecture plan (pre-vibe)

## Agent notes

- **Current**: Stage 0 — Checkpoint 0.0 (Project scaffolding & setup, NOT_STARTED).
- All architecture, design, market research, and mockup work is complete.
- Next: implement Stage 0.0 — backend scaffold + frontend scaffold + Makefile + configuration.
