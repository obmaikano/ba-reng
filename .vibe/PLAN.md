# PLAN — Ba Reng? (Botswana Parliament MP Monitor)

## How to use this file

- This is the checkpoint backlog.
- Each checkpoint must include: Objective, Deliverables, Acceptance, Demo commands, Evidence.
- Build order follows the pipeline dependency graph: foundation → data pipeline → API → frontend → admin → launch.
- Stages 1–5 track the data-to-ui flow; Stage 0 is foundation/infra.

## Architecture overview

```
Source Connectors → Parsers → Entity Resolution → SQLite → API → Static Site (React + Blueprint.js)
                                                → Admin Dashboard (RBAC) → Social Publisher
```

Visual direction: Palantir-inspired. Cold slate canvas `#0B0E14`, zero radius, hairline borders, Inter + JetBrains Mono, functional color only (blue=data, amber=warning, green=health, red=destructive).

## Stage 0 — Foundation & Setup

Parallel tracks: none (everything depends on scaffold existing).

### 0.0 — Project scaffolding & setup
- depends_on: []
- parallel_eligible: false
- flag: no flag — infra
- sprint: 1
- **Objective:**
  Initialize the Ba Reng monorepo with Python backend scaffold, React/Vite/Blueprint.js frontend scaffold, and all configuration files.
- Deliverables:
  - Git repo initialized (if not already)
  - `backend/` with `pyproject.toml`, FastAPI skeleton, SQLite migration directory
  - `frontend/` with Vite + React 19 + Blueprint.js + Tailwind CSS
  - `Makefile` with `install`, `dev-backend`, `dev-frontend`, `lint`, `test` commands
  - `.env.example`, `.gitignore` (excludes `.vibe/`, `node_modules/`, `.env`, build artifacts)
- Acceptance:
  - [ ] `make install` succeeds for both backend and frontend dependencies
  - [ ] `make dev-backend` starts FastAPI on `localhost:8000` with health endpoint
  - [ ] `make dev-frontend` starts Vite on `localhost:5173` with Blueprint.js rendering
  - [ ] `tsc --noEmit` clean on frontend
- Demo commands:
  - `make install && make dev-backend` — visit `http://localhost:8000/docs`
  - `make dev-frontend` — visit `http://localhost:5173`
- Evidence:
  - Terminal output for each command; screenshot of Blueprint.js component rendering in browser

### 0.1 — CI/CD pipeline (GitHub Actions) [stretch]
- depends_on: [0.0]
- parallel_eligible: true
- flag: no flag — infra
- **Objective:**
  Set up GitHub Actions for automated linting, type checking, and testing on push/PR.
- Deliverables:
  - `.github/workflows/ci.yml`: backend lint + test, frontend lint + tsc + build
  - `.github/workflows/deploy.yml`: daily scheduled build + deploy (GitHub Pages or Vercel)
  - Daily crawl: `cron: '0 6 * * *'` to trigger crawl → parse → resolve → build → deploy
- Acceptance:
  - [ ] CI passes on push (green checkmark)
  - [ ] Deploy workflow runs on schedule and produces a working site
- Demo commands:
  - Push a trivial change; verify CI green
  - `gh workflow run deploy` — verify site at deployed URL

## Stage 1 — Data Pipeline (Crawl → Parse → Resolve → Store)

### 1.0 — Botswana Speaks connector + hash cache
- depends_on: [0.0]
- parallel_eligible: false
- flag: no flag — data pipeline
- **Objective:**
  Scrape `botswanaspeaks.gov.bw` listing pages and download new/modified PDFs, skipping unchanged documents via hash cache.
- Deliverables:
  - `backend/crawl/botswanaspeaks_conn.py` — fetch listing, check `raw_text_hash` against DB, download new PDFs
  - `backend/crawl/__init__.py` — connector registry
  - `backend/db/schema.sql` — `documents`, `crawl_runs` tables
  - `backend/db/init.py` — SQLite connection + migration runner
- Acceptance:
  - [ ] First run downloads all PDFs and records them in `crawl_runs`
  - [ ] Second run skips all already-crawled documents (hash dedup)
  - [ ] `crawl_runs` table shows SUCCESS with correct `new_documents` count
- Demo commands:
  - `python -m backend.crawl.botswanaspeaks_conn`
  - `sqlite3 data/bareng.db "SELECT source, status, new_documents FROM crawl_runs;"`
