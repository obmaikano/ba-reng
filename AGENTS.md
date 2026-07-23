# AGENTS.md — Execution Contract (Repo Baseline)

## Purpose

This file defines the working contract for coding agents and humans collaborating in this repository.

- This repo uses **project-local workflow files** stored under `.vibe/`.
- The agent must follow the **precedence order** and **stop conditions** below.

## Authoritative files and precedence

When instructions conflict, follow this order:

1. **User instructions in the current chat**
2. **This file: `AGENTS.md`**
3. **`.vibe/STATE.md`** (current truth: what we are doing now)
4. **`.vibe/SPRINT.md`** (current sprint commitments and WIP limit)
5. **`.vibe/PLAN.md`** (checkpoint backlog and acceptance criteria)
6. **`.vibe/HISTORY.md`** (non-authoritative rollups, context only)
7. Repository source code and tests
8. Anything else (including assumptions)

## Required behavior

### Read order at the start of a session

1. Read `AGENTS.md` (optional if already read this session)
2. Read `.vibe/STATE.md`
3. Read `.vibe/SPRINT.md`
4. Read `.vibe/PLAN.md`
5. Optionally read `.vibe/HISTORY.md` if needed

### Work granularity

- Do **one coherent unit of work** at a time (typically one checkpoint step).
- Prefer **small, reviewable diffs**.
- When ambiguity affects correctness, ask **1–2 clarifying questions max** as issues in `.vibe/STATE.md`, then stop.

### Output discipline

- Keep outputs concise and structured.
- Prefer checklists, acceptance evidence, and exact commands over narrative.

### Quality bar (hard rule)

- The standard is **operator-trust quality**, not "the code changed" or "a placeholder output exists."
- The agent must actively understand the **user's real intent**.
- Do not stop at the first technically passing condition.
- Quality gates must validate **meaningful behavior**.
- If behavior is confusing, disappointing, or clearly below the intended bar, treat that as unfinished work.
- If the result is brittle, misleading, stub-like, or likely to fail the first real manual test, keep going.
- Prefer fewer honest `BLOCKED`/`IN_REVIEW` states over weak signoffs.

## Role loops

| Role key | Intent |
|---|---|
| `design` | Refine checkpoints in `.vibe/PLAN.md` |
| `implement` | Implement active checkpoint deliverables |
| `product_validation` | Verify user value and scope before technical review |
| `review` | Verify acceptance and decide PASS/FAIL |
| `issues_triage` | Resolve/clarify active issues |
| `advance` | Move pointer to next checkpoint |
| `consolidation` | Archive completed stage |
| `stop` | End loop when plan is exhausted |

## Stop conditions (hard)

Stop and ask for input (as issue) if:
- Missing required information to meet acceptance criteria
- Conflicting instructions between authoritative sources
- A decision point that changes scope, architecture, or dependencies
- The work would require secrets, credentials, destructive actions, or external side effects
- Tests/builds fail and the failure mode is not clearly attributable to the change

## Issue handling (lightweight)

Each active issue in `.vibe/STATE.md` must use:

```
- [ ] ISSUE-<id>: <short title>
  - Impact: QUESTION|MINOR|MAJOR|BLOCKER
  - Status: OPEN|IN_PROGRESS|BLOCKED|RESOLVED
  - Owner: agent|human
  - Unblock Condition: <what must be true to proceed>
  - Evidence Needed: <command/output/link proving resolution>
  - Notes: <optional context>
```

## Version control policy

### Branch discipline (hard rule)

- Create a **feature branch** for each checkpoint: `checkpoint/0.1-scraper-skeleton`.
- Work on the feature branch, not `main`.
- Push the feature branch when the checkpoint is ready for review.
- Open a **Pull Request** against `main` for every checkpoint completion.
- Never push directly to `main`.

### Commit discipline (hard rule)

- If you change tracked files, you must produce commits.
- **Before setting Status to `IN_REVIEW`**, ensure at least one commit exists implementing the checkpoint and files are clean.
- Minimum standard: **≥ 1 commit per completed checkpoint**.
- Use imperative mood. Prefix with checkpoint ID, e.g., `0.1: Add scraper skeleton`.
- Never commit knowingly broken builds/tests.

### PR discipline (hard rule)

- Always create a PR for every checkpoint, even single-commit checkpoints.
- PR title: checkpoint ID + short description, e.g. `0.1: Add scraper skeleton`.
- Do not merge your own PR unless the user explicitly asks.
- After PR is created, present the PR URL to the user.
