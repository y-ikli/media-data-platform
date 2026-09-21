.DEFAULT_GOAL := help
DBT = DBT_PROFILES_DIR=dbt/mdp uv run dbt
DBT_DIR = --project-dir dbt/mdp

.PHONY: help install lint test dbt-duckdb ci ingest-demo dbt-build docs

help: ## Liste les commandes
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

install: ## Environnement de développement (Python, dbt, dbt-duckdb)
	uv sync --group dev --group dbt
	$(DBT) deps $(DBT_DIR)

lint: ## ruff (Python) et sqlfluff (SQL dbt)
	uv run ruff check .
	uv run python -m mdp.dev.duckdb_fixtures --path dbt/mdp/target/ci.duckdb >/dev/null
	DBT_TARGET=duckdb DBT_DUCKDB_PATH=$$PWD/dbt/mdp/target/ci.duckdb uv run sqlfluff lint dbt/mdp/models

test: ## Tests Python (unitaires + dbt sur DuckDB) avec couverture
	uv run pytest --cov

dbt-duckdb: ## dbt build complet sur DuckDB (sans identifiants)
	uv run python -m mdp.dev.duckdb_fixtures --path dbt/mdp/target/ci.duckdb
	DBT_TARGET=duckdb $(DBT) build $(DBT_DIR)

ci: lint test ## Ce que la CI exécute

ingest-demo: ## Ingestion simulée (dry-run, sans GCP)
	uv run mdp-ingest --source meta_ads --start 2024-01-01 --end 2024-03-31 --dry-run
	uv run mdp-ingest --source google_ads --start 2024-01-01 --end 2024-03-31 --dry-run

dbt-build: ## dbt build sur BigQuery (cible dev ; GCP_PROJECT_ID requis)
	DBT_TARGET=dev $(DBT) build $(DBT_DIR)

docs: ## Documentation dbt (catalogue et lignée) sur DuckDB
	DBT_TARGET=duckdb $(DBT) docs generate $(DBT_DIR)
	DBT_TARGET=duckdb $(DBT) docs serve $(DBT_DIR)
