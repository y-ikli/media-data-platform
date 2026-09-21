# Image unique des jobs Cloud Run : ingestion (mdp-ingest) et transformations (dbt).
# Le job choisit sa commande ; l'image ne contient ni secret ni donnée.
FROM python:3.13-slim AS build
ENV UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1 UV_PYTHON_DOWNLOADS=never
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --group dbt --extra meta --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev --group dbt --extra meta
COPY dbt ./dbt
RUN /app/.venv/bin/dbt deps --project-dir dbt/mdp --profiles-dir dbt/mdp

FROM python:3.13-slim
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 DBT_PROFILES_DIR=/app/dbt/mdp DBT_SEND_ANONYMOUS_USAGE_STATS=false \
    DBT_TARGET_PATH=/tmp/dbt-target DBT_LOG_PATH=/tmp/dbt-logs
RUN useradd --create-home --uid 10001 mdp
WORKDIR /app
COPY --from=build --chown=mdp:mdp /app /app
USER mdp
ENTRYPOINT []
CMD ["mdp-ingest", "--help"]