- Evidence:
  - Terminal output showing download/skip counts; SQLite query confirming dedup

### 1.1 — Notice Paper parser + Contribution extractor
- depends_on: [1.0]
- parallel_eligible: false
- flag: no flag — data pipeline
- **Objective:**
  Parse downloaded Notice Paper PDFs into structured Contribution records with MP names, constituencies, ministries, and subject text.
- Deliverables:
  - `backend/parse/notice_paper.py` — PDF text extraction + structured field parsing
  - `backend/db/schema.sql` — `contributions` table
  - `backend/parse/run.py` — orchestration: iterate documents → parse → insert contributions
  - `backend/db/entity_review_queue.py` — `entity_review_queue` table for unmatched names
- Acceptance:
  - [ ] Parser extracts ≥1 Contribution from a real Notice Paper PDF
  - [ ] Each contribution has `raw_match_name`, `ministry_addressed`, `subject_text`, `date`
  - [ ] Unmatched names land in `entity_review_queue` with `status='UNRESOLVED'`
- Demo commands:
  - `python -m backend.parse.run`
  - `sqlite3 data/bareng.db "SELECT COUNT(*) FROM contributions;"`
  - `sqlite3 data/bareng.db "SELECT raw_match_name FROM entity_review_queue WHERE status='UNRESOLVED';"`
- Evidence:
  - Contribution count; entity_review_queue rows with garbled/missing names

### 1.2 — MP roster + entity resolution
- depends_on: [1.1]
- parallel_eligible: false
- flag: no flag — data pipeline
- **Objective:**
  Fetch canonical MP roster from Wikipedia 13th Parliament page and resolve parsed names to canonical MPs.
- Deliverables:
  - `backend/roster/wikipedia.py` — fetch Wikipedia table, normalize names + constituencies
  - `backend/db/schema.sql` — `mps` table
  - `backend/resolve/entity.py` — constituency-first resolution with surname fallback
  - `backend/resolve/run.py` — batch-resolve all UNRESOLVED entities in `entity_review_queue`
- Acceptance:
  - [ ] Roster contains ≥57 MPs (all constituencies) with name, constituency, party
  - [ ] Resolution matches ≥80% of parsed contributions to an MP
  - [ ] Unresolved names remain in `entity_review_queue` with a suggested MP dropdown
- Demo commands:
  - `python -m backend.roster.wikipedia`
  - `python -m backend.resolve.run`
  - `sqlite3 data/bareng.db "SELECT COUNT(*) FROM contributions WHERE mp_id IS NOT NULL;"`
- Evidence:
  - Roster count; resolution rate percentage; entity_review_queue with remaining unmatched names

### 1.3 — SQLite store + migration system
- depends_on: [1.2]
- parallel_eligible: true
- flag: no flag — data pipeline
- **Objective:**
  Productionize the SQLite store with versioned migrations, connection pooling, and a migration runner.
- Deliverables:
  - `backend/db/migrations/` — numbered `.sql` migration files (001–004 covering schema from 1.0–1.2)
  - `backend/db/migrate.py` — migration runner with `applied_migrations` tracking table
  - `backend/db/connection.py` — connection pool with WAL mode, foreign keys enabled
  - `sit_calendar` table added for sitting day tracking
- Acceptance:
  - [ ] `python -m backend.db.migrate` applies all pending migrations
  - [ ] Re-run is idempotent (skips already-applied migrations)
  - [ ] WAL mode confirmed: `sqlite3 data/bareng.db 'PRAGMA journal_mode;'` returns `wal`
- Demo commands:
  - `python -m backend.db.migrate`
  - `sqlite3 data/bareng.db ".tables"`
- Evidence:
  - Migration output; table listing showing all expected tables

## Stage 2 — API Layer (FastAPI read endpoints)

### 2.0 — Read API: MPs, contributions, constituencies
- depends_on: [1.3]
- parallel_eligible: false
- flag: no flag — API
- **Objective:**
  Expose data through a FastAPI read-only API with the 9 endpoints from the architecture spec.
- Deliverables:
  - `backend/api/main.py` — FastAPI app with CORS
  - `backend/api/routes/mps.py` — `GET /api/v1/mps`, `GET /api/v1/mps/{id}`, `GET /api/v1/mps/{id}/contributions`
  - `backend/api/routes/contributions.py` — `GET /api/v1/contributions`, `GET /api/v1/contributions/{id}`
  - `backend/api/routes/constituencies.py` — `GET /api/v1/constituencies`, `GET /api/v1/constituencies/{name}`
  - `backend/api/routes/search.py` — `GET /api/v1/search?q=`
  - `backend/api/routes/status.py` — `GET /api/v1/status` (system health)
  - Every response includes `source_url` back to original PDF/document
