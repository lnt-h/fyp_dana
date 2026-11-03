# ADR-003 — PostgreSQL 16 + PostGIS + pgvector as the single data store

| Field | Value |
|---|---|
| Status | Proposed (pending mentor approval at the design gate) |
| Date | 2026-11-04 |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Parent | GONARRA-SAD 0.1 §4.0; prompt `design/SAD_prompt.md` v2.0 |
| Decision source | CON-005, agent brief stack |

## Context

The system needs relational private data with transactions (Save, BR-011), spatial queries (nearby 300 m, ASM-009;
city membership, BR-006), and vector retrieval for the Guide (BR-015). The catalog is about 250 published places
(ASM-030). Migration `20261102_0001` already enables `pgcrypto`, `postgis` and `vector` (SRC-009). Budget
forbids extra managed services (CON-001); AGENTS.md forbids Redis/queues (SRC-003).

## Drivers

CON-001, CON-005, DC-001, BR-006, BR-011, BR-015, BR-017, ASM-030.

## Options considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| A. One PostgreSQL 16 with PostGIS + pgvector (RDS) | One backup, one transaction scope; spatial + vector filters joined with publication state; already migrated | Vector index tuning limited on a micro instance | **Chosen** |
| B. PostgreSQL + dedicated vector DB (e.g., managed vector service) | Specialised ANN | Extra cost and sync between stores; tiny corpus does not need it | Rejected |
| C. PostgreSQL + OpenSearch | Full-text and vectors | Cost far beyond credits | Rejected |
| D. Add Redis for cache/quotas | Fast counters | Forbidden without plan change; single instance does not need it | Rejected |

## Decision

All persistent state lives in RDS PostgreSQL 16 with PostGIS and pgvector. Quotas, idempotency records and
previews are tables. Embeddings of reviewed knowledge chunks are stored next to their place and source revision,
filtered by place, locale and publication before similarity ranking. Schema details belong to the data design.

## Consequences

- Positive: one consistency boundary; simple backup/restore; spatial and vector filters in one query.
- Negative: vector search competes with OLTP on a 1 GiB instance (RSK-035) — acceptable at this corpus size.
- Follow-up: data design (`databaseDesign_SQL_prompt.md`, VectorDB prompt) fixes index types and dimensions after
  the embedding model is pinned (OQ-032).
