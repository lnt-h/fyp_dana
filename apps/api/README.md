# Gonarra API

Python 3.12 FastAPI modular monolith for identity, catalog, trips, planning, routing and local guidance, with a Typer CLI for ingestion, publication, retention and account deletion.

```sh
cp .env.example .env
docker compose up -d db
uv sync --all-groups
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Verify the foundation with `uv run ruff check .`, `uv run mypy app`, `uv run pytest` and `uv run python scripts/export_openapi.py --check`. OpenAPI is available at `/openapi.json` in development and staging.

Catalog content is imported and published by the automated pipeline (DEC-022, no human review): `uv run python -m app.cli pipeline run`. Policies, gate rules, the owner sheet columns, area polygons and the operator calendar are documented in [`data/README.md`](data/README.md).

`GONARRA_ENVIRONMENT` fails safe: unset means `production` (no `/docs`, no estimated legs, no demo user, ACTIVE provider policies only). `.env.example` sets `development` for local work.

Integration tests write and delete rows, so they refuse any database whose name does not end in `_test`, `_it` or `_ci` (optionally numbered, e.g. `gonarra_it3`) unless `GONARRA_ALLOW_INTEGRATION_DB=1` is set. Unit tests never read `.env`.

```sh
docker compose exec -T db psql -U gonarra -d postgres -c "CREATE DATABASE gonarra_test"
export GONARRA_DATABASE_URL=postgresql+psycopg://gonarra:gonarra@localhost:5432/gonarra_test
uv run alembic upgrade head && uv run python -m app.cli seed && uv run pytest -m integration
```

Provider cache retention (ADR-006) runs daily on the host timer: `uv run python -m app.cli caches sweep` deletes expired `research_cache`, `routes_matrix_cache`, `places_lookup_cache` and `query_embedding_cache` rows and clears Google Places lat/lng older than 30 days. It is idempotent and prints counts only.
