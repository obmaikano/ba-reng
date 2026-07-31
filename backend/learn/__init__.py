"""System-learning module — the system learns from its own data.

The learning target is the system, not a model. Knowledge is harvested
from the live database (entity resolutions, ministry keyword mappings,
glossary, data quality) and exported to plain, model-agnostic files
(docs/LEARNED.md and data/knowledge/learned.json) that any model working
on this codebase can read.

Layers:
  config       — Shared configuration (env vars, defaults)
  connection   — Thread-safe SQLite connection (singleton)
  memory       — Persistent knowledge store (facts, decisions, patterns)
  decision     — Structured decision log with outcome-based learning
  collector    — Harvests knowledge from the live app database
  export       — Model-agnostic markdown/JSON knowledge export
  pipeline     — Orchestrates collect -> consolidate -> export
  run          — CLI entry point (python -m backend.learn.run)
  program.md   — System-learning objectives and constraints
"""