- Acceptance:
  - [ ] All 9 endpoints respond with JSON
  - [ ] `GET /api/v1/mps` returns MP list with contribution counts + participation_index
  - [ ] `GET /api/v1/mps/{id}` returns profile with breakdown by type + timeline
  - [ ] `GET /api/v1/contributions` supports `?type=&ministry=&party=&constituency=` filters
  - [ ] `GET /api/v1/search?q=Mohembo` returns relevant results
  - [ ] Each response includes `source_url`
  - [ ] Auto-generated docs at `/docs` are navigable
- Demo commands:
  - `curl http://localhost:8000/api/v1/status`
  - `curl http://localhost:8000/api/v1/mps/1`
  - `curl "http://localhost:8000/api/v1/search?q=Mohembo"`
- Evidence:
  - curl outputs; OpenAPI docs screenshot

### 2.1 — Participation Index computation
- depends_on: [2.0]
- parallel_eligible: true
- flag: no flag — API
- **Objective:**
  Implement the weighted Participation Index formula with `is_proxy` flag enforced at endpoint and component level.
- Deliverables:
  - `backend/api/metrics/participation_index.py` — weighted score per MP with breakdown
  - Integration into `GET /api/v1/mps` and `GET /api/v1/mps/{id}` responses
  - `is_proxy: true` and `caveat` string in every response that includes the index
- Acceptance:
  - [ ] Participation Index returns score + breakdown per MP
  - [ ] Response includes `is_proxy: true` and `caveat: "Based on recorded contributions only. Not attendance data."`
  - [ ] Weighted correctly: motions + committee_of_supply = 1.5x, oral_questions = 1.0x
- Demo commands:
  - `curl http://localhost:8000/api/v1/mps/1 | python -m json.tool | grep -A10 participation_index`
- Evidence:
  - API response showing proxy flag and caveat

## Stage 3 — Frontend (React + Blueprint.js Static Site)

### 3.0 — Layout shell: 3-column grid + navigation
- depends_on: [2.0]
- parallel_eligible: true
- flag: frontend_shell_3
- **Objective:**
  Build the persistent 3-column layout shell with TopNav, SystemStatusBar, and context-aware sidebars.
- Deliverables:
  - `TopNav` — minimal header with Ba Reng logo, version, nav buttons (public + admin, auth-gated)
  - `SystemStatusBar` — mono text strip showing pipeline health, crawl status, unresolved count
  - 3-column grid: left sidebar (filters ↔ admin nav), content column (col-7), right panel (index ↔ health)
  - Layout transitions: full-width (Screen 01) ↔ 3-column (Screens 02-11)
  - Design token system as CSS custom properties (`--bg-canvas`, `--accent-blue`, etc.)
- Acceptance:
  - [ ] Shell renders with correct Palantir token colors
  - [ ] Sidebar and right panel swap content based on active screen (data ↔ admin)
  - [ ] `anim-out` (150ms) + `anim-in` (250ms) transitions on navigation
  - [ ] `tsc --noEmit` clean
- Demo commands:
  - `cd frontend && npm run dev`
  - Click through screens 01-11 to verify sidebar + right panel swapping
- Evidence:
  - Screenshots of layout in data mode and admin mode; transition animation captured

### 3.1 — Screen 01: This Week in Parliament (narrative dashboard)
- depends_on: [3.0, 2.1]
- parallel_eligible: true
- flag: frontend_week_01
- **Objective:**
  Build the narrative home page: week at a glance, top story, weekly timeline, hot topics, recent contributions, quick actions.
- Deliverables:
  - `WeekAtGlance` — 4 stat cards (sitting days, contributions, active MPs, top ministry)
  - `TopStory` — featured contribution contextualized
  - `WeeklyTimeline` — day-by-day breakdown
  - `WhoWasActive` — top 5 MPs with contribution counts, clickable to MP Profile
  - `ByTheNumbers` — quick stats table
  - `HotTopics` — thematic grouping of contributions
  - `RecentContributions` — compact scrollable list
  - `QuickActions` — Find MP, Compare MPs, Browse Bills
