# ADR-001 — Modular monolith API with three deployables over HTTP API `/v1`

| Field | Value |
|---|---|
| Status | Proposed (mentor approval at M0). Re-affirmed 2026-11-06 (DEC-021) |
| Date | 2026-11-04 (1.0: 2026-11-06) |
| Version | 1.0 |
| Owner / decider | Lê Ngọc Tấn Hiền |
| Approver | trantrongminh, FYP mentor ([Pending]) |
| Decision source | DEC-006 (SRC-100), CON-004; module layout DEC-014 (SRC-105) |

## Context

One developer delivers catalog, planning, Guide, research, stays and curation by 2027-02-01 for ≤ 15 concurrent
users. Traveler app and curator tool must be separate from the backend and use only its HTTP API. The foundation is
already one FastAPI service. Microservices, queues and Redis are out without a plan change.

## Decision

- Three deployables: `apps/api` (FastAPI), `apps/mobile` (Expo), `apps/admin` (React + Vite). They share only the
  versioned contract `/v1` (REST + SSE); `apps/api/openapi.json` is generated and drift-checked in CI; clients
  generate types with `openapi-typescript`.
- `apps/api/app` is a modular monolith: `ai/`, `agents/`, `planning/`, `routing/`, `guide/`, `research/`,
  `providers/`, `catalog/`, `api/` (see `docs/architecture.md` §2). Modules call each other through Python
  interfaces, never another module's tables; provider SDKs live only in their adapter.
- Import rules are enforced by `import-linter`: solver, calendar, health and routing never import agents or AI;
  only workflows import both agents and repositories; `api` imports workflows only.
- Curator endpoints live under `/v1/admin` and require the curator role.

## Options

| Option | Verdict | Why |
|---|---|---|
| A. Modular monolith API + separate mobile and admin clients over `/v1` | **Chosen** | One process to deploy and debug; in-process calls; clear contract; fits a 2 GiB host |
| B. Microservices per module | Rejected | Distributed failure modes and cost with no load that needs them |
| C. Admin pages rendered by the API | Rejected | Breaks client/server separation (CON-004) |
| D. Clients read the database directly | Rejected | Bypasses owner checks and provider-secret rules |

## Consequences

- Positive: one image, one deploy, one log stream; simple transactions (Save); fast iteration.
- Negative: a fault in one module affects the whole process; mitigated by timeouts, quotas, the single-repair rule
  and the import rules. Breaking contract changes need a new path version.

## Drivers

CON-003, CON-004, CON-005, C-008, C-012, QAS-14.
