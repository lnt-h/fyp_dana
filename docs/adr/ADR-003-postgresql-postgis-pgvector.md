# ADR-003 — PostgreSQL 16 + PostGIS + pgvector as the single data store

| Field | Value |
|---|---|
| Status | Proposed (mentor approval at M0). Re-affirmed 2026-11-06 (DEC-021) |
| Date | 2026-11-04 (1.0: 2026-11-06) |
| Version | 1.0 |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Decision source | CON-005, DEC-018 (SRC-105: caches and quota ledger in PostgreSQL) |

## Context

The system needs transactional private data (Save), spatial queries (300 m nearby, city and area membership) and
vector plus trigram retrieval for the city-level Guide. The catalog is about 100 published places. Budget forbids
extra managed services; Redis and queues are out. Free-tier provider limits require caches and a quota ledger.

## Decision

- All persistent state lives in one PostgreSQL 16 database with `postgis`, `vector`, `pg_trgm` and `pgcrypto`.
- Quotas (`ai_quota_ledger`, `provider_usage_daily`), idempotency records, previews and all provider caches
  (`routes_matrix_cache`, `research_cache`, `places_lookup_cache`, `query_embedding_cache`) are tables with TTL
  columns swept by the CLI `jobs` command; no in-memory or external cache.
- Chunk embeddings are `vector(768)` (`gemini-embedding-001`, `output_dimensionality=768`, L2-normalised; OQ-126)
  with an HNSW index; lexical and entity legs use trigram indexes on names, aliases and chunk text.

## Options

| Option | Verdict | Why |
|---|---|---|
| A. One PostgreSQL with PostGIS + pgvector + pg_trgm | **Chosen** | One backup and transaction scope; spatial, lexical and vector filters joined with publication state |
| B. PostgreSQL + dedicated vector database | Rejected | Extra cost and sync for a tiny corpus |
| C. PostgreSQL + OpenSearch | Rejected | Cost far beyond credits |
| D. Redis for caches and quotas | Rejected | Forbidden without a plan change; one instance does not need it |

## Consequences

- Positive: one consistency boundary; simple restore; quota reservation is a single `UPDATE … RETURNING`.
- Negative: vector and trigram search compete with OLTP on a 1 GiB instance; acceptable at this corpus size.
  Vietnamese recall without `unaccent`/tsvector is an assumption (ASM-019) measured on the Guide golden set.

## Drivers

CON-001, CON-005, DC-001, BR-006, BR-011, BR-015, ASM-019, ASM-030.
