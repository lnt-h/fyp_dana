# syntax=docker/dockerfile:1
# Gonarra API image. Multi-stage (uv build -> slim runtime), non-root, linux/amd64 + linux/arm64.
# Build:  docker build -t gonarra-api apps/api
# The same image runs the API (default CMD), migrations (`alembic upgrade head`) and the
# Typer CLI (`python -m app.cli ...`).

FROM ghcr.io/astral-sh/uv:0.13.6-python3.12-trixie-slim AS build

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /app
# Dependencies first so the layer is cached across code-only changes.
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev --no-install-project
COPY app ./app
COPY alembic.ini ./
COPY migrations ./migrations
COPY data ./data
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev

FROM python:3.12-slim-trixie AS runtime

LABEL org.opencontainers.image.title="gonarra-api" \
      org.opencontainers.image.source="https://github.com/lnt-h/fyp_dana"
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Uvicorn reads these: one worker by default (t4g.small, 2 GB); Caddy is the only peer that
    # can reach the container, so forwarded headers from any address on the network are trusted.
    WEB_CONCURRENCY=1 \
    FORWARDED_ALLOW_IPS="*"
WORKDIR /app
RUN groupadd --system --gid 999 gonarra \
    && useradd --system --gid 999 --uid 999 --no-create-home --home-dir /app gonarra
COPY --from=build --chown=gonarra:gonarra /app /app
USER gonarra
EXPOSE 8000
# /ready checks the database connection. python is used because the slim image has no curl.
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import sys, urllib.request as u; sys.exit(0 if u.urlopen('http://127.0.0.1:8000/ready', timeout=4).status == 200 else 1)"]
# Exec form so SIGTERM reaches uvicorn for a graceful shutdown (FastAPI lifespan runs).
# No uvicorn access log: query strings carry search text and coordinates (AGENTS.md logging rule);
# Caddy writes the access log with the query redacted.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--no-access-log", "--timeout-graceful-shutdown", "20"]
