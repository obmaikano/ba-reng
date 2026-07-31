"""System-learning pipeline — collect, consolidate, and export knowledge.

The system learns from its own data (entity resolutions, ministry keyword
mappings, glossary, data quality). The learned knowledge is exported to
plain files any model can read. No model is trained or called.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.learn.collector import SystemCollector
from backend.learn.config import get_config
from backend.learn.connection import LearnConnection
from backend.learn.export import KnowledgeExporter
from backend.learn.memory import Memory

logger = logging.getLogger(__name__)


class LearningPipeline:
    """Orchestrate the system-learning loop."""

    def __init__(self) -> None:
        """Initialize collector, memory, and exporter."""
        self._collector = SystemCollector()
        self._memory = Memory()
        self._exporter = KnowledgeExporter()

    def collect(self) -> dict[str, int]:
        """Harvest knowledge from the live database.

        Returns:
            Per-source counts of facts stored.
        """
        return self._collector.collect_all()

    def consolidate(self) -> int:
        """Prune stale, low-confidence memory entries.

        Returns:
            Number of entries pruned.
        """
        return self._memory.prune()

    def export(self) -> dict[str, str]:
        """Write the knowledge artifacts.

        Returns:
            Dict of artifact kind to output path.
        """
        return self._exporter.export_all()

    def run(self) -> dict[str, Any]:
        """Run the full learning loop.

        Returns:
            Dict with collected counts, pruned count, and export paths.
        """
        collected = self.collect()
        pruned = self.consolidate()
        exports = self.export()
        return {
            'collected': collected,
            'pruned': pruned,
            'exports': exports,
        }

    def status(self) -> dict[str, Any]:
        """Return current learning status.

        Returns:
            Dict with memory stats and export paths.
        """
        cfg = get_config()
        return {
            'memory': self._memory.stats(),
            'exports': {
                'markdown': cfg.markdown_path,
                'json': cfg.json_path,
            },
        }

    def close(self) -> None:
        """Close the shared database connection."""
        LearnConnection.close()
