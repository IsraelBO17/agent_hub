# Shortcuts for common commands. Each folder keeps its own tools (uv, npm, terraform); this file only calls them.
# Run `make` to list targets.

# Local, disposable Postgres (api/README.md). Override DATABASE_URL_DIRECT to point elsewhere.
DB_CONTAINER ?= agenthub-pg
DB_PORT ?= 55432
export DATABASE_URL_DIRECT ?= postgresql://postgres:dev@localhost:$(DB_PORT)/agent_hub

.DEFAULT_GOAL := help
.PHONY: help db-up db-down api-migrate api-check api-test contract-lint design-index infra-validate infra-plan-bootstrap infra-init infra-plan

help: ## List targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-22s %s\n", $$1, $$2}'

db-up: ## Start the local Postgres 17 container
	@docker start $(DB_CONTAINER) >/dev/null 2>&1 || docker run -d --rm --name $(DB_CONTAINER) \
		-e POSTGRES_PASSWORD=dev -e POSTGRES_DB=agent_hub -p $(DB_PORT):5432 postgres:17-alpine >/dev/null
	@until docker exec $(DB_CONTAINER) pg_isready -U postgres >/dev/null 2>&1; do sleep 1; done
	@echo "Postgres ready on localhost:$(DB_PORT)"

db-down: ## Stop the local Postgres container (its data is discarded)
	@docker stop $(DB_CONTAINER) >/dev/null 2>&1 || true

api-migrate: ## Apply migrations to the local database
	cd api && uv run alembic upgrade head

api-check: ## Check the models and migrations agree
	cd api && uv run alembic upgrade head && uv run alembic check

api-test: ## Run the API tests (they recreate the schema; local database only)
	cd api && uv run pytest

contract-lint: ## Lint the OpenAPI contract
	cd api && npx -y @redocly/cli@2.56.1 lint openapi.yaml

design-index: ## Regenerate design/INDEX.md after saving the design in Pencil
	python3 design/tools/pen_index.py

# Terraform: plans only. Applying is a deliberate `terraform -chdir=... apply` after reading the plan (infra/README.md).
# TF_DATA_DIR keeps validation away from the real backend setup, so it needs no AWS credentials.
infra-validate: ## Format-check and validate the Terraform (no AWS calls)
	terraform -chdir=infra fmt -check -recursive
	cd infra/bootstrap && TF_DATA_DIR=.terraform-validate terraform init -backend=false -input=false >/dev/null && TF_DATA_DIR=.terraform-validate terraform validate
	cd infra/envs/dev && TF_DATA_DIR=.terraform-validate terraform init -backend=false -input=false >/dev/null && TF_DATA_DIR=.terraform-validate terraform validate

infra-plan-bootstrap: ## Plan the state bucket and DNS zone (needs AWS_PROFILE)
	terraform -chdir=infra/bootstrap init -input=false >/dev/null && terraform -chdir=infra/bootstrap plan

infra-init: ## Point infra/envs/dev at the state bucket created by bootstrap
	terraform -chdir=infra/envs/dev init -input=false -reconfigure \
		-backend-config="bucket=$$(terraform -chdir=infra/bootstrap output -raw state_bucket)"

infra-plan: ## Plan the dev environment (needs AWS_PROFILE and infra-init)
	terraform -chdir=infra/envs/dev plan
