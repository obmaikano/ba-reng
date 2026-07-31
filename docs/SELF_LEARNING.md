# System Learning

The system learns from its own operational data. The learning target is the
system, not a model. No model is trained, fine-tuned, or called. No vector
database or LLM API is used.

## What the system learns

The pipeline harvests durable knowledge from the live database:

| Source | Knowledge |
|--------|-----------|
| `entity_review_queue` | Ground-truth entity resolutions: raw name -> MP |
| `ministry_keywords` (static seed) | Canonical ministry keyword mappings |
| `parliamentary_glossary` | Setswana -> English glossary terms |
| Database snapshot | Document counts, contribution counts, review state |

## How knowledge is consumed

The pipeline writes two model-agnostic artifacts:

- `docs/LEARNED.md` — markdown digest, committed to the repo.
- `data/knowledge/learned.json` — structured export, runtime artifact.

Any model working on this codebase can read `docs/LEARNED.md` as context.
The digest is plain text. It has no dependency on a specific model,
embedding store, or API.

## Run the pipeline

```bash
make learn-run
# or: python -m backend.learn.run
```

Re-export without re-collecting:

```bash
make learn-export
```

Show status:

```bash
make learn-status
```

## Python API

```python
from backend.learn.pipeline import LearningPipeline

pipeline = LearningPipeline()
result = pipeline.run()
print(result['collected'])
print(result['exports'])
pipeline.close()
```

## Decision log

Agents may record structured decisions. Successful decisions become memory
entries with boosted confidence. See `backend/learn/decision.py`.

```python
from backend.learn.decision import DecisionLog

d = DecisionLog()
did = d.record(
    "Normalise ministry names before matching",
    "Strip prefixes and look up the canonical name in the DB",
    files_read=["backend/parse/base.py"],
    constraints_checked=["All tests must pass"],
)
d.mark_outcome(did, "success", "9 tests fixed")
```

## Program

`backend/learn/program.md` holds the system-learning objectives, commands,
and constraints. Edit it to change what the system records.
