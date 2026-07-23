# VIBE

This repo uses the Vibe coding-agent workflow.

## Start here (read order)

1) `AGENTS.md` (execution contract)
2) `.vibe/STATE.md` (current focus: stage/checkpoint/status)
3) `.vibe/SPRINT.md` (current sprint window, WIP limit, committed checkpoints)
4) `.vibe/PLAN.md` (checkpoint backlog + acceptance criteria)
5) `.vibe/HISTORY.md` (optional context; non-authoritative)

## Working files

Project-specific workflow files live under `.vibe/` and are gitignored:
- `.vibe/STATE.md`
- `.vibe/SPRINT.md`
- `.vibe/PLAN.md`
- `.vibe/HISTORY.md`
- `.vibe/CONTEXT.md`

## Canonical STATE.md format

```md
# STATE

## Session read order
1) `AGENTS.md` (optional if already read this session)
2) `.vibe/STATE.md` (this file)
3) `.vibe/PLAN.md`
4) `.vibe/HISTORY.md` (optional)

## Current focus
- Stage: 0
- Checkpoint: 0.0
- Status: NOT_STARTED
- Sprint: <N> (tagged when committed in SPRINT.md)

## Objective (current checkpoint)

## Deliverables (current checkpoint)

## Acceptance (current checkpoint)

## Work log (current session)

## Evidence

## Active issues
- [ ] ISSUE-001: <short title>
  - Impact: QUESTION | MINOR | MAJOR | BLOCKER
  - Status: OPEN | IN_PROGRESS | BLOCKED | RESOLVED
  - Owner: agent|human
  - Unblock Condition: <what must be true to proceed>
  - Evidence Needed: <command/output/link proving resolution>
  - Notes: <optional context>

## Decisions
- YYYY-MM-DD: <decision> (1-2 line rationale)
```

## Canonical PLAN.md format

```md
# PLAN

## Stage <N> — <stage name>

### <N>.<M> — <checkpoint name>
- depends_on: []
- parallel_eligible: true|false
- flag: <flag name> | no flag — <reason>
- sprint: <N>
- Objective:
  - <1 sentence>
- Deliverables:
  - <concrete files/modules/behaviors>
- Acceptance:
  - [ ] <verifiable condition>
- Demo commands:
  - `<exact command>`
- Evidence:
  - <what to paste into STATE.md Evidence>
```

## Workflow

- `IN_PROGRESS` → implement → `IN_REVIEW` → product_validation/review → PASS → `DONE`
- `BLOCKED` or `BLOCKER` issue → triage → resolve or stop

## Postmortems

Any issue that reaches `IN_REVIEW` with a real defect, or ships with one, gets a postmortem in `docs/postmortems/`.

## Commit discipline

- Imperative mood, prefix with checkpoint ID
- At least 1 commit per completed checkpoint
- No WIP commits
- Never commit broken builds/tests
