# ADR-012 — Catalog ingestion and embedding as Typer CLI commands in apps/api (DuckDB, Wikidata SPARQL)

| Field | Value |
|---|---|
| Status | Accepted by the owner (SRC-100 A-021, 2026-11-04); mentor review at the design gate [Pending] |
| Date | 2026-11-04 |
| Version | 0.2 (0.1 → 0.2: DA-GONARRA-01 fixes F-01, embedding before publication) |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Parent | GONARRA-SAD 0.1 §4.0; prompt `design/SAD_prompt.md` v2.0 |
| Decision source | DEC-009, owner-level stack review relayed 2026-11-04 — **Accepted** (SRC-100 A-021) |

## Context

Candidates come from Overture Places and Foursquare OS Places releases (GeoParquet) and Wikidata (SRC-104,
DEP-004), bounded to five cities. Imports must be idempotent and never publish (DATA.md). One curator (CON-002). No
worker, queue or Redis (SRC-003, DC-002). Guide chunks need embeddings before publication (ADR-010).

## Drivers

CON-001, CON-002, DC-002, BR-004, BRU-003, BRU-004, DEP-004.

## Options considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| A. Typer CLI inside `apps/api`: DuckDB reads GeoParquet with a city bounding-box filter; Wikidata via SPARQL query (or dump); writes staging through the curation module; embedding command before publication | Same code, models and policies as the API; no extra service; runs on EC2 or the owner's machine | Manual or timer-triggered, not event-driven | **Chosen** |
| B. Separate worker service with a queue (e.g., SQS/Celery/Redis) | Async, retries | Forbidden without plan change; cost; ops burden | Rejected |
| C. Import endpoints called from the admin SPA | UI-driven | Long-running HTTP requests on a small host; large files through the API | Rejected |
| D. Load the full planet files into PostgreSQL | Simple SQL | Huge data; violates "bounded to five cities" | Rejected |

## Decision

`apps/api` gains a Typer entry point with `import` (overture, foursquare, wikidata), `embed` and `jobs`
command groups, run with `docker compose run --rm api …` (CMP-018). DuckDB reads only rows inside each city's
bounding box from a pinned release; every run records provider, release, checksum and importer version, writes
only staging rows allowed by the provider policy (ADR-006), and is idempotent. Wikidata is queried by SPARQL for
linked IDs and VI/EN labels as evidence. Before the curator publishes, `embed` computes embeddings for new or
changed draft chunks via the AI gateway, so they can be approved and pinned by the first publication. Scheduled jobs (deletion retry, preview expiry, freshness) use the same
CLI from systemd timers.

## Consequences

- Positive: one codebase; reproducible imports; no new infrastructure.
- Negative: adds `typer` and `duckdb` dependencies (arm64 wheels in the multi-arch image); DuckDB memory must be
  capped on the 2 GiB host, or heavy extracts run on the owner's machine via an SSM-tunnelled DB connection.
