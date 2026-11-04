---
task_id: TASK-004
wbs_element_id: WP-012
wbs_element_number: "1.3.2.2"
wbs_element_name: "Alembic revision 0003_planning"
title: "Alembic revision 0003_planning from schema.sql §7"
type: migration
slice: horizontal
priority: P1
milestone: M2
wave: "Sprint 1"
owner_role: Developer (Lê Ngọc Tấn Hiền, with coding agent under review)
estimate_days: 0.5
estimate_hours: 4
estimate_confidence: Medium
depends_on: ["TASK-003 (FS)"]
blocks: ["TASK-005"]
requirement_links: ["FR-032", "FR-040", "FR-041", "FR-042", "FR-043", "FR-044", "FR-045", "FR-046", "FR-068"]
design_links: ["CMP-016", "schema.sql §7", "data-model §9.2", "ADR-009"]
deliverable: DEL-005
risk: —
branch: feat/db-0003-planning
pr_title: "feat(db): add Alembic revision 0003_planning"
status: NOT STARTED
---

# TASK-004 — Alembic revision 0003_planning from schema.sql §7

Parent: [`WBS.md`](../WBS.md) WP-012 (1.3.2.2). Source plan: GONARRA-SDP 0.1. Prompt: `development/TaskBreakdown_ISO_21511_Prompt.md` v2.0 (adapted copy).

## 1. Objective

`alembic upgrade head` creates the private planning tables of schema.sql §7 with `fn_check_trip_day_index` and their triggers.

## 2. Context

Revision plan [Source: data-model.md §9.2]. Horizontal slice justified: schema for the planner sprint.

## 3. Scope

**In scope (closed list)**

- `apps/api/migrations/versions/20261210_0003_planning.py` executing schema.sql §7 and the §9 `updated_at` triggers of §7 tables
- Downgrade drops §7 tables in reverse order
- Extend the migration integration test

**Do not do (out of scope)**

- Do not create ORM models or endpoints
- Do not touch 0001/0002
- Do not add role grants

## 4. Inputs

- docs/04-design/data/schema.sql §7, §9
- data-model.md §9.2

## 5. Files and components touched

| Path | State |
|---|---|
| `apps/api/migrations/versions/20261210_0003_planning.py` | planned (data-model §9.2) |
| `apps/api/tests/integration/test_migrations.py` | planned (TASK-003) |

## 6. Implementation guidance

- Copy DDL verbatim; keep owner-scoped foreign keys to `accounts` as designed.
- Follow AGENTS.md: no secrets, tokens, precise locations or question text in logs; contract-first for any API change.

## 7. Acceptance criteria

Traced to: FR-032, FR-040, FR-041, FR-042, FR-043, FR-044, FR-045, FR-046, FR-068.

- **AC1.** Given a database at 0002, when `alembic upgrade head` runs, then account_preferences, trips, trip_days, trip_stops, route_legs, plan_previews, preview_revisions, guide_sessions, guide_messages, guide_message_citations, ai_invocations, idempotency_records and account_deletion_jobs exist.
- **AC2.** Given the upgraded database, when downgrade to 0002 then upgrade runs, then both succeed.

## 8. Verification

```sh
cd apps/api && uv sync --all-groups
uv run ruff check . && uv run mypy app && uv run pytest
docker compose up -d db && uv run alembic upgrade head && uv run pytest -m integration
uv run python scripts/export_openapi.py --check
uv run alembic downgrade base && uv run alembic upgrade head
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

- Triggers referencing §9 functions created in 0002 → assert dependency order

## 11. Rollback

`alembic downgrade` to 0002; revert the PR.

## 12. Dependencies and ordering notes

- Must be true before start: TASK-003 (FS).
- Unblocks: TASK-005.

## 13. Execution guardrails

- Branch `feat/db-0003-planning` from up-to-date `main`; one PR titled `feat(db): add Alembic revision 0003_planning`; Conventional Commits.
- Iteration cap: 3 agent iterations; stop and split the card if the change exceeds ~400 lines or 1 developer-day.
- Context files: `AGENTS.md`, `CLAUDE.md`, this card and its Inputs only; grep large docs by ID.
- Forbidden: push to `main`, force-push, editing BRD/PRD/design files, committing `.env*`, `plan.md`, `progress.md`, `AGENTS.md`, `CLAUDE.md`.
- Human approval point: the owner reviews the PR and decides the merge.

## 14. Open questions

- None.
