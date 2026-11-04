# ADR-012 — Catalog ingestion as Typer CLI commands in apps/api (DuckDB, Wikidata SPARQL); embeddings on write

| Field | Value |
|---|---|
| Status | Accepted by the owner (SRC-100 A-021, 2026-11-04; embedding on write A-028, 2026-11-05); mentor review at the design gate [Pending] |
| Date | 2026-11-04 (0.3: 2026-11-05) |
| Version | 0.3 (0.1 → 0.2: DA-GONARRA-01 fixes F-01, embedding before publication; 0.2 → 0.3: DEC-012 — embedding computed by the curation API on write, CLI keeps backfill and re-embed) |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Parent | GONARRA-SAD 0.1 §4.0; prompt `design/SAD_prompt.md` v2.0 |
| Decision source | DEC-009 (SRC-100 A-021); DEC-012 (SRC-100 A-028) |

## Context

Candidates come from Overture Places and Foursquare OS Places releases (GeoParquet) and Wikidata (SRC-104,
DEP-004), bounded to five cities. Imports must be idempotent and never publish (DATA.md). One curator (CON-002). No
worker, queue or Redis (SRC-003, DC-002). Guide chunks need embeddings before they can be approved and pinned by a
publication (ADR-010). In the 0.2 design the curator had to run a CLI command between writing a chunk and approving
it; a forgotten run blocks approval (constraint `ck_knowledge_chunks_approved_embedded`) with no explanation in the
curator tool.

## Drivers

CON-001, CON-002, DC-002, BR-004, BRU-003, BRU-004, DEP-004, QAS-06.

## Options considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| A. Typer CLI inside `apps/api` for imports (DuckDB bounding-box reads, Wikidata SPARQL) and scheduled jobs; chunk embeddings computed synchronously by the curation API when a chunk is saved; CLI `embed` for backfill and re-embed | Same code, models and policies as the API; no extra service; no manual step between edit and approve; one Gemini embed call per changed chunk | Curation API depends on the AI gateway for chunk saves (typed 503 when Gemini is down) | **Chosen** |
| B. Embedding only in the CLI (0.2 design) | API has no AI dependency during review | Manual step; forgotten runs block approval | Superseded |
| C. Separate worker service with a queue (e.g., SQS/Celery/Redis) | Async, retries | Forbidden without plan change; cost; ops burden | Rejected |
| D. Import endpoints called from the admin SPA | UI-driven | Long-running HTTP requests on a small host; large files through the API | Rejected |
| E. Load the full planet files into PostgreSQL | Simple SQL | Huge data; violates "bounded to five cities" | Rejected |

## Decision

- `apps/api` gains a Typer entry point with `import` (overture, foursquare, wikidata, csv), `embed` and `jobs`
  command groups, run with `docker compose run --rm api …` (CMP-018). DuckDB reads only rows inside each city's
  bounding box from a pinned release; every run records provider, release, checksum and importer version, writes
  only staging rows allowed by the provider policy (ADR-006), and is idempotent. Wikidata is queried by SPARQL for
  linked IDs and VI/EN labels as evidence. The `csv` importer loads the curator's research sheet (WP-023).
- **Embedding on write.** `PATCH /v1/admin/candidates/{place_id}` (API-035) accepts `chunks[]` (section, locale,
  content, source revision IDs). For each chunk whose `content_sha256` is new or changed, the curation module calls
  the AI gateway, stores `embedding` and `embedding_model` in the same transaction as the chunk, and returns the
  chunk with `embedding_state: EMBEDDED`. If the gateway fails, the chunk is stored as DRAFT with
  `embedding_state: PENDING` and the response carries a warning; approval stays blocked until `embed` succeeds (a
  later save or `cli embed --pending`). Publication pins the latest approved corpus revision (`fn_publish_place`).
- **CLI `embed`** keeps two jobs: `--pending` (backfill chunks without an embedding) and `--reembed-all --model
  <id>` (re-embed every approved chunk in place after a model change, then update the configured question model).
- Scheduled jobs (deletion retry, preview expiry, freshness) use the same CLI from systemd timers.

## Consequences

- Positive: one codebase; reproducible imports; no manual step in the review flow; the chunk and its embedding are
  always consistent; model changes are one command.
- Negative: adds `typer` and `duckdb` dependencies (arm64 wheels in the multi-arch image); DuckDB memory must be
  capped on the 2 GiB host, or heavy extracts run on the owner's machine via an SSM-tunnelled DB connection; the
  curation API now depends on Gemini availability for chunk saves (degrades to PENDING, never blocks other edits).
