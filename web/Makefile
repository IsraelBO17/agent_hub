# Commands for people and coding agents (standard §6.1). `make check` is the "done" gate.
.DEFAULT_GOAL := help
.PHONY: help install dev check types lint tokens-check test api-check no-radix build budget audit e2e tokens api fmt

# The API contract lives in the monorepo's api/ folder (profile: Contract).
CONTRACT := ../api/openapi.yaml
OPENAPI_TS := npx openapi-typescript $(CONTRACT) -o src/service/generated/schema.d.ts --root-types --root-types-no-schema-prefix

help: ## List targets
	@grep -E '^[a-z0-9-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-13s %s\n", $$1, $$2}'

install: ## Install dependencies from the lockfile
	npm ci

dev: ## Run the app on :5173 with mocks (VITE_API_MOCKS=true in .env.local, see .env.example)
	npm run dev

check: types lint tokens-check test api-check no-radix build budget audit ## The done gate: types, lint, tokens, tests, contract drift, no Radix, build, budget, audit
	@echo "make check: all passed"

types: ## Type-check (tsc -b)
	npx tsc -b

lint: ## ESLint with zero warnings
	npx eslint . --max-warnings 0

tokens-check: ## Tokens file current, and no hand-written design values in src/
	node scripts/gen-tokens.ts --check
	node scripts/check-tokens.ts

test: ## Unit and component tests (Vitest)
	npx vitest run

api-check: ## Generated API types match the contract
	$(OPENAPI_TS) --check

no-radix: ## No @radix-ui package, directly or through a dependency (profile: No Radix, D28)
	@if npm ls --all 2>/dev/null | grep -q '@radix-ui/'; then echo 'A @radix-ui package is installed (npm ls --all | grep @radix-ui)'; exit 1; fi

build: ## Production build
	npx vite build

budget: ## Initial JS within package.json's budget (needs a build)
	node scripts/check-bundle.ts

audit: ## No unaccepted high or critical advisories in production dependencies
	node scripts/check-audit.ts

e2e: ## Playwright with axe, in mock mode, desktop and mobile (builds first)
	npx playwright test

tokens: ## Regenerate src/styles/tokens.css from the design
	node scripts/gen-tokens.ts

api: ## Regenerate the API types from the contract
	$(OPENAPI_TS)

fmt: ## Fix what ESLint can fix
	npx eslint . --fix
