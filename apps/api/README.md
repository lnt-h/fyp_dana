# Gonarra API

Python 3.12 FastAPI modular monolith for identity, catalog, trips, planning and local guidance. The foundation phase exposes liveness, database readiness and an authenticated identity endpoint. AI, Routes and trip persistence enter in later phases.

```sh
cp .env.example .env
docker compose up -d db
uv sync --all-groups
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Verify the foundation with `uv run ruff check .`, `uv run mypy app`, `uv run pytest` and `uv run python scripts/export_openapi.py --check`. OpenAPI is available at `/openapi.json` in development and staging.
