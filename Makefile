.PHONY: install dev dev-backend dev-frontend lint test typecheck build clean dc-up dc-down dc-build dc-logs

BACKEND_DIR = backend
FRONTEND_DIR = frontend
VENV = $(BACKEND_DIR)/.venv

# Native (local) targets — fallback when Docker is not available
install:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip -q
	$(VENV)/bin/pip install -e . -q
	$(VENV)/bin/pip install "pytest>=8" "pytest-cov>=6" "httpx2" "ruff>=0.6" -q
	cd $(FRONTEND_DIR) && npm install

dev-backend:
	$(VENV)/bin/uvicorn backend.main:app --reload --port 8000

dev-frontend:
	cd $(FRONTEND_DIR) && npm run dev

lint:
	$(VENV)/bin/ruff check $(BACKEND_DIR)
	cd $(FRONTEND_DIR) && npm run lint

test:
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

# Docker targets (primary dev workflow)
dc-up:
	docker compose up --build

dc-down:
	docker compose down

dc-build:
	docker compose build

dc-logs:
	docker compose logs -f
