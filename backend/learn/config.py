"""Shared configuration for the system-learning module."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class LearnConfig:
    """Configuration for the system-learning module.

    Environment variables:
        DATABASE_PATH: SQLite database path, shared with the main app.
        LEARN_MARKDOWN_PATH: Markdown knowledge digest path.
        LEARN_JSON_PATH: Structured knowledge export path.
    """

    db_path: str = field(
        default_factory=lambda: os.environ.get(
            'DATABASE_PATH',
            str(PROJECT_ROOT / 'data' / 'bareng.db'),
        ),
    )
    project_root: str = field(default_factory=lambda: str(PROJECT_ROOT))
    markdown_path: str = field(
        default_factory=lambda: os.environ.get(
            'LEARN_MARKDOWN_PATH',
            str(PROJECT_ROOT / 'docs' / 'LEARNED.md'),
        ),
    )
    json_path: str = field(
        default_factory=lambda: os.environ.get(
            'LEARN_JSON_PATH',
            str(PROJECT_ROOT / 'data' / 'knowledge' / 'learned.json'),
        ),
    )
    memory_table: str = 'learn_memory'
    decision_table: str = 'learn_decision'
    memory_prune_age_days: int = 30
    export_limit: int = 500


@lru_cache(maxsize=1)
def get_config() -> LearnConfig:
    """Return the singleton LearnConfig instance."""
    return LearnConfig()
