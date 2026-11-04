.PHONY: help setup test lint fmt api web ingest up down clean

help: ## Show this help
	@grep -hE '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed -e 's/:.*## /\t/' | expand -t 12

setup: ## Install the dependencies for both services
	cd api && uv sync
	cd web && npm install

test: ## Run the tests
	cd api && uv run pytest -q

lint: ## Check the style and the types
	cd api && uv run ruff check . && uv run ruff format --check .
	cd web && npm run lint && npm run typecheck

fmt: ## Format the code
	cd api && uv run ruff check --fix . && uv run ruff format .

api: ## Run the API on port 8000
	PYTHONPATH=api uv run --project api uvicorn app.main:app --reload --port 8000

web: ## Run the web app on port 3000
	cd web && npm run dev

ingest: ## Index a repository. Use REPO=<path or git url>
ifndef REPO
	$(error Set REPO. For example: make ingest REPO=~/.config/dotfiles)
endif
	PYTHONPATH=api uv run --project api python -m app.ingest.cli "$(REPO)" --db data/store.db

up: ## Build and start the containers
	docker compose up --build

down: ## Stop the containers
	docker compose down

clean: ## Remove the build output
	rm -rf api/.venv api/.pytest_cache api/.ruff_cache web/node_modules web/.next
