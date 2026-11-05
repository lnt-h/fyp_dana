# ADR-012 — Catalog ingestion as Typer CLI commands in `apps/api`; embeddings on write; web candidates via the curator queue

| Field | Value |
|---|---|
| Status | Accepted by the owner (SRC-100 A-021, A-028); mentor review at M0 [Pending] |
| Date | 2026-11-04 (0.4: 2026-11-06) |
| Version | 0.4 (0.3 → 0.4: DEC-013 post-merger Đà Nẵng bounding box and areas; DEC-015 web candidates enter through the research agent and the admin queue; CLI `routes warm` and cache sweeps) |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Decision source | DEC-009, DEC-012 (SRC-100); DEC-013, DEC-015, DEC-018 (SRC-105) |

## Context

Candidates come from Overture Places and Foursquare OS Places releases (GeoParquet), Wikidata and the curator's
research sheet, now bounded to post-merger Đà Nẵng (Hội An included as an area). Imports must be idempotent and
never publish. Web-found places from the research agent need a review path. No worker, queue or Redis. Guide
chunks need embeddings before approval.

## Decision

- Typer entry point in `apps/api` with command groups `import` (overture, foursquare, wikidata, csv), `embed`,
  `routes` and `jobs`, run with `docker compose run --rm api …` or a timer.
- **Bounding box and areas.** DuckDB reads only rows inside the post-merger Đà Nẵng polygon (OQ-121) from a pinned
  release; each run records provider, release, checksum and importer version and writes staging rows allowed by
  the provider policy. Imported places get an `area_code` from the `areas` seed (travel areas, not wards):
  `da-nang-center`, `son-tra`, `my-khe-ngu-hanh-son`, `ba-na-hoa-vang`, `hoi-an-old-town`,
  `hoi-an-beaches-islands`. No `hoi-an` city row exists.
- **Web candidates.** The research agent writes `web_place_candidates` (ADR-014); the admin queue (API-046..049)
  lists, promotes or rejects them. Promotion creates a `places` row (IMPORTED), an `external_place_identities` row
  for the Google `place_id` and a localization draft; it never publishes. Expired, unreferenced candidates are swept.
- **Embedding on write.** `PATCH /v1/admin/candidates/{place_id}` accepts `chunks[]`; a new or changed
  `content_sha256` is embedded in the same transaction (`embedding_state: EMBEDDED`), or stored as PENDING with a
  warning if the model is unavailable. `embed --pending` backfills; `embed --reembed-all --model <id>` re-embeds
  after a model change.
- **Caches and jobs.** `routes warm` pre-fills `routes_matrix_cache` for published places and anchors; `jobs`
  sweeps expired cache rows, previews, Guide sessions and web candidates, retries deletions and recomputes
  freshness.

## Options

| Option | Verdict | Why |
|---|---|---|
| A. Typer CLI in the API image; embeddings on write; queue for web candidates | **Chosen** | Same code, models and policies as the API; no extra service |
| B. Embedding only in the CLI | Superseded | Forgotten runs block approval |
| C. Worker service with a queue | Rejected | Forbidden without plan change; cost |
| D. Import endpoints called from the SPA | Rejected | Long requests on a small host |
| E. Auto-publish web candidates | Rejected | Only the curator publishes; a model never creates a published place |

## Consequences

- Positive: reproducible imports; chunk and embedding always consistent; web content reaches the catalog only
  through review.
- Negative: `typer`, `duckdb` and `ortools` arm64 wheels; DuckDB memory capped on a 2 GiB host; the curation API
  depends on the embedding model for chunk saves (degrades to PENDING).

## Drivers

CON-001, CON-002, DC-002, BR-004, BRU-003, BRU-004, DEP-004, MET-011, OQ-121, ASM-022.