- Acceptance:
  - [ ] Dashboard renders with live API data (not hardcoded)
  - [ ] Top story expands inline Q&A on click
  - [ ] All links navigate to correct screens (MP Profile, Compare, Feed, Bill Tracker)
  - [ ] Visual QA matches ba-reng-combined.html Screen 01
- Demo commands:
  - Navigate to `/` or click "01 Week"
  - Click each Quick Action and verify navigation
- Evidence:
  - Screenshot vs combined mockup; click-through recordings

### 3.2 — Screen 02: Live Record Stream
- depends_on: [3.0, 2.0]
- parallel_eligible: true
- flag: frontend_feed_02
- **Objective:**
  Build the raw filtered feed using Blueprint.js Table2 with virtualized rows, sortable columns, filters, and CSV export.
- Deliverables:
  - `RecordStream` — `Table2` with Timestamp | Entity | Type | Subject columns, sortable
  - `FilterPanel` — collapsible sidebar with type, party, date range, ministry, constituency filters
  - CSV export of current view
  - Pagination via "Load more"
  - Click row → expanded detail; click MP name → MP Profile
- Acceptance:
  - [ ] Table renders with live data, virtualized for performance
  - [ ] All filters work and narrow results correctly
  - [ ] CSV export downloads a valid CSV file
  - [ ] "Load more" fetches next page
- Demo commands:
  - Apply each filter; verify URL params update
  - Click CSV export; open the file
- Evidence:
  - Screenshots of filtered states; CSV content verified

### 3.3 — Screen 03: Find My MP
- depends_on: [3.0, 2.0]
- parallel_eligible: true
- flag: frontend_findmp_03
- **Objective:**
  Build constituency search with autocomplete and browse-all-directory.
- Deliverables:
  - `ConstituencySearch` — input with autocomplete suggestions
  - Constituency directory with browse-all view (57 constituencies)
  - Search result card → MP Profile navigation
  - Suggested constituency quick-links (Gaborone, Francistown)
- Acceptance:
  - [ ] Typing partial name shows autocomplete suggestions
  - [ ] Selecting a result navigates to correct MP Profile
  - [ ] Browse-all shows all 57 constituencies with current MP
- Demo commands:
  - Type "Tati" → select result → verify MP Profile
  - Click "Browse all 57 constituencies"
- Evidence:
  - Screenshot of search results and directory

### 3.4 — Screen 04: MP Profile
- depends_on: [3.0, 2.0, 2.1]
- parallel_eligible: true
- flag: frontend_profile_04
- **Objective:**
  Build MP profile page with session focus narrative, contribution timeline, and breakdowns.
- Deliverables:
  - MP header: photo placeholder (monogram fallback), name, constituency, party, role
  - Stats: total contributions, breakdown by type, most-addressed ministries
  - `SessionFocus` — amber/blue-bordered narrative block derived from ministry focus
  - Timeline tab: chronological contributions, each linking to source PDF
  - By Type tab: breakdown chart
  - Ministries tab: ministry-addressed breakdown
  - Compare button → Screen 05 pre-filled
  - Share button, Export CSV, View source docs
- Acceptance:
  - [ ] Profile loads with real data from API
  - [ ] Tabs switch between Timeline/Type/Ministries views
  - [ ] Compare button pre-fills Screen 05
  - [ ] Methodology caveat visible (amber "What does this mean?")
- Demo commands:
  - Navigate from Find My MP to a profile
  - Click each tab; click Compare
- Evidence:
  - Screenshot of profile with tabs; methodology caveat visible

### 3.5 — Screen 05: MP Compare
- depends_on: [3.4]
- parallel_eligible: true
- flag: frontend_compare_05
- **Objective:**
  Build side-by-side MP comparison with auto-generated comparison story prose.
- Deliverables:
  - Two MP selectors (dropdown/search)
  - Side-by-side stat cards: total contributions, breakdown by type
  - Comparison story prose (e.g., "Boko's motions suggest legislative initiative; Furniture's oral questions indicate oversight focus")
  - Bar chart comparison
  - Download as PDF
- Acceptance:
  - [ ] Selecting two MPs shows side-by-side data
  - [ ] Comparison story prose is auto-generated and meaningful
  - [ ] PDF download works
- Demo commands:
  - Select Boko vs Furniture → verify comparison renders
  - Click "Download as PDF"
- Evidence:
  - Screenshot of comparison; PDF file content verified

