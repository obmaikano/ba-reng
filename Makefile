.PHONY: install install-backend install-frontend dev-backend dev-frontend lint lint-backend lint-frontend test test-backend typecheck build clean

BACKEND_DIR = backend
FRONTEND_DIR = frontend
VENV = $(BACKEND_DIR)/.venv

install: install-backend install-frontend init-vibe

install-backend:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -e .
	$(VENV)/bin/pip install pytest ruff

install-frontend:
	cd $(FRONTEND_DIR) && npm install

init-vibe:
	@if [ ! -f .vibe/STATE.md ]; then \
		mkdir -p .vibe; \
		echo "# STATE\n\n## Current focus\n\n- Stage: 0\n- Checkpoint: 0.0\n- Status: NOT_STARTED" > .vibe/STATE.md; \
		echo "# HISTORY\n\nInitialized $(shell date +%Y-%m-%d)" > .vibe/HISTORY.md; \
		echo "Vibe tracking initialized."; \
	fi

dev-backend:
	$(VENV)/bin/uvicorn backend.main:app --reload --port 8000

dev-frontend:
	cd $(FRONTEND_DIR) && npm run dev

lint: lint-backend lint-frontend

lint-backend:
	$(VENV)/bin/ruff check $(BACKEND_DIR)

lint-frontend:
	cd $(FRONTEND_DIR) && npm run lint

test: test-backend

test-backend:
	$(VENV)/bin/pytest

typecheck:
	cd $(FRONTEND_DIR) && npm run typecheck

build:
	cd $(FRONTEND_DIR) && npm run build

clean:
	rm -rf $(VENV)
	rm -rf $(FRONTEND_DIR)/node_modules $(FRONTEND_DIR)/dist
	rm -rf data/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
