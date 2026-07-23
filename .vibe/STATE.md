# STATE

## Session read order

1) `AGENTS.md` (optional if already read this session)
2) `.vibe/STATE.md` (this file)
3) `.vibe/SPRINT.md`
4) `.vibe/PLAN.md`
5) `.vibe/HISTORY.md` (optional)

## Current focus

- Stage: 0
- Checkpoint: 0.0 — Project scaffolding & setup
- Status: NOT_STARTED
- Sprint: 1

## Objective (current checkpoint)

Initialize the Ba Reng monorepo with Python backend scaffold, React/Vite/Blueprint.js frontend scaffold, and all configuration files so subsequent checkpoints build on a consistent foundation.

## Deliverables (current checkpoint)

- Initialize git repo (if not already)
- Backend scaffold: `backend/` with `pyproject.toml`, FastAPI skeleton, SQLite schema migrations directory
- Frontend scaffold: `frontend/` with Vite + React 19 + Blueprint.js + Tailwind CSS
- Shared config: `.env.example`, `Makefile` with common commands
- `.gitignore` excluding `.vibe/`, node_modules, .env, build artifacts

## Acceptance (current checkpoint)

- [ ] `make install` installs backend and frontend dependencies without errors
- [ ] `make dev-backend` starts FastAPI dev server on `localhost:8000`
- [ ] `make dev-frontend` starts Vite dev server on `localhost:5173`
- [ ] `tsc --noEmit` clean on frontend
- [ ] `git status` shows clean working tree after init

## Work log (current session)

- 2026-07-23: Architecture & design complete — BA_RENG_ARCHITECTURE_AND_DESIGN.md (10 sections), BA_RENG_USER_JOURNEY_MAP.md (146 touchpoints, 4 personas), ba-reng-combined.html (11-screen merged mockup). Vibe workflow files created from movers template.

## Evidence

## Active issues

- ISSUE-001: Refero MCP tools not configured — used web research + bundled craft methodology instead
  - Impact: MINOR
  - Status: OPEN
  - Owner: human
  - Unblock Condition: Refero MCP server installed and configured

## Decisions

- 2026-07-23: Using Vibe workflow (copied from movers project) for agent orchestration
- 2026-07-22: Blueprint.js (not shadcn/Radix) for data-dense tables and native dark mode
- 2026-07-22: Palantir-inspired visual direction — cold slate canvas, zero radius, hairline borders, functional color
- 2026-07-22: Participation Index explicitly labeled PROXY_METRIC with enforced component-level caveat
- 2026-07-22: Unresolved entity names stored in `entity_review_queue` — never silently guessed
