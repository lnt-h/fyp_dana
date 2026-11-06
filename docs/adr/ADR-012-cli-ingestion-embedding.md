# ADR-012 — Automated catalog ingestion pipeline (Typer CLI in `apps/api`), deterministic publication gate, embeddings on write, YAML closure rules

| Field | Value |
|---|---|
| Status | Accepted by the owner (SRC-100 A-021, A-028; DEC-022 2026-11-06); mentor review at M0 [Pending] (OQ-131) |
| Date | 2026-11-04 (0.4: 2026-11-06; 0.5: 2026-11-06) |
| Version | 0.5 |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Decision source | DEC-009, DEC-012 (SRC-100); DEC-013, DEC-015, DEC-018, DEC-022 (`docs/decisions.md`) |

## Context

Gonarra needs ≥ 100 bilingual Đà Nẵng places (≥ 30 in the Hội An area) before release (MET-011 rev. 2). One person
builds and operates the whole system; the workload of human review (RSK-001) threatened that gate, so the owner
removed human review (DEC-022). Content must therefore enter through an automated, reproducible pipeline whose
publication decision is deterministic code, with every shown fact backed by an attributed source. Web-found places
from the research agent (ADR-014) need a path into the catalog without a review queue. No worker, queue or Redis.
Guide chunks need embeddings before publication. Closure and calendar rules (ADR-011) need a maintained source that
no model writes.

## Decision

- **Typer CLI in `apps/api`** (`app/ingestion/cli.py`) with command groups `ingest` (wikidata, osm, wikipedia, csv,
  `run` = all sources then the gate), `publish` (run the gate), `closure-rules load`, `embed`, `routes` and `jobs`,
  run with `docker compose run --rm api …` or a timer.
- **Sources.** Open data — Wikidata, OSM and Wikipedia extracts (VI and EN, attribution kept) — plus the owner's CSV
  sheet. Overture and Foursquare OS Places remain optional importers. Each run records provider, release or file
  hash, checksum and importer version, and writes staging rows allowed by the provider policy (ADR-006). Every value
  shown to travelers links to a `source_revisions` row (URL or file, retrieved date, hash, licence, attribution).
- **Boundary and areas.** Only rows inside the post-merger Đà Nẵng polygon (OQ-121) are imported; each place gets an
  `area_code` from the `areas` seed (travel areas, not wards): `da-nang-center`, `son-tra`, `my-khe-ngu-hanh-son`,
  `ba-na-hoa-vang`, `hoi-an-old-town`, `hoi-an-beaches-islands`. No `hoi-an` city row exists.
- **Unknown stays unknown.** A fact with no attributed source value is stored as unknown; nothing is invented. If AI
  extraction is added later, a model may extract a fact only together with a verbatim quote that code finds in the
  fetched source text; otherwise the fact is rejected. Models never author free-form displayed facts, hours, prices,
  distances or durations.
- **Deterministic publication gate** (`app/curation/auto_publish.py`). A candidate is published when all checks pass:
  VI and EN name and description present; location inside the city boundary; category set; every shown fact backed by
  an attributed source revision; licence recorded for every cited source. The actor is the seeded system account
  `system:gonarra-pipeline`. Failed checks are named per candidate in the run report and counted per reason in
  `GET /v1/admin/cities/summary`. The gate is idempotent: unchanged input creates no new publication; a place the
  operator unpublished is not re-published unless its source revision changes. No model call happens in the gate.
- **Web candidates (DEC-022).** The research agent writes `web_place_candidates` (ADR-014). When its Places check
  returns `EXISTS_OPERATIONAL` inside the boundary, `ingestion/promote_web.py` auto-promotes it: a `places` row
  (IMPORTED) and an `external_place_identities` row for the Google `place_id` (identifier only, ADR-006); it is
  published only if the gate passes it later. Other outcomes stay request-scoped `WEB_UNVERIFIED`. Expired,
  unreferenced candidates are swept.
- **Closure rules.** The owner maintains `apps/api/data/closure_rules/da-nang.yaml` (weekly, date, lunar incl. Tết
  and Hội An lantern night, season, Old Town ticket validity; bilingual notes; source), versioned in git.
  `closure-rules load` validates the schema, upserts `place_closure_rules` idempotently and records the file's git
  revision. AI never writes the file or the rows.
- **Embedding on write.** The pipeline embeds a new or changed chunk (`content_sha256`) in the same transaction
  (`embedding_state: EMBEDDED`), or stores it PENDING with a warning if the model is unavailable; PENDING chunks are
  not retrievable. `embed --pending` backfills; `embed --reembed-all --model <id>` re-embeds after a model change.
- **Operator surface.** No admin SPA and no review endpoints. The owner keeps `POST /v1/admin/places/{id}/unpublish`
  (emergency takedown) and `GET /v1/admin/cities/summary` (release-gate count) behind `GONARRA_CURATOR_CLERK_USER_IDS`.
- **Caches and jobs.** `routes warm` pre-fills `routes_matrix_cache`; `jobs` sweeps expired cache rows, previews,
  Guide sessions and web candidates, retries deletions and recomputes freshness.

## Options

| Option | Verdict | Why |
|---|---|---|
| A. Typer CLI pipeline + deterministic auto-publish gate + YAML closure rules (0.5) | **Chosen** (DEC-022) | Reaches the gate with one person; reproducible; publishing stays code, not a model |
| B. CLI import + curator review in an admin SPA (0.4) | Superseded by DEC-022 | Review workload threatens MET-011 (RSK-001); SPA cost |
| C. Worker service with a queue | Rejected | Forbidden without plan change; cost |
| D. Model publishes or writes facts directly | Rejected | Models never publish or author displayed facts (BRU-002 rev. 1) |
| E. Closure rules edited in a UI or extracted by AI | Rejected | No UI exists; AI never writes rules; git gives history and versioning |

## Consequences

- Positive: catalog growth is limited by sources, not review hours; every run is reproducible and auditable from
  `source_revisions`, run reports and git; chunk and embedding stay consistent.
- Negative: no human catches a wrong-but-sourced fact (RSK-105); `VERIFIED` must be described as "source-checked",
  never "reviewed"; open-data coverage of VI descriptions may be thin, so the owner's CSV carries more load; `typer`,
  `duckdb` and `ortools` arm64 wheels; DuckDB memory capped on a 2 GiB host.

## Drivers

CON-001, CON-002, BR-004, BRU-002, BRU-003, BRU-004, FR-009, FR-011, FR-013, FR-014, FR-016, FR-101, FR-107,
MET-011, OQ-121, OQ-131, ASM-022, RSK-001, RSK-105.

## History

| Version | Date | Change |
|---|---|---|
| 0.3 | 2026-11-05 | Embeddings on write by the curation API (DEC-012) |
| 0.4 | 2026-11-06 | DEC-013 post-merger Đà Nẵng bounding box and areas; DEC-015 web candidates via the research agent and the admin queue; CLI `routes warm` and cache sweeps |
| 0.5 | 2026-11-06 | DEC-022: curator review, admin queue and curation API removed; automated pipeline (Wikidata, OSM, Wikipedia, owner CSV) with a deterministic publication gate and system actor; auto-promotion of `EXISTS_OPERATIONAL` web candidates; closure rules from owner-maintained YAML; verbatim-quote rule for future AI extraction |