### 3.6 — Screen 06: Participation Index (Leaderboard)
- depends_on: [3.0, 2.1]
- parallel_eligible: true
- flag: frontend_rank_06
- **Objective:**
  Build ranked participation leaderboard with proxy-metric caveat always visible.
- Deliverables:
  - Ranked table: Rank | MP | Party | Score | Breakdown
  - Party filter
  - CSV export
  - Amber caveat: "Proxy metric — based on recorded contributions only. Not attendance data." Always visible, not dismissible
  - Each MP row clickable → MP Profile
- Acceptance:
  - [ ] Leaderboard renders with correct weighted scores
  - [ ] Party filter narrows results
  - [ ] Caveat is a structural UI element (not a popup), always visible
- Demo commands:
  - Filter by party; click an MP row
- Evidence:
  - Screenshot showing caveat as structural element, not popup

### 3.7 — Screen 07: Bill Tracker
- depends_on: [3.0, 2.0]
- parallel_eligible: true
- flag: frontend_bills_07
- **Objective:**
  Build legislative bill tracker with stage progression timeline.
- Deliverables:
  - Bill list with stage filter (Introduced, 1st Reading, 2nd Reading, Committee, 3rd Reading, Passed)
  - Bill detail with stage progression timeline (Blueprint.js Timeline)
  - "View debate" link → Screen 02 filtered to that bill
- Acceptance:
  - [ ] Bill list filters by stage
  - [ ] Bill detail shows stage timeline with current stage highlighted
  - [ ] "View debate" navigates to filtered feed
- Demo commands:
  - Filter by "2nd Reading"; click a bill; click "View debate"
- Evidence:
  - Screenshots of list and detail views

### 3.8 — Screen 08: Full-Text Search
- depends_on: [3.0, 2.0]
- parallel_eligible: true
- flag: frontend_search_08
- **Objective:**
  Build full-text search across subjects, MP names, and ministries.
- Deliverables:
  - Search input (accessible via ⌘K shortcut)
  - Filter bar: type, party, ministry
  - Results grouped by relevance with MP name, contribution type, date
  - Clear filters
  - Result click → contribution detail
- Acceptance:
  - [ ] Search returns relevant results from API
  - [ ] Filters narrow results
  - [ ] ⌘K opens search from any screen
  - [ ] Results link to contribution detail
- Demo commands:
  - Press ⌘K; type "Mohembo Bridge"; click result
- Evidence:
  - Search results screenshot; ⌘K shortcut verified

## Stage 4 — Administration & Auth (RBAC)

### 4.0 — Auth system (login, JWT, roles)
- depends_on: [2.0]
- parallel_eligible: true
- flag: admin_auth
- **Objective:**
  Implement email+password authentication with JWT tokens and RBAC (Admin/Editor/Viewer).
- Deliverables:
  - `backend/api/auth/login.py` — POST `/api/v1/auth/login` with JWT
  - `backend/api/auth/logout.py` — POST `/api/v1/auth/logout`
  - `backend/api/auth/me.py` — GET `/api/v1/auth/me` (current user + role)
  - `backend/db/schema.sql` — `users`, `sessions` tables
  - Password hashing via `passlib` + `bcrypt`
  - `backend/api/middleware/auth.py` — `get_current_user()`, `require_role(roles)` FastAPI dependencies
  - Frontend: `AuthContext` React context, `ProtectedRoute` component, Login page
  - JWT in httpOnly cookie
- Acceptance:
  - [ ] Login with valid credentials returns JWT cookie
  - [ ] Login with invalid credentials returns 401
  - [ ] Protected routes correctly reject insufficient roles (e.g., Viewer accessing admin-only endpoint)
  - [ ] `/admin/*` routes guarded by ProtectedRoute
- Demo commands:
  - `curl -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"email":"admin@bareng.bw","password":"test"}'`
  - Navigate to `/admin` unauthenticated → redirect to `/login`
- Evidence:
  - curl output showing JWT; login → redirect flow

### 4.1 — Admin Dashboard (Screen 09)
- depends_on: [4.0, 3.0]
- parallel_eligible: true
- flag: admin_dashboard_09
- **Objective:**
  Build admin dashboard with pipeline health, data quality stats, crawl runs, and quick links.
- Deliverables:
  - Pipeline health stat cards (crawler status, last run, doc count, unresolved count)
  - Data quality stats
  - Recent crawl runs table
  - Quick links to Entity Review, User Management, Crawl Log
  - Trigger Crawl button (Admin only)
  - Export button
