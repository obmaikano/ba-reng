"""Command-line entry point for the system-learning pipeline.

Usage:
    python -m backend.learn.run

Runs the full loop: collect -> consolidate -> export, then prints a
JSON summary. The exported markdown digest (docs/LEARNED.md) is the
model-agnostic knowledge artifact any model can read.
"""

from __future__ import annotations

import argparse
import json

from backend.learn.pipeline import LearningPipeline


def main() -> None:
    """Run the learning pipeline and print the result as JSON."""
    parser = argparse.ArgumentParser(
        description='Run the Ba Reng? system-learning pipeline.',
    )
    parser.add_argument(
        '--export-only',
        action='store_true',
        help='Skip collection; only re-export existing knowledge.',
    )
    args = parser.parse_args()

    pipeline = LearningPipeline()
    try:
        if args.export_only:
            result = {'exports': pipeline.export()}
        else:
            result = pipeline.run()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    finally:
        pipeline.close()


if __name__ == '__main__':
    main()
