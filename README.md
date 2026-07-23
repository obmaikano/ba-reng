# Ba Reng?

**Botswana Parliament MP Monitor**

Ba Reng? (Setswana: "What did they say?") tracks MP contributions, and parliamentary activity from public sources. It gives citizens a clear view of who speaks, what they say, and how they vote.

An open government weekend project.

## Quick Start

```bash
docker compose up --build
```

Open http://localhost:5173. Backend API at http://localhost:8000.

Without Docker:

```bash
make install      # install backend + frontend deps
make dev-backend  # uvicorn on :8000
make dev-frontend # vite on :5173
```

## Data Sources

| Source | Data | Frequency |
|--------|------|-----------|
| botswanaspeaks.gov.bw | MP contributions, order papers | Daily |
| Wikipedia (13th Parliament) | MP roster, constituencies | Static |
| Parliament website | Hansard | Per session |

## Visual Direction

Palantir-inspired: cold slate canvas (`#0B0E14`), zero-radius UI, hairline borders, Inter + JetBrains Mono. Data is the visual — no decoration.

See `docs/mockups/combined.html` for the full merged mockup.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLite |
| Frontend | React 19, Blueprint.js v6, Tailwind CSS v4, Vite |
| Infrastructure | Docker Compose |

## Project Structure

```
backend/          # FastAPI + SQLite
  api/            # Route handlers
  crawl/          # Source connectors
  db/             # Database connection + migrations
  parse/          # Document parsers
  resolve/        # Entity resolution
  roster/         # MP roster management
  routes/         # View routes
  social/         # Social feed pipeline
frontend/         # React SPA
docs/             # Architecture, mockups, user journeys
```

## Roadmap

- **P0**: Core pipeline — feed, MP profiles, search, filters
- **P1**: Coverage & trust — order paper, MP review period, compare, bills
- **P2**: Hansard transcripts, AI summaries, WhatsApp bot

## License

MIT

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). All skill levels welcome — this is a learning project.
