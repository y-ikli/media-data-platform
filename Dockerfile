# Une seule image pour tout le pipeline : l'ingestion (adsdata-ingest) et la transformation (dbt).
# Cloud Run Jobs choisit la commande à lancer.

# --- Étape 1 : construire l'environnement Python ------------------------------------------------
FROM python:3.14-slim AS build

COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# Les dépendances d'abord : cette couche est réutilisée tant que uv.lock ne change pas.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-dev --group dbt --extra meta

COPY src ./src
RUN uv sync --locked --no-dev --group dbt --extra meta

COPY dbt ./dbt
RUN /app/.venv/bin/dbt deps --project-dir dbt

# --- Étape 2 : l'image finale, sans uv ni fichiers de construction ------------------------------
FROM python:3.14-slim

RUN useradd --create-home --uid 1000 app
COPY --from=build --chown=app:app /app /app

ENV PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    DBT_PROJECT_DIR=/app/dbt \
    DBT_PROFILES_DIR=/app/dbt \
    DBT_TARGET=prod

USER app
WORKDIR /app

CMD ["adsdata-ingest", "--help"]
