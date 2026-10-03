# Commands for people and coding agents (standard §6.1). `make check` is the "done" gate.
.DEFAULT_GOAL := help
.PHONY: help check fmt lint types test migrate migration downgrade db-up db-down db-reset run worker audit image token invite

# The local database: the same container as the root Makefile's `make db-up`. Settings come from
# .env.example (then .env).
DB_CONTAINER ?= agenthub-pg
DB_PORT ?= 55432

help: ## List targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

check: lint types migrate test audit ## The done gate: lint, format, types, migrations in sync, tests, audit. Needs `make db-up`.
	uv run alembic check
	@echo "make check: all passed"

fmt: ## Fix lint and formatting where possible
	uv run ruff check --fix .
	uv run ruff format .

lint: ## Lint and format check
	uv run ruff check .
	uv run ruff format --check .

types: ## mypy, strict
	uv run mypy

test: ## Unit, integration and contract tests (integration and contract need `make db-up`)
	uv run pytest

migrate: ## Apply migrations to $$DATABASE_URL_DIRECT or $$DATABASE_URL
	uv run alembic upgrade head

migration: ## New migration from the models, numbered 0002, 0003…: make migration m="add invoices"
	@n=$$(printf %04d $$(( $$(ls migrations/versions/[0-9]*.py 2>/dev/null | wc -l) + 1 ))); \
	uv run alembic revision --autogenerate --rev-id $$n -m "$(m)" && \
	f=$$(ls migrations/versions/$${n}_*.py) && \
	sed -i.bak '/# ### /d' "$$f" && rm -f "$$f.bak" && uv run ruff format -q "$$f"

downgrade: ## Undo the latest migration (local database)
	uv run alembic downgrade -1

db-up: ## Start a disposable local Postgres 17
	@docker start $(DB_CONTAINER) >/dev/null 2>&1 || docker run -d --rm --name $(DB_CONTAINER) \
		-e POSTGRES_PASSWORD=dev -e POSTGRES_DB=agent_hub -p $(DB_PORT):5432 postgres:17-alpine >/dev/null
	@until docker exec $(DB_CONTAINER) pg_isready -U postgres >/dev/null 2>&1; do sleep 1; done
	@echo "Postgres ready on localhost:$(DB_PORT)"

db-down: ## Stop the local Postgres (its data is discarded)
	@docker stop $(DB_CONTAINER) >/dev/null 2>&1 || true

db-reset: ## Empty the local database (drop every table and the migration history)
	docker exec $(DB_CONTAINER) psql -U postgres -d agent_hub -q -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

run: ## Run the API locally on :8000
	uv run python -m app.serve

worker: ## Run the job worker locally
	uv run python -m app.worker

audit: ## Known vulnerabilities in the locked dependencies
	uv export --format requirements.txt --no-emit-project --no-dev --locked --quiet -o requirements-audit.txt
	uv run pip-audit -r requirements-audit.txt --disable-pip --require-hashes --progress-spinner off
	@rm -f requirements-audit.txt

invite: ## Let an email sign in (D9): make invite email=<address> (uses DATABASE_URL)
	uv run python -m app.cli users invite "$(email)"

token: ## Print a local access token: make token [user=<uuid>]
	@uv run python -c "import sys, uuid; from app.core.auth import issue_access_token; \
	from app.core.settings import get_settings; s = get_settings(); \
	s.env == 'local' or sys.exit('make token is for local use only'); \
	print(issue_access_token(s, uuid.UUID('$(user)') if '$(user)' else uuid.uuid4()))"

image: ## Build the arm64 image, tagged with the git SHA
	docker build --platform linux/arm64 -t agent-hub-api:$$(git rev-parse --short HEAD) .
