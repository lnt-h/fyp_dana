# ADR-001 — Modular monolith API with three separate deployables over HTTP API /v1

| Field | Value |
|---|---|
| Status | Proposed (pending mentor approval at the design gate) |
| Date | 2026-11-04 |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Parent | GONARRA-SAD 0.1 §4.0; prompt `design/SAD_prompt.md` v2.0 |
| Decision source | DEC-006 (SRC-100), CON-004 |

## Context

One developer must deliver catalog, planning, Guide, stays and curation by ~2027-02-01 (CON-003, ASM-002) for
≤ 15 concurrent users (ASM-030). The traveler app and the curator tool must be separate from the backend and use
only its HTTP API (CON-004). The foundation already exists as one FastAPI service (SRC-009). AGENTS.md forbids
microservices, queues and Redis without a plan change (SRC-003).

## Drivers

CON-003, CON-004, CON-005, C-008, C-012, QAS-11, QAS-14.

## Options considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| A. Modular monolith API + separate mobile and admin deployables over `/v1` REST + SSE | One process to deploy and debug; in-process calls between modules; clear contract for clients; fits t4g.small | Module discipline must be enforced by rules/tests, not by the network | **Chosen** |
| B. Microservices (one per module) | Independent scaling | Several containers, network calls, distributed failure modes; no load that needs it; more AWS cost | Rejected |
| C. Admin pages rendered by the API (server-side templates) | One less deployable | Violates CON-004 separation; mixes curator UI into the API | Rejected |
| D. Clients read the database directly (e.g., BaaS) | Fewer endpoints | Breaks owner checks, provider-secret rules and BR-020 | Rejected |

## Decision

- Three deployables: `apps/api` (CMP-003), `apps/mobile` (CMP-001), `apps/admin` (CMP-002). They share only the
  versioned HTTP contract `/v1` (REST + SSE). `apps/api/openapi.json` is generated and drift-checked in CI;
  clients generate types with `openapi-typescript`.
- `apps/api` is a modular monolith with modules identity, catalog, curation, trips, planning, routing, guide,
  stays (CMP-004..CMP-011), plus shared AI gateway, provider adapters and platform kernel (CMP-012..CMP-014).
- Module rules (SAD §3.2.2): call other modules only through their service interface; never read another module's
  tables; acyclic dependency direction; provider SDKs only inside their adapter.
- Curator endpoints live under `/v1/admin` and require the curator role.

## Consequences

- Positive: one image, one deploy, one log stream; simple transactions (e.g., Save); fast iteration.
- Negative: a fault in one module can affect the whole API process; mitigated by timeouts, quotas, and the single
  repair rule. Module boundaries need an import-rule test.
- Follow-up: OQ-034 (move to module packages). Breaking contract changes require a new path version.

## Verification

CI OpenAPI drift check (existing); import-rule test; client type check against generated types (QAS-14).
