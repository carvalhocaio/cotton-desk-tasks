.PHONY: help install migrate run worker test lint lint-fix format format-check audit ci clean

help: ## Lists the available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Installs the project dependencies (including dev)
	uv sync

migrate: ## Applies the Django migrations
	uv run python manage.py migrate

run: ## Runs the development server
	uv run python manage.py runserver

worker: ## Runs the worker that processes the task queues
	uv run python manage.py db_worker

test: ## Runs the test suite
	uv run pytest

lint: ## Checks the code with ruff
	uv run ruff check

lint-fix: ## Checks and automatically fixes with ruff
	uv run ruff check --fix

format: ## Formats the code with ruff
	uv run ruff format

format-check: ## Checks formatting without modifying files
	uv run ruff format --check

audit: ## Audits dependencies for vulnerabilities
	uv run pip-audit

ci: lint format-check audit test ## Runs the same pipeline as CI locally

clean: ## Removes caches (.ruff_cache, .pytest_cache, __pycache__)
	rm -rf .ruff_cache .pytest_cache
	find . -type d -name '__pycache__' -exec rm -rf {} +
