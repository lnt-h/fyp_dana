---
task_id: TASK-002
wbs_element_id: WP-010
wbs_element_number: "1.3.1"
wbs_element_name: "Verified backend foundation (local runtime evidence)"
title: "Re-verify the backend foundation locally with uv and Docker"
type: test
slice: horizontal
priority: P0
milestone: M2
wave: "Sprint 1 (may start in M0/M1 slack)"
owner_role: Developer (Lê Ngọc Tấn Hiền, with coding agent under review)
estimate_days: 0.5
estimate_hours: 4
estimate_confidence: High
depends_on: []
blocks: ["TASK-001", "TASK-003"]
requirement_links: ["FR-068", "FR-069", "NFR-014"]
design_links: ["CMP-003", "CMP-004", "CMP-014", "API-001", "API-002", "API-003"]
deliverable: DEL-005
risk: RSK-103
branch: chore/api-local-verification
pr_title: "chore(api): record local verification of the backend foundation"
status: NOT STARTED
---

# TASK-002 — Re-verify the backend foundation locally with uv and Docker

Parent: [`WBS.md`](../WBS.md) WP-010 (1.3.1). Source plan: GONARRA-SDP 0.1. Prompt: `development/TaskBreakdown_ISO_21511_Prompt.md` v2.0 (adapted copy).

## 1. Objective

All backend checks run green on the owner's machine and the evidence is recorded, so later tasks start from a verified base.

## 2. Context

The backend foundation exists but has not been re-verified on this machine; `uv` and Docker may be missing [Source: progress.md Tracker; CLAUDE.md Commands]. Horizontal slice justified: it is the enabling baseline for every API task.

## 3. Scope

**In scope (closed list)**

- Install `uv` and start Docker Desktop (owner machine)
- Run every API check in CLAUDE.md including integration tests and migration round-trip
- Apply `docs/04-design/data/schema.sql` to a scratch database as validation evidence (data-model §13 step 1)
- Fix only setup documentation in `apps/api/README.md` if a step is wrong
- Record the results in the PR body and in progress.md

**Do not do (out of scope)**

- Do not change application code or migrations
- Do not upgrade dependencies
- Do not apply schema.sql to the `gonarra` development database (use a scratch database)

## 4. Inputs

- CLAUDE.md Commands
- apps/api/README.md
- docker-compose.yml
- .github/workflows/ci.yml
- docs/04-design/data/schema.sql

## 5. Files and components touched

| Path | State |
|---|---|
| `apps/api/README.md` | existing (only if a step is wrong) |

## 6. Implementation guidance

- Scratch DB: `createdb -h localhost -U gonarra gonarra_scratch` then `psql -f docs/04-design/data/schema.sql`; drop it afterwards.
- On Apple Silicon the PostGIS image runs under amd64 emulation (docker-compose.yml comment); note the timing.
- Follow AGENTS.md: no secrets, tokens, precise locations or question text in logs; contract-first for any API change.

## 7. Acceptance criteria

Traced to: FR-068, FR-069, NFR-014.

- **AC1.** Given a clean clone with uv and Docker installed, when the API checks of CLAUDE.md run, then ruff, mypy, pytest, integration tests and the OpenAPI drift check all pass.
- **AC2.** Given the local database is up, when `alembic downgrade base && alembic upgrade head` runs, then both succeed.
- **AC3.** Given a scratch database, when schema.sql is applied, then it completes with no error and the 40 tables exist.

## 8. Verification

```sh
cd apps/api && uv sync --all-groups
uv run ruff check . && uv run mypy app && uv run pytest
docker compose up -d db && uv run alembic upgrade head && uv run pytest -m integration
uv run python scripts/export_openapi.py --check
uv run alembic downgrade base && uv run alembic upgrade head
psql -h localhost -U gonarra -d gonarra_scratch -f ../../docs/04-design/data/schema.sql && psql -h localhost -U gonarra -d gonarra_scratch -c "select count(*) from information_schema.tables where table_schema='public' and table_type='BASE TABLE'"
```

Expected: every command exits 0 (or prints nothing where stated). Any check not run is named in the PR body with the reason (AGENTS.md).

## 9. Definition of Done

- [ ] All acceptance criteria demonstrated, with evidence in the PR body
- [ ] Tests written for new logic and passing locally and in CI (or the reason they do not apply)
- [ ] CI jobs green (`gh pr checks <n> --watch`)
- [ ] PR ≤ ~400 changed lines (or the exception named in §14)
- [ ] Owner reviewed and approved the diff; merged with a merge commit on the owner's instruction
- [ ] `tasks/README.md` status, `progress.md` and traceability updated

## 10. Risks and mitigations

- schema.sql fails on the scratch DB → raise an OQ and fix in TASK-003, do not edit schema.sql here

## 11. Rollback

Nothing to roll back (no code change); drop the scratch database.

## 12. Dependencies and ordering notes

- Must be true before start: none.
- Unblocks: TASK-001, TASK-003.

## 13. Execution guardrails

- Branch `chore/api-local-verification` from up-to-date `main`; one PR titled `chore(api): record local verification of the backend foundation`; Conventional Commits.
- Iteration cap: 3 agent iterations; stop and split the card if the change exceeds ~400 lines or 1 developer-day.
- Context files: `AGENTS.md`, `CLAUDE.md`, this card and its Inputs only; grep large docs by ID.
- Forbidden: push to `main`, force-push, editing BRD/PRD/design files, committing `.env*`, `plan.md`, `progress.md`, `AGENTS.md`, `CLAUDE.md`.
- Human approval point: the owner reviews the PR and decides the merge.

## 14. Open questions

- None.
