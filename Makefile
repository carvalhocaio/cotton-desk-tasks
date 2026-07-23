.PHONY: help install migrate run worker test lint lint-fix format format-check audit ci clean

help: ## Lista os comandos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Instala as dependências do projeto (incluindo dev)
	uv sync

migrate: ## Aplica as migrações do Django
	uv run python manage.py migrate

run: ## Roda o servidor de desenvolvimento
	uv run python manage.py runserver

worker: ## Roda o worker que processa as filas de tasks
	uv run python manage.py db_worker

test: ## Roda a suíte de testes
	uv run pytest

lint: ## Verifica o código com ruff
	uv run ruff check

lint-fix: ## Verifica e corrige automaticamente com ruff
	uv run ruff check --fix

format: ## Formata o código com ruff
	uv run ruff format

format-check: ## Verifica a formatação sem alterar arquivos
	uv run ruff format --check

audit: ## Audita dependências em busca de vulnerabilidades
	uv run pip-audit

ci: lint format-check audit test ## Roda o mesmo pipeline da CI localmente

clean: ## Remove caches (.ruff_cache, .pytest_cache, __pycache__)
	rm -rf .ruff_cache .pytest_cache
	find . -type d -name '__pycache__' -exec rm -rf {} +