- Acceptance:
  - [ ] Dashboard shows real pipeline health from `GET /api/v1/status`
  - [ ] Trigger Crawl button initiates crawl (Admin only, hidden from Editor/Viewer)
  - [ ] Quick links navigate to correct admin screens
  - [ ] Role-gating: Viewer sees health read-only, no Trigger Crawl
- Demo commands:
  - Login as Admin → see Trigger Crawl; login as Viewer → it is hidden
  - Click each quick link
- Evidence:
  - Screenshots of admin dashboard in Admin and Viewer roles

### 4.2 — Entity Review Queue (Screen 10)
- depends_on: [4.0, 1.2]
- parallel_eligible: true
- flag: admin_entities_10
- **Objective:**
  Build entity review queue for resolving unmatched MP names with suggestion engine.
- Deliverables:
  - Unresolved entity list with raw name, source document, suggested MP match
  - Resolve dropdown → choose matching MP from roster
  - Resolve button → updates `entity_review_queue.status='RESOLVED'` and sets `mp_id`
  - Skip button → marks as `IGNORED`
  - Refresh button
- Acceptance:
  - [ ] Queue shows all UNRESOLVED entities from `entity_review_queue`
  - [ ] Resolve flow updates DB correctly
  - [ ] Skip flow marks as IGNORED, removes from active queue
  - [ ] Editor+ can access; Viewer sees read-only list
- Demo commands:
  - Login as Editor; skip an entity; resolve another → verify DB state
- Evidence:
  - Screenshots of queue before/after resolution

### 4.3 — User Management (Screen 11, Admin only)
- depends_on: [4.0]
- parallel_eligible: true
- flag: admin_users_11
- **Objective:**
  Build user management screen for CRUD users with role assignment.
- Deliverables:
  - User table: Email | Display Name | Role | Status | Last Login | Actions
  - Inline edit: change role, deactivate/reactivate
  - Add User form: email, display name, role → sends invitation
  - Role badges (Admin=red, Editor=amber, Viewer=blue)
- Acceptance:
  - [ ] Admin can create, edit, and deactivate users
  - [ ] Role changes take effect immediately (next API call)
  - [ ] Non-Admin users cannot access this screen (route-guarded)
- Demo commands:
  - Login as Admin → create a new Editor user; login as that user → verify only Editor-accessible screens
- Evidence:
  - Screenshots of user table, add form, role badges

## Stage 5 — Launch & Publishing

### 5.0 — Static site build + deploy
- depends_on: [3.8, 4.3]
- parallel_eligible: true
- flag: no flag — deploy
- **Objective:**
  Configure the frontend as a fully static site that can be deployed to GitHub Pages or Vercel.
- Deliverables:
  - Vite static build output configured for SPA routing
  - Backend API as a separate deployment (FastAPI on VPS or serverless)
  - GitHub Actions deploy workflow
  - `CNAME` or custom domain config if applicable
- Acceptance:
  - [ ] `npm run build` produces a deployable static site
  - [ ] SPA routing works on the static host (404 → index.html)
  - [ ] All API calls point to the live backend URL
- Demo commands:
  - `cd frontend && npm run build && npx serve dist`
- Evidence:
  - Build output; site loads in browser with live data

### 5.1 — Social draft-post generator
- depends_on: [5.0]
- parallel_eligible: true
- flag: social_publisher
- **Objective:**
  Generate draft social posts for new contributions since last run, with human-in-loop review gate.
- Deliverables:
  - `backend/social/draft_generator.py` — diff contributions since last run, generate draft posts
  - Draft review queue (markdown file or simple DB table)
  - Never auto-post: human must approve before any tweet/post goes live
- Acceptance:
  - [ ] Generator produces readable draft posts from new contributions
  - [ ] Drafts land in review queue, never posted automatically
  - [ ] Running twice produces no duplicates
- Demo commands:
  - `python -m backend.social.draft_generator`
  - Review generated drafts in queue
- Evidence:
  - Draft text output; review queue showing pending drafts

## Post-MVP (not in current scope)

- Hansard parser (free-form debate transcripts)
- Promise-vs-delivery tracking (cross-ref with manifesto)
- WhatsApp/citizen query layer (from RAIA pattern)
- AI bill summaries (with human review)
- CSV/PDF export on every view
- Ministries most-questioned leaderboard
- Head-to-head MP comparison (Screen 05, improved)
