---
task_id: TASK-003
wbs_element_id: WP-011
wbs_element_number: "1.3.2.1"
wbs_element_name: "Alembic revision 0002_catalog"
title: "Alembic revision 0002_catalog from schema.sql §1–§6, §9 (drop duplicate index)"
type: migration
slice: horizontal
priority: P0
milestone: M2
wave: "Sprint 1"
owner_role: Developer (Lê Ngọc Tấn Hiền, with coding agent under review)
estimate_days: 1.0
estimate_hours: 8
estimate_confidence: Medium
depends_on: ["TASK-002 (FS)"]
blocks: ["TASK-004", "TASK-006", "TASK-008"]
requirement_links: ["FR-002", "FR-004", "FR-009", "FR-010", "FR-011", "FR-012", "FR-013", "FR-014", "FR-015", "FR-016", "FR-056"]
design_links: ["CMP-016", "schema.sql §1–§6, §9", "data-model §9.2", "OQ-020 (closed A-023)", "ADR-003"]
deliverable: DEL-005
risk: RSK-102
branch: feat/db-0002-catalog
pr_title: "feat(db): add Alembic revision 0002_catalog from schema.sql"
status: NOT STARTED
---

# TASK-003 — Alembic revision 0002_catalog from schema.sql §1–§6, §9 (drop duplicate index)

Parent: [`WBS.md`](../WBS.md) WP-011 (1.3.2.1). Source plan: GONARRA-SDP 0.1. Prompt: `development/TaskBreakdown_ISO_21511_Prompt.md` v2.0 (adapted copy).

## 1. Objective

`alembic upgrade head` creates every catalog, curation, Guide-corpus and publication object of schema.sql §1–§6 and §9, seeds the reference data, and drops the redundant index `ix_accounts_clerk_user_id`.

## 2. Context

The data design plans three new revisions; 0002_catalog holds §1–§6 and §9 [Source: data-model.md §9.2]. OQ-020 is closed: drop `ix_accounts_clerk_user_id` in 0002, leave 0001 unchanged [Source: data-model.md OQ-020]. Horizontal slice justified: shared schema for all catalog features. Size exception EXC-001 / OQ-105.

## 3. Scope

**In scope (closed list)**

- New file `apps/api/migrations/versions/20261209_0002_catalog.py` with `down_revision` = the 0001 revision ID
- Executes the DDL of schema.sql §1–§6 and the catalog part of §9 (triggers, views, reference seed)
- `DROP INDEX IF EXISTS ix_accounts_clerk_user_id` (OQ-020)
- Downgrade drops views, functions, triggers and §2–§6 tables in reverse FK order, drops `pg_trgm`, keeps 0001 objects and recreates the dropped index
- An integration test that asserts key tables and views exist after upgrade

**Do not do (out of scope)**

- Do not edit `20261102_0001_foundation.py` or `schema.sql`
- Do not create ORM models (later, per module)
- Do not add role grants (WP-014, M3)
- Do not include §7 or §8 objects (TASK-004, TASK-005)

## 4. Inputs

- docs/04-design/data/schema.sql §0–§6, §9
- docs/04-design/data/data-model.md §9.2, §13
- apps/api/migrations/versions/20261102_0001_foundation.py
- apps/api/migrations/env.py

## 5. Files and components touched

| Path | State |
|---|---|
| `apps/api/migrations/versions/20261209_0002_catalog.py` | planned (data-model §9.2) |
| `apps/api/tests/integration/test_migrations.py` | planned |

## 6. Implementation guidance

- Use `op.execute()` with SQL copied verbatim from schema.sql; keep section comments so a reviewer can diff it.
- Do not re-create objects marked EXISTS in §0.
- Revision must be idempotent-safe on an empty DB and additive on a DB at 0001.
- Follow AGENTS.md: no secrets, tokens, precise locations or question text in logs; contract-first for any API change.

## 7. Acceptance criteria

Traced to: FR-002, FR-004, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-056.

- **AC1.** Given a database at revision 0001, when `alembic upgrade head` runs, then it succeeds and tables cities, categories, places, place_localizations, place_aliases, place_facts, sources, catalog_publications, knowledge_chunks and views vw_published_places, vw_published_place_facts, vw_guide_chunks exist.
- **AC2.** Given the upgraded database, when the index list of `accounts` is read, then `ix_accounts_clerk_user_id` is absent and `accounts_clerk_user_id_key` remains.
- **AC3.** Given the upgraded database, when `alembic downgrade 20261102_0001` then `upgrade head` runs, then both succeed (CI round-trip).
- **AC4.** Given the reference seed, when cities are counted, then five launch cities exist as defined in schema.sql.

## 8. Verification

```sh
cd apps/api && uv sync --all-groups
uv run ruff check . && uv run mypy app && uv run pytest
docker compose up -d db && uv run alembic upgrade head && uv run pytest -m integration
uv run python scripts/export_openapi.py --check
uv run alembic downgrade base && uv run alembic upgrade head
Schema diff: `pg_dump --schema-only` of the migrated DB vs a scratch DB loaded from schema.sql §0–§6, §9 shows no differences other than ordering
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

- DDL order errors → run section by section
- PostGIS/pgvector extension availability in CI → already provided by infra/postgres image

## 11. Rollback

`alembic downgrade 20261102_0001` (development only); revert the PR.

## 12. Dependencies and ordering notes

- Must be true before start: TASK-002 (FS).
- Unblocks: TASK-004, TASK-006, TASK-008.

## 13. Execution guardrails

- Branch `feat/db-0002-catalog` from up-to-date `main`; one PR titled `feat(db): add Alembic revision 0002_catalog from schema.sql`; Conventional Commits.
- Iteration cap: 3 agent iterations; stop and split the card if the change exceeds ~400 lines or 1 developer-day.
- Context files: `AGENTS.md`, `CLAUDE.md`, this card and its Inputs only; grep large docs by ID.
- Forbidden: push to `main`, force-push, editing BRD/PRD/design files, committing `.env*`, `plan.md`, `progress.md`, `AGENTS.md`, `CLAUDE.md`.
- Human approval point: the owner reviews the PR and decides the merge.

## 14. Open questions

- OQ-105 size exception (EXC-001) — owner Lê Ngọc Tấn Hiền; due per SDP Appendix E or source document
