# Contributing to Ba Reng?

All contributions are welcome. This is an open government weekend project — your first PR is a great start.

## Getting Started

1. Fork the repository.
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/ba-reng.git
   cd ba-reng
   ```
3. Copy the environment file:
   ```bash
   cp .env.example .env
   ```
4. Start the dev environment:
   ```bash
   docker compose up --build
   ```
   Or use the native fallback:
   ```bash
   make install
   make dev-backend  # terminal 1
   make dev-frontend # terminal 2
   ```

## Code Standards

| Check | Command | Config |
|-------|---------|--------|
| Python lint | `make lint` | ruff (pyproject.toml) |
| TypeScript check | `make typecheck` | tsconfig.json |
| Frontend lint | `make lint` | eslint.config.js |
| Tests | `make test` | pytest |

Hard limits enforced:
- Python: max complexity 15, max args 7, max nested blocks 4
- TypeScript: max complexity 15, max depth 4, max params 7, max lines 1000

## Pull Request Workflow

1. Create a feature branch from `main`:
   ```bash
   git checkout -b checkpoint/0.x-your-feature
   ```
2. Make your changes. Keep diffs small and reviewable.
3. Run lint and typecheck:
   ```bash
   make lint && make typecheck
   ```
4. Push and open a PR against `main`:
   ```bash
   git push origin checkpoint/0.x-your-feature
   ```
   PR title format: `0.x: Short description`

## Code of Conduct

Be respectful. We are all here to learn and build something useful for Botswana.

## Questions

Open a [GitHub Issue](https://github.com/obmaikano/ba-reng/issues) or start a Discussion.
