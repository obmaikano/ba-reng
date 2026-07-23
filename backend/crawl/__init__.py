"""Connector registry for data source crawlers."""

from typing import Any

from backend.db.connection import get_connection

REGISTRY: list[str] = []


def register(name: str) -> None:
    """Add a connector module name to the crawl registry."""
    REGISTRY.append(name)


def crawl_all() -> dict[str, dict[str, Any]]:
    """Run every registered crawler and return results keyed by name."""
    conn = get_connection()
    results: dict[str, dict[str, Any]] = {}
    for name in REGISTRY:
        try:
            mod = __import__(f'backend.crawl.{name}', fromlist=['crawl'])
            result = mod.crawl(conn)
            results[name] = result
        except Exception as exc:  # noqa: BLE001
            results[name] = {'status': 'ERROR', 'error': str(exc)}
    conn.close()
    return results
